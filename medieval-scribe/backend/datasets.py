"""Retrieve related Shakespeare dialogue; dialogue responses are not translations."""
import csv
import io
import re
import zipfile
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / 'data'
STOP = set('a an the i you he she it we they is are was were to of and or in on for my your his her this that do not will have'.split())
def terms(text):
    return set(re.findall(r'[a-z]+', text.lower())) - STOP

@lru_cache(maxsize=1)
def corpus():
    rows = []
    postings = defaultdict(set)
    # Train only: test.csv stays held out, and is not treated as aligned translations.
    with zipfile.ZipFile(DATA / 'Shakespeare.zip') as archive:
        with archive.open('Shakespeare/train.csv') as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig')):
                idx = len(rows)
                rows.append(row)
                for term in terms(row['translated_dialog']):
                    postings[term].add(idx)
    return rows, postings

def examples(text, limit=3):
    rows, postings = corpus()
    hits = Counter()
    for term in terms(text):
        for idx in postings.get(term, ()):
            hits[idx] += 1
    query_terms = terms(text)
    ranked = sorted(hits, key=lambda i: (-hits[i] / max(1, len(query_terms | terms(rows[i]['translated_dialog']))), i))
    return [dict(id=rows[i]['id'], modern_dialogue=rows[i]['translated_dialog'],
                 shakespeare_reply=rows[i]['og_response'].strip(), matched_terms=hits[i],
                 source='Shakespeare/train.csv', relation='Reply, NOT a translation')
            for i in ranked[:limit]]
