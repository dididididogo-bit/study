#!/usr/bin/env python3
"""Embed the Markdown study guides (guides/<SUBJECT>/*.md) into index.html as JSON.

Explanations and questions are kept apart: every ``:::q`` block is moved out of the
chapter text into a question set, so chapters read as pure explanations and the app
shows the questions in their own "Perguntas" area.

- ``NN-name.md`` (NN < 90) is a chapter. Its inline questions become one question set
  with the same id (so saved progress keeps its ids), grouped under the chapter's headings.
- ``9N-name.md`` is a question file. Each ``##`` section becomes its own question set.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Only the subjects listed here are shipped in the app.
SUBJECTS = {
    'FQ': {
        'title': 'Físico-Química', 'subtitle': 'Guia de estudo · FAQ 8 · 8.º ano',
        'parts': {'0': 'Reações Químicas', '1': 'Reações Químicas', '2': 'Som', '3': 'Luz', '4': 'Luz'},
        'missing': [
            'Livro 1 (Reações Químicas): o capítulo 3 "Velocidade das reações químicas" (pp. 108–128) não estava nos PDFs.',
            'Livro 2 (Som e Luz): faltam as pp. 94–95, e os PDFs terminam na p. 105 (o capítulo 4 pode continuar).',
        ],
    },
    'ESP': {
        'title': 'Espanhol', 'subtitle': '¡A bordo! 8 · Guia de estudo · 8.º ano',
                'missing': [
            'O Manual (livro do aluno) é uma digitalização sem texto e tem 192 MB (25 MB comprimido): não dá para o ler pelo Google Drive. '
            'Este guia foi feito a partir do Caderno de ejercicios completo (pp. 4–61) e das suas soluções.',
            'As soluções do Caderno terminam na p. 46: as respostas das pp. 47–61 (Unidades 5 e 6) estão marcadas como resolução própria.',
        ],
    },
}

FRONT = re.compile(r'^---\n(.*?)\n---\n', re.S)
QBLOCK = re.compile(r'^:::q[^\n]*\n.*?^:::[ \t]*$\n?', re.S | re.M)


def front(text):
    meta, body = {}, text
    m = FRONT.match(text)
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            k, _, v = line.partition(':')
            meta[k.strip()] = v.strip()
    return meta, body


def drop_empty_headings(md):
    """Remove headings whose section became empty once the questions were taken out."""
    lines = md.split('\n')
    keep = []
    for i, line in enumerate(lines):
        h = re.match(r'^(#{2,6})\s', line)
        if h:
            level = len(h.group(1))
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            nxt = re.match(r'^(#{1,6})\s', lines[j]) if j < len(lines) else None
            if j >= len(lines) or (nxt and len(nxt.group(1)) <= level):
                continue
        keep.append(line)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(keep)).strip()


def split_chapter(md):
    """Return (explanations, questions) where questions keep the nearest ## heading as a group title."""
    out, qs, heading, last = [], [], None, None
    pos = 0
    for m in QBLOCK.finditer(md):
        before = md[pos:m.start()]
        out.append(before)
        for line in before.split('\n'):
            if re.match(r'^#{2,3}\s', line):
                heading = re.sub(r'^#+\s*', '', line).strip()
        if heading and heading != last:
            qs.append(f'## {heading}')
            last = heading
        qs.append(m.group(0).rstrip())
        pos = m.end()
    out.append(md[pos:])
    return drop_empty_headings(''.join(out)), '\n'.join(qs).strip()


def load(sid, cfg):
    chapters, qsets = [], []
    parts = cfg.get('parts', {})
    for f in sorted((ROOT / 'guides' / sid).glob('*.md')):
        meta, body = front(f.read_text(encoding='utf-8'))
        title, pages = meta.get('title', f.stem), meta.get('pages', '')
        if f.stem.startswith('9'):
            body = re.sub(r'^#\s[^\n]*\n', '', body.strip())
            for k, sec in enumerate(re.split(r'^## ', body, flags=re.M)[1:]):
                head, _, rest = sec.partition('\n')
                if '\n:::q' in '\n' + rest:
                    qsets.append({'id': f'{f.stem}-{k}', 'title': head.strip(), 'pages': pages,
                                  'part': meta.get('part', title), 'md': rest.strip()})
            continue
        part = meta.get('part') or parts.get(f.stem[0]) or parts.get('*', '')
        text, qs = split_chapter(body.strip())
        chapters.append({'id': f.stem, 'title': title, 'pages': pages, 'part': part, 'md': text})
        if qs:
            qsets.append({'id': f.stem, 'title': title, 'pages': pages, 'part': part, 'md': qs, 'chapter': f.stem})
    return chapters, qsets


data = {}
for sid, cfg in SUBJECTS.items():
    chapters, qsets = load(sid, cfg)
    data[sid] = {'title': cfg['title'], 'subtitle': cfg['subtitle'], 'missing': cfg.get('missing', []),
                 'chapters': chapters, 'qsets': qsets}

blob = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
html = (ROOT / 'index.html').read_text(encoding='utf-8')
new = re.sub(r'(<script id="guide-data" type="application/json">).*?(</script>)',
             lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
assert new != html or blob in html, 'guide-data placeholder not found'
(ROOT / 'index.html').write_text(new, encoding='utf-8')
for sid, g in data.items():
    n = sum(len(QBLOCK.findall(s['md'])) for s in g['qsets'])
    left = sum(len(QBLOCK.findall(c['md'])) for c in g['chapters'])
    print(f"{sid}: {len(g['chapters'])} chapters, {len(g['qsets'])} question sets, {n} questions ({left} left in chapters)")
print(f'{len(blob) // 1024} KB embedded')
