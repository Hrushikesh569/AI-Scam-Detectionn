# AI Scam Detection System

This project combines a React/Vite frontend with a FastAPI backend to analyze chat or SMS text for scam signals.

## What You Need

- Node.js 18+
- Python 3.10+
- Optional: a Gemini API key if you want the LLM fallback layer enabled

## Setup After Cloning

1. Install the frontend dependencies from the project root:

	```bash
	npm install
	```

2. Create and activate a Python virtual environment, then install the backend dependencies:

	```bash
	cd backend
	python -m venv .venv
	.venv\Scripts\activate
	pip install -r requirements.txt
	```

3. If you want Gemini support, create a `backend/.env` file with:

	```env
	GEMINI_API_KEY=your_api_key_here
	```

## Run the Backend

From the `backend` folder, start the API on port `8000`:

```bash
python main.py
```

You can also use Uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API exposes `POST http://localhost:8000/analyze`.

## Run the Frontend

Open a second terminal in the project root and start the Vite app:

```bash
npm run dev
```

Then open the local URL shown by Vite, usually `http://localhost:5173`.

The frontend sends analysis requests to `http://localhost:8000/analyze`, so make sure the backend is running first.

## Notes

- The backend creates its SQLite database automatically on startup.
- Some large trained model artifacts are not committed to git because they exceed GitHub limits. The backend still runs without the optional DistilBERT weights.
- If you retrain the models, keep generated checkpoints and local database files out of version control.
