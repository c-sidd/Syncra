# Relational Databases & PostgreSQL Reference Guide

Relational databases store data in structured tables with rows (records) and columns (attributes), enforcing relational constraints (foreign keys, check rules) to ensure data integrity.

---

## 1. Database Decision Matrix

When building a backend, choosing the right database depends on scale, concurrency, and relationships:

| Feature / Detail | SQLite | MySQL / MariaDB | PostgreSQL (Chosen) |
|---|---|---|---|
| **Architecture** | File-based (embedded in application process). | Client-Server (separate server daemon process). | Client-Server (separate process with process-per-connection pool). |
| **Concurrency** | Single-writer lock. If one request writes, others are blocked. | Multi-writer using row-level locking. | Advanced Multi-Version Concurrency Control (MVCC) for high concurrent reads/writes. |
| **Data Types** | Weak typing (allows string inside integer columns). | Standard SQL typing. | Strict typing, robust JSONB support, geometric types, array columns. |
| **Use Case** | Local testing, mobile apps, low-traffic sites. | Generic CRUD apps, web hosting, e-commerce. | Enterprise applications, complex query analysis, relational parent-child systems. |

---

## 2. Why PostgreSQL is Chosen for this Project
1. **Concurrency**: Unlike SQLite, PostgreSQL does not lock the entire database file during writes. It manages multiple parallel connections from web workers simultaneously using MVCC.
2. **Relational Integrity**: Perfect for modeling parent-child relationships like nested folders. PostgreSQL strictly enforces foreign keys, verifying that child folders point to valid parent records.
3. **Data Type Richness**: Supports array data types and native JSON indexing, which is highly useful when scaling metadata tracking systems.

---

## 3. The Python Database Adapter (`psycopg2`)

Django is written in Python; PostgreSQL is written in C. They cannot talk directly without a driver (database adapter).

```text
  [ Django App (Python) ]
             │ (Python ORM Calls: e.g. Folder.objects.all())
             ▼
  [ django.db.backends.postgresql ] (Django Internal DB engine wrapper)
             │
             ▼
  [ psycopg2 (C-module binary driver) ]
             │ (Translates SQL string + Python types into wire-protocol packets)
             ▼
  [ PostgreSQL Database Server ]
```

* **What is `psycopg2`?**: It is the standard PostgreSQL database adapter for Python. It implements the Python DB-API 2.0 specification, allowing Python code to open network sockets, send SQL query strings, handle transaction rollbacks, and translate database types (like Postgres TIMESTAMP) into Python types (like datetime objects).
* **`psycopg2` vs `psycopg2-binary`**:
  * `psycopg2`: Installs from source code. Compiles C code during installation, requiring Postgres developer headers (`libpq-dev` on Linux) and C compilers on the host system.
  * `psycopg2-binary` (Used here): A pre-compiled wheel package that includes pre-built C library files. It installs instantly without compiling, which is perfect for local development.

---

## 4. Connection Lifecycle

Every query run by the backend travels through this sequence:
1. **Connection Pooling**: Django opens a network TCP socket connection to PostgreSQL (default port `5432`).
2. **Transaction Start**: Django starts a transaction (`BEGIN`).
3. **Query Execution**: Django passes the compiled SQL statement to `psycopg2`, which sends it over the socket.
4. **Data Deserialization**: PostgreSQL executes the query, returns binary rows, and `psycopg2` parses the columns into Python lists/tuples.
5. **Commit / Rollback**: If the view completes successfully, Django sends `COMMIT`. If an error occurs, it sends `ROLLBACK` to revert database alterations.

---

## 5. Logical Schema Maps

Here is how our Python models map physically to PostgreSQL relational database tables:

### A. Folders Table (`folders_folder`)
| Column Name | PostgreSQL Data Type | Relational Constraint / Key | Purpose |
|---|---|---|---|
| `id` | `BIGINT` | `PRIMARY KEY` (Auto-incrementing) | Unique folder identifier. |
| `name` | `VARCHAR(255)` | None | Display folder name. |
| `user_id` | `BIGINT` | `FOREIGN KEY REFERENCES auth_user(id)` | Identifies the owner user. |
| `parent_id` | `BIGINT` | `FOREIGN KEY REFERENCES folders_folder(id)` (Allows NULL) | Reference to parent folder. NULL represents root. |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | None | Stamped automatically on row creation. |

### B. Files Table (`files_file`)
| Column Name | PostgreSQL Data Type | Relational Constraint / Key | Purpose |
|---|---|---|---|
| `id` | `BIGINT` | `PRIMARY KEY` (Auto-incrementing) | Unique file identifier. |
| `name` | `VARCHAR(255)` | None | Original display name of file. |
| `file` | `VARCHAR(100)` | None | String path pointing to file in object storage. |
| `user_id` | `BIGINT` | `FOREIGN KEY REFERENCES auth_user(id)` | Identifies the owner user. |
| `folder_id` | `BIGINT` | `FOREIGN KEY REFERENCES folders_folder(id)` (Allows NULL) | Folder where file is placed. NULL represents root. |
| `size` | `BIGINT` | None | File size in bytes. |
| `uploaded_at` | `TIMESTAMP WITH TIME ZONE` | None | Stamped automatically on upload. |

### Relational Integrity (Cascading Deletes)
In both tables, `on_delete=models.CASCADE` is configured on foreign key constraints.
* If a User is deleted, PostgreSQL automatically runs cascading deletion rules: deleting all corresponding records in `folders_folder` and `files_file` matching their `user_id`.
* If a parent Folder is deleted, PostgreSQL cascades: deleting all nested subfolders where `parent_id` equals the folder ID, and deleting all files where `folder_id` equals the folder ID. This guarantees no orphaned rows remain in our database.

