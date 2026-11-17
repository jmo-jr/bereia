# AncientBible em inglês — avaliação e propostas para revisão

## Integridade

O arquivo `../bibliaaberta/sources/ancientbible-corcordance_en.json` é JSON
válido. Todos os 17.771 registros têm seis campos e foram lidos integralmente.
Não foi necessário recuperar prefixos nem reparar a fonte.

## Cobertura

A lista atual da LXX contém 563 lemas e 1.046 ocorrências pendentes.

- 23 lemas correspondem exatamente após normalização Unicode NFC: 82 ocorrências.
- 2 lemas estão explicitamente listados entre variantes do cabeçalho: 7 ocorrências.
- 1 lema coincide ao ignorar caixa/sigma final: 6 ocorrências.
- 1 lema é apenas candidato após retirar diacríticos: 1 ocorrência.
- Total das buscas em grego: 27 lemas / 96 ocorrências.
- Incluindo candidatos adicionais por transliteração e identificador TBESG:
  41 lemas / 112 ocorrências, distribuídos em 44 pares para revisão.
- 522 lemas ficam separados em `sem_candidato`.

A melhoria principal é a integridade do arquivo e de seus campos. A glosa
inglesa e o identificador coincidem exatamente com os da TBESG local em 42
dos 44 pares. As exceções são ἄκρα e καλέω. Essa coincidência não comprova a
origem do arquivo, mas mostra que as glosas oferecem pouca evidência nova para
resolver os casos já marcados como INCERTO.

## Arquivo para revisão

`lxx-ancientbible-en-revisao.json` contém, em cada par:

- `termo_faltante`: lema pendente na LXX.
- `candidato_concordance`: cabeçalho original da fonte inglesa.
- `traducao_concordance`: glosa inglesa intacta.
- `traducao_proposta_pt`: tradução portuguesa da glosa, sem aprovação contextual.
- `traducao_revisada`: campo vazio para a revisão humana.
- `aplicar`: inicialmente `false`.
- Referências, formas, identificador da fonte e alertas de ambiguidade.

As propostas não convertem uma glosa problemática em tradução aprovada do
grego. Por exemplo, “to cure” foi traduzido como “curar” e “templecourtesans”
como “cortesãs do templo”, mantendo o alerta de que os respectivos verbetes
continuam INCERTO no cadastro. Homógrafos e candidatos que diferem do lema
grego também estão assinalados; nenhum deles foi escolhido automaticamente.

Para conferir o termo inglês “woad”, foi consultada a nomenclatura portuguesa
registrada em [All About Woad](https://www.woad.org.uk/html/etymology.html).
A proposta “pastel-dos-tintureiros” traduz a glosa inglesa, sem validar sua
associação com ἀνθράκινος.

## Reprodução

```sh
python3 -B tools/lxx/audit_ancientbible.py ../bibliaaberta/sources/ancientbible-corcordance_en.json --output tools/relatorios/lxx-ancientbible-en-cobertura.json
python3 -B tools/lxx/prepare_ancientbible_review.py --audit tools/relatorios/lxx-ancientbible-en-cobertura.json --output tools/relatorios/lxx-ancientbible-en-revisao.json --translations tools/lxx/ancientbible_en_glosses_pt.json
```

Foram conferidos os campos originais de todos os pares, a cobertura dos 563
lemas e das 1.046 ocorrências e o hash da fonte. Todas as propostas estão
preenchidas; todos os campos de revisão continuam vazios e `aplicar: false`.
Os arquivos de revisão anteriores foram preservados. Nenhuma tradução foi
aplicada ao suplemento, aos livros ou ao dicionário.
