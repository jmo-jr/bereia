# Aplicação das bases TBESG — etapa 2

- Livros ativos: 39.
- Ocorrências sem correspondência no dicionário principal: 74.603.
- Preenchimentos da beta anterior preservados: 63,191 ocorrências.
- Novos preenchimentos: 9,653 ocorrências.
- Total com preenchimento complementar: 72,844 ocorrências.
- Restantes sem tradução: 1,759 ocorrências.

Dos novos preenchimentos, 9.502 usam as bases por identificador TBESG da etapa 1;
151 usam bases portuguesas já disponíveis cujo processamento de flexão foi
corrigido/ampliado. A contagem de preenchimentos inclui nomes transliterados
herdados da beta anterior; esta etapa não criou traduções de nomes próprios.

## Validação

Os testes abrangem particípios ativos/passivos, concordância, infinitivos,
verbos intransitivos, ordinais compostos, numerais, referências, apresentação
sem Strong e coerência dos totais. Repetir a geração manteve o mesmo SHA-256 do
suplemento. Os hashes confirmam preservação do léxico principal, dos 39 livros
gregos convertidos e dos respectivos originais.

## Limites

As análises continuam sendo as do lxx-morph e as flexões portuguesas são de
versão beta. Não foram inferidas análises não reconhecidas. Os 13 verbetes
INCERTO da etapa 1 permanecem bloqueados (39 ocorrências). As traduções anteriores
à etapa 2 não foram refeitas. O campo Morph da TBESG não substitui a análise da
palavra na ocorrência. Não foram adicionados identificadores Strong à apresentação.

## Pendências por motivo

- Sem base portuguesa adequada: 1,685 ocorrências.
- Análise original não reconhecida; flexão não inferida: 17 ocorrências.
- Base não reconhecida como infinitivo português: 16 ocorrências.
- Verbete INCERTO no cadastro de bases; aplicação automática bloqueada: 39 ocorrências.
- Análise verbal incompleta: 2 ocorrências.

O relatório JSON contém os itens efetivamente aplicados; o CSV corrente contém
apenas lacunas. As auditorias anteriores e o cadastro da etapa 1 foram mantidos.
