import csv
import json
import re
import shutil
from pathlib import Path

BASE = Path(
    "/Users/admin/Documents/BIBLIA-INTERLINEAR/"
    "bereia/src/_data"
)

JSON_PATH = BASE / "nt_greek-pt_dict.json"
CSV_PATH = BASE / "candidatas_nao_aplicadas.csv"

BACKUP_PATH = BASE / "nt_greek-pt_dict.json.pre_decisoes.bak"
ALTERACOES_PATH = BASE / "alteracoes_decisoes.csv"
IGNORADAS_PATH = BASE / "decisoes_sem_correspondencia.csv"

shutil.copy2(JSON_PATH, BACKUP_PATH)

with JSON_PATH.open(encoding="utf-8") as f:
    dados = json.load(f)

with CSV_PATH.open(encoding="utf-8", newline="") as f:
    linhas = list(csv.DictReader(f, delimiter=";"))

alteracoes = []
sem_correspondencia = []
sem_decisao = 0

for linha in linhas:
    decisao = linha["decisao"].strip()

    if not decisao:
        sem_decisao += 1
        continue

    grego = linha["grego"]
    campo = linha["campo"]
    original = linha["palavra_suspeita"].strip()

    entrada = dados.get(grego)

    if entrada is None or campo not in entrada:
        sem_correspondencia.append(linha)
        continue

    valor_antes = entrada[campo]

    padrao = re.compile(
        r"(?<![A-Za-zÀ-ÖØ-öø-ÿ])"
        + re.escape(original)
        + r"(?![A-Za-zÀ-ÖØ-öø-ÿ])",
        re.IGNORECASE,
    )

    def substituir(match):
        encontrado = match.group(0)

        if encontrado[:1].isupper():
            return decisao[:1].upper() + decisao[1:]

        return decisao

    valor_depois, quantidade = padrao.subn(
        substituir,
        valor_antes,
    )

    if quantidade == 0:
        sem_correspondencia.append(linha)
        continue

    entrada[campo] = valor_depois

    alteracoes.append({
        "grego": grego,
        "strongs": linha["strongs"],
        "campo": campo,
        "palavra_original": original,
        "decisao": decisao,
        "antes": valor_antes,
        "depois": valor_depois,
    })

with JSON_PATH.open("w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)
    f.write("\n")

with ALTERACOES_PATH.open("w", encoding="utf-8", newline="") as f:
    campos = [
        "grego",
        "strongs",
        "campo",
        "palavra_original",
        "decisao",
        "antes",
        "depois",
    ]

    writer = csv.DictWriter(f, fieldnames=campos, delimiter=";")
    writer.writeheader()
    writer.writerows(alteracoes)

with IGNORADAS_PATH.open("w", encoding="utf-8", newline="") as f:
    campos = list(linhas[0].keys())

    writer = csv.DictWriter(f, fieldnames=campos, delimiter=";")
    writer.writeheader()
    writer.writerows(sem_correspondencia)

print("Aplicadas:", len(alteracoes))
print("Sem decisão:", sem_decisao)
print("Sem correspondência:", len(sem_correspondencia))
print("Backup:", BACKUP_PATH)
print("Relatório:", ALTERACOES_PATH)
print("Não encontradas:", IGNORADAS_PATH)
