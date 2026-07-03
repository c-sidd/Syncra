# System Architecture & Lifecycle Flows

This document details how the frontend client, backend application server, relational database, and cloud object store interact. 

---

## 1. High-Level Architecture Diagram

Our Google Drive Clone is split into a **Client Layer**, an **Application Layer**, and a **Storage Layer**:

```text
       [ CLIENT LAYER ]
    ┌────────────────────┐
    │     React SPA      │
    │  (Axios HTTP Client)│
    └─────────┬──────────┘
              │ (HTTPS requests / JSON & Form data)
              ▼
       [ APPLICATION LAYER ]
    ┌────────────────────┐
    │  Django + DRF API  │
    └────┬──────────┬────┘
         │          │
         │ (SQL Queries)
         │          │ (boto3 SDK streams)
         ▼          ▼
   [ DATABASE ]  [ STORAGE ]
  ┌──────────┐  ┌──────────┐
  │PostgreSQL│  │  AWS S3  │
  └──────────┘  └──────────┘
```

---

## 2. Component Roles in Detail

### 1. React Frontend SPA
* **Role**: Runs in the user's browser. Renders the UI, manages UI state (loading spinners, folder trees, list views), captures inputs, and triggers API calls.
* **Role Internally**: React component states control what is rendered on screen. When state changes, React updates the virtual DOM, re-rendering only the changed elements.

### 2. Django + DRF Backend
* **Role**: Operates as a stateless API server. It receives requests, validates incoming parameters, verifies authentication credentials, queries the database, talks to AWS S3, and returns standard JSON responses.
* **Role Internally**: Django acts as the gatekeeper. It does not render HTML (like classical Django templates). Instead, Django REST Framework serializes database objects to JSON strings.

### 3. PostgreSQL Relational Database
* **Role**: The single source of truth for structural records.
* **Role Internally**: Stores table data representing:
  * Users (username, email, password hashes).
  * Folders (ID, name, parent folder pointer).
  * Files (ID, physical file name, S3 object key, file size, content type, parent folder pointer).

### 4. AWS S3 Cloud Storage
* **Role**: Stores raw bytes.
* **Role Internally**: It is a key-value store in the cloud. We push a file stream to S3, associated with a key (e.g. `user_1/files/document_4.pdf`). In return, S3 stores it and allows retrieval via signed URLs.

---

## 3. End-to-End Request Lifecycles

### Flow A: Authentication Lifecycle (Login)

```text
Browser/React           Django REST API / Database
   │                                │
   │─── 1. POST /api/auth/login ───>│
   │    (username, password)        │── 2. Query user record ──> [PostgreSQL]
   │                                │<─ 3. Return user hash ───
   │                                │
   │                                │── 4. Verify password hash using PBKDF2
   │                                │── 5. Generate Auth Token
   │                                │── 6. Save Token associated with User ──> [PostgreSQL]
   │<── 7. Return Token (JSON) ─────│
   ▼
[Store Token in LocalStorage]
```

### Flow B: File Upload Lifecycle

```text
Browser/React                   Django API                      S3 & PostgreSQL
   │                                │                                  │
   │── 1. POST /api/files/upload ──>│ (Validate token & size)          │
   │   (File payload & folder_id)   │                                  │
   │                                │── 2. Stream bytes to S3 ────────>│ [AWS S3]
   │                                │<─ 3. Confirm upload success ─────│
   │                                │                                  │
   │                                │── 4. INSERT file metadata ──────>│ [PostgreSQL]
   │                                │      (S3 object key & name)      │
   │<─ 5. Return success (JSON) ────│                                  │
```

### Flow C: File Download Lifecycle

```text
Browser/React                   Django API                      AWS S3
   │                                │                              │
   │── 1. GET /api/files/X/download>│ (Verify user ownership in DB)│
   │                                │                              │
   │                                │── 2. Compute Presigned URL ──> (Internal Crypto Check)
   │                                │<─ 3. Return Presigned URL ───│
   │<─ 4. Return URL to React ──────│                              │
   │                                                               │
   │── 5. GET URL directly from S3 ───────────────────────────────>│
   │<─ 6. Streams bytes directly to Client ────────────────────────│
```
