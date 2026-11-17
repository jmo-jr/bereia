# LXX beta — etapa 4

Rodada de revisão dos gentílicos mais frequentes e de φοβέομαι.
As escolhas são editoriais para a beta, não correções do texto grego.

- 416 ocorrências examinadas, agrupadas por forma, lema, análise e classe.
- 394 ocorrências preenchidas: 309 de gentílicos e 85 de φοβέομαι.
- 73.163 ocorrências anteriormente preenchidas preservadas integralmente.
- O suplemento cobre agora 73.557 ocorrências; restam 1.046 sem tradução.
- Das ocorrências examinadas, 22 continuam INCERTO. As demais lacunas ainda
  precisam de investigação em rodadas posteriores.

## Alterações aplicadas

- Ἀσσύριος: 117 ocorrências.
- Ἀμορραῖος: 66 ocorrências.
- φοβέομαι: 85 ocorrências.
- χαναναῖος: 12 ocorrências.
- Χετταῖος: 36 ocorrências.
- Χαναναῖος: 26 ocorrências.
- Γεργεσαῖος: 12 ocorrências.
- Φερεζαῖος: 16 ocorrências.
- Εὐαῖος: 7 ocorrências.
- Μωαβίτης: 11 ocorrências.
- Μωαβῖτις: 4 ocorrências.
- Ευαῖος: 1 ocorrências.
- Χετταία: 1 ocorrências.

As traduções incluem assírio, amorreu, heteu/heteia, cananeu, ferezeu,
girgaseu, heveu e moabita, com concordância e preposições próprias de cada
forma revisada. Os identificadores usados no relatório são internos à revisão;
não são números Strong e não geram links ou detalhes lexicais na interface.

Para φοβέομαι, a leitura lexical média/passiva “temer” é traduzida por formas
ativas portuguesas, como “temerás”, “temi” e “temendo”. Isso não muda a voz grega
registrada na morfologia. A distinção foi fundamentada na definição de G5399
da TBESG e no uso do dicionário BEREIA: ἐφοβήθη → “temeu”, ἐφοβήθησαν →
“temeram” e φοβεῖσθε → “temeis/temei”. As formas foram conferidas nos JSONs
do Texto Majoritário, incluindo Mt 2:22; 17:6; Mc 4:41 e 1Pe 2:17.
O ativo causativo φοβῆσαι, em 2Cr 32:18, permanece pendente.

## Pendências examinadas

- Sentido territorial ou grupo que mistura pessoa e território; exige decisão por ocorrência: 15 ocorrências.
- Grupo inclui Os 4:18: gentílico ou sentido de mercadores; revisão por ocorrência: 3 ocorrências.
- Gênero da análise original não esclarecido no contexto coletivo/territorial; revisão manual: 3 ocorrências.
- Infinitivo ativo causativo em 2Cr 32:18; não aplicar a equivalência média/passiva temer: 1 ocorrências.

Μωαβῖτις ficou preenchido apenas nos grupos inequivocamente referentes a
mulheres: Μωαβίτιδας (Rt 1:4; 1Rs 11:1; 2Esd 23:23) e Μωαβῖτίς (Rt 2:6).
Os grupos restantes incluem o território em Isaías/Jeremias ou compartilham
forma/análise entre pessoa e território; nenhum significado foi propagado a eles.

A forma Χαναναίους com lema χαναναῖος também reúne Os 4:18 e outros contextos.
O léxico consultado admite o sentido de mercador; o grupo permanece pendente,
sem impor uma tradução comum a todas as suas ocorrências.

A análise feminina de Ἀσσυρίων (Zc 10:10–11) e Φερεζαίων (Êx 13:5) foi
preservada sem tradução adicional nesta rodada. Não se alterou o parsing por
preferência nem se presumiu uma correção da fonte.

## Fontes e reprodução

- [GreekDoc: assírios](https://greekdoc.com/names/as.html),
  [amorreus](https://greekdoc.github.io/names/am.html),
  [heteus](https://greekdoc.github.io/names/ce.html),
  [cananeus](https://greekdoc.github.io/names/ca.html),
  [ferezeus](https://greekdoc.github.io/names/fe.html),
  [girgaseus](https://greekdoc.github.io/names/ge.html),
  [heveus](https://greekdoc.github.io/names/eu.html) e
  [moabitas](https://greekdoc.github.io/names/mw.html).
- TBESG local: Tyndale House e STEPBible.org, CC BY 4.0, verbete G5399.
- Dicionário BEREIA e textos gregos originais do projeto.

`tools/lxx/reviewed_step4.json` guarda as decisões explícitas, as fontes e
o conjunto completo de referências de cada grupo. A geração rejeita auditoria,
contagens ou referências divergentes. Não há classificação automática de sentidos
por contexto, nem substituição de nomes próprios.

`lxx-beta-etapa4.json` registra os preenchimentos; `lxx-beta-pendencias.csv`
contém somente pendências não aplicadas. Os relatórios das etapas 2 e 3 e os
13 verbetes INCERTO do cadastro de bases foram preservados.

## Validação

- 13 testes Python e 2 testes Node aprovados.
- Regeneração idempotente; todas as traduções das etapas anteriores preservadas.
- Textos gregos do AT/NT e léxico principal preservados por hash.
- Build de produção concluído com saída 0: 1.422 arquivos em 98,12 segundos.
- Conferidos no HTML os exemplos Χετταίου → “do heteu” (Gn 25),
  φοβηθήσῃ → “temerás” (Dt 6) e Μωαβῖτίς → “moabita” (Rt 2),
  todos com âncora Strong vazia.
- `dict:check`, `dict:review-state` e `dict:review-state:check` aprovados.

O build sincronizou automaticamente o dicionário derivado com valores já
existentes no léxico principal. Não houve edição do léxico nesta tarefa.
A auditoria `lxx-tbesg-cobertura-etapa4.json` acompanha esse derivado atualizado;
comparada com a auditoria anterior, conserva exatamente registros, referências,
lexicon, fontes gregas, contagens e cobertura. O suplemento continuou idêntico
ao utilizado no build validado.
