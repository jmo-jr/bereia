#!/usr/bin/env python3
import sys
import re
import unicodedata
from pathlib import Path

ROUGH = '\u0314'  # COMBINING REVERSED COMMA ABOVE

# Base transliteration map
BASE_MAP = {
    'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'ē', 'θ': 'th', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y', 'φ': 'ph', 'χ': 'ch', 'ψ': 'ps', 'ω': 'ō',
    'Α': 'a', 'Β': 'b', 'Γ': 'g', 'Δ': 'd', 'Ε': 'e', 'Ζ': 'z', 'Η': 'ē', 'Θ': 'th', 'Ι': 'i', 'Κ': 'k', 'Λ': 'l', 'Μ': 'm', 'Ν': 'n', 'Ξ': 'x', 'Ο': 'o', 'Π': 'p', 'Ρ': 'r', 'Σ': 's', 'Τ': 't', 'Υ': 'y', 'Φ': 'ph', 'Χ': 'ch', 'Ψ': 'ps', 'Ω': 'ō',
}

VOWELS = set('αεηιουωΑΕΗΙΟΥΩ')

# Diphthongs (lowercase base letters); initial case will be handled after
PAIR_MAP = {
    ('ο', 'υ'): 'ou',
    ('ε', 'υ'): 'eu',
    ('α', 'υ'): 'au',
    ('η', 'υ'): 'ēu',
    ('ε', 'ι'): 'ei',
    ('ο', 'ι'): 'oi',
    ('α', 'ι'): 'ai',
    ('υ', 'ι'): 'yi',
}

def transliterate(greek_word: str) -> str:
    s = unicodedata.normalize('NFD', greek_word)
    clusters = []  # list of (base, [combining marks])
    base = None
    marks = []
    for ch in s:
        if unicodedata.category(ch).startswith('M'):
            marks.append(ch)
        else:
            if base is not None:
                clusters.append((base, marks))
            base = ch
            marks = []
    if base is not None:
        clusters.append((base, marks))

    out = []
    i = 0
    while i < len(clusters):
        b, m = clusters[i]
        # Directly append non-letters
        if not (b.isalpha() or b in BASE_MAP):
            out.append(b)
            i += 1
            continue

        has_rough = ROUGH in m
        t = BASE_MAP.get(b, b)

        # rho with rough breathing => rh
        if b in ('ρ', 'Ρ') and has_rough:
            t = 'rh'

        # Handle diphthongs
        if b.lower() in 'αεηοωυι' and i + 1 < len(clusters):
            nb, nm = clusters[i + 1]
            key = (b.lower(), nb.lower())
            if key in PAIR_MAP and '\u0308' not in nm:  # no diaeresis on next
                t = PAIR_MAP[key]
                if has_rough:
                    t = 'h' + t
                out.append(t)
                i += 2
                continue

        # Add aspiration for vowels with rough breathing
        if b in VOWELS and has_rough:
            t = 'h' + t

        out.append(t)
        i += 1

    result = ''.join(out)
    # Capitalize initial if original starts uppercase alpha char
    first_letter = next((c for c in greek_word if c.isalpha()), None)
    if first_letter and first_letter.isupper() and result:
        result = result[0].upper() + result[1:]
    return result


TITLE_TAIL_RE = re.compile(r'(\s*[\-–—]{1,2}\s*Ocorrência.*)$')

SPAN_GREEK_RE = re.compile(r'<span class="greek">([^<]+)</span>')
SPAN_ENG_RE = re.compile(r'<span class="eng">([^<]*)</span>')
TITLE_ATTR_RE = re.compile(r'(title=")([^"]*)(")')
ANCHOR_TEXT_RE = re.compile(r'(>)([^<]*)(</a>)')

def process_file(path: Path) -> int:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)
    changed = 0
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if '<span class="translit"' not in line:
            i += 1
            continue
        # Find the anchor line containing (possibly corrupted) title
        j = i + 1
        while j < n and '<a ' not in lines[j]:
            j += 1
        if j >= n:
            i = j
            continue
        anchor_line = lines[j]
        # Find greek line following
        k = j + 1
        while k < n and '<span class="greek">' not in lines[k]:
            k += 1
        if k >= n:
            i = k
            continue
        greek_line = lines[k]
        m_g = SPAN_GREEK_RE.search(greek_line)
        if not m_g:
            i = k + 1
            continue
        greek_word = m_g.group(1).strip()

        # Find translation line following greek
        l = k + 1
        while l < n and '<span class="eng">' not in lines[l]:
            l += 1
        if l >= n:
            i = l
            continue
        eng_line = lines[l]
        m_e = SPAN_ENG_RE.search(eng_line)
        if not m_e:
            i = l + 1
            continue
        eng_text = m_e.group(1).strip()

        # Compute transliteration from greek
        translit = transliterate(greek_word)

        # Prepare new title, preserving tail if present
        m_title = TITLE_ATTR_RE.search(anchor_line)
        title_val = m_title.group(2) if m_title else ''
        m_tail = TITLE_TAIL_RE.search(title_val)
        tail = m_tail.group(1) if m_tail else ''
        new_title_val = f"{translit}: {eng_text}{tail}"

        new_anchor_line = anchor_line
        if m_title:
            # Replace title value using a function
            def repl_title(m):
                return m.group(1) + new_title_val + m.group(3)
            new_anchor_line = TITLE_ATTR_RE.sub(repl_title, new_anchor_line, count=1)
        else:
            # Try to salvage previously corrupt backref markers like \1...\3
            marker = new_anchor_line.find('\\1')
            if marker != -1:
                # Preserve previous line (start of <a ...), rebuild current line with indentation
                indent = new_anchor_line[:len(new_anchor_line) - len(new_anchor_line.lstrip())]
                new_anchor_line = f"{indent} title=\"{new_title_val}\">{translit}</a></span><br />\n"
            else:
                # Insert title attribute before the first '>' of the anchor tag
                gt_pos = new_anchor_line.find('>')
                if gt_pos != -1:
                    new_anchor_line = new_anchor_line[:gt_pos] + f' title="{new_title_val}"' + new_anchor_line[gt_pos:]

        # Replace inner anchor text regardless of title presence
        def repl_anchor_text(m):
            return m.group(1) + translit + m.group(3)
        new_anchor_line = ANCHOR_TEXT_RE.sub(repl_anchor_text, new_anchor_line, count=1)

        if new_anchor_line != anchor_line:
            lines[j] = new_anchor_line
            changed += 1

        # advance
        i = l + 1

    if changed:
        path.write_text(''.join(lines), encoding='utf-8')
    return changed


def main():
    if len(sys.argv) != 2:
        print("Uso: update_interlinear_translit.py <caminho/para/arquivo.html>")
        sys.exit(2)
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Arquivo não encontrado: {file_path}")
        sys.exit(1)
    changed = process_file(file_path)
    print(f"Atualizações aplicadas: {changed}")

if __name__ == '__main__':
    main()
