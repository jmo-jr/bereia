#!/usr/bin/env python3
"""Executa as rotinas de flexão para verbos e itens não verbais do léxico grego.

O script apenas orquestra `flexiona_verbos.py` e `flexiona_nao_verbos.py`,
evitando manter cópias divergentes das regras de flexão. Ele lê o arquivo de
entrada uma única vez, aplica os dois transformadores (verbos primeiro, depois
os demais itens) e grava o resultado de volta no arquivo original — ou em
`--output`, se informado.

Uso sugerido (não execute automaticamente):
    python3 tools/flexiona_todas_traducoes.py \
        --input src/_data/dict_lex_nt-lxx_greek-pt.json

Também é possível limitar o processamento a códigos Strong específicos:
    python3 tools/flexiona_todas_traducoes.py \
        --input src/_data/dict_lex_nt-lxx_greek-pt.json --strong 1096
"""

from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from pathlib import Path
from typing import Optional, Set

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.preenche_strongs import (
    load_strongs,
    transform_dictionary as transform_strongs_dictionary,
)
from tools.flexiona_io import DEFAULT_INPUT, preview

from tools.flexiona_verbos import (  # noqa: E402
    PortugueseConjugator,
    load_dictionary as load_verb_dictionary,
    transform_dictionary as transform_verb_dictionary,
    write_dictionary,
)
from tools.flexiona_nao_verbos import (
    PortugueseNominalInflector,
    transform_dictionary as transform_nonverb_dictionary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Arquivo JSON de origem.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Arquivo JSON de destino. Se omitido, sobrescreve o mesmo arquivo de entrada.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Não grava arquivo; apenas exibe alguns exemplos.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Quantidade de linhas exibidas em modo dry-run.",
    )
    parser.add_argument(
        "--strong",
        dest="strongs",
        action="append",
        metavar="CODE",
        help="Processa apenas os códigos Strong informados (argumento repetível).",
    )
    parser.add_argument(
        "--skip-verbs",
        action="store_true",
        help="Pula a etapa de flexão verbal.",
    )
    parser.add_argument(
        "--skip-nonverbs",
        action="store_true",
        help="Pula a etapa de flexão para itens não verbais.",
    )
    parser.add_argument(
        "--nofill",
        action="store_true",
        help="Preserva os verbetes atuais, sem preenchê-los pelas definições Strong.",
    )
    return parser.parse_args()


def fill_verbetes(data, strongs, strong_filter=None):
    """Preenche também as variantes lexicais, sem escolher ou eliminar nenhuma."""
    updated = deepcopy(data)
    targets = ["G" + code for code in strong_filter] if strong_filter else None
    for key, group in updated.items():
        code = str(key if "flexoes" in group else group.get("strongs", "")).strip()
        if strong_filter and code not in strong_filter:
            continue
        transform_strongs_dictionary(group, strongs, targets)
        if "flexoes" in group and "verbetes" in group:
            group["verbetes"] = [
                transform_strongs_dictionary({"verbete": text}, strongs, targets)["verbete"]
                for text in group["verbetes"]
            ]
    return updated


def main() -> None:
    args = parse_args()
    strong_filter: Optional[Set[str]] = (
        {code.strip() for code in args.strongs if code} if args.strongs else None
    )

    data = load_verb_dictionary(args.input)

    if not args.nofill:
        data = fill_verbetes(data, load_strongs(), strong_filter)

    if not args.skip_verbs:
        conjugator = PortugueseConjugator()
        data = transform_verb_dictionary(data, conjugator, strong_filter)

    if not args.skip_nonverbs:
        inflector = PortugueseNominalInflector()
        data = transform_nonverb_dictionary(data, strong_filter, inflector)

    if args.dry_run:
        preview(data, strong_filter, args.limit, verbs=not args.skip_verbs,
                nonverbs=not args.skip_nonverbs)
        return

    output_path = args.output or args.input
    write_dictionary(output_path, data, template_path=args.input)


if __name__ == "__main__":
    main()
