# Deployment

MongoDB stores accounts, career records, roadmap completion, resume analysis, career intelligence, and interview sessions. The backend does not fall back to JSON files.

## Local Development

1. Install dependencies from the project directory: `pip install -r backend/requirements.txt`.
2. Copy `.env.example` to `.env` and set `MONGODB_URI` to a reachable MongoDB instance.
3. Start the API from the project directory: `python backend/api.py`.
4. Serve `frontend/` on port `5500`; the frontend config selects the local API automatically.

## Production

1. Set `APP_ENV=production` and provide a stable, randomly generated `SECRET_KEY` of at least 32 characters. The server refuses production startup without it.
2. Set `MONGODB_URI` and `MONGODB_DATABASE` through the deployment secret/configuration manager.
3. Set `CORS_ORIGINS` to comma-separated HTTPS frontend origins when frontend and API use different origins. Localhost and HTTP origins are rejected in production.
4. Configure `frontend/config.js` with the deployed API base URL when the frontend is not served from the API's origin.
5. Run from `backend/` with a production WSGI server, for example: `gunicorn --workers 2 --bind 0.0.0.0:5000 api:app`.
6. Terminate TLS at a trusted reverse proxy and configure it to forward the original host/protocol headers.
7. Monitor `GET /api/health/ready`; it returns 503 when MongoDB cannot be reached. `GET /api/status` is a liveness check only.

Resume uploads, optimized files, and explicit CSV/TXT exports remain filesystem assets. Deployments must provide persistent storage and backups for `uploads/`, or move those assets to object storage before using ephemeral containers. Keep `.env` out of source control and use a managed secrets store in production.