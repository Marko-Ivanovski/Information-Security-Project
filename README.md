# Secure File Sharing System with Zero Knowledge Proof Authentication

A lightweight Flask-based application that allows users to securely register, log in, and manage their private files without ever exposing passwords. Authentication is handled via a Zero Knowledge Proof (ZKP) protocol (e.g. Schnorr), so the user’s secret never leaves the browser. Uploaded files are (optionally) encrypted on disk and stored in a Docker volume, with metadata saved in PostgreSQL.

## Features
- **ZKP Registration & Login**: Users create a secret locally; only a public value is sent to the server. Login uses a challenge–response proof instead of a password.
- **File Upload/Download/Delete**: After login, users can upload files (automatically encrypted), list their files on a dashboard, download them, or delete them.
- **Secure Storage**: Files are stored under a per-user directory in a Docker volume; PostgreSQL tracks metadata (filename, hash, timestamps, etc.).
- **Dockerized**: The entire stack (Flask app, Postgres, file-storage volume) runs via Docker Compose for easy setup and portability.

## Tech Stack
- **Backend**: Python · Flask · SQLAlchemy
- **Database**: PostgreSQL (in Docker)
- **Authentication**: Schnorr-style Zero Knowledge Proof
- **Storage**: Filesystem volume (inside Docker) with optional symmetric encryption (Fernet)
- **Deployment**: Docker Compose

---

```bash
# Quick start (after cloning):
docker-compose up --build
# Visit http://localhost:5000 to register, log in, and manage files.
