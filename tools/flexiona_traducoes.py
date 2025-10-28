#!/usr/bin/env python3
"""Atualiza o campo `traducao` do dicionário grego com a flexão verbal em português.

O script lê `nt_greek_dict.json`, identifica entradas verbais e deriva a forma
flexionada a partir da morfologia (tempo, modo, voz, pessoa/número) presente em
`desgram`. O resultado é gravado em um novo arquivo, tipicamente
`new_nt_greek_dict.json`, preservando as demais chaves e adicionando a coluna
`pt` com a forma flexionada principal.

Uso sugerido (não execute automaticamente):
    python3 tools/flexiona_traducoes.py \
        --input src/_data/nt_greek_dict.json \
        --output src/_data/new_nt_greek_dict.json
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Utilidades gerais
# ---------------------------------------------------------------------------

ACCENT_STRIPPER = unicodedata.normalize


def strip_accents(text: str) -> str:
    """Remove acentos para facilitar comparações insensíveis a diacríticos."""
    normalized = ACCENT_STRIPPER("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def tidy_spaces(text: str) -> str:
    """Normaliza espaços sucessivos e remove espaços antes de pontuação."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:?!)])", r"\1", text)
    text = re.sub(r"([(])\s+", r"\1", text)
    return text.strip()


# Ordem preferencial de chaves dentro de cada entrada.
ENTRY_KEY_ORDER = [
    "strongs",
    "grego",
    "transliteracao",
    "verbete",
    "ocorrencia",
    "traducao",
    "pt",
    "classegram",
    "desgram",
]


# ---------------------------------------------------------------------------
# Estruturas de morfologia
# ---------------------------------------------------------------------------


@dataclass
class Morphology:
    tense: Optional[str] = None
    mood: Optional[str] = None
    voice: Optional[str] = None
    person: Optional[int] = None
    number: Optional[str] = None
    case: Optional[str] = None
    gender: Optional[str] = None
    extra: Optional[str] = None

    @property
    def is_finite(self) -> bool:
        return self.mood in {"indicativo", "subjuntivo", "imperativo"}

    @property
    def is_participle(self) -> bool:
        return self.mood == "participo"

    @property
    def is_infinitive(self) -> bool:
        return self.mood == "infinitivo"

    @property
    def is_nonfinite(self) -> bool:
        return not self.is_finite


class MorphologyParser:
    """Extrai características da string `desgram`."""

    MOOD_ALIASES = {
        "indicativo": "indicativo",
        "subjuntivo": "subjuntivo",
        "imperativo": "imperativo",
        "infinitivo": "infinitivo",
        "participio": "participo",
        "participo": "participo",
        "optativo": "optativo",
        "gerundio": "gerundio",
    }

    TENSE_ALIASES = {
        "presente": "presente",
        "aoristo": "aoristo",
        "imperfeito": "imperfeito",
        "futuro": "futuro",
        "perfeito": "perfeito",
        "pluperfeito": "pluperfeito",
    }
    # A string possui variantes “PluPerfeito” que geram os mesmos resultados.

    VOICE_ALIASES = {
        "ativa": "ativa",
        "ativo": "ativa",
        "passiva": "passiva",
        "passivo": "passiva",
        "media": "media",
        "média": "media",
        "medio": "media",
        "medio ou passiva": "media_passiva",
        "media ou passiva": "media_passiva",
        "média ou passiva": "media_passiva",
        "média ou passivo": "media_passiva",
    }

    CASE_KEYWORDS = {"nominativo", "acusativo", "genitivo", "dativo", "vocativo"}
    GENDER_KEYWORDS = {"masculino", "feminino", "neutro"}
    NUMBER_KEYWORDS = {"singular", "plural"}

    PERSON_RE = re.compile(r"([123])ª?\s*pessoa", re.IGNORECASE)

    def parse(self, description: str) -> Morphology:
        morph = Morphology(extra=description if description else None)
        if not description or "Verbo" not in description:
            return morph

        segments = [segment.strip() for segment in description.split("-")]
        core = segments[1] if len(segments) > 1 else ""
        tail = segments[2] if len(segments) > 2 else ""

        voice, leftover = self._extract_voice(core)
        mood, tense = self._extract_mood_tense(leftover)

        morph.voice = voice
        morph.mood = mood
        morph.tense = tense

        if tail:
            person, number = self._extract_person_number(tail)
            case, gender, inferred_number = self._extract_case_gender_number(
                tail, fallback_number=number
            )
            morph.person = person
            morph.number = inferred_number or number
            morph.case = case
            morph.gender = gender

        return morph

    def _extract_voice(self, chunk: str) -> Tuple[Optional[str], str]:
        if not chunk:
            return None, ""

        lowered = strip_accents(chunk.lower())
        matched_key = None
        for key in sorted(self.VOICE_ALIASES, key=len, reverse=True):
            if key in lowered:
                matched_key = key
                break
        if not matched_key:
            return None, chunk.strip()

        voice = self.VOICE_ALIASES[matched_key]
        pattern = re.compile(re.escape(matched_key), re.IGNORECASE)
        leftover = pattern.sub("", lowered, count=1)
        original_leftover = pattern.sub("", chunk, count=1)
        return voice, original_leftover.strip()

    def _extract_mood_tense(self, chunk: str) -> Tuple[Optional[str], Optional[str]]:
        if not chunk:
            return None, None

        lowered = strip_accents(chunk.lower())
        mood = None
        for key in sorted(self.MOOD_ALIASES, key=len, reverse=True):
            if key in lowered:
                mood = self.MOOD_ALIASES[key]
                lowered = lowered.replace(key, "")
                break

        tense = None
        tokens = lowered.split()
        for token in tokens:
            normalized = token.replace("º", "")
            if normalized in self.TENSE_ALIASES:
                tense = self.TENSE_ALIASES[normalized]
                break
            if normalized.startswith("pluperfeito"):
                tense = "pluperfeito"
                break

        if not tense and "pluperfeito" in lowered:
            tense = "pluperfeito"

        return mood, tense

    def _extract_person_number(self, chunk: str) -> Tuple[Optional[int], Optional[str]]:
        person_match = self.PERSON_RE.search(chunk)
        person = int(person_match.group(1)) if person_match else None

        lowered = strip_accents(chunk.lower())
        number = None
        for candidate in self.NUMBER_KEYWORDS:
            if candidate in lowered:
                number = candidate
                break

        return person, number

    def _extract_case_gender_number(
        self, chunk: str, fallback_number: Optional[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        lowered = strip_accents(chunk.lower())
        case = None
        for candidate in self.CASE_KEYWORDS:
            if candidate in lowered:
                case = candidate
                break

        gender = None
        for candidate in self.GENDER_KEYWORDS:
            if candidate in lowered:
                gender = candidate
                break

        number = fallback_number
        if not number:
            for candidate in self.NUMBER_KEYWORDS:
                if candidate in lowered:
                    number = candidate
                    break

        return case, gender, number


# ---------------------------------------------------------------------------
# Conjugação em português
# ---------------------------------------------------------------------------


FINITE_TENSE_MAP: Dict[Tuple[str, Optional[str]], str] = {
    ("indicativo", "presente"): "presente_indicativo",
    ("indicativo", "imperfeito"): "preterito_imperfeito",
    ("indicativo", "aoristo"): "preterito_perfeito",
    ("indicativo", "perfeito"): "preterito_perfeito_composto",
    ("indicativo", "futuro"): "futuro_presente",
    ("indicativo", "pluperfeito"): "mais_que_perfeito",
    ("subjuntivo", "presente"): "presente_subjuntivo",
    ("subjuntivo", "aoristo"): "presente_subjuntivo",
    ("subjuntivo", "perfeito"): "preterito_imperfeito_subjuntivo",
    ("subjuntivo", "futuro"): "futuro_subjuntivo",
    ("imperativo", "presente"): "imperativo",
    ("imperativo", "aoristo"): "imperativo",
}

FALLBACK_TENSE_ORDER = [
    "presente_indicativo",
    "preterito_perfeito",
    "preterito_imperfeito",
    "mais_que_perfeito",
    "futuro_presente",
]


REGULAR_ENDINGS: Dict[str, Dict[str, List[str]]] = {
    "presente_indicativo": {
        "ar": ["o", "as", "a", "amos", "ais", "am"],
        "er": ["o", "es", "e", "emos", "eis", "em"],
        "ir": ["o", "es", "e", "imos", "is", "em"],
    },
    "preterito_perfeito": {
        "ar": ["ei", "aste", "ou", "amos", "astes", "aram"],
        "er": ["i", "este", "eu", "emos", "estes", "eram"],
        "ir": ["i", "iste", "iu", "imos", "istes", "iram"],
    },
    "preterito_imperfeito": {
        "ar": ["ava", "avas", "ava", "ávamos", "áveis", "avam"],
        "er": ["ia", "ias", "ia", "íamos", "íeis", "iam"],
        "ir": ["ia", "ias", "ia", "íamos", "íeis", "iam"],
    },
    "mais_que_perfeito": {
        "ar": ["ara", "aras", "ara", "áramos", "áreis", "aram"],
        "er": ["era", "eras", "era", "êramos", "êreis", "eram"],
        "ir": ["ira", "iras", "ira", "íramos", "íreis", "iram"],
    },
    "futuro_presente": {
        "ar": ["arei", "arás", "ará", "aremos", "areis", "arão"],
        "er": ["erei", "erás", "erá", "eremos", "ereis", "erão"],
        "ir": ["irei", "irás", "irá", "iremos", "ireis", "irão"],
    },
    "presente_subjuntivo": {
        "ar": ["e", "es", "e", "emos", "eis", "em"],
        "er": ["a", "as", "a", "amos", "ais", "am"],
        "ir": ["a", "as", "a", "amos", "ais", "am"],
    },
    "preterito_imperfeito_subjuntivo": {
        "ar": ["asse", "asses", "asse", "ássemos", "ásseis", "assem"],
        "er": ["esse", "esses", "esse", "êssemos", "êsseis", "essem"],
        "ir": ["isse", "isses", "isse", "íssemos", "ísseis", "issem"],
    },
    "futuro_subjuntivo": {
        "ar": ["ar", "ares", "ar", "armos", "ardes", "arem"],
        "er": ["er", "eres", "er", "ermos", "erdes", "erem"],
        "ir": ["ir", "ires", "ir", "irmos", "irdes", "irem"],
    },
    "imperativo": {
        "ar": ["", "a", "e", "emos", "ai", "em"],
        "er": ["", "e", "a", "amos", "ei", "am"],
        "ir": ["", "e", "a", "amos", "i", "am"],
    },
}


IRREGULAR_BASES: Dict[str, Dict[str, List[str]]] = {
    # Os verbos listados contêm as seis pessoas na ordem 1s,2s,3s,1p,2p,3p.
    "ser": {
        "presente_indicativo": ["sou", "és", "é", "somos", "sois", "são"],
        "preterito_perfeito": ["fui", "foste", "foi", "fomos", "fostes", "foram"],
        "preterito_imperfeito": ["era", "eras", "era", "éramos", "éreis", "eram"],
        "mais_que_perfeito": ["fora", "foras", "fora", "fôramos", "fôreis", "foram"],
        "futuro_presente": ["serei", "serás", "será", "seremos", "sereis", "serão"],
        "presente_subjuntivo": ["seja", "sejas", "seja", "sejamos", "sejais", "sejam"],
        "preterito_imperfeito_subjuntivo": [
            "fosse",
            "fosses",
            "fosse",
            "fôssemos",
            "fôsseis",
            "fossem",
        ],
        "futuro_subjuntivo": ["for", "fores", "for", "formos", "fordes", "forem"],
        "imperativo": ["", "sê", "seja", "sejamos", "sede", "sejam"],
    },
    "estar": {
        "presente_indicativo": ["estou", "estás", "está", "estamos", "estáis", "estão"],
        "preterito_perfeito": ["estive", "estiveste", "esteve", "estivemos", "estivestes", "estiveram"],
        "preterito_imperfeito": ["estava", "estavas", "estava", "estávamos", "estáveis", "estavam"],
        "futuro_presente": ["estarei", "estarás", "estará", "estaremos", "estareis", "estarão"],
        "presente_subjuntivo": ["esteja", "estejas", "esteja", "estejamos", "estejais", "estejam"],
        "preterito_imperfeito_subjuntivo": [
            "estivesse",
            "estivesses",
            "estivesse",
            "estivéssemos",
            "estivésseis",
            "estivessem",
        ],
        "futuro_subjuntivo": ["estiver", "estiveres", "estiver", "estivermos", "estiverdes", "estiverem"],
        "imperativo": ["", "está", "esteja", "estejamos", "estai", "estejam"],
    },
    "ter": {
        "presente_indicativo": ["tenho", "tens", "tem", "temos", "tendes", "têm"],
        "preterito_perfeito": ["tive", "tiveste", "teve", "tivemos", "tivestes", "tiveram"],
        "preterito_imperfeito": ["tinha", "tinhas", "tinha", "tínhamos", "tínheis", "tinham"],
        "futuro_presente": ["terei", "terás", "terá", "teremos", "tereis", "terão"],
        "presente_subjuntivo": ["tenha", "tenhas", "tenha", "tenhamos", "tenhais", "tenham"],
        "preterito_imperfeito_subjuntivo": [
            "tivesse",
            "tivesses",
            "tivesse",
            "tivéssemos",
            "tivésseis",
            "tivessem",
        ],
        "futuro_subjuntivo": ["tiver", "tiveres", "tiver", "tivermos", "tiverdes", "tiverem"],
        "imperativo": ["", "tem", "tenha", "tenhamos", "tende", "tenham"],
    },
    "haver": {
        "presente_indicativo": ["hei", "hás", "há", "havemos", "haveis", "hão"],
        "preterito_perfeito": ["houve", "houveste", "houve", "houvemos", "houvestes", "houveram"],
        "preterito_imperfeito": ["havia", "havias", "havia", "havíamos", "havíeis", "haviam"],
        "futuro_presente": ["haverei", "haverás", "haverá", "haveremos", "havereis", "haverão"],
        "presente_subjuntivo": ["haja", "hajas", "haja", "hajamos", "hajais", "hajam"],
        "futuro_subjuntivo": ["houver", "houveres", "houver", "houvermos", "houverdes", "houverem"],
        "imperativo": ["", "há", "haja", "hajamos", "hai", "hajam"],
    },
    "ir": {
        "presente_indicativo": ["vou", "vais", "vai", "vamos", "ides", "vão"],
        "preterito_perfeito": ["fui", "foste", "foi", "fomos", "fostes", "foram"],
        "preterito_imperfeito": ["ia", "ias", "ia", "íamos", "íeis", "iam"],
        "futuro_presente": ["irei", "irás", "irá", "iremos", "ireis", "irão"],
        "presente_subjuntivo": ["vá", "vás", "vá", "vamos", "vades", "vão"],
        "futuro_subjuntivo": ["for", "fores", "for", "formos", "fordes", "forem"],
        "imperativo": ["", "vai", "vá", "vamos", "ide", "vão"],
    },
    "dar": {
        "presente_indicativo": ["dou", "dás", "dá", "damos", "dais", "dão"],
        "preterito_perfeito": ["dei", "deste", "deu", "demos", "destes", "deram"],
        "preterito_imperfeito": ["dava", "davas", "dava", "dávamos", "dáveis", "davam"],
        "futuro_presente": ["darei", "darás", "dará", "daremos", "dareis", "darão"],
        "presente_subjuntivo": ["dê", "dês", "dê", "demos", "deis", "deem"],
        "futuro_subjuntivo": ["der", "deres", "der", "dermos", "derdes", "derem"],
        "imperativo": ["", "dá", "dê", "demos", "dai", "deem"],
    },
    "ver": {
        "presente_indicativo": ["vejo", "vês", "vê", "vemos", "vedes", "veem"],
        "preterito_perfeito": ["vi", "viste", "viu", "vimos", "vistes", "viram"],
        "preterito_imperfeito": ["via", "vias", "via", "víamos", "víeis", "viam"],
        "futuro_presente": ["verei", "verás", "verá", "veremos", "vereis", "verão"],
        "presente_subjuntivo": ["veja", "vejas", "veja", "vejamos", "vejais", "vejam"],
        "futuro_subjuntivo": ["vir", "vires", "vir", "virmos", "virdes", "virem"],
        "imperativo": ["", "vê", "veja", "vejamos", "vede", "vejam"],
    },
    "vir": {
        "presente_indicativo": ["venho", "vens", "vem", "vimos", "vindes", "vêm"],
        "preterito_perfeito": ["vim", "vieste", "veio", "viemos", "viestes", "vieram"],
        "preterito_imperfeito": ["vinha", "vinhas", "vinha", "vínhamos", "vínheis", "vinham"],
        "futuro_presente": ["virei", "virás", "virá", "viremos", "vireis", "virão"],
        "presente_subjuntivo": ["venha", "venhas", "venha", "venhamos", "venhais", "venham"],
        "futuro_subjuntivo": ["vier", "vieres", "vier", "viermos", "vierdes", "vierem"],
        "imperativo": ["", "vem", "venha", "venhamos", "vinde", "venham"],
    },
    "fazer": {
        "presente_indicativo": ["faço", "fazes", "faz", "fazemos", "fazeis", "fazem"],
        "preterito_perfeito": ["fiz", "fizeste", "fez", "fizemos", "fizestes", "fizeram"],
        "preterito_imperfeito": ["fazia", "fazias", "fazia", "fazíamos", "fazíeis", "faziam"],
        "futuro_presente": ["farei", "farás", "fará", "faremos", "fareis", "farão"],
        "presente_subjuntivo": ["faça", "faças", "faça", "façamos", "façais", "façam"],
        "futuro_subjuntivo": ["fizer", "fizeres", "fizer", "fizermos", "fizerdes", "fizerem"],
        "imperativo": ["", "faz", "faça", "façamos", "fazei", "façam"],
    },
    "dizer": {
        "presente_indicativo": ["digo", "dizes", "diz", "dizemos", "dizeis", "dizem"],
        "preterito_perfeito": ["disse", "disseste", "disse", "dissemos", "dissestes", "disseram"],
        "preterito_imperfeito": ["dizia", "dizias", "dizia", "dizíamos", "dizíeis", "diziam"],
        "futuro_presente": ["direi", "dirás", "dirá", "diremos", "direis", "dirão"],
        "presente_subjuntivo": ["diga", "digas", "diga", "digamos", "digais", "digam"],
        "futuro_subjuntivo": ["disser", "disseres", "disser", "dissermos", "disserdes", "disserem"],
        "imperativo": ["", "diz", "diga", "digamos", "dizei", "digam"],
    },
    "poder": {
        "presente_indicativo": ["posso", "podes", "pode", "podemos", "podeis", "podem"],
        "preterito_perfeito": ["pude", "pudeste", "pôde", "pudemos", "pudestes", "puderam"],
        "preterito_imperfeito": ["podia", "podias", "podia", "podíamos", "podíeis", "podiam"],
        "futuro_presente": ["poderei", "poderás", "poderá", "poderemos", "podereis", "poderão"],
        "presente_subjuntivo": ["possa", "possas", "possa", "possamos", "possais", "possam"],
        "futuro_subjuntivo": ["puder", "puderes", "puder", "pudermos", "puderdes", "puderem"],
        "imperativo": ["", "pode", "possa", "possamos", "podei", "possam"],
    },
    "trazer": {
        "presente_indicativo": ["trago", "trazes", "traz", "trazemos", "trazeis", "trazem"],
        "preterito_perfeito": ["trouxe", "trouxeste", "trouxe", "trouxemos", "trouxestes", "trouxeram"],
        "futuro_presente": ["trarei", "trarás", "trará", "traremos", "trareis", "trarão"],
        "presente_subjuntivo": ["traga", "tragas", "traga", "tragamos", "tragais", "tragam"],
        "futuro_subjuntivo": ["trouxer", "trouxeres", "trouxer", "trouxermos", "trouxerdes", "trouxerem"],
        "imperativo": ["", "traz", "traga", "tragamos", "trazei", "tragam"],
    },
    "querer": {
        "presente_indicativo": ["quero", "queres", "quer", "queremos", "quereis", "querem"],
        "preterito_perfeito": ["quis", "quiseste", "quis", "quisemos", "quisestes", "quiseram"],
        "preterito_imperfeito": ["queria", "querias", "queria", "queríamos", "queríeis", "queriam"],
        "futuro_presente": ["quererei", "quererás", "quererá", "quereremos", "querereis", "quererão"],
        "presente_subjuntivo": ["queira", "queiras", "queira", "queiramos", "queirais", "queiram"],
        "futuro_subjuntivo": ["quiser", "quiseres", "quiser", "quisermos", "quiserdes", "quiserem"],
        "imperativo": ["", "quer", "queira", "queiramos", "querei", "queiram"],
    },
    "saber": {
        "presente_indicativo": ["sei", "sabes", "sabe", "sabemos", "sabeis", "sabem"],
        "preterito_perfeito": ["soube", "soubeste", "soube", "soubemos", "soubestes", "souberam"],
        "preterito_imperfeito": ["sabia", "sabias", "sabia", "sabíamos", "sabíeis", "sabiam"],
        "futuro_presente": ["saberei", "saberás", "saberá", "saberemos", "sabereis", "saberão"],
        "presente_subjuntivo": ["saiba", "saibas", "saiba", "saibamos", "saibais", "saibam"],
        "futuro_subjuntivo": ["souber", "souberes", "souber", "soubermos", "souberdes", "souberem"],
        "imperativo": ["", "sabe", "saiba", "saibamos", "sabei", "saibam"],
    },
    "pôr": {
        "presente_indicativo": ["ponho", "pões", "põe", "pomos", "pondes", "põem"],
        "preterito_perfeito": ["pus", "puseste", "pôs", "pusemos", "pusestes", "puseram"],
        "preterito_imperfeito": ["punha", "punhas", "punha", "púnhamos", "púnheis", "punham"],
        "futuro_presente": ["porei", "porás", "porá", "poremos", "poreis", "porão"],
        "presente_subjuntivo": ["ponha", "ponhas", "ponha", "ponhamos", "ponhais", "ponham"],
        "futuro_subjuntivo": ["puser", "puseres", "puser", "pusermos", "puserdes", "puserem"],
        "imperativo": ["", "põe", "ponha", "ponhamos", "ponde", "ponham"],
    },
}

PARTICIPLE_IRREGULAR = {
    "ser": "sido",
    "estar": "estado",
    "ter": "tido",
    "haver": "havido",
    "ir": "ido",
    "ver": "visto",
    "vir": "vindo",
    "fazer": "feito",
    "dizer": "dito",
    "poder": "podido",
    "trazer": "trazido",
    "querer": "querido",
    "saber": "sabido",
    "dar": "dado",
    "pôr": "posto",
}

GERUND_IRREGULAR = {
    "ser": "sendo",
    "estar": "estando",
    "ir": "indo",
    "ver": "vendo",
    "vir": "vindo",
    "pôr": "pondo",
    "ter": "tendo",
    "fazer": "fazendo",
    "dizer": "dizendo",
    "trazer": "trazendo",
}


PRONOUNS = {
    (1, "singular"): "eu",
    (2, "singular"): "tu",
    (3, "singular"): "ele(a)",
    (1, "plural"): "nós",
    (2, "plural"): "vocês",
    (3, "plural"): "eles(as)",
}

REFLEXIVE_PRONOUNS = {
    (1, "singular"): "me",
    (2, "singular"): "te",
    (3, "singular"): "se",
    (1, "plural"): "nos",
    (2, "plural"): "vos",
    (3, "plural"): "se",
}


WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÂÊÔÃÕÀÈÌÒÙáéíóúâêôãõàèìòùçÇ]+(?:-se)?")

INF_ENDINGS = ("ar", "er", "ir", "or", "ôr", "ír", "êr", "uzir")


@dataclass
class LemmaInfo:
    lemma: str
    root: str
    reflexive: bool
    start: int
    end: int


class PortugueseConjugator:
    """Gera uma frase flexionada respeitando a morfologia."""

    def __init__(self) -> None:
        self.morph_parser = MorphologyParser()

    # ---- Funções públicas -------------------------------------------------
    def build_phrase(self, base_phrase: str, morphology: Morphology) -> Tuple[Optional[str], str]:
        lemma_info = self._extract_lemma(base_phrase)
        if not lemma_info:
            return None, tidy_spaces(base_phrase)

        subject = self._resolve_subject(morphology)
        predicate = self._conjugate_predicate(base_phrase, lemma_info, morphology)
        return subject, tidy_spaces(predicate)

    def conjugate_entry(self, base_phrases: Iterable[str], morphology: Morphology) -> List[str]:
        phrases = []
        for phrase in base_phrases:
            subject, predicate = self.build_phrase(phrase, morphology)
            phrases.append((subject, predicate))

        rendered: List[str] = []
        for idx, (subject, predicate) in enumerate(phrases):
            if idx == 0 and subject:
                rendered.append(tidy_spaces(f"{subject} {predicate}"))
            else:
                rendered.append(predicate)
        return rendered

    # ---- Conjugação interna ----------------------------------------------
    def _conjugate_predicate(
        self, phrase: str, lemma: LemmaInfo, morph: Morphology
    ) -> str:
        if morph.is_finite:
            return self._conjugate_finite_phrase(phrase, lemma, morph)
        if morph.is_infinitive:
            return self._conjugate_infinitive_phrase(phrase, lemma, morph)
        if morph.is_participle:
            return self._conjugate_participle_phrase(phrase, lemma, morph)
        if morph.mood == "gerundio":
            return self._conjugate_gerund_phrase(phrase, lemma, morph)
        if morph.mood == "optativo":
            # Aproxima com subjuntivo no português.
            cloned = Morphology(
                tense=morph.tense,
                mood="subjuntivo",
                voice=morph.voice,
                person=morph.person,
                number=morph.number,
            )
            return self._conjugate_finite_phrase(phrase, lemma, cloned)
        # fallback: devolver frase original
        return phrase

    def _conjugate_finite_phrase(
        self, phrase: str, lemma: LemmaInfo, morph: Morphology
    ) -> str:
        target_tense = self._map_finite_tense(morph)
        if not target_tense:
            target_tense = "presente_indicativo"

        if morph.person is None or morph.number is None:
            return phrase

        index = self._person_index(morph.person, morph.number)
        reflexive_pron = None
        needs_reflexive = self._needs_reflexive(lemma, morph)
        if needs_reflexive:
            reflexive_pron = REFLEXIVE_PRONOUNS.get(
                (morph.person, morph.number)
            )

        verb_form = self._conjugate_simple_verb(
            lemma.root.lower(), target_tense, index
        )
        if verb_form is None:
            return phrase

        verb_form = self._restore_case(lemma.root, verb_form)
        replacement = verb_form

        if morph.voice == "passiva" and morph.person and morph.number:
            replacement = self._build_passive(
                lemma.root.lower(), morph, index
            )
        elif morph.voice == "media_passiva" and morph.person and morph.number:
            # Prefer reflexiva por padrão.
            replacement = self._attach_reflexive(
                replacement, reflexive_pron
            )
        elif needs_reflexive and reflexive_pron:
            replacement = self._attach_reflexive(
                replacement, reflexive_pron
            )

        new_phrase = (
            phrase[: lemma.start]
            + replacement
            + phrase[lemma.end :]
        )

        return new_phrase

    def _conjugate_infinitive_phrase(
        self, phrase: str, lemma: LemmaInfo, morph: Morphology
    ) -> str:
        root = lemma.root.lower()
        if morph.tense in {"aoristo", "perfeito"}:
            verb_form = f"ter {self._past_participle(root)}"
        elif morph.tense == "futuro":
            verb_form = f"vir a {root}"
        else:
            verb_form = root

        verb_form = self._restore_case(lemma.root, verb_form)
        return phrase[: lemma.start] + verb_form + phrase[lemma.end :]

    def _conjugate_participle_phrase(
        self, phrase: str, lemma: LemmaInfo, morph: Morphology
    ) -> str:
        root = lemma.root.lower()
        if morph.tense in {"presente"}:
            form = self._gerund(root)
        elif morph.tense in {"aoristo", "perfeito"}:
            form = f"tendo {self._past_participle(root)}"
        elif morph.tense == "futuro":
            form = f"prestes a {root}"
        else:
            form = self._past_participle(root)

        form = self._restore_case(lemma.root, form)
        return phrase[: lemma.start] + form + phrase[lemma.end :]

    def _conjugate_gerund_phrase(
        self, phrase: str, lemma: LemmaInfo, morph: Morphology
    ) -> str:
        root = lemma.root.lower()
        form = self._gerund(root)
        form = self._restore_case(lemma.root, form)
        return phrase[: lemma.start] + form + phrase[lemma.end :]

    # ---- Auxiliares ------------------------------------------------------
    def _person_index(self, person: int, number: str) -> int:
        base = {1: 0, 2: 1, 3: 2}[person]
        if number == "plural":
            base += 3
        return base

    def _needs_reflexive(self, lemma: LemmaInfo, morph: Morphology) -> bool:
        if lemma.reflexive:
            return True
        if morph.voice in {"media", "media_passiva"}:
            return True
        return False

    def _map_finite_tense(self, morph: Morphology) -> Optional[str]:
        key = (morph.mood, morph.tense)
        if key in FINITE_TENSE_MAP:
            return FINITE_TENSE_MAP[key]
        if morph.mood == "indicativo":
            return "presente_indicativo"
        if morph.mood == "subjuntivo":
            return "presente_subjuntivo"
        if morph.mood == "imperativo":
            return "imperativo"
        return None

    def _conjugate_simple_verb(self, lemma: str, tense: str, index: int) -> Optional[str]:
        lemma_norm = lemma.lower()
        if lemma_norm in IRREGULAR_BASES and tense in IRREGULAR_BASES[lemma_norm]:
            forms = IRREGULAR_BASES[lemma_norm][tense]
            if index < len(forms):
                return forms[index]

        group = self._verb_group(lemma_norm)
        if tense not in REGULAR_ENDINGS or not group:
            if lemma_norm in IRREGULAR_BASES:
                for fallback in FALLBACK_TENSE_ORDER:
                    if fallback in IRREGULAR_BASES[lemma_norm]:
                        forms = IRREGULAR_BASES[lemma_norm][fallback]
                        return forms[index]
            return None

        radical = self._radical(lemma_norm, group)
        endings = REGULAR_ENDINGS[tense][group]
        return radical + endings[index]

    def _build_passive(self, lemma: str, morph: Morphology, index: int) -> str:
        aux_tense = self._passive_aux_tense(morph)
        aux_forms = IRREGULAR_BASES["ser"].get(aux_tense)
        if not aux_forms:
            aux_forms = IRREGULAR_BASES["ser"]["presente_indicativo"]
        auxiliar = aux_forms[index]
        partic = self._past_participle(lemma)
        return f"{auxiliar} {partic}"

    def _passive_aux_tense(self, morph: Morphology) -> str:
        mapping = {
            ("indicativo", "presente"): "presente_indicativo",
            ("indicativo", "imperfeito"): "preterito_imperfeito",
            ("indicativo", "aoristo"): "preterito_perfeito",
            ("indicativo", "perfeito"): "preterito_perfeito_composto",
            ("indicativo", "futuro"): "futuro_presente",
            ("indicativo", "pluperfeito"): "mais_que_perfeito",
            ("subjuntivo", "presente"): "presente_subjuntivo",
            ("subjuntivo", "aoristo"): "presente_subjuntivo",
            ("subjuntivo", "futuro"): "futuro_subjuntivo",
        }
        return mapping.get((morph.mood, morph.tense), "presente_indicativo")

    def _attach_reflexive(self, verb_form: str, pronoun: Optional[str]) -> str:
        if not pronoun:
            return f"{verb_form}-se"
        return f"{pronoun} {verb_form}"

    def _resolve_subject(self, morph: Morphology) -> Optional[str]:
        if morph.person is None or morph.number is None:
            return None
        return PRONOUNS.get((morph.person, morph.number))

    def _extract_lemma(self, phrase: str) -> Optional[LemmaInfo]:
        for match in WORD_RE.finditer(phrase):
            candidate = match.group(0)
            if self._is_infinitive(candidate):
                lemma = candidate
                root = candidate
                reflexive = False
                if candidate.endswith("-se"):
                    root = candidate[:-3]
                    reflexive = True
                return LemmaInfo(
                    lemma=lemma,
                    root=root,
                    reflexive=reflexive,
                    start=match.start(),
                    end=match.end(),
                )
        return None

    def _is_infinitive(self, token: str) -> bool:
        token_lower = token.lower()
        if token_lower.endswith("-se"):
            token_lower = token_lower[:-3]
        token_lower = token_lower.rstrip(".,;:!?")
        return any(token_lower.endswith(ending) for ending in INF_ENDINGS)

    def _verb_group(self, lemma: str) -> Optional[str]:
        for group in ("ar", "er", "ir"):
            if lemma.endswith(group):
                return group
        if lemma.endswith("or"):
            return "er"
        if lemma.endswith("êr"):
            return "er"
        if lemma.endswith("ôr"):
            return "er"
        if lemma.endswith("ír"):
            return "ir"
        return None

    def _radical(self, lemma: str, group: str) -> str:
        if group in {"ar", "er", "ir"}:
            return lemma[: -len(group)]
        if lemma.endswith("or"):
            return lemma[:-2]
        if lemma.endswith("êr") or lemma.endswith("ôr") or lemma.endswith("ír"):
            return lemma[:-2]
        return lemma

    def _past_participle(self, lemma: str) -> str:
        if lemma in PARTICIPLE_IRREGULAR:
            return PARTICIPLE_IRREGULAR[lemma]
        group = self._verb_group(lemma)
        if group == "ar":
            return self._radical(lemma, group) + "ado"
        if group in {"er", "ir"}:
            return self._radical(lemma, group) + "ido"
        return lemma

    def _gerund(self, lemma: str) -> str:
        if lemma in GERUND_IRREGULAR:
            return GERUND_IRREGULAR[lemma]
        group = self._verb_group(lemma)
        if group == "ar":
            return self._radical(lemma, group) + "ando"
        if group in {"er", "ir"}:
            return self._radical(lemma, group) + "endo" if group == "er" else self._radical(lemma, group) + "indo"
        return lemma

    def _restore_case(self, reference: str, word: str) -> str:
        if reference.istitle():
            return word.capitalize()
        if reference.isupper():
            return word.upper()
        return word


# ---------------------------------------------------------------------------
# Construção das traduções
# ---------------------------------------------------------------------------


def split_phrases(base_text: str) -> List[str]:
    if not base_text:
        return []
    parts = re.split(r"[;,]", base_text)
    return [part.strip() for part in parts if part.strip()]


def load_dictionary(path: Path) -> Dict[str, Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_dictionary(path: Path, data: Dict[str, Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def build_translation_value(entry: Dict[str, Any], conjugator: PortugueseConjugator) -> Optional[str]:
    verbete = entry.get("verbete")
    if not verbete:
        return None
    base_part = verbete.split(":", 1)[1].strip() if ":" in verbete else verbete
    if not base_part:
        return None

    morphology = conjugator.morph_parser.parse(entry.get("desgram", ""))
    phrases = split_phrases(base_part)
    if not phrases:
        phrases = [base_part]

    rendered = conjugator.conjugate_entry(phrases, morphology)
    return ", ".join(rendered)


def reorder_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    for key in ENTRY_KEY_ORDER:
        if key in payload:
            ordered[key] = payload[key]
    for key, value in payload.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def transform_dictionary(
    data: Dict[str, Dict[str, Any]], conjugator: PortugueseConjugator
) -> Dict[str, Dict[str, Any]]:
    updated = {}
    for lemma, payload in data.items():
        new_payload = dict(payload)
        classegram = payload.get("classegram", "")
        # Garante que verbete permaneça exatamente como veio do arquivo fonte.
        if "verbete" in payload:
            new_payload["verbete"] = payload["verbete"]
        if classegram.startswith("V"):
            new_traducao = build_translation_value(payload, conjugator)
            if new_traducao:
                new_payload["traducao"] = new_traducao

        traducao_value = new_payload.get("traducao", "")
        if isinstance(traducao_value, str) and traducao_value:
            pt_value = traducao_value.split(",", 1)[0].strip()
        else:
            pt_value = ""
        new_payload["pt"] = pt_value

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
        default=Path("src/_data/nt_greek_dict.json"),
        help="Arquivo JSON de origem.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("src/_data/nt_greek-pt_dict.json"),
        help="Arquivo JSON de destino com traduções flexionadas.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Não grava arquivo; exibe alguns exemplos no console.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Quantidade de exemplos exibidos em dry-run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_dictionary(args.input)
    conjugator = PortugueseConjugator()
    transformed = transform_dictionary(data, conjugator)

    if args.dry_run:
        count = 0
        for lemma, payload in transformed.items():
            if not payload.get("classegram", "").startswith("V"):
                continue
            print(f"{lemma}: {payload.get('traducao', '')}")
            count += 1
            if count >= args.limit:
                break
        return

    write_dictionary(args.output, transformed)


if __name__ == "__main__":
    main()
