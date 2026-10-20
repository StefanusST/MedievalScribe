# MedievalScribe
A translator from modern english to old traditional english shakespear style

how to run

1. Start Python in the first terminal
python -m venv .venv

On Mac/Linux: source .venv/bin/activate

Then run:
python -m pip install -r backend/requirements.txt
python -m backend.download_data
python -m uvicorn backend.main:app --reload --port 8000

2. Start Vite in a second terminal
cd frontend
npm ci
npm run dev

3. Open the website
