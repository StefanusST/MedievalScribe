"""Explainable archaic-style transfer, not historical Middle English translation."""
import re
import unicodedata
from functools import lru_cache
import nltk
from .datasets import examples
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import TreebankWordTokenizer

TOKENIZER = TreebankWordTokenizer()
STEMMER = PorterStemmer()
LEMMATIZER = WordNetLemmatizer()
from .vocabulary import LEXICON, VERBS, PHRASES, ADDRESS, UTTERANCE_ONLY, SECOND_PRESENT, SECOND_PAST

SECOND = {'are': 'art', 'were': 'wert', 'have': 'hast', 'do': 'dost',
          'did': 'didst', 'will': 'wilt', 'shall': 'shalt', 'can': 'canst',
          'may': 'mayst', 'would': 'wouldst', 'could': 'couldst',
          'should': 'shouldst', 'must': 'must'}


def match_case(source, replacement):
    if source.isupper() and len(source) > 1:
        return replacement.upper()
    return replacement[:1].upper() + replacement[1:] if source[:1].isupper() else replacement


def normalize(text):
    text = unicodedata.normalize('NFC', text).replace('’', "'")
    # Expand only unambiguous contractions. 's and 'd remain untouched.
    contractions = {"can't": 'can not', "won't": 'will not', "shan't": 'shall not',
                    "I'm": 'I am', "let's": 'let us'}
    text = re.sub(r'\bcannot\b', lambda m: match_case(m[0], 'can not'), text, flags=re.I)
    for source, target in contractions.items():
        text = re.sub(r'\b' + re.escape(source) + r'\b',
                      lambda m: match_case(m[0], target), text, flags=re.I)
    for suffix, expanded in [("n't", ' not'), ("'re", ' are'), ("'ve", ' have'), ("'ll", ' will')]:
        text = re.sub(r"\b([A-Za-z]+)" + re.escape(suffix) + r'\b',
                      lambda m: m[1] + expanded, text, flags=re.I)
    return text


@lru_cache(maxsize=1)
def sentence_tokenizer():
    return nltk.data.load('tokenizers/punkt/english.pickle')


def check_resources():
    # Fail clearly instead of silently falling back to fake POS labels.
    sentence_tokenizer()
    nltk.pos_tag(['ready'])
    LEMMATIZER.lemmatize('words')


def second_person_verb(lemma):
    if lemma in SECOND_PRESENT:
        return SECOND_PRESENT[lemma]
    if lemma.endswith('e'):
        return lemma + 'st'
    return lemma + 'est'


def phrase_matches(words, tags, spans, normalized, address):
    """Non-overlapping longest-first matches, with original normalized offsets."""
    matches = {}
    ordered = sorted(PHRASES.items(), key=lambda item: -len(item[0].split()))
    i = 0
    while i < len(words):
        for source, target in ordered:
            parts = source.lower().split()
            stop = i + len(parts)
            if words[i:stop] != parts:
                continue
            # Never consume punctuation or a paragraph break between words.
            if any(not normalized[spans[j][1]:spans[j+1][0]].isspace()
                   or '\n' in normalized[spans[j][1]:spans[j+1][0]]
                   for j in range(i, stop-1)):
                continue
            if source in UTTERANCE_ONLY and i != 0:
                continue
            # Avoid changing e.g. "a very good morning" or proper-name phrases.
            if any(tag.startswith('NNP') and not (i == 0 and j == i)
                   for j, (_, tag) in enumerate(tags[i:stop], start=i)):
                continue
            # Sentence-initial questions only, avoiding embedded/quoted questions.
            if source.split()[0] in ('who', 'what', 'where', 'why', 'how') and i != 0:
                continue
            matches[i] = (stop, target.format(**ADDRESS[address]), source)
            i = stop
            break
        else:
            i += 1
    return matches


def convert(text, address='singular', mode='shakespeare'):
    normalized = normalize(text)
    rows, replacements, sentences, phrase_count = [], [], 0, 0
    for start, end in sentence_tokenizer().span_tokenize(normalized):
        sentences += 1
        spans = [(start + a, start + b) for a, b in TOKENIZER.span_tokenize(normalized[start:end])]
        words = [normalized[a:b] for a, b in spans]
        tags = nltk.pos_tag(words)
        lower = [w.lower() for w in words]
        phrases = phrase_matches(lower, tags, spans, normalized, address)
        phrase_members = {}
        for first, (stop, target, source) in phrases.items():
            a, b = spans[first][0], spans[stop-1][1]
            out = match_case(normalized[a:b], target)
            replacements.append((a, b, out))
            phrase_count += 1
            for j in range(first, stop):
                phrase_members[j] = dict(source=source, output=out, start=a, end=b, first=j == first)
        subjects, verb_indices = set(), set()
        for i, word in enumerate(lower):
            if word != 'you':
                continue
            j = i + 1
            while j < len(tags) and tags[j][1].startswith('RB'):
                j += 1
            prev = lower[i-1] if i else ''
            if i and tags[i-1][1] in ('IN', 'TO'):
                continue
            if j < len(tags) and (tags[j][1].startswith('VB') or tags[j][1] == 'MD'):
                subjects.add(i)
                verb_indices.add(i-1 if prev in SECOND else j)
            elif prev in SECOND and (i == 1 or (i == 2 and tags[0][1].startswith('W'))):
                subjects.add(i)
                verb_indices.add(i-1)
        for i, ((a, b), (word, pos)) in enumerate(zip(spans, tags)):
            low = word.lower()
            wn_pos = {'J': 'a', 'V': 'v', 'N': 'n', 'R': 'r'}.get(pos[:1])
            lemma = LEMMATIZER.lemmatize(low, wn_pos) if wn_pos else low
            stem = STEMMER.stem(low) if any(c.isalpha() for c in low) else low
            out, rule = word, 'Preserved'
            phrase = phrase_members.get(i)
            if phrase:
                out = phrase['output'] if phrase['first'] else ''
                rule = 'Phrase rule: ' + phrase['source'] + (' (continued)' if not phrase['first'] else '')
            elif address == 'singular' and low in ('you', 'your', 'yours', 'yourself'):
                nxt = lower[i+1] if i+1 < len(lower) else ''
                out = {'you': 'thou' if i in subjects else 'thee',
                       'your': 'thine' if nxt[:1] in 'aeiou' and nxt else 'thy',
                       'yours': 'thine', 'yourself': 'thyself'}[low]
                rule = 'Singular address (local grammar heuristic)'
            elif address == 'plural' and low == 'you' and i in subjects:
                out, rule = 'ye', 'Plural subject'
            elif address == 'singular' and i in verb_indices:
                if low in SECOND:
                    out, rule = SECOND[low], 'Second-person auxiliary'
                elif pos in ('VBP', 'VB'):
                    base = VERBS.get(lemma, {}).get('VB', lemma)
                    out, rule = second_person_verb(base), 'Second-person present verb'
                elif pos == 'VBD' and lemma in SECOND_PAST:
                    out, rule = SECOND_PAST[lemma], 'Second-person past verb'
            elif pos == 'VBZ' and low in ('has', 'does'):
                out, rule = {'has': 'hath', 'does': 'doth'}[low], 'Third-person auxiliary'
            elif lemma in VERBS and pos in VERBS[lemma]:
                out, rule = VERBS[lemma][pos], 'POS + lemma verb lookup'
            elif low in ('here', 'there') and i and tags[i-1][1].startswith('VB') and LEMMATIZER.lemmatize(lower[i-1], 'v') in ('come','go','bring','send','travel','ride','walk','run'):
                out, rule = {'here':'hither','there':'thither'}[low], 'Directional adverb after movement verb'
            elif low == 'please' and i == 0 and i+1 < len(tags) and tags[i+1][1].startswith('VB'):
                out, rule = ('prithee' if address == 'singular' else 'I pray you'), 'Polite imperative'
            elif low in LEXICON and pos in LEXICON[low][1]:
                out, rule = LEXICON[low][0], 'POS-restricted vocabulary'
            if not phrase:
                out = match_case(word, out)
                replacements.append((a, b, out))
            rows.append(dict(token=word, pos=pos, lemma=lemma, stem=stem,
                             replacement=out, rule=rule, start=a, end=b, phrase=phrase,
                             changed=(normalized[phrase['start']:phrase['end']] != phrase['output']) if phrase else out != word,
                             sentence=sentences))
    pieces, cursor = [], 0
    for a, b, out in sorted(replacements):
        pieces.extend([normalized[cursor:a], out])
        cursor = b
    pieces.append(normalized[cursor:])
    return dict(original=text, normalized=normalized, translation=''.join(pieces),
                mode=mode, corpus_examples=examples(text), tokens=rows,
                stats=dict(tokens=len(rows), sentences=sentences, phrases=phrase_count,
                           changed=sum(row['changed'] for row in rows)),
                vocabulary_stats=dict(words=len(LEXICON), verb_lemmas=len(VERBS), phrases=len(PHRASES)),
                note='Shakespeare-inspired style using hand-authored rules, not a trained translator. Phrase rules take priority; review complex clauses and word meanings.')
