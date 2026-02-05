# Food Image Segmentation & Nutrition Analysis (Django)
<img width="1881" height="304" alt="Screenshot 2026-02-05 210341" src="https://github.com/user-attachments/assets/902e9182-1bb7-4ee9-b9a3-cc28ec1a5485" />

A Django web app where users can register, upload food photos, and receive:

- food segmentation output image
- ingredient area estimates (JSON)
- nutrition analysis computed from a reference CSV

This repo is a portfolio snapshot of an older project; the original model inference ran on a separate machine.

<img width="1650" height="444" alt="專題海報 69104 (2)" src="https://github.com/user-attachments/assets/f0a66fc0-1336-4aae-945a-a48d658d8610" />

## Tech stack
- Django
- Paramiko (SSH/SFTP) for remote inference orchestration
- Remote inference via `docker exec ...` (configurable)

## Security note
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

## Remote inference
Set `INFERENCE_MODE=remote` and fill the `INFERENCE_*` variables in your `.env`.

At minimum:
- `INFERENCE_SSH_HOST`, `INFERENCE_SSH_PORT`, `INFERENCE_SSH_USER`, `INFERENCE_SSH_PASSWORD`
- `INFERENCE_REMOTE_UPLOAD_PATH`, `INFERENCE_REMOTE_SEGMENTED_PATH`, `INFERENCE_REMOTE_JSON_PATH`
- optionally `INFERENCE_DOCKER_COMMAND`
