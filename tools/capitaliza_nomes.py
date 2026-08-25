import json
import csv
import re
import shutil
import subprocess
from pathlib import Path

base = Path("/Users/admin/Documents/BIBLIA-INTERLINEAR/bereia/src/_data")
json_path = base / "nt_greek-pt_dict.json"
csv_path = base / "candidatas_nao_aplicadas.csv"

backup_path = base / "nt_greek-pt_dict.json.pre_capitalizacao.bak"
shutil.copy2(json_path, backup_path)

with json_path.open(encoding="utf-8") as f:
    data = json.load(f)

with csv_path.open(encoding="utf-8", newline="") as f:
    antiga = list(csv.DictReader(f))

# Nomes próprios identificados com segurança razoável.
nomes = set(
    linha["palavra_suspeita"].lower()
    for linha in antiga
    if linha["palavra_suspeita"].lower()
    in {
        "abba", "abel", "abias", "abiatar", "abilene", "abiúde",
        "acaz", "alexandre", "alfeu", "amon", "amós", "ana",
        "ananias", "andré", "andrônico", "antioquia", "apoliom",
        "apolónia", "aquim", "areopagito", "arimatéia", "aristóbulo",
        "armagedom", "arquelau", "arquipo", "asafe", "aser", "atália",
        "azor", "balaque", "balaão", "baraque", "barrabás", "barsabás",
        "bartimeu", "beliar", "belzebu", "benjamin", "bereano",
        "berenice", "beréia", "betesda", "betesdo", "betfagé",
        "betsaida", "betânia", "bitínia", "boaz", "caifá", "canaã",
        "candace", "capadócia", "cedron", "cefas", "cencréias",
        "cesareia", "chipre", "chloé", "cilícia", "cirene", "cláudia",
        "cláudio", "colossas", "corinto", "dalmácia", "damare", "davi",
        "decápoli", "demas", "demétrio", "derbe", "drusila", "efraim",
        "egito", "eleazar", "elias", "eliseu", "eliézer", "emanuel",
        "epafro", "epafrodito", "erasto", "esaú", "esrom", "estêvão",
        "espanha", "eufrate", "eunice", "euódia", "fanuel", "febe",
        "filadélfia", "filemom", "filipos", "félix", "gabriel",
        "galiléia", "galácia", "gamaliel", "genesaré", "getsêmani",
        "gogue", "gomorra", "grécia", "gálatos", "hades", "hamor",
        "harã", "hebréia", "herodes", "herodias", "icônio", "iduméia",
        "isaque", "isaías", "israelito", "issacar", "itália", "jacó",
        "jairo", "jasão", "jefté", "jezabel", "joel", "jope", "joram",
        "jordão", "josafá", "josé", "jotão", "judá", "judéia", "júlia",
        "júlio", "júnia", "lameque", "laodicéia", "levi", "lídia",
        "magadan", "magogue", "malco", "mamon", "manassé", "manaém",
        "mateu", "melquisedeque", "midiã", "mileta", "mnason", "moisé",
        "naamã", "naasson", "naftali", "naim", "naor", "natanael", "naum",
        "nazaré", "nereu", "nicanor", "nicodemos", "nicópoli", "ninive",
        "obede", "onesíforo", "onésimo", "parmeno", "patma", "pelegue",
        "perga", "pisídia", "priscila", "prócoro", "ptolemaida",
        "putéolis", "pôncio", "públio", "quirino", "raabe", "ruben",
        "salatiel", "salomé", "samaria", "samuel", "sarepta", "sarom",
        "saul", "saulo", "selêucia", "sicar", "sidon", "siloé", "simeão",
        "siquém", "sodoma", "sosípatro", "sérgio", "síntique", "sópater",
        "sóstene", "tabito", "tadeu", "tessalônica", "teófilo", "tiago",
        "tiatiros", "tiberíades", "tibério", "timeu", "timóteo", "tir",
        "trófimo", "trôade", "tértulo", "tíquico", "zacarias", "zadoque",
        "zaqueu", "zebedeu", "zebulon", "zeu", "zorobabel", "ágabo",
        "ártemas", "ártemis", "éber", "éfeso", "êubulo", "êutico"
    }
)

token = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", re.UNICODE)

alteracoes = []

for grego, entrada in data.items():
    for campo in ("traducao", "pt"):
        valor = entrada.get(campo)
        if not isinstance(valor, str):
            continue

        novo = valor

        for nome in nomes:
            padrao = re.compile(
                r"(?<![A-Za-zÀ-ÖØ-öø-ÿ])"
                + re.escape(nome)
                + r"(?![A-Za-zÀ-ÖØ-öø-ÿ])",
                re.IGNORECASE,
            )

            novo = padrao.sub(
                lambda m: m.group(0)[0].upper() + m.group(0)[1:],
                novo,
            )

        if novo != valor:
            entrada[campo] = novo
            alteracoes.append([grego, entrada.get("strongs", ""), campo, valor, novo])

with json_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")

palavras = set()

for entrada in data.values():
    for campo in ("traducao", "pt"):
        for palavra in token.findall(entrada.get(campo, "").lower()):
            if len(palavra) >= 3:
                palavras.add(palavra)

words_path = Path("/tmp/words_after_capitalizacao.txt")
words_path.write_text("\n".join(sorted(palavras)) + "\n", encoding="utf-8")

resultado = subprocess.run(
    ["aspell", "--lang=pt_BR", "--encoding=utf-8", "list"],
    input=words_path.read_text(encoding="utf-8"),
    text=True,
    capture_output=True,
    check=True,
)

suspeitas = set(resultado.stdout.lower().split())

residuais = []

for grego, entrada in data.items():
    for campo in ("traducao", "pt"):
        valor = entrada.get(campo, "")
        palavras_valor = token.findall(valor.lower())

        for palavra in palavras_valor:
            if palavra in suspeitas:
                residuais.append([
                    grego,
                    entrada.get("strongs", ""),
                    campo,
                    palavra,
                    valor,
                    "",
                    "",
                ])

with csv_path.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "grego",
        "strongs",
        "campo",
        "palavra_suspeita",
        "texto_contexto",
        "sugestao",
        "decisao",
    ])
    writer.writerows(residuais)

print(f"Capitalizações aplicadas: {len(alteracoes)}")
print(f"Ocorrências restantes no CSV: {len(residuais)}")
print(f"Backup: {backup_path}")
print(f"CSV atualizado: {csv_path}")
