# Study app

Single-file app: `index.html` (Liquid Glass UI, tab bar, Study tab with one guide per subject).
Study guides are Markdown in `guides/<SUBJECT>/` and are embedded into `index.html` by `tools/build_guides.py`.
Only subjects listed in `SUBJECTS` in that script are shipped.

## Guide format
- `NN-name.md` (NN < 90): a chapter of **explanations only**. Front matter: `title`, `pages`, optional `part`.
- `9N-name.md`: the **questions** for the subject. Each `## Section` becomes its own question set in the app.
- Question block: `:::q Tag · Tag · Question text` then `?? answer` then `:::`.
- Callouts: `:::key`, `:::note`, `:::warn`, `:::tip`, `:::faq`, `:::steps` … `:::`.
- Questions never go in the middle of the explanations. The build also moves any inline `:::q` out of chapters.
- Mark answers that are not from the teacher or book answer key with `_(resolução própria)_`.

## "Update the app" procedure
When the user says **update the app**:
1. List the Google Drive folder **Classes** (`1g491WUyjxR8-GwKELCl_KzSvO-3kGJ8p`) recursively with `search_files` (`parentId = '<id>'`). The subject folder ids are in `sync/drive-manifest.json`.
2. Compare with `sync/drive-manifest.json`. Anything new or modified (by `modifiedTime`) must be read.
3. Read each file:
   - Try `read_file_content` first. It returns Drive's OCR text for some PDFs (for example the Spanish Caderno) and works for images.
   - If it only returns page placeholders, use `download_file_content` (works up to about 5 MB) and render with `pdftoppm`.
   - Larger files cannot be read through the connector. Record them as `too_large` and ask the user to split them into files under ~5 MB.
4. Write or extend the guides: explanations in `NN-*.md`, every exercise with its answer in `90-*.md`. Nothing from the files may be left out.
5. Update the manifest (status `done` / `duplicate` / `too_large` / `empty`, and which guide covers each file).
6. Run `python3 tools/build_guides.py` and check the "0 left in chapters" line.
7. Test with Playwright (`/opt/node22/lib/node_modules/playwright/index.js`): every chapter and question set opens, no question cards inside chapters, no empty answers, no page errors.
8. Commit, push, and republish the artifact (strip doctype/html/head/body/charset/viewport lines into the scratchpad copy, then publish that same path so the URL stays the same).

The user wants subjects done **one at a time**, each one finished completely before moving on.
