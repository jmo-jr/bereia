# Revisão dos 48 alertas de voz

Foram examinados os 48 alertas anteriores: 47 registros corrigidos (38 com voz ativa e nove com voz média), em 94 campos técnicos. Um registro genérico foi preservado e retirado da categoria indevida de omissão de voz.

## Critérios e limites

- Preservadas todas as demais características das análises. Não foram combinados casos, gêneros, pessoas ou números nesta rodada.
- Nos futuros de εἰμί e πάρειμι, a voz é média. O código Robinson D identifica média deponente; não foi convertido em ativa nem estendido a outras famílias.
- Sete registros não têm parsing auxiliar integralmente alinhado para a grafia exata. A decisão sobre voz usa o paradigma e a identificação lexical; não se atribui parsing auxiliar a essas ocorrências.
- Grafias sem ocorrência literal no TM foram preservadas; não foi removido nenhum diacrítico para provar identidade.
- A tradução portuguesa não foi usada para inferir voz e permaneceu intacta.

## Registro genérico G1507

`εἱλίσσω` está registrado com `abrev_morf: V`, `morfologia: Verbo`, contagem NT vazia e sem ocorrência literal/NFC no TM. Isso informa a classe verbal, não uma análise de tempo/modo/pessoa à qual faltaria voz. O registro permanece inteiramente preservado e explicitamente contado como genérico no auditor. Não foi inventada uma flexão nem uma ocorrência NT.

## Alterações aplicadas

- **G1510/0 — εἶ**: `V-PI-2S` → `V-PIA-2S`; `Verbo - Presente Indicativo Ativa - 2ª Pessoa Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/2 — εἰμί**: `V-PI-1S` → `V-PIA-1S`; `Verbo - Presente Indicativo Ativa - 1ª Pessoa Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/3 — εἶναί**: `V-PN` → `V-PNA`; `Verbo - Presente Infinitivo Ativa`. Base: parsing alinhado e paradigma copular.

- **G1510/4 — εἰσίν**: `V-PI-3P` → `V-PIA-3P`; `Verbo - Presente Indicativo Ativa - 3ª Pessoa Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/5 — ἔσεσθαι**: `V-FN` → `V-FNM`; `Verbo - Futuro Infinitivo Média`. Base: parsing alinhado e paradigma copular.

- **G1510/6 — ἔσεσθέ**: `V-FI-2P` → `V-FIM-2P`; `Verbo - Futuro Indicativo Média - 2ª Pessoa Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/7 — ἔσῃ**: `V-FI-2S` → `V-FIM-2S`; `Verbo - Futuro Indicativo Média - 2ª Pessoa Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/8 — ἐσμέν**: `V-PI-1P` → `V-PIA-1P`; `Verbo - Presente Indicativo Ativa - 1ª Pessoa Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/9 — ἔσομαι**: `V-FI-1S` → `V-FIM-1S`; `Verbo - Futuro Indicativo Média - 1ª Pessoa Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/10 — ἐσόμεθα**: `V-FI-1P` → `V-FIM-1P`; `Verbo - Futuro Indicativo Média - 1ª Pessoa Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/11 — ἐσόμενον**: `V-FP-ANS` → `V-FPM-ANS`; `Verbo - Futuro Particípio Média - Acusativo Neutro Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/12 — ἔσονταί**: `V-FI-3P` → `V-FIM-3P`; `Verbo - Futuro Indicativo Média - 3ª Pessoa Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/13 — ἔσται**: `V-FI-3S` → `V-FIM-3S`; `Verbo - Futuro Indicativo Média - 3ª Pessoa Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/14 — ἐστέ**: `V-PI-2P` → `V-PIA-2P`; `Verbo - Presente Indicativo Ativa - 2ª Pessoa Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/15 — ἐστί**: `V-PI-3S` → `V-PIA-3S`; `Verbo - Presente Indicativo Ativa - 3ª Pessoa Singular`. Base: paradigma copular e identificação lexical; sem parsing contextual alinhado.

- **G1510/16 — ἐστίν**: `V-PI-3S` → `V-PIA-3S`; `Verbo - Presente Indicativo Ativa - 3ª Pessoa Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/17 — ἔστω**: `V-PM-3S` → `V-PMA-3S`; `Verbo - Presente Imperativo Ativa - 3ª Pessoa Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/18 — ἔστωσαν**: `V-PM-3P` → `V-PMA-3P`; `Verbo - Presente Imperativo Ativa - 3ª Pessoa Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/31 — ὂν**: `V-PP-NNS` → `V-PPA-NNS`; `Verbo - Presente Particípio Ativa - Nominativo Neutro Singular`. Base: paradigma copular e identificação lexical; sem parsing contextual alinhado.

- **G1510/32 — ὄντα**: `V-PP-AMS` → `V-PPA-AMS`; `Verbo - Presente Particípio Ativa - Acusativo Masculino Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/33 — ὄντας**: `V-PP-AMP` → `V-PPA-AMP`; `Verbo - Presente Particípio Ativa - Acusativo Masculino Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/34 — ὄντες**: `V-PP-NMP` → `V-PPA-NMP`; `Verbo - Presente Particípio Ativa - Nominativo Masculino Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/35 — ὄντι**: `V-PP-DMS` → `V-PPA-DMS`; `Verbo - Presente Particípio Ativa - Dativo Masculino Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/36 — ὄντος**: `V-PP-GMS` → `V-PPA-GMS`; `Verbo - Presente Particípio Ativa - Genitivo Masculino Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/37 — ὄντων**: `V-PP-GMP` → `V-PPA-GMP`; `Verbo - Presente Particípio Ativa - Genitivo Masculino Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/38 — οὖσα**: `V-PP-NFS` → `V-PPA-NFS`; `Verbo - Presente Particípio Ativa - Nominativo Feminino Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/39 — οὖσαι**: `V-PP-NFP` → `V-PPA-NFP`; `Verbo - Presente Particípio Ativa - Nominativo Feminino Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/40 — οὖσαν**: `V-PP-AFS` → `V-PPA-AFS`; `Verbo - Presente Particípio Ativa - Acusativo Feminino Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/41 — οὔσῃ**: `V-PP-DFS` → `V-PPA-DFS`; `Verbo - Presente Particípio Ativa - Dativo Feminino Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/42 — οὔσης**: `V-PP-GFS` → `V-PPA-GFS`; `Verbo - Presente Particípio Ativa - Genitivo Feminino Singular`. Base: parsing alinhado e paradigma copular.

- **G1510/43 — οὖσιν**: `V-PP-DMP` → `V-PPA-DMP`; `Verbo - Presente Particípio Ativa - Dativo Masculino Plural`. Base: parsing alinhado e paradigma copular.

- **G1510/44 — οὐσῶν**: `V-PP-GFP` → `V-PPA-GFP`; `Verbo - Presente Particípio Ativa - Genitivo Feminino Plural`. Base: parsing alinhado e paradigma copular.

- **G1751/0 — ἐνόντα**: `V-PP-ANP` → `V-PPA-ANP`; `Verbo - Presente Particípio Ativa - Acusativo Neutro Plural`. Base: parsing alinhado de LC 11:41 e composição ἐν + εἰμί.

- **G3918/0 — πάρει**: `V-PI-2S` → `V-PIA-2S`; `Verbo - Presente Indicativo Ativa - 2ª Pessoa Singular`. Base: paradigma copular e identificação lexical; sem parsing contextual alinhado.

- **G3918/1 — παρεῖναί**: `V-PN` → `V-PNA`; `Verbo - Presente Infinitivo Ativa`. Base: parsing alinhado e paradigma copular.

- **G3918/2 — πάρεισιν**: `V-PI-3P` → `V-PIA-3P`; `Verbo - Presente Indicativo Ativa - 3ª Pessoa Plural`. Base: parsing alinhado e paradigma copular.

- **G3918/3 — πάρεσμεν**: `V-PI-1P` → `V-PIA-1P`; `Verbo - Presente Indicativo Ativa - 1ª Pessoa Plural`. Base: parsing alinhado e paradigma copular.

- **G3918/4 — παρέσται**: `V-FI-3S` → `V-FIM-3S`; `Verbo - Futuro Indicativo Média - 3ª Pessoa Singular`. Base: parsing alinhado e paradigma copular.

- **G3918/5 — πάρεστε**: `V-PI-2P` → `V-PIA-2P`; `Verbo - Presente Indicativo Ativa - 2ª Pessoa Plural`. Base: paradigma copular e identificação lexical; sem parsing contextual alinhado.

- **G3918/6 — πάρεστιν**: `V-PI-3S` → `V-PIA-3S`; `Verbo - Presente Indicativo Ativa - 3ª Pessoa Singular`. Base: parsing alinhado e paradigma copular.

- **G3918/7 — Παρῆσαν**: `V-II-3P` → `V-IIA-3P`; `Verbo - Imperfeito Indicativo Ativa - 3ª Pessoa Plural`. Base: parsing alinhado e paradigma copular.

- **G3918/8 — παρὸν**: `V-PP-ANS` → `V-PPA-ANS`; `Verbo - Presente Particípio Ativa - Acusativo Neutro Singular`. Base: paradigma copular e identificação lexical; sem parsing contextual alinhado.

- **G3918/9 — παρόντες**: `V-PP-NMP` → `V-PPA-NMP`; `Verbo - Presente Particípio Ativa - Nominativo Masculino Plural`. Base: paradigma copular e identificação lexical; sem parsing contextual alinhado.

- **G3918/10 — παρόντος**: `V-PP-GNS` → `V-PPA-GNS`; `Verbo - Presente Particípio Ativa - Genitivo Neutro Singular`. Base: parsing alinhado e paradigma copular.

- **G3918/11 — παρούσῃ**: `V-PP-DFS` → `V-PPA-DFS`; `Verbo - Presente Particípio Ativa - Dativo Feminino Singular`. Base: parsing alinhado e paradigma copular.

- **G3918/12 — παροῦσιν**: `V-PP-DNP` → `V-PPA-DNP`; `Verbo - Presente Particípio Ativa - Dativo Neutro Plural`. Base: paradigma copular e identificação lexical; sem parsing contextual alinhado.

- **G3918/13 — παρὼν**: `V-PP-NMS` → `V-PPA-NMS`; `Verbo - Presente Particípio Ativa - Nominativo Masculino Singular`. Base: parsing alinhado e paradigma copular.

## Fontes gramaticais

- [Robinson — PARSING.COD, Voice](https://github.com/byztxt/robinson-documentation/blob/master/doc/PARSING.COD): D identifica voz média deponente. A adaptação contextual é restrita aos futuros revisados de G1510/G3918; O/N e outras famílias não são equiparados.

- [Major/Laughy — Ancient Greek for Everyone, §22.8](https://dcc.dickinson.edu/grammar/age/middle-future-verbs): O futuro de εἰμί tem forma média; isso não autoriza mudar suas traduções portuguesas.

- [Major/Laughy — índice dos paradigmas de εἰμί](https://dcc.dickinson.edu/grammar/age/greek-index): Presente, imperfeito, infinitivo e particípio presentes pertencem ao sistema ativo; aplica-se também aos compostos lexicais confirmados.

- [LSJ — πάρειμι, composto de εἰμί](https://atlas.perseus.tufts.edu/dictionaries/entry/urn%3Acite2%3Ascaife-viewer%3Adictionaries.v1%3Alsj-n79223/): Confere a identidade do composto e o futuro médio; não confundir com o homônimo composto de εἶμι, ir.

## Reprodução

`python3 -B -m tools.audit.apply_missing_voice --apply` aplica somente o manifesto revisado. `--check` verifica o resultado. Ambas as operações recusam fontes alteradas; reaplicar o lote sobre seu resultado é idempotente.

O balanço geral atualizado está em `reports/audit/morfologia/resumo.md`. As demais divergências e o registro G1510/49 com marcador invisível continuam fora desta aplicação.
