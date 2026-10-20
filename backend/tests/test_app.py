import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.nlp import convert

@pytest.mark.parametrize('source,expected', [
    ('You are my friend.', 'Thou art my companion.'),
    ('I will help you.', 'I will help thee.'),
    ('Do you have your sword?', 'Dost thou have thy sword?'),
    ('You want your answer.', 'Thou desirest thine answer.'),
    ('You will go.', 'Thou wilt go.'),
    ('Are you ready?', 'Art thou ready?'),
    ("You're my friend.", 'Thou art my companion.'),
    ('You have my word.\n\nI will help you.', 'Thou hast my word.\n\nI will help thee.'),
    ('He has a sword.', 'He hath a sword.'),
    ('The children wanted help.', 'The children desired help.'),
])
def test_translation(source, expected):
    assert convert(source)['translation'] == expected

def test_plural():
    assert convert('You are my friends. I will help you.', 'plural')['translation'] == 'Ye are my companions. I will help you.'

def test_analysis_and_offsets():
    result = convert('The children were running.')
    row = next(t for t in result['tokens'] if t['token'] == 'running')
    assert row['pos'] == 'VBG'
    assert row['lemma'] == 'run'
    assert row['stem'] == 'run'
    for row in result['tokens']:
        assert result['normalized'][row['start']:row['end']] == row['token']

def test_api():
    with TestClient(app) as client:
        assert client.get('/api/health').status_code == 200
        assert client.post('/api/translate', json={'text':'You are kind.'}).json()['translation'] == 'Thou art kind.'
        for body in ({'text':''}, {'text':'   '}, {'text':'a'*10001}, {'text':'hi','address':'invalid'}):
            assert client.post('/api/translate', json=body).status_code == 422
