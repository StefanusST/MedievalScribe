from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .nlp import check_resources, convert

@asynccontextmanager
async def lifespan(app):
    try:
        check_resources()
    except LookupError as exc:
        raise RuntimeError('Missing NLP data. Run: python -m backend.download_data') from exc
    yield

app = FastAPI(title='Medieval Scribe API', lifespan=lifespan)

class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    mode: Literal['shakespeare'] = 'shakespeare'
    address: Literal['singular', 'plural'] = 'singular'

@app.get('/api/health')
def health():
    return {'status': 'ok'}

@app.post('/api/translate')
def translate(payload: TranslationRequest):
    if not payload.text.strip():
        raise HTTPException(422, 'Enter some text first.')
    return convert(payload.text, payload.address, payload.mode)

# Production: one origin serves the real Python API and compiled React app.
dist = Path(__file__).resolve().parents[1] / 'frontend' / 'dist'
if dist.is_dir():
    app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
