# auditoria_v6.py
# Ajuste baseado na v5: reconhece "ser + particípio" como passiva explícita
# e remove essas entradas do relatório de passiva_a_confirmar. [1]

import json
import re
from collections import defaultdict
from pathlib import Path

# =========================
# Configurações
# =========================
DICT_PATH = Path("src/_data/dict_flex_nt-lxx_greek-pt.json")
RELATORIO_PATH = Path("relatorio_auditoria_v6.json")

# Auxiliares de "ser" (formas mais comuns; pode expandir se necessário)
AUX_SER = {
    "é", "foi", "será", "seria", "sendo", "sido",
    "eram", "foram", "serão", "éramos", "fomos", "somos", "sois", "são",
    "és", "éreis", "fôramos", "fora", "foras", "fôreis", "fôram",
    "seja", "sejas", "sejamos", "sejais", "sejam",
    "fosse", "fosses", "fôssemos", "fôsseis", "fossem",
    "sejas", "sejamos", "sejais", "sejam",  # repetido por segurança
}

# Sufixos típicos de particípio
PARTICIPIO_SUFFIXES = {"ado", "ido", "to", "so", "do"}

# Particípios irregulares frequentes
PARTICIPIO_IRREG = {
    "feito", "dito", "posto", "visto", "escrito", "aberto",
    "morto", "nascido", "vindo", "tido", "rido", "sido",
    "estado", "hvido", "posto", "aceito", "eleito", "expresso",
    "impresso", "incluso", "anexo", "suspenso", "extinto",
    "pago", "ganho", "gasto", "morto", "nascido", "posto",
    "visto", "dito", "feito", "escrito", "aberto", "coberto",
    "descoberto", "oferecido", "surgido", "tido", "havido",
}

# Pronomes/clíticos que podem aparecer entre auxiliar e particípio
CLITICOS = {"se", "lhe", "lhes", "o", "a", "os", "as", "me", "te", "nos", "vos"}

# =========================
# Funções auxiliares
# =========================

def tokenizar(texto: str):
    # Separa por espaços e preserva pontuação como tokens separados
    # Remove pontuação final de cada token para análise, mas mantém lista original
    tokens = re.findall(r"\w+|[^\w\s]", texto, flags=re.UNICODE)
    return tokens

def eh_participio(token: str) -> bool:
    t = token.lower()
    if t in PARTICIPIO_IRREG:
        return True
    return any(t.endswith(suf) for suf in PARTICIPIO_SUFFIXES)

def eh_passiva_explicita(traducao: str) -> bool:
    tokens = tokenizar(traducao)
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.lower() in AUX_SER:
            # avança ignorando clíticos entre auxiliar e particípio
            j = i + 1
            while j < len(tokens) and tokens[j].lower() in CLITICOS:
                j += 1
            if j < len(tokens) and eh_participio(tokens[j]):
                return True
        i += 1
    return False

# =========================
# Auditoria (base v5 + regra v6)
# =========================

def auditar_dicionario(dados: dict) -> dict:
    relatorio = {
        "erros_concordancia": [],
        "construcoes_malformadas": [],
        "infinitivo_ativo_em_forma_passiva": [],
        "medios_deponentes_decisao_lexical": [],
        "passiva_a_confirmar": [],      # só entra aqui se NÃO for "ser + particípio"
        "passiva_explicita": [],        # nova categoria (opcional, para auditoria)
        "total_entradas": 0,
        "total_alertas": 0,
    }

    for chave, entrada in dados.items():
        relatorio["total_entradas"] += 1
        traducao = entrada.get("traducao", "")
        if not traducao:
            continue

        # Exemplo de regra v5: detectar construções malformadas (pode expandir)
        if re.search(r"\b(fazer|dar|ter)\s+que\s+\w+", traducao, flags=re.IGNORECASE):
            relatorio["construcoes_malformadas"].append({
                "chave": chave,
                "traducao": traducao,
                "motivo": "construção potencialmente malformada (fazer/dar/ter + que)",
            })

        # Exemplo de regra v5: erros de concordância simples (particípio vs sujeito)
        # (aqui entra a lógica específica que você já tinha na v5)
        # ...

        # Exemplo de regra v5: infinitivo ativo em forma passiva (lógica específica)
        # ...

        # Exemplo de regra v5: médios/deponentes que exigem decisão lexical
        # ...

        # Regra v6: passiva
        # Se houver indicativo de voz passiva (palavras-chave, contexto, etc.),
        # mas NÃO for "ser + particípio", entra em passiva_a_confirmar.
        # Se for "ser + particípio", entra em passiva_explicita e NÃO em passiva_a_confirmar.

        # Exemplo de gatilho de passiva (ajuste conforme sua lógica v5):
        gatilho_passiva = re.search(r"\b(foi|é|será|seria|sendo|sido|eram|foram|serão)\b", traducao, flags=re.IGNORECASE)

        if gatilho_passiva:
            if eh_passiva_explicita(traducao):
                relatorio["passiva_explicita"].append({
                    "chave": chave,
                    "traducao": traducao,
                })
            else:
                relatorio["passiva_a_confirmar"].append({
                    "chave": chave,
                    "traducao": traducao,
                    "motivo": "passiva provável, mas não identificada como 'ser + particípio'",
                })

    # total_alertas
    relatorio["total_alertas"] = (
        len(relatorio["erros_concordancia"])
        + len(relatorio["construcoes_malformadas"])
        + len(relatorio["infinitivo_ativo_em_forma_passiva"])
        + len(relatorio["medios_deponentes_decisao_lexical"])
        + len(relatorio["passiva_a_confirmar"])
    )

    return relatorio

# =========================
# Execução
# =========================

if __name__ == "__main__":
    if not DICT_PATH.exists():
        raise FileNotFoundError(f"Dicionário não encontrado: {DICT_PATH}")

    with DICT_PATH.open("r", encoding="utf-8-sig") as f:
        dados = json.load(f)

    relatorio = auditar_dicionario(dados)

    with RELATORIO_PATH.open("w", encoding="utf-8-sig") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)

    print(f"Auditoria v6 concluída. Relatório salvo em: {RELATORIO_PATH}")
    print(f"Total de entradas: {relatorio['total_entradas']}")
    print(f"Total de alertas: {relatorio['total_alertas']}")
    print(f"Passivas explícitas (ser + particípio): {len(relatorio['passiva_explicita'])}")
    print(f"Passivas a confirmar (restantes): {len(relatorio['passiva_a_confirmar'])}")
