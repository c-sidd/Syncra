# How Google Drive Works: Storage Systems & Decoupling

Before writing code, it is essential to understand the systems architecture behind real-world cloud storage services like Google Drive. This document explains how files are handled, stored, and managed at scale.

---

## 1. What Happens When a File is Uploaded?

When a user uploads a file through a web browser, the process goes through several distinct layers:

```text
[ Browser / Client ] 
        │  (File Uploaded via HTTP Multipart Form Request)
        ▼
[ API Web Server ] 
        │  (Authentication & Serializer Validation)
        ├──────────────────────────┐
        │                          │
        ▼ (Raw File Stream)        ▼ (Metadata: Name, Size, Path)
[ Object Storage (AWS S3) ]  [ Relational Database (PostgreSQL) ]
```

1. **Client Action**: The user selects a file and clicks "Upload". The browser splits the file into standard chunks and wraps it in an HTTP `POST` request using `multipart/form-data` encoding.
2. **Server Routing**: The backend web server (e.g., Django) receives the request. It first authenticates the user, then parses the request stream.
3. **Storage Decoupling**: 
   * The **raw file data** is sent directly to an **Object Storage service** (like AWS S3).
   * The **metadata** (file name, size, upload timestamp, ownership, and S3 object location key) is stored in a **Relational Database** (like PostgreSQL).
4. **Response**: The server returns a JSON response indicating whether the upload succeeded.

---

## 2. Why Google Drive Doesn't Store Files in a Database

A common beginner mistake is attempting to store files directly inside database tables using binary types (like PostgreSQL `BYTEA` or SQL Server `VARBINARY`), commonly known as **BLOBs** (Binary Large Objects). 

### Why BLOB Storage in DBs is Bad Practice:
* **Memory & Performance**: Databases load rows into memory (RAM) to run queries. If a row contains a 50MB PDF or a 1GB video, it consumes excessive RAM, slowing down query speeds for all users.
* **Database Scaling is Expensive**: Relational databases scale vertically (requiring faster CPU, more RAM, and fast SSDs). Scaling storage in a relational database is hundreds of times more expensive than storing raw bytes on distributed hard drives.
* **Backup and Recovery**: Backing up a 10GB database takes seconds. Backing up a 1TB database that contains raw files takes hours, locking database tables and risking downtime.

### The Decoupled Solution:
We store **Metadata** in the database (fast, searchable, indexed) and **Raw Files** in object storage (cheap, highly scalable, durable).

---

## 3. Why Object Storage (AWS S3) is Used

Cloud providers design **Object Storage** (such as AWS Simple Storage Service, or S3) specifically for unstructured data (images, videos, PDFs, zip files).

### Key Concepts:
* **Buckets**: Think of a bucket as a root directory in the cloud. It has a globally unique name and holds your files.
* **Objects**: In object storage, files are called "Objects". An object consists of the file data (bytes) and a unique identifier called the **Object Key** (e.g., `uploads/user_1/my_document.pdf`).
* **Flat Structure**: S3 does not have real folders. It is a flat key-value store. S3 *simulates* folders by using forward slashes (`/`) in the object key.
* **Durable and Scalable**: AWS S3 automatically replicates files across multiple data centers, offering 99.999999999% durability.

---

## 4. How Folders Are Represented

In a computer's operating system, folders are real physical directories on a disk. In a cloud storage web app, folders are modeled logically in a database table.

We use the **Adjacency List Pattern** to model directories in our relational database:

| folder_id | name | parent_folder_id (Foreign Key) | user_id |
|-----------|------|---------------------------------|---------|
| 1         | Root | NULL                            | 1       |
| 2         | Docs | 1                               | 1       |
| 3         | PDFs | 2                               | 1       |

### How It Works:
* Every folder is a database row.
* A folder has a pointer (`parent_folder_id`) that references another folder's primary key (`folder_id`).
* If `parent_folder_id` is `NULL`, it means the folder resides in the user's root directory.
* When a user requests a folder's contents, we query the database: 
  * "Give me all folders where `parent_folder_id = X`."
  * "Give me all files where `folder_id = X`."

---

## 5. How Downloads Work (Signed URLs)

Instead of the backend server downloading a file from S3 and proxying it to the client (which wastes server bandwidth and RAM), we use **Signed URLs** (or Presigned URLs).

```text
Browser                 Django Server                   AWS S3
   │                          │                           │
   │─── 1. Click Download ───>│                           │
   │                          │── 2. Request Signed URL ──> (Internal calculation using credentials)
   │                          │<── 3. Return Signed URL ──│
   │<── 4. Return URL (JSON) ─│                           │
   │                                                      │
   │────────────────────── 5. GET Signed URL ────────────>│
   │<───────────────────── 6. Streams Bytes ──────────────│
```

1. The client requests to download a file.
2. The Django server verifies the user's permission to access that file metadata.
3. Django uses AWS credentials to generate a temporary, cryptographically signed URL (valid for e.g., 15 minutes).
4. The server returns this URL to the browser.
5. The browser directly fetches the file from S3 using the signed URL. S3 validates the signature and streams the file to the user's machine.

---

## 6. How Deletions Work

Deleting a file requires coordinated cleanup in both layers:
1. **Database Update**: The server deletes the file metadata row from the PostgreSQL database.
2. **Object Storage Update**: The server sends a delete request to AWS S3 using the object key to remove the raw bytes.
* *Note*: If we only delete it from S3, the database contains broken links. If we only delete it from the database, we waste money storing orphaned files on S3.
