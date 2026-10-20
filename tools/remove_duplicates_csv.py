import csv
from pathlib import Path

PASTA_SCRIPT = Path(__file__).resolve().parent

entrada = PASTA_SCRIPT / "correcoes_dicionario.csv"
saida = PASTA_SCRIPT / "correcoes_dicionario_sem_duplicatas.csv"

with entrada.open("r", encoding="utf-8-sig", newline="") as arquivo:
    amostra = arquivo.read(8192)
    arquivo.seek(0)

    try:
        dialeto = csv.Sniffer().sniff(amostra, delimiters=",;\t")
    except csv.Error:
        dialeto = csv.excel
        dialeto.delimiter = ";"

    leitor = csv.reader(arquivo, dialect=dialeto)
    linhas = list(leitor)

cabecalho = None

if linhas and any(
    coluna.strip().lower() in {"linha", "grego", "campo"}
    for coluna in linhas[0]
):
    cabecalho = linhas[0]
    dados = linhas[1:]
else:
    dados = linhas

vistas = set()
linhas_unicas = []
duplicatas = 0

for numero, linha in enumerate(dados, start=1):
    if len(linha) < 3:
        print(f"Aviso: linha {numero} possui menos de 3 colunas e foi preservada.")
        linhas_unicas.append(linha)
        continue

    chave = (
        linha[0].strip(),  # linha
        linha[1].strip(),  # grego
        linha[2].strip()   # campo
    )

    if chave in vistas:
        duplicatas += 1
    else:
        vistas.add(chave)
        linhas_unicas.append(linha)

with saida.open("w", encoding="utf-8-sig", newline="") as arquivo:
    escritor = csv.writer(arquivo, dialect=dialeto)

    if cabecalho is not None:
        escritor.writerow(cabecalho)

    escritor.writerows(linhas_unicas)

print(f"Arquivo de entrada: {entrada}")
print(f"Linhas originais: {len(dados)}")
print(f"Linhas únicas: {len(linhas_unicas)}")
print(f"Duplicatas removidas: {duplicatas}")
print(f"Arquivo gerado: {saida}")
