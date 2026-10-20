# Medieval Scribe

A React web interface backed by a real Python/FastAPI + NLTK NLP pipeline. No paid API key or LLM is needed. Text is processed on your Python server and is not stored by the application.

**Scope:** readable medieval-inspired / archaic English, with familiar forms such as “thou”, “thee”, “hast” and “art”. This is not an authentic Middle English translator. True historical translation requires a period-specific corpus and much more extensive grammar.

## Quick start — Docker

Install Docker with Docker Compose. From the extracted `medieval-scribe` folder:

```bash
docker compose up --build
```

Open **http://localhost:8000**. The first build needs internet access to download npm/Python dependencies and NLTK data. Subsequent requests use the installed data. Stop with Ctrl+C.

## Run without Docker

Requirements: Python 3.12 and Node.js 22 or newer.

From the project root:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Install the backend and its language data:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m backend.download_data
python -m uvicorn backend.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open the URL Vite prints (normally **http://localhost:5173**). Vite forwards `/api` calls to Python on port 8000. Keep both terminals running. The automatically generated API documentation is at **http://localhost:8000/docs**.

## One-server production build

```bash
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Start or restart Python **after** building React. FastAPI then serves both the frontend and API at **http://localhost:8000**. A prebuilt frontend is also included in this archive.

To host online, deploy the included Dockerfile on a Python/container-capable host and route traffic to port 8000. No live online deployment is included. For access from another device on your network, use the server computer's LAN IP with port 8000 and permit that port in its firewall. A public deployment should add HTTPS, request-size limits and rate limits at the hosting proxy. The app itself has no authentication.

## Features

- Editable text input and five topics with 80 randomly combined example lines.
- Singular or plural “you” selection.
- Copyable output with preserved whitespace and paragraphs.
- Visible NLP table: token, Penn Treebank POS tag, Porter stem, WordNet lemma, replacement and applied rule.
- Filter for changed tokens and inspect the complete JSON result.
- Request validation, loading/error states and a 30-second frontend timeout.
- Responsive layout and labeled controls.

## How the NLP works

| Stage | Implementation | Purpose |
| --- | --- | --- |
| Normalization | Unicode NFC, curly apostrophe normalization, conservative contraction expansion | Makes common contractions available for grammar rules. Ambiguous `'s` and `'d` are not expanded. |
| Sentence tokenization | NLTK Punkt | Establishes sentence boundaries so rules don't cross them. |
| Word tokenization | `TreebankWordTokenizer.span_tokenize` | Splits words and punctuation while retaining character positions. |
| POS tagging | `nltk.pos_tag` | Identifies verbs, nouns, pronouns and other roles. |
| Stemming | `PorterStemmer.stem` | Displays a stem for each word for educational comparison. Stems are not used to generate prose. |
| Lemmatization | `WordNetLemmatizer.lemmatize` with mapped POS | Resolves forms such as “wanted” to “want” for a lemma-based lookup. |
| Style transfer | Explicit lexicon, inflection tables and local grammar heuristics | Changes vocabulary, pronouns and supported verb forms. |
| Reconstruction | Character-span replacement | Preserves spacing, punctuation and paragraph breaks in normalized text. |

Example intended output:

```text
Input:  You are my friend. Do you have your sword?
Output: Thou art my companion. Dost thou have thy sword?
```

POS examples: `PRP` = personal pronoun, `NN` = singular noun, `NNS` = plural noun, `VBP` = non-third-person present verb, `VBZ` = third-person singular present verb, `VBG` = participle/gerund, `MD` = modal.

Why both stems and lemmas? A stem may not be a valid word. A lemma is a dictionary base form. The interface exposes both, but the converter uses POS-aware lemmas to choose supported vocabulary substitutions. Removing stop words would discard grammar needed for conversion, so stop-word removal is deliberately not used.

## API

`POST /api/translate`

```json
{"text":"You are my friend.","address":"singular"}
```

`address` must be `singular` or `plural`. Text must be nonblank and no longer than 10,000 characters. The response contains `original`, `normalized`, `translation`, `tokens`, `stats` and `note`. Token offsets refer to **normalized** text, not the original input. API schema: `/docs`. Health check: `/api/health`.

## Project files

```text
backend/
  nlp.py                 NLP pipeline and span-based phrase matching
  vocabulary.py          Editable words, verb forms and phrase rules
  main.py                FastAPI routes and production static serving
  download_data.py       One-time language-data installation
  requirements.txt       Runtime Python dependencies
  requirements-dev.txt   Test dependencies
  tests/test_app.py      Model-backed conversion/API regression tests
  tests/test_helpers.py  Resource-independent normalization tests
frontend/
  src/main.jsx           React interface
  src/style.css          Responsive styling
  vite.config.js         Development proxy
  package.json           Frontend dependencies and scripts
  package-lock.json      Reproducible frontend installation
  dist/                  Prebuilt React application
Dockerfile               React build + Python runtime
compose.yaml             One-command local web application
```

## Testing and verification

After installing the language data:

```bash
python -m pytest -q
```

Resource-independent checks:

```bash
python -m pytest -q backend/tests/test_helpers.py
python -m compileall -q backend
cd frontend
npm run build
```

Delivery verification: the React production build and Python compilation were successful. Model-backed tests could not complete in the authoring environment because NLTK's secure downloader rejected its configured proxy and no language data was preinstalled. The included integration expectations are therefore **not verified against the model**. Browser interaction and Docker execution were not tested here.

## Troubleshooting

- **Missing NLP data:** activate the same Python environment and run `python -m backend.download_data`. Restart the server.
- **Restricted/proxied network:** use an environment where NLTK can fetch its official resources, or ask your administrator to install them in a shared directory and set `NLTK_DATA` to that directory. Do not disable network protections just to bypass this error.
- **API unavailable:** start the backend on port 8000. Use the Vite URL during development, not the HTML file directly.
- **Production page missing:** run `npm run build`, then restart Python.
- **Fonts unavailable:** the CSS uses optional Google Fonts, with local serif/sans-serif fallbacks.

## Limitations and extension points

Vocabulary and phrase rules are editable in `backend/vocabulary.py`. Unrecognized words remain unchanged; the project does not invent historical equivalents for modern concepts. Sentence segmentation and POS tags can be wrong. Subject/object detection uses neighboring words rather than a dependency parser, so relative clauses, coordinated subjects, ambiguous pronouns, negation and unusual word order can produce awkward output. The vowel-letter rule for `thy/thine` is approximate. Second-person inflection remains heuristic; a small explicit irregular past-tense table is supported. Non-English input is not rejected, but this model is designed for English.

A stronger future version could use dependency parsing to resolve grammatical subjects, a larger inflected lexicon, and a human-reviewed parallel corpus for evaluation. Keep the present system described as **rule-based NLP style transfer**, not a trained translation model.

References: [NLTK WordNet lemmatization](https://www.nltk.org/api/nltk.stem.wordnet.html), [NLTK Porter stemmer](https://www.nltk.org/api/nltk.stem.PorterStemmer.html), [FastAPI static files](https://fastapi.tiangolo.com/tutorial/static-files/).

## Shakespeare mode update

The app now has one mode: **Shakespeare**. Conversion uses the original explainable vocabulary and grammar rules. The supplied Shakespeare corpus provides related dialogue examples, not translation training pairs. Kaikki and its generated dictionary index have been removed from this version.

**Try a line** has five topics: Love, Adventure, Friendship, Royal Court and Mystery. Each click randomly combines an opening and ending from that topic (16 possible lines per topic), avoiding the last generated line for that topic. This is local template generation, not an external generative model. Input is modern English so users can observe its conversion.

Run as before: start the Python backend on port 8000 and Vite with `cd frontend`, `npm ci`, `npm run dev`. Open http://localhost:5173. Backend setup instructions above still apply. The API accepts `mode: "shakespeare"`; it defaults to Shakespeare when omitted.

The archive under `backend/data/Shakespeare.zip` contains `train.csv` and `test.csv`. Only train.csv is retrieved, using content-word overlap. `translated_dialog` and `og_response` are a dialogue turn and a character reply, NOT aligned translations. No translation model is trained. The uploaded archive contains no license file; verify source terms before publishing its contents.

Verification: Vite production build, sample-generation checks, Python compilation and corpus retrieval checks passed. Full model-backed NLTK/API tests remain unverified because the secure NLTK downloader rejected the environment proxy. Python packages installed successfully.


## Expanded vocabulary and phrases

This release includes **69 POS-restricted word rules, 86 verb lemmas with six form slots each, and 111 phrase rules**. These are hand-authored Shakespeare-inspired style rules, not mappings learned from the conversational dataset or an academically validated historical lexicon. Many verb forms are unchanged: the tables explicitly preserve tense while supporting archaic agreement such as `knows → knoweth` and `says → saith`.

Phrase matching runs after tokenization/POS tagging, before individual-word conversion. It selects the longest matching token sequence, prevents overlaps, respects punctuation and paragraph boundaries, and substitutes one original span. Every input token still has its own POS, stem and lemma. Phrase members include a shared `phrase` object; only the first member displays the complete output, and the UI labels remaining members as part of the phrase. Character offsets still refer to normalized input.

Examples of rule behavior (checked with fixed POS/lemma fixtures):

| Input | Shakespeare-style output |
| --- | --- |
| Thank you very much. | I thank thee most heartily. |
| Where are you going? | Whither art thou going? |
| How are you? (plural address) | How do ye fare? |
| Please forgive me. | I pray thee, forgive me. |
| Do not be afraid. | Be not afraid. |
| Come here. | Come hither. |
| Stay here. | Stay here. |
| He says yes. | He saith aye. |
| You run. | Thou runnest. |
| I stand before the king. | I stand before the king. |

Words such as `here`/`there` change only after selected movement verbs. `no` is not replaced when it is a determiner. The verb `please` is preserved outside polite imperatives/interjections. `cry` is not blindly changed to `weep`, and `ask` is not blindly changed to `beseech`. Proper-name POS tags are excluded from lexical substitutions. These guards reduce mistakes but do not perform full semantic understanding.

See **VOCABULARY_RULES.md** for the full editable rule inventory. Edit `backend/vocabulary.py`, then restart the server. Add a contextual test before introducing ambiguous words or phrases.

### Verification of this release

- 144 resource-independent checks passed: normalization, corpus retrieval, phrase templates in both address modes, longest matching, contextual safeguards, span preservation and API validation/serialization.
- The rule pipeline/API checks use explicitly supplied POS tags and lemmas; they do not verify the downloaded NLTK models or real-world translation accuracy.
- React/Vite production build passed.
- The 13 existing model-backed tests could not pass because required NLTK language data was absent; the secure downloader rejected this environment's configured proxy. They must be rerun after installing language data on the target machine.

Run the resource-independent tests:

```bash
python -m pytest backend/tests/test_helpers.py backend/tests/test_datasets.py backend/tests/test_expanded_rules.py -q
```

Run all checks after `python -m backend.download_data` succeeds:

```bash
python -m pytest backend/tests -q
```
