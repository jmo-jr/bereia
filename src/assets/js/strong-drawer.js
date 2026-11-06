(() => {
  const drawer = document.querySelector('#strong-drawer');
  if (!drawer) return;
  const title = drawer.querySelector('h1');
  const body = drawer.querySelector('.drawer-body');
  let request;
  let trigger;
  let revision = 0;
  const normalizeGreek = value =>
    value.normalize('NFD').replace(/\p{M}/gu, '').toLocaleLowerCase('el');

  function load() {
    if (!request) {
      request = fetch(drawer.dataset.lexicoUrl)
        .then(response => {
          if (!response.ok) throw new Error('Não foi possível carregar o léxico.');
          return response.json();
        })
        .catch(error => {
          request = undefined;
          throw error;
        });
    }
    return request;
  }

  function element(tag, text, className) {
    const node = document.createElement(tag);
    node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  function section(label, text, className) {
    if (text === undefined || text === null || text === '') return;
    body.append(element('h3', label), element('p', text, className));
  }

  function morphologySection(morphology) {
    if (typeof morphology !== 'string' || !morphology.trim()) return;

    const parts = morphology.split(/\s+-\s+/).map(part => part.trim());
    const grammaticalClass = parts.shift();
    const details = [];
    const isVerb = grammaticalClass.toLowerCase() === 'verbo';
    const ending = (isVerb ? parts.slice(1) : parts).join(' - ');
    const rows = [['Classe gramatical', grammaticalClass]];

    if (isVerb) {
      const verbFeatures = (parts[0] || '').split(/\s+/).filter(Boolean);
      if (verbFeatures[0]) rows.push(['Tempo', verbFeatures[0]]);
      if (verbFeatures[1]) rows.push(['Modo', verbFeatures[1]]);
      if (verbFeatures.length > 2) rows.push(['Voz', verbFeatures.slice(2).join(' ')]);
    }

    const personMatch = /^(\d+[ªº]?\s+Pessoa)\s+(.+)$/u.exec(ending);
    if (personMatch) {
      rows.push(['Pessoa', personMatch[1]], ['Número', personMatch[2]]);
    } else {
      const grammaticalFeatures = ending.split(/\s+/).filter(Boolean);
      if (grammaticalFeatures.length >= 3) {
        rows.push(
          ['Caso', grammaticalFeatures[0]],
          ['Gênero', grammaticalFeatures[1]],
          ['Número', grammaticalFeatures.slice(2).join(' ')]
        );
      } else if (ending) {
        details.push(ending);
      }
    }

    if (details.length) rows.push(['Detalhes', [...new Set(details)].join(' — ')]);

    const list = document.createElement('ul');
    for (const [label, value] of rows) {
      const item = document.createElement('li');
      item.append(element('strong', label + ':'), ' ', document.createTextNode(value));
      list.append(item);
    }
    body.append(element('h3', 'Morfologia'), list);
  }

  function close() {
    revision += 1;
    drawer.hidden = true;
    drawer.classList.remove('is-open');
    trigger?.setAttribute('aria-expanded', 'false');
    trigger?.focus();
  }

  drawer.querySelector('.close-drawer').addEventListener('click', close);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !drawer.hidden) close();
  });

  document.addEventListener('click', event => {
    if (!drawer.hidden && event.target instanceof Node && !drawer.contains(event.target)) close();
  });

  document.addEventListener('click', async event => {
    const link = event.target.closest('a[data-strong]');
    if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    trigger?.setAttribute('aria-expanded', 'false');
    trigger = link;
    const current = ++revision;
    const strong = link.dataset.strong.trim().replace(/^G0+(?=\d)/, 'G');
    const token = link.closest('.token');
    const word = token?.querySelector('.greek')?.textContent.trim();
    link.setAttribute('aria-controls', drawer.id);
    link.setAttribute('aria-expanded', 'true');
    title.replaceChildren(element('span', strong, 'strong-chip'));
    body.replaceChildren(element('p', 'Carregando verbete…'));
    drawer.hidden = false;
    drawer.classList.add('is-open');
    drawer.scrollTop = 0;
    drawer.focus();
    try {
      const data = await load();
      if (current !== revision) return;
			// Dados da entrada principal (lema)
      const entry = data.verbetes[strong];
			console.log(entry);
      if (!entry) throw new Error('Verbete não encontrado no léxico.');
			// Título (Strong Lema)
      title.append(document.createTextNode(' ' + entry.lema));
      body.replaceChildren();
			// Dados do array 'flexoes'
      const forms = entry.flexoes.filter(
				form => word && normalizeGreek(form.grego) === normalizeGreek(word)
			);

      for (const form of forms) {
				// Forma (Transliteração)
				if (word) {
					const heading = document.createElement('h2');
					const greek = element('span', word, 'greek-term');
					const transliteration = element('em', form.transliteracao);
					heading.append(greek, ' (', transliteration, ')');
					body.append(heading);
				}
        // Morfologia
			  morphologySection(form.morfologia);
				// Traduções
        if (form.verbete) {
					section('Traduções', form.verbete);
				} else if (entry.verbete) {
					section('Traduções', entry.verbete);
				}
				// Ocorrências
				const numNt = element('strong', form.ocorrencias);
				const numLxx = element('strong', form.ocorrencias_lxx);
        body.append(element('h3', 'Ocorrências da forma'));
				const ntCount = element('p', '', 'ocorrencias');
				ntCount.append(numNt, ' no Texto Majoritário do NT');
				body.append(ntCount);
				const lxxCount = element('p', '');
				lxxCount.append(numLxx, ' na LXX');
				body.append(lxxCount);
      }
			// Se array 'flexoes' vazio (altamente improvável)
      if (!forms.length) {
			  morphologySection(token?.querySelector('.refs')?.getAttribute('title'));
        section('Tradução da ocorrência', token?.querySelector('.translate')?.textContent);
      }
      //section('Verbete', entry.verbete);
      if (entry.verbetes) section('Variantes do verbete', entry.verbetes.join('\n'));
			// Etimologia
      section('Etimologia e significado', entry.nota);
			// Traduz o hebraico
      if (entry.hebraico.length) {
        body.append(element('h3', 'Traduz o hebraico'));
        for (const item of entry.hebraico) {
          body.append(element('p', item.texto, 'hebrew-words'));
        }
      }
			// Outras flexões
      section('Outras flexões de ' + entry.lema, [...new Set(entry.flexoes.map(form => form.grego))].join(', '), 'greek-words');
    } catch (error) {
      if (current !== revision) return;
      body.replaceChildren(element('p', error.message));
      const fallback = element('a', 'Consultar a fonte externa');
      fallback.href = link.href;
      fallback.target = '_blank';
      fallback.rel = 'noopener';
      body.append(fallback);
    }
  });
})();