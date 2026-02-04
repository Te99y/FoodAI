# Food Image Segmentation & Nutrition Analysis (Django)

A Django web app where users can register, upload food photos, and receive:
- food segmentation output image
- ingredient area estimates (JSON)
- nutrition analysis computed from a reference CSV

This repo is a portfolio snapshot of an older project; the original model inference ran on a separate machine.

## Tech stack
- Django
- Paramiko (SSH/SFTP) for remote inference orchestration
- Remote inference via `docker exec ...` (configurable)

## Security note (important)
**No credentials are stored in this repo.**  
If you want to use the original remote-inference flow, provide secrets via environment variables (see `.env.example`).

## Quick start (demo mode)
Demo mode skips SSH and uses local placeholder outputs so the app can be started without access to the inference machine.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env (INFERENCE_MODE=demo is the default in the example)

python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000/

## Remote inference (optional)
Set `INFERENCE_MODE=remote` and fill the `INFERENCE_*` variables in your `.env`.

At minimum:
- `INFERENCE_SSH_HOST`, `INFERENCE_SSH_PORT`, `INFERENCE_SSH_USER`, `INFERENCE_SSH_PASSWORD`
- `INFERENCE_REMOTE_UPLOAD_PATH`, `INFERENCE_REMOTE_SEGMENTED_PATH`, `INFERENCE_REMOTE_JSON_PATH`
- optionally `INFERENCE_DOCKER_COMMAND`

## What I would improve next
- Replace SSH/SFTP orchestration with an HTTP inference API (FastAPI) + queue (Celery/RQ)
- Add tests for the nutrition calculation pipeline
- Containerize with Docker Compose for reproducible dev setup
