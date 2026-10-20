"""Rules tested with fixture POS/lemmas, real Treebank tokenization and stemming."""
import pytest
from backend import nlp
from backend.vocabulary import PHRASES, ADDRESS, LEXICON, VERBS

class Spans:
    def span_tokenize(self, text):
        yield (0, len(text))
class Lemmas:
    def lemmatize(self, word, pos='n'):
        return {'knows':'know','says':'say','cries':'cry','went':'go'}.get(word, word)
@pytest.fixture
def engine(monkeypatch):
    monkeypatch.setattr(nlp, 'sentence_tokenizer', lambda: Spans())
    monkeypatch.setattr(nlp, 'LEMMATIZER', Lemmas())
    def run(text, tags, address='singular'):
        tokens = [text[a:b] for a,b in nlp.TOKENIZER.span_tokenize(text)]
        assert len(tokens) == len(tags), tokens
        monkeypatch.setattr(nlp.nltk, 'pos_tag', lambda words: list(zip(words, tags)))
        return nlp.convert(text, address)
    return run
@pytest.mark.parametrize('source,tags,expected', [
 ('Good morning!', 'JJ NN .', 'Good morrow!'),
 ('Thank you very much.', 'VB PRP RB RB .', 'I thank thee most heartily.'),
 ('Where are you going?', 'WRB VBP PRP VBG .', 'Whither art thou going?'),
 ('Please forgive me.', 'VB VB PRP .', 'I pray thee, forgive me.'),
 ('Do not be afraid.', 'VB RB VB JJ .', 'Be not afraid.'),
 ('Come here.', 'VB RB .', 'Come hither.'),
 ('Go there.', 'VB RB .', 'Go thither.'),
 ('Stay here.', 'VB RB .', 'Stay here.'),
 ('I live here.', 'PRP VBP RB .', 'I live here.'),
 ('He knows.', 'PRP VBZ .', 'He knoweth.'),
 ('He says yes.', 'PRP VBZ UH .', 'He saith aye.'),
 ('She cries loudly.', 'PRP VBZ RB .', 'She crieth loudly.'),
 ('You run.', 'PRP VBP .', 'Thou runnest.'),
 ('You went.', 'PRP VBD .', 'Thou wentest.'),
 ('I want no trouble.', 'PRP VBP DT NN .', 'I desire no trouble.'),
 ('They please the king.', 'PRP VBP DT NN .', 'They please the king.'),
 ('Please stay.', 'VB VB .', 'Prithee stay.'),
 ('I am very tired.', 'PRP VBP RB JJ .', 'I am most weary.'),
 ('A good morning.', 'DT JJ NN .', 'A good morning.'),
 ('Good\nmorning.', 'JJ NN .', 'Good\nmorning.'),
 ('Good, morning.', 'JJ , NN .', 'Good, morning.'),
 ('Happy is a name.', 'NNP VBZ DT NN .', 'Happy is a name.'),
 ('THANK YOU!', 'VB PRP .', 'I THANK THEE!'),
])
def test_context(engine, source, tags, expected):
    assert engine(source, tags.split())['translation'] == expected

def test_plural(engine):
    assert engine('How are you?', ['WRB','VBP','PRP','.'], 'plural')['translation'] == 'How do ye fare?'

def test_offsets(engine):
    source = 'Thank you very much, my friend.'
    result = engine(source, ['VB','PRP','RB','RB',',','PRP$','NN','.'])
    assert result['translation'] == 'I thank thee most heartily, my companion.'
    assert result['stats']['phrases'] == 1
    assert len(result['tokens']) == 8
    for row in result['tokens']:
        assert source[row['start']:row['end']] == row['token']
    members = [t for t in result['tokens'] if t['phrase']]
    assert len(members) == 4
    assert sum(t['phrase']['first'] for t in members) == 1

@pytest.mark.parametrize('source', list(PHRASES))
def test_templates(source):
    words = source.lower().split(); text = ' '.join(words)
    spans = list(nlp.TOKENIZER.span_tokenize(text))
    for address in ADDRESS:
        result = nlp.phrase_matches(words, [(w,'NN') for w in words], spans, text, address)
        assert result[0][0] == len(words)
        assert result[0][1] == PHRASES[source].format(**ADDRESS[address])

def test_safeguards():
    assert 'here' not in LEXICON and 'where' not in LEXICON
    assert LEXICON['no'][1].isdisjoint({'DT'})
    assert VERBS['ask']['VB'] == 'ask' and VERBS['cry']['VB'] == 'cry'
    assert VERBS['say']['VBZ'] == 'saith'

def test_spatial_before(engine):
    assert engine('I stand before the king.', ['PRP','VBP','IN','DT','NN','.'])['translation'] == 'I stand before the king.'

def test_temporal_before(engine):
    assert engine('Come before the sun rises.', ['VB','IN','DT','NN','VBZ','.'])['translation'] == 'Come ere the sun riseth.'

def test_api_with_fixture_models(engine, monkeypatch):
    from backend import main
    from fastapi.testclient import TestClient
    engine('Good morning!', ['JJ','NN','.'])
    monkeypatch.setattr(main, 'check_resources', lambda: None)
    with TestClient(main.app) as client:
        response = client.post('/api/translate', json={'text':'Good morning!', 'mode':'shakespeare'})
        assert response.status_code == 200
        assert response.json()['translation'] == 'Good morrow!'
        assert response.json()['stats']['phrases'] == 1
        assert client.post('/api/translate', json={'text':'hi','mode':'middle'}).status_code == 422
