"""Run once during setup; requests never download models."""
import nltk

if __name__ == '__main__':
    for resource in ('punkt_tab', 'averaged_perceptron_tagger_eng', 'wordnet', 'omw-1.4'):
        if not nltk.download(resource, raise_on_error=True):
            raise SystemExit(f'Could not download {resource}')
