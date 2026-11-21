# Alinhamento lexical do BEREIA

O piloto acrescenta tooltips à tradução publicada de Mateus 8, em
`src/biblia/nt/mateus/8.liquid`. O shortcode `verse` usa os tokens do Texto
Majoritário em `src/interlinear/nt/MT.json` e consulta o léxico organizado
por Strong em `src/_data/nt/dict_lex_nt-lxx_greek-pt.json`, por meio do índice
de formas que o build já gera. O campo `lemma` do TM contém a grafia da
ocorrência. O tooltip mostra essa grafia e usa a transliteração, a morfologia
e o verbete da entrada confirmada.

## Executar

```sh
npm ci
npm run test:alignment
npm run build
```

Abra `_site/biblia/mateus/8/index.html` pelo servidor do projeto (`npm run serve`).
As palavras alinhadas abrem o tooltip ao passar o ponteiro, receber foco ou
ser ativadas por teclado ou toque. Use **Escape** ou toque fora para fechar.
A página interlinear continua usando a consulta existente.

O build gera três relatórios em `reports/lexical-alignment/mt-8/`:

- `coverage.json` agrupa as pendências e as inserções editoriais por palavra.
  As sugestões mostram sua evidência. A lista de formas presentes no
  versículo serve de contexto para revisão.
- `ambiguities.json` registra candidatas, lemas, Strong, resoluções por
  exceção e problemas de validação.
- `summary.json` conta tokens, resoluções, pendências e a cobertura
  confirmada. As assinaturas dos versículos ficam em `verseSignatures`.

Esses arquivos são reconstruídos pelo build. Use um build completo para
atualizar o piloto após alterar os dados lexicais.

## Regras de alinhamento

- A posição começa em 1 e conta palavras e números no corpo do versículo.
  Número do versículo, títulos, notas ocultas ou semânticas e pontuação
  isolada ficam fora. Palavras visíveis em colchetes contam e são
  identificadas como inserções editoriais. Contrações, hífens e apóstrofos
  internos mantêm um token. A marcação inline e as entidades HTML são
  interpretadas antes da contagem.
- O alinhamento compara palavras e expressões inteiras de `pt` e
  `traducao`. Uma expressão confirmada pode ligar várias palavras PT à
  mesma flexão. Alternativas de uma palavra separadas por barra são
  reconhecidas. Palavras gramaticais que só coincidem com uma alternativa
  em `traducao` exigem revisão contextual. O verbete oferece sugestões.
- A consulta começa pela grafia exata. Caixa e alternância entre grave e
  agudo são admitidas fora das exceções do projeto. Outras diferenças de
  diacríticos podem gerar sugestões, sempre sem confirmação automática.
  Repetições da mesma análise no versículo são agrupadas. Análises
  concorrentes continuam pendentes. Uma forma já dentro de um controle ou
  tooltip existente é contada, mas o build evita aninhar controles.
- Sinônimos aprovados entram no campo da flexão correspondente do léxico.
  Depois de editar a fonte lexical, rode o build novamente. Cada pendência
  é uma ocorrência a revisar e pode ter origem lexical, sintática ou
  editorial.

## Revisar exceções

1. Consulte `ambiguities.json`, a tradução exibida e o TM. Confira a
   ocorrência portuguesa, a forma grega e sua análise.
2. Em `exceptions.json`, mantenha a estrutura
   `palavra PT → forma grega do TM → ["Livro capítulo:versículo:posição"]`.
   Para múltiplos termos gregos no mesmo tooltip, repita a referência em
   cada forma. A referência repetida dentro de um mesmo array é inválida.
3. Após conferir as posições, copie a assinatura do versículo em
   `summary.json` para `approved-verses.json`. Esse arquivo conserva a
   sequência aprovada por meio da assinatura. Alterações de palavras ou de
   sua ordem suspendem as exceções do versículo até nova conferência. Tags
   e pontuação que preservam a tokenização permitem continuar usando a
   assinatura original.
4. Rode o build e confira a validação. Se a mesma forma grega tiver várias
   análises no versículo, o JSON exige que o TM identifique uma delas antes
   que a grafia possa resolver a exceção. Se a exceção se tornar redundante
   após uma revisão lexical, remova-a e retire sua assinatura quando o
   versículo ficar sem exceções.

## Resultado do piloto

| Métrica | Total |
|---|---:|
| Versículos | 34 |
| Tokens portugueses | 797 |
| Associações automáticas | 540 |
| Associações pelo JSON | 6 |
| Tokens ligados a mais de um termo grego | 1 |
| Inserções editoriais sem equivalente | 3 |
| Pendências lexicais | 158 |
| Ambiguidades em aberto | 90 |
| Ocorrências gregas sem flexão identificada | 40 |
| Cobertura confirmada | 68,51% |

As associações manuais de teste incluem `da` em Mt 8:1:5 → `ἀπὸ` +
`τοῦ`, e os dois `vai` em Mt 8:9:18 e 8:9:20 → `Πορεύθητι` e
`πορεύεται`. `leproso` em Mt 8:2:5 → `λεπρὸς` é automático.
A cobertura contabiliza o resultado das regras do piloto e das seis
exceções conferidas. A auditoria lexical das demais ocorrências continua
em aberto.
