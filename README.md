# ☁️ Syncra

**Your S3. Your files. One clean interface.**

Syncra is a full-stack cloud storage manager built with React, Django REST Framework, PostgreSQL and AWS S3. Instead of opening the AWS Console every time you need a file, you connect your own S3 bucket once and manage it from Syncra.

## ✨ What Syncra Does

- 🔐 Register, login and logout
- ☁️ Connect **your own AWS S3 bucket** from Account settings
- 🔒 Encrypt the stored S3 secret key at rest
- 📤 Upload files directly to your bucket
- 📥 Download through short-lived S3 presigned URLs
- 🗑️ Delete S3 objects from Syncra
- 📁 Create and browse nested folders
- 🧊 Configure S3 Lifecycle transitions to Intelligent-Tiering, Standard-IA, Glacier, Glacier Instant Retrieval or Deep Archive
- 👤 Keep each user's objects isolated under a user-specific S3 prefix

## 🏗️ Architecture

```text
React + Vite
     │
     │ Token-authenticated API
     ▼
Django REST Framework
     │
     ├── PostgreSQL ── users, folders, file metadata
     │
     └── boto3 ─────── user's AWS S3 bucket
                          │
                          ├── Upload
                          ├── Presigned Download
                          ├── Delete
                          └── Lifecycle → Glacier / Archive
```

Syncra does **not** require your AWS root credentials. Create a dedicated IAM identity with only the S3 permissions the application needs.

## 🛠️ Stack

- **Frontend:** React 19 + Vite + Tailwind CSS
- **Backend:** Django 4.2 + Django REST Framework
- **Database:** PostgreSQL
- **Cloud:** AWS S3 + boto3
- **Auth:** DRF token authentication
- **Security:** encrypted S3 secret storage + ownership checks + presigned downloads

## 🚀 Local Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env` using `.env.example`.

Generate a Fernet encryption key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Put that value into `CREDENTIAL_ENCRYPTION_KEY`.

Then:

```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## 🔑 Connecting AWS

1. Create an S3 bucket in your AWS account.
2. Create a dedicated IAM user/role for Syncra with the required S3 permissions.
3. Copy its Access Key ID and Secret Access Key.
4. Open **Syncra → Account**.
5. Enter the bucket name and AWS region.
6. Click **Connect S3**.
7. Syncra tests the connection before saving it.

The secret key is never returned by the Account API after it is stored.

## 🧊 Glacier Automation

Syncra can create an S3 Lifecycle rule scoped to the current user's prefix:

```text
new file
   ↓
S3 Standard
   ↓  after N days
Intelligent-Tiering / Standard-IA / Glacier
   ↓
optional deeper archive policies in AWS
```

Lifecycle transitions are handled by **Amazon S3**, not by a background process running inside Syncra.

## ⚠️ Security Notes

- Never commit `.env` files or AWS credentials.
- Never use an AWS root access key for Syncra.
- Give the IAM identity only the S3 permissions it actually needs.
- Keep `DJANGO_SECRET_KEY` and `CREDENTIAL_ENCRYPTION_KEY` private.
- The repository previously contained a hardcoded Django secret; it has been removed from the source. If that old secret was ever used outside local development, rotate it.

## 🧪 Tests

```bash
cd backend
python manage.py test
```
