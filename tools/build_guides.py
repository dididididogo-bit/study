#!/usr/bin/env python3
"""Embed the Markdown study guides (guides/<SUBJECT>/*.md) into index.html as JSON."""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PARTS = {'0': 'Reações Químicas', '1': 'Reações Químicas', '2': 'Som', '3': 'Luz', '4': 'Luz'}

def load(subject):
    chapters = []
    for f in sorted((ROOT / 'guides' / subject).glob('*.md')):
        text = f.read_text(encoding='utf-8')
        meta, body = {}, text
        m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
        if m:
            body = text[m.end():]
            for line in m.group(1).splitlines():
                k, _, v = line.partition(':')
                meta[k.strip()] = v.strip()
        chapters.append({'id': f.stem, 'title': meta.get('title', f.stem), 'pages': meta.get('pages', ''),
                         'part': PARTS.get(f.stem[0], ''), 'md': body.strip()})
    return chapters

data = {'FQ': {
    'title': 'Físico-Química', 'subtitle': 'Guia de estudo · FAQ 8 · 8.º ano',
    'missing': [
        'Livro 1 (Reações Químicas): o capítulo 3 "Velocidade das reações químicas" (pp. 108–128) não estava nos PDFs.',
        'Livro 2 (Som e Luz): faltam as pp. 94–95, e os PDFs terminam na p. 105 (o capítulo 4 pode continuar).',
    ],
    'chapters': load('FQ')}}

blob = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
html = (ROOT / 'index.html').read_text(encoding='utf-8')
new = re.sub(r'(<script id="guide-data" type="application/json">).*?(</script>)',
             lambda m: m.group(1) + blob + m.group(2), html, flags=re.S)
assert new != html or blob in html, 'guide-data placeholder not found'
(ROOT / 'index.html').write_text(new, encoding='utf-8')
print(f"{sum(len(c['chapters']) for c in data.values())} chapters, {len(blob)//1024} KB embedded")
