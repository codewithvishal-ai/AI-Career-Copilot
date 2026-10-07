# AI Career Copilot

## About

AI Career Copilot is an AI-assisted career development platform that helps people turn career goals into practical next steps. Explore career paths, build and track learning roadmaps, improve resumes, find relevant courses, and practice interviews in one place.

The application combines a browser-based frontend with a Flask API and MongoDB-backed accounts and career data. Optional integrations provide AI-powered guidance, interview speech features, and YouTube learning-resource search.

## Features

- Account registration and login
- Career dashboard and career intelligence
- AI-assisted career roadmaps, progress tracking, and roadmap chat
- Resume analysis, job matching, resume generation, and optimization
- Course suggestions and YouTube learning-resource search
- Interview practice with evaluation, reports, and optional speech features

## Tech stack

- **Frontend:** HTML, CSS, and JavaScript served as static files
- **Backend:** Python, Flask, and Flask-CORS
- **Database:** MongoDB
- **Optional integrations:** Google Gemini, ElevenLabs, and YouTube Data API

## Requirements

- Python with `pip`
- A running MongoDB instance or a MongoDB connection string
- A modern web browser

Node.js is not required to serve the frontend.

## Run locally

Run these commands from the repository root.

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   On macOS or Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the backend dependencies:

   ```bash
   python -m pip install -r backend/requirements.txt
   ```

3. Create a local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

   On macOS or Linux, use `cp .env.example .env`. Set `MONGODB_URI` in `.env` to a reachable MongoDB instance. The example uses `mongodb://127.0.0.1:27017`.

4. Start the API in one terminal:

   ```bash
   python backend/api.py
   ```

   The API defaults to `http://127.0.0.1:5000`.

5. In a second terminal, serve the frontend from the repository root:

   ```bash
   python -m http.server 5500 --directory frontend
   ```

6. Open [http://127.0.0.1:5500](http://127.0.0.1:5500).

The frontend automatically uses the local API when served on `localhost` or `127.0.0.1` at port `5500` or `8000`. To use a different API URL, set `window.CAREER_COPILOT_API_URL` before `frontend/config.js` runs.

## Configuration

Copy `.env.example` to `.env` and configure values for your environment:

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | Application environment; use `production` for production deployments. |
| `SECRET_KEY` | Flask signing key. Production requires a randomly generated key of at least 32 characters. |
| `MONGODB_URI` | MongoDB connection URI. |
| `MONGODB_DATABASE` | MongoDB database name. |
| `CORS_ORIGINS` | Comma-separated frontend origins when the frontend and API have different origins. |
| `HOST` | API bind address; defaults to `0.0.0.0`. |
| `PORT` | API port; defaults to `5000`. |
| `AUTH_TOKEN_MAX_AGE` | Authentication-token lifetime in seconds. |
| `GEMINI_API_KEY` | Optional Google Gemini key for AI interview features. |
| `ELEVENLABS_API_KEY` | Optional ElevenLabs key for speech features. |
| `ELEVENLABS_VOICE_ID` | Optional ElevenLabs voice identifier. |
| `YOUTUBE_API_KEY` | Optional YouTube Data API key for learning-resource search. |

Never commit `.env` or real API keys. `.env.example` contains placeholders only. Optional integrations may be unavailable until their keys are configured.

## Production deployment

See [MONGODB_SETUP.md](./MONGODB_SETUP.md) for database and deployment notes. In brief:

- Set `APP_ENV=production` and provide a secure `SECRET_KEY`.
- Configure MongoDB and store secrets with your deployment platform.
- Set `CORS_ORIGINS` to the HTTPS frontend origins when deploying the frontend and API separately.
- Configure the frontend API base URL for the deployed API.
- Run the Flask application with a production WSGI server, such as Gunicorn, behind a TLS-terminating reverse proxy.
- Provide persistent storage and backups for `uploads/` and generated resume files.
- Monitor `/api/health/ready` for API and database readiness; `/api/status` is a liveness check.

## Project structure

```text
backend/       Flask API, career features, interview engine, and services
frontend/      Static web pages and browser-side JavaScript
.env.example   Environment-variable template
MONGODB_SETUP.md
               Database and deployment guidance
```
