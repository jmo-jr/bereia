#!/usr/bin/env python3
"""Gera flexões português-centradas para entradas não verbais do léxico grego.

O script analisa `nt_greek-pt_dict.json`, identifica palavras que não são verbos
e tenta declinar a tradução de acordo com gênero, número e caso informados em
`morfologia`. A forma gerada sempre reflete exatamente a morfologia descrita;
casos dativo e genitivo recebem os prefixos `a` e `de`, respectivamente.

Uso sugerido (não execute automaticamente):
    python3 tools/flexiona_nao_verbos.py \
        --input src/_data/nt_greek-pt_dict.json

Para limitar a um ou mais códigos Strong específicos:
    python3 tools/flexiona_nao_verbos.py \
        --input src/_data/nt_greek-pt_dict.json --strong 537
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Utilidades gerais
# ---------------------------------------------------------------------------

ACCENT_STRIPPER = unicodedata.normalize
WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÂÊÔÃÕÀÈÌÒÙáéíóúâêôãõàèìòùçÇ]+")


def strip_accents(text: str) -> str:
    """Remove diacríticos para comparações insensíveis a acentos."""
    normalized = ACCENT_STRIPPER("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def tidy_spaces(text: str) -> str:
    """Condensa espaços e remove lacunas antes de pontuação."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:?!)])", r"\1", text)
    text = re.sub(r"([(])\s+", r"\1", text)
    return text.strip()


def unique_everseen(values: Iterable[str]) -> List[str]:
    """Mantém ordem de inserção e remove duplicidades vazias."""
    seen: Set[str] = set()
    ordered: List[str] = []
    for value in values:
        clean = tidy_spaces(value)
        if not clean or clean in seen:
            continue
        ordered.append(clean)
        seen.add(clean)
    return ordered


# Ordem preferencial das chaves em cada entrada.
ENTRY_KEY_ORDER = [
    "strongs",
    "grego",
    "transliteracao",
    "verbete",
    "ocorrencias",
    "traducao",
    "pt",
    "abrev_morf",
    "morfologia",
]


# ---------------------------------------------------------------------------
# Morfologia nominal
# ---------------------------------------------------------------------------


@dataclass
class NominalMorphology:
    pos: Optional[str] = None
    case: Optional[str] = None
    gender: Optional[str] = None
    number: Optional[str] = None
    extra: Optional[str] = None

class NominalMorphologyParser:
    """Extrai POS, caso, gênero e número a partir de `morfologia`."""

    CASE_KEYWORDS = {
        "nominativo",
        "acusativo",
        "genitivo",
        "dativo",
        "vocativo",
    }
    GENDER_KEYWORDS = {
        "masculino",
        "feminino",
        "neutro",
        "comum",
    }
    NUMBER_KEYWORDS = {
        "singular",
        "plural",
        "dual",
    }

    def parse(self, description: str) -> NominalMorphology:
        morph = NominalMorphology(extra=description if description else None)
        if not description:
            return morph

        segments = [segment.strip() for segment in description.split("-")]
        head = segments[0] if segments else ""
        morph.pos = head.split()[0].lower() if head else None

        lowered = strip_accents(description.lower())

        for candidate in self.CASE_KEYWORDS:
            if candidate in lowered:
                morph.case = candidate
                break

        for candidate in self.GENDER_KEYWORDS:
            if candidate in lowered:
                morph.gender = "masculino" if candidate == "comum" else candidate
                break

        for candidate in self.NUMBER_KEYWORDS:
            if candidate in lowered:
                morph.number = "plural" if candidate == "dual" else candidate
                break

        return morph


# ---------------------------------------------------------------------------
# Flexão em português
# ---------------------------------------------------------------------------


FEMININE_EXCEPTIONS: Dict[str, str] = {
    "bom": "boa",
    "mau": "má",
    "meu": "minha",
    "teu": "tua",
    "seu": "sua",
    "nosso": "nossa",
    "vosso": "vossa",
    "todo": "toda",
    "algum": "alguma",
    "nenhum": "nenhuma",
    "um": "uma",
    "o": "a",
    "este": "esta",
    "esse": "essa",
    "aquele": "aquela",
    "outro": "outra",
}

PLURAL_EXCEPTIONS: Dict[str, str] = {
    "mão": "mãos",
    "cão": "cães",
    "pão": "pães",
    "alemão": "alemães",
    "cidadão": "cidadãos",
    "mau": "maus",
    "mauzão": "mauzões",
}

MASC_EXCEPTIONS: Dict[str, str] = {
    value: key for key, value in FEMININE_EXCEPTIONS.items()
}


class PortugueseNominalInflector:
    """Aplica heurísticas simples para declinação em português."""

    def __init__(self) -> None:
        self.parser = NominalMorphologyParser()

    # ---- Interface principal ----------------------------------------------
    def expand_forms(self, base_phrase: str, morph: NominalMorphology) -> List[str]:
        """Retorna a frase traduzida compatível com a morfologia."""
        canonical = self._canonical_phrase(base_phrase)
        gender = self._normalize_gender(morph.gender)
        number = morph.number or "singular"

        inflected = self._inflect_phrase(canonical, gender, number)
        inflected = self._apply_case_prefix(
            inflected,
            morph.case,
            morph.gender or gender,
            morph.number or number,
        )
        return [inflected]

    # ---- Heurísticas básicas ----------------------------------------------
    def _canonical_phrase(self, phrase: str) -> str:
        """Tenta obter forma masculina singular a partir do verbete."""
        word_match = WORD_RE.search(phrase)
        if not word_match:
            return phrase
        word = word_match.group(0)
        canonical = self._to_masculine_singular(word)
        return phrase[: word_match.start()] + canonical + phrase[word_match.end() :]

    def _inflect_phrase(self, phrase: str, gender: str, number: str) -> str:
        match = WORD_RE.search(phrase)
        if not match:
            return tidy_spaces(phrase)

        token = match.group(0)
        transformed = token

        if gender == "feminino":
            transformed = self._to_feminine(transformed)
        else:
            transformed = self._to_masculine_singular(transformed)

        if number == "plural":
            transformed = self._to_plural(transformed)
        else:
            transformed = self._to_singular(transformed)

        inflected = phrase[: match.start()] + transformed + phrase[match.end() :]
        return tidy_spaces(inflected)

    def _apply_case_prefix(
        self,
        phrase: str,
        case: Optional[str],
        gender: Optional[str],
        number: Optional[str],
    ) -> str:
        if case == "dativo":
            prefix_map = {
                ("masculino", "singular"): "ao",
                ("feminino", "singular"): "à",
                ("neutro", "singular"): "a",
                ("masculino", "plural"): "aos",
                ("feminino", "plural"): "às",
                ("neutro", "plural"): "aos",
            }
            prefix = prefix_map.get((gender, number), "a")
            return tidy_spaces(f"{prefix} {phrase}")
        if case == "genitivo":
            prefix_map = {
                ("masculino", "singular"): "do",
                ("feminino", "singular"): "da",
                ("neutro", "singular"): "de",
                ("masculino", "plural"): "dos",
                ("feminino", "plural"): "das",
                ("neutro", "plural"): "dos",
            }
            prefix = prefix_map.get((gender, number), "de")
            return tidy_spaces(f"{prefix} {phrase}")
        return phrase

    def _normalize_gender(self, gender: Optional[str]) -> str:
        if not gender:
            return "masculino"
        if gender == "neutro":
            return "masculino"
        return gender

    # ---- Conversões de gênero/número --------------------------------------
    def _to_feminine(self, word: str) -> str:
        lower = word.lower()
        if lower in FEMININE_EXCEPTIONS:
            return self._restore_case(word, FEMININE_EXCEPTIONS[lower])
        if lower.endswith("o"):
            return self._restore_case(word, lower[:-1] + "a")
        if lower.endswith("or"):
            return self._restore_case(word, lower + "a")
        return word

    def _to_masculine_singular(self, word: str) -> str:
        lower = word.lower()
        if lower in MASC_EXCEPTIONS:
            return self._restore_case(word, MASC_EXCEPTIONS[lower])
        if lower.endswith("as"):
            return self._restore_case(word, lower[:-1])
        if lower.endswith("es") and len(lower) > 2:
            return self._restore_case(word, lower[:-1])
        if lower.endswith("a"):
            return self._restore_case(word, lower[:-1] + "o")
        if lower.endswith("s") and len(lower) > 1:
            return self._restore_case(word, lower[:-1])
        return word

    def _to_plural(self, word: str) -> str:
        lower = word.lower()
        if lower in PLURAL_EXCEPTIONS:
            return self._restore_case(word, PLURAL_EXCEPTIONS[lower])
        if lower.endswith(("r", "z", "n")):
            return self._restore_case(word, lower + "es")
        if lower.endswith("m"):
            return self._restore_case(word, lower[:-1] + "ns")
        if lower.endswith("ão"):
            return self._restore_case(word, lower[:-2] + "ões")
        if lower.endswith("al"):
            return self._restore_case(word, lower[:-2] + "ais")
        if lower.endswith("el"):
            return self._restore_case(word, lower[:-2] + "éis")
        if lower.endswith("ol"):
            return self._restore_case(word, lower[:-2] + "óis")
        if lower.endswith("ul"):
            return self._restore_case(word, lower[:-2] + "uis")
        if lower.endswith("il"):
            return self._restore_case(word, lower[:-2] + "is")
        if lower.endswith("s") or lower.endswith("x"):
            return word
        return self._restore_case(word, lower + "s")

    def _to_singular(self, word: str) -> str:
        lower = word.lower()
        if lower in PLURAL_EXCEPTIONS.values():
            for key, value in PLURAL_EXCEPTIONS.items():
                if value == lower:
                    return self._restore_case(word, key)
        if lower.endswith("ns"):
            return self._restore_case(word, lower[:-2] + "m")
        if lower.endswith("ões"):
            return self._restore_case(word, lower[:-3] + "ão")
        if lower.endswith("es") and len(lower) > 2:
            return self._restore_case(word, lower[:-2])
        if lower.endswith("s") and len(lower) > 1:
            return self._restore_case(word, lower[:-1])
        return word

    # ---- Utilidades -------------------------------------------------------
    def _restore_case(self, reference: str, word: str) -> str:
        if reference.istitle():
            return word.capitalize()
        if reference.isupper():
            return word.upper()
        return word


# ---------------------------------------------------------------------------
# Transformações
# ---------------------------------------------------------------------------


def extract_base_phrase(entry: Dict[str, Any]) -> str:
    verbete = entry.get("verbete", "")
    if ":" in verbete:
        verbete = verbete.split(":", 1)[1]
    verbete = verbete.strip()
    if not verbete:
        verbete = entry.get("traducao", "")
    if not verbete:
        return ""
    first = re.split(r"[;,]", verbete)[0].strip()
    return first


def reorder_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    for key in ENTRY_KEY_ORDER:
        if key in payload:
            ordered[key] = payload[key]
    for key, value in payload.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def load_dictionary(path: Path) -> Dict[str, Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_dictionary(path: Path, data: Dict[str, Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def transform_dictionary(
    data: Dict[str, Dict[str, Any]],
    strong_filter: Optional[Set[str]],
    inflector: PortugueseNominalInflector,
) -> Dict[str, Dict[str, Any]]:
    updated: Dict[str, Dict[str, Any]] = {}
    for lemma, payload in data.items():
        new_payload = dict(payload)
        abrev_morf = payload.get("abrev_morf", "")

        if abrev_morf.startswith("V"):
            updated[lemma] = reorder_payload(new_payload)
            continue

        strong_code = str(payload.get("strongs", "")).strip()
        if strong_filter and strong_code not in strong_filter:
            updated[lemma] = reorder_payload(new_payload)
            continue

        base_phrase = extract_base_phrase(payload)
        morphology = inflector.parser.parse(payload.get("morfologia", ""))
        forms = inflector.expand_forms(base_phrase, morphology) if base_phrase else []

        if forms:
            new_payload["traducao"] = ", ".join(forms)
            new_payload["pt"] = forms[0]
        else:
            new_payload.setdefault("pt", new_payload.get("traducao", ""))

        updated[lemma] = reorder_payload(new_payload)

    return updated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("src/_data/nt_greek-pt_dict.json"),
        help="Arquivo JSON de origem.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Arquivo JSON de destino. Se omitido, o próprio --input será sobrescrito.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Não grava arquivo; apenas exibe exemplos.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Quantidade de linhas exibidas em dry-run.",
    )
    parser.add_argument(
        "--strong",
        dest="strongs",
        action="append",
        metavar="CODE",
        help="Processa apenas os códigos Strong informados (argumento repetível).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    strong_filter = {code.strip() for code in args.strongs if code} if args.strongs else None

    data = load_dictionary(args.input)
    inflector = PortugueseNominalInflector()
    transformed = transform_dictionary(data, strong_filter, inflector)
    output_path = args.output or args.input

    if args.dry_run:
        shown = 0
        for lemma, payload in transformed.items():
            original = data.get(lemma, {})
            if original.get("abrev_morf", "").startswith("V"):
                continue
            if strong_filter and str(original.get("strongs", "")).strip() not in strong_filter:
                continue
            print(f"{lemma}: {payload.get('traducao', '')}")
            shown += 1
            if shown >= args.limit:
                break
        return

    write_dictionary(output_path, transformed)


if __name__ == "__main__":
    main()
