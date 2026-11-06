# Geração de rascunhos de tradução

O script `tools/biblech/traduz_capitulos.py` monta, por padrão, rascunhos mecânicos
locais, sem API, sem chave e sem cobrança de geração. Requer Python 3.10 ou superior,
sem bibliotecas adicionais. A tradução contínua e as decisões linguísticas serão
feitas na revisão posterior; esta montagem não equivale à tradução assistida produzida
nos capítulos anteriores.

## Fluxo recomendado: local e sem API

Na raiz do repositório:

```sh
python3 -B tools/biblech/traduz_capitulos.py --chapters 14-28 --resume
```

O script copia glosas do dicionário na ordem do grego, separadas por ` | `, para
`reports/traducao/mateus/N/N.txt`. Não resolve concordância, sintaxe, polissemia ou
expressões idiomáticas. Se a correspondência de grafia não for única, escreve
`[INCERTO: forma]` sem escolher entre os candidatos. Mesmo uma correspondência única
precisa de revisão contextual. As traduções alternativas da própria glosa são mantidas.

Cada pasta contém `alinhamento.json`, com grego original, Strong e morfologia do TM,
candidatos e glosas originais, além de `decisoes.md` com as pendências e `manifest.json`
com hashes e estado de revisão. As referências editoriais são preservadas no pacote
para a revisão posterior; o modo local não tenta imitar seu estilo por heurísticas.
Depois, peça a revisão dos rascunhos para transformá-los em tradução contínua.

Mesmo se houver `OPENAI_API_KEY`, `OPENAI_MODEL` ou `--model`, o modo padrão não
chama a API. **Somente `--use-api` ativa o modo pago opcional.**

Não edita dicionários, capítulos existentes, decisões gerais ou arquivos de publicação.
Não cria backups nem faz commits. Nenhum resultado é declarado aprovado. Os testes
estruturais não verificam se cada decisão de tradução é linguisticamente correta.

## Preparar sem usar a API

Na raiz do repositório:

```sh
python3 -B tools/biblech/traduz_capitulos.py --chapters 14-28 --prepare-only
```

Isso grava os pacotes em `reports/traducao/mateus/preparacao/`, sem chave e sem
requisições externas. Cada pacote inclui a requisição completa, o grego, a análise
morfológica do CSV, candidatos do dicionário para cada forma, protocolo, decisões
gerais e referência editorial. É possível inspecioná-lo antes da geração.

O protocolo ainda menciona o caminho antigo do dicionário. O script detecta primeiro
`src/_data/nt/dict_flex_nt-lxx_greek-pt.json`, localização atual do derivado usado no
interlinear, e depois o caminho antigo. Registra o caminho efetivamente consultado
no pacote e os hashes no manifesto. Não usa cópias históricas de `tools` ou backups,
nem regenera o dicionário. É possível informar `--dictionary CAMINHO` explicitamente.

## Modo opcional pago: gerar tradução assistida pela API

Este modo não é necessário para o fluxo local acima. Use outra pasta de saída para
não misturar rascunhos mecânicos com traduções assistidas.

Configure a chave de API no ambiente, sem escrevê-la em arquivos do repositório.
No zsh do macOS, este comando solicita a chave sem exibi-la na tela:

```sh
read -rs 'OPENAI_API_KEY?Chave da API: '
export OPENAI_API_KEY
echo
```

Escolha um identificador de modelo disponível na sua conta que aceite Responses
API e saídas estruturadas JSON Schema. O script não presume um modelo nem seu custo.
Substitua `SEU_MODELO` no comando:

```sh
python3 -B tools/biblech/traduz_capitulos.py \
  --chapters 14-28 \
  --use-api \
  --model SEU_MODELO \
  --output reports/traducao/mateus-api \
  --resume
```

O modelo decide a redação a partir das fontes fornecidas. A chave é enviada apenas
ao endpoint fixo `https://api.openai.com/v1/responses`. O conteúdo dos capítulos,
recortes do dicionário e referências é enviado à API; a requisição usa `store: false`.
Não há execução de ferramentas nem escrita no projeto por parte do modelo.
Chamadas de geração consomem a API. A execução é sequencial, um capítulo por chamada;
repetições de HTTP 429/5xx podem produzir novas chamadas. Teste primeiro um capítulo:

```sh
python3 -B tools/biblech/traduz_capitulos.py --chapters 14 --use-api \
  --model SEU_MODELO --output reports/traducao/mateus-api --resume
```

Depois execute o intervalo completo com a mesma configuração. `--resume` verifica
os hashes e pula o capítulo já concluído. Não pula arquivos alterados nem resultados
feitos com outras fontes, referências, versão do script, modelo ou configurações.
O campo de aprovação continua pendente, inclusive após a retomada.

`--reasoning high` é opcional, somente para modelos que suportem esse parâmetro.
O padrão é não enviar a configuração de raciocínio. Se a resposta ficar incompleta,
ajuste `--max-output-tokens` (padrão: 24000), conforme os limites do modelo. Esse teto
também pode ser consumido pelo raciocínio do modelo. O timeout padrão é 600 segundos;
`--timeout` e `--retries` podem ser ajustados. Conexões interrompidas não são repetidas
automaticamente, pois o servidor pode já ter processado a chamada.

## Arquivos de saída

No modo local, cada capítulo concluído fica em sua própria pasta (o modo API usa
a pasta escolhida, e não produz `alinhamento.json`):

```text
reports/traducao/mateus/14/
  14.txt
  decisoes.md
  alinhamento.json
  request.json
  response.json
  manifest.json
```

- `14.txt`: glosas mecânicas compatíveis com o conversor; no modo API, tradução proposta.
- `decisoes.md`: pendências locais; no modo API, escolhas propostas pelo modelo.
- `alinhamento.json`: formas, análises do TM e candidatos, somente no modo local.
- `request.json`: pacote de fontes; somente no modo API é enviado ao servidor.
- `response.json`: indicador de execução local; no modo API, resposta do servidor.
- `manifest.json`: hashes, modo de geração e estado de aprovação pendente.

Respostas recusadas, incompletas ou estruturalmente inválidas são preservadas em
`falhas/`, sem gerar um TXT aceito. Corrija a causa e execute novamente. Nenhum reparo
linguístico ou nova chamada é feito silenciosamente. Em caso de interrupção durante
a gravação, uma pasta incompleta pode permanecer; escolha outra pasta `--output`
ou mova a pasta incompleta para inspeção antes de tentar de novo. Não use `--resume`
para ignorar arquivos editados manualmente.

Arquivos de preparação não são respostas prontas e não substituem as fontes na
geração seguinte: o script as relê. Se você preparou sem `--model`, o pacote contém
um marcador de modelo no modo API; a geração paga usa o modelo explicitamente escolhido. Preparações
com configurações diferentes exigem outra pasta `--output`, pois não são sobrescritas.

## Referências aprovadas e outros livros

Por padrão, o script usa somente `src/biblia/nt/mateus/8.txt` como exemplo de estilo
aprovado, além do protocolo e das decisões gerais. Os capítulos 9–13 e suas escolhas
propostas não são promovidos automaticamente a padrões. Para acrescentar referências
que você tenha aprovado, repita `--reference` (ao usá-lo, a lista substitui o padrão):

```sh
python3 -B tools/biblech/traduz_capitulos.py --chapters 14-28 \
  --reference src/biblia/nt/mateus/8.txt \
  --reference src/biblia/nt/mateus/9.txt \
  --output reports/traducao/mateus-nova-rodada
```

Para outro livro, informe conjuntamente `--source`, `--morphology`, `--book-name`,
`--output` e referências aprovadas adequadas. `--chapters all` seleciona todos os
capítulos desse JSON; intervalos como `1-4,7` também são aceitos. Os identificadores
de arquivo do JSON e do CSV podem diferir: por exemplo, Mateus usa `MT.json` e `MAT.csv`.
O script compara a sequência de formas das duas fontes por versículo e interrompe
se divergir; não escolhe uma variante silenciosamente.

As buscas lexicais mantêm os registros candidatos, inclusive homógrafos, e distinguem
coincidência exata de normalização. A remoção de diacríticos serve só à busca de
candidatos; a escolha morfológica cabe à análise e fica sujeita à revisão humana.

## Testes locais

```sh
python3 -B -m unittest discover -s tests -p test_traduz_capitulos.py -v
```

Os testes usam respostas artificiais; não fazem chamadas pagas. A validação local
confere numeração, perícopes, correspondência TM/CSV, compatibilidade com o conversor,
aspas/colchetes, retomada e proteção contra sobrescrita. Não avalia exegese ou tradução.

Implementação baseada na documentação oficial OpenAI:
[Responses e saídas estruturadas](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).
