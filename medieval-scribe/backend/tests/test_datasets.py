from backend.datasets import examples, corpus

def test_dialogue_is_not_translation():
    rows, _ = corpus()
    result = examples(rows[0]['translated_dialog'])
    assert result
    assert all(e['relation'] == 'Reply, NOT a translation' for e in result)
    assert all(e['source'] == 'Shakespeare/train.csv' for e in result)
    assert examples('zzzxxyyqq') == []
