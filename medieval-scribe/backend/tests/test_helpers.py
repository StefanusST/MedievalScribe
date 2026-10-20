from backend.nlp import normalize, match_case, second_person_verb


def test_contractions_keep_negation_and_paragraphs():
    assert normalize("You're here.\n\nYou can't go and won't stay.") == 'You are here.\n\nYou can not go and will not stay.'
    assert normalize('You cannot go.') == 'You can not go.'


def test_ambiguous_contractions_not_guessed():
    assert normalize("He's ready. I'd go.") == "He's ready. I'd go."


def test_inflection_and_case():
    assert second_person_verb('desire') == 'desirest'
    assert second_person_verb('walk') == 'walkest'
    assert match_case('YOU', 'thou') == 'THOU'
    assert match_case('You', 'thou') == 'Thou'
