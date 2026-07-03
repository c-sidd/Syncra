# AWS S3 Cloud Object Storage Reference Guide

Amazon Simple Storage Service (S3) is an object storage service offering industry-leading scalability, data availability, security, and performance.

---

## 1. What is Object Storage?

Traditional file systems (like NTFS on Windows or ext4 on Linux) use **Block Storage**, where files are split into sectors and organized in a hierarchical tree of folders. 

Object Storage is a **Flat Key-Value Store**. Instead of files and folders, S3 stores **Objects** inside **Buckets**.

```text
[ BLOCK STORAGE ]                       [ OBJECT STORAGE ]
    Root/                                  Root Bucket: "driveclone-bucket"
    ├── Docs/                              ├── Object Key: "uploads/resume.pdf"
    │   └── resume.pdf                     └── Object Key: "uploads/work/invoice.jpg"
    └── Images/
        └── photo.jpg
```

* **No Real Folders**: The path `uploads/work/invoice.jpg` is a single string key. S3 does not have physical subdirectories. S3 simply scans for forward slashes (`/`) in keys to *simulate* folder structures in visual user interfaces.
* **Metadata**: Every object in S3 consists of:
  * **Key**: The unique string ID (e.g. `uploads/resume.pdf`).
  * **Value**: The raw bytes of the file itself.
  * **Metadata**: Key-value pairs describing the object (e.g., Content-Type: `application/pdf`, Size: `1048576`).

---

## 2. Why Not Store Files Inside databases (PostgreSQL)?
1. **Database Bloat**: Database tables are loaded into system memory to execute indexes. Storing binary bytes (BLOBs) slows down index scans.
2. **Horizontal Scaling**: If your application scales to run on three servers, a local file system is isolated to each server. Object Storage (S3) acts as a centralized cloud file warehouse that all servers connect to.
3. **Cost**: Database storage SSDs are expensive. S3 storage costs a fraction of database disk space.

---

## 3. Storage Security (Private Buckets & Presigned URLs)

For a Google Drive Clone, **security is paramount**. Files uploaded to S3 should **never** be publicly readable on the internet.

```text
  [ Client Browser ]             [ Django Backend ]                [ AWS S3 Bucket ]
          │                              │                                 │
          │── 1. GET /api/files/5/ ─────>│                                 │
          │   (Authorization: Token)     │ (Verify ownership)              │
          │                              │── 2. Request Signed URL ───────> (Generate signature using AWS secrets)
          │                              │<─ 3. Return Signed URL ─────────│
          │<─ 4. Returns URL (JSON) ─────│                                 │
          │                              (Valid for 15 minutes)            │
          │                                                                │
          │── 5. GET Presigned URL ───────────────────────────────────────>│ (Verify signature matches credentials)
          │<─ 6. Streams Bytes directly to Client ─────────────────────────│
```

1. **Private by Default**: The S3 bucket is configured to block all public access. Only our backend server (using IAM keys) can read/write objects.
2. **Presigned URLs**: When a user wants to view/download a file, our Django backend runs a cryptographic signature calculation using its AWS secret keys. It generates a temporary download URL that contains an authentication signature token:
   `https://driveclone-bucket.s3.amazonaws.com/uploads/resume.pdf?AWSAccessKeyId=AKIA...&Expires=170000000&Signature=xyz...`
3. **Expiration**: This URL is valid for a short window (e.g., 15 minutes). After expiration, S3 rejects requests, ensuring files remain private.
