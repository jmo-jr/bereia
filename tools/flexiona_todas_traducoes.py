#!/usr/bin/env python3
"""Executa as rotinas de flexão para verbos e itens não verbais do léxico grego.

O script apenas orquestra `flexiona_verbos.py` e `flexiona_nao_verbos.py`,
evitando manter cópias divergentes das regras de flexão. Ele lê o arquivo de
entrada uma única vez, aplica os dois transformadores (verbos primeiro, depois
os demais itens) e grava o resultado de volta no arquivo original — ou em
`--output`, se informado.

Uso sugerido (não execute automaticamente):
    python3 tools/flexiona_todas_traducoes.py \
        --input src/_data/nt_greek-pt_dict.json

Também é possível limitar o processamento a códigos Strong específicos:
    python3 tools/flexiona_todas_traducoes.py \
        --input src/_data/nt_greek-pt_dict.json --strong 1096
"""

from __future__ import annotations

import argparse
import sys
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
        # default=Path("src/_data/nt_greek-pt_dict.json"),
        default=Path("src/_data/dict_flex_nt-lxx_greek-pt.json"),
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
        help="Bypass o preenchimento"
		)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    strong_filter: Optional[Set[str]] = (
        {code.strip() for code in args.strongs if code} if args.strongs else None
    )

    data = load_verb_dictionary(args.input)
    
    strongs = load_strongs()
    
    if not args.nofill:
        if args.strongs:
            data = transform_strongs_dictionary(data, strongs, "G" + args.strongs[0])
        else:
            for code in strongs.keys():
                data = transform_strongs_dictionary(data, strongs, code)

    if not args.skip_verbs:
        conjugator = PortugueseConjugator()
        data = transform_verb_dictionary(data, conjugator, strong_filter)

    if not args.skip_nonverbs:
        inflector = PortugueseNominalInflector()
        data = transform_nonverb_dictionary(data, strong_filter, inflector)

    if args.dry_run:
        shown = 0
        for lemma, payload in data.items():
            if strong_filter and str(payload.get("strongs", "")).strip() not in strong_filter:
                continue
            print(f"{lemma}: {payload.get('traducao', '')}")
            shown += 1
            if shown >= args.limit:
                break
        return

    output_path = args.output or args.input
    write_dictionary(output_path, data)


if __name__ == "__main__":
    main()
