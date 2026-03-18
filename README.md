# Tempest — Secure File Sharing with Self-Destruct Links

[![Django](https://img.shields.io/badge/Django-5.0+-092e20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Cloudflare R2](https://img.shields.io/badge/Cloudflare-R2-f38020?style=for-the-badge&logo=cloudflare)](https://www.cloudflare.com/products/r2/)
[![Encryption](https://img.shields.io/badge/AES--256-Fernet-blue?style=for-the-badge&logo=lock)](https://cryptography.io/)

**Tempest** is a privacy-first, ephemeral file-sharing platform designed for maximum security and minimal footprint. Built on Django and Cloudflare R2, it provides a "Snapchat for files" experience where every link is a ticking clock.

---

## Features

- **AES-256 Encryption**: Every file is encrypted on-the-fly using unique keys that never touch long-term storage.
- **Self-Destruct Links**: Files automatically vanish based on your rules — one-time downloads or customizable timer limits (1hr - 7days).
- **Cloudflare R2 Storage**: Globally distributed, high-performance object storage with zero egress fees.
- **Live Access Logs**: Real-time auditing of file lifecycle, from encrypted upload to permanent destruction.
- **Password Protection**: Optional second layer of defense with industry-standard hashing.
- **Celery Automation**: Asynchronous background workers for guaranteed data purging and cache management.

---

## Tech Stack

- **Core**: Django 5.0+, Python 3.10+
- **Storage**: Cloudflare R2 (S3 Compatible API)
- **Database**: SQLite (Local) / Cloudflare D1 (Edge)
- **Task Queue**: Celery + Redis
- **Security**: Cryptography (Fernet), Django Ratelimit
- **Deployment**: Render / Docker

---

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/sedegahkim/tempest.git
cd tempest
```

### 2. Set Up Environment
Create a `.env` file based on `.env.example`:

```env
# Cloudflare R2
CLOUDFLARE_R2_ACCOUNT_ID="your_account_id"
CLOUDFLARE_R2_SECRET_ACCESS_KEY="your_api_token"
CLOUDFLARE_R2_STORAGE_BUCKET_NAME="tempest-fileshare"
CLOUDFLARE_R2_PUBLIC_URL="https://pub-your-id.r2.dev"

# Django
SECRET_KEY="your_django_secret_key"
DEBUG=True
ALLOWED_HOSTS="localhost,127.0.0.1"
```

### 3. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
python manage.py migrate
python manage.py runserver
```

---

## Architecture

Tempest uses a decoupled architecture where the Django backend serves as the orchestration layer for Cloudflare's edge services. Files are streamed directly through a custom storage backend that handles on-the-fly encryption/decryption, ensuring that the raw data is never persisted in a vulnerable state.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Contact
Built by **sedegahkim** - [sedegahkim@gmail.com](mailto:sedegahkim@gmail.com)

Project Link: [https://github.com/sedegahkim/tempest](https://github.com/sedegahkim/tempest)
