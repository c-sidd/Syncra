# Project Overview & Scope Definition

This document defines the requirements, scope constraints, tech stack, and foundational design decisions for our Google Drive Clone.

---

## 1. Project Goal

The primary objective is **educational**. This codebase is built as a learning platform to teach full-stack architecture, relational database modeling, cloud integration, API lifecycle, and modern UI state management.

---

## 2. Technology Stack & Component Roles

| Tech | Role | Reason / Why |
|---|---|---|
| **React (Vite)** | Frontend SPA | High performance, rich developer ecosystem, component-based, quick UI updates via Virtual DOM. |
| **Tailwind CSS** | Styling Utility | Rapid UI development, responsive utilities, maintains consistent spacing/color system without heavy CSS files. |
| **Axios** | HTTP Client | Simple promise-based API, automatic JSON transformation, easy interceptors for authorization headers. |
| **React Router** | Navigation | Client-side routing for SPA experience. User navigates pages without page-reloads. |
| **Django** | Backend Framework | High security defaults, built-in ORM, batteries-included (manages routing, admin tools, middleware). |
| **Django REST Framework (DRF)** | API Layer | Translates Django models into RESTful JSON endpoints, handles request validation, and serialization. |
| **PostgreSQL** | Relational Database | Enterprise-grade, supports transactions, strong relational integrity (perfect for modeling folder trees). |
| **AWS S3** | Cloud Object Storage | Scalable, highly available, secure, industry-standard for raw unstructured file storage. |

---

## 3. Features Matrix

### In-Scope Features (We will build these):
1. **User Authentication**: Secure user registration, login, logout, and credential validation (Token Auth).
2. **Dashboard Views**: View files and folders in a clean layout.
3. **Folder Management**: Create, nest, and list directories using the Adjacency List Database pattern.
4. **File Management**: Upload files, download files via signed URLs, and delete files.
5. **AWS Cloud Sync**: Stream file contents directly from Django up to S3 bucket.

### Out-of-Scope Features (Explicitly excluded to keep codebase focused):
* File sharing & collaborator permissions.
* Global search bar.
* Version history / file recovery.
* Realtime updates or collaborative editing.
* Drag-and-drop file operations.
* Admin panel customizing frontend.
* In-app notifications.

---

## 4. Key Design Decisions (Why vs Alternatives)

### Backend: Django vs Flask vs FastAPI
* **Flask**: Extremely minimal. Good for tiny apps, but you must choose and install database plugins, auth systems, and folder architectures manually. Too fragmented for beginners.
* **FastAPI**: Modern, fast, and uses Python type hints. Great for pure API services. However, it lacks a mature built-in ORM (like Django's) out of the box.
* **Django (Chosen)**: "Batteries included". Offers Django ORM, built-in security features, and migrations right out of the box. It teaches standard backend patterns (Models, Views, Middleware) that translate to frameworks like Ruby on Rails or Spring Boot.

### Database: PostgreSQL vs SQLite vs MongoDB
* **SQLite**: Runs as a local file. Good for dev, but does not support concurrent write operations well, nor does it scale to cloud deployments.
* **MongoDB**: A NoSQL document database. Excellent for loose, unstructured documents. However, modeling nested folders (relational parent-child trees) is safer and cleaner using Relational Database constraints (Foreign Keys).
* **PostgreSQL (Chosen)**: Standard relational database used in production environments. Enforces relational safety (cascading deletes, foreign key checks).

### Storage: Local Disk Storage vs AWS S3
* **Local Disk**: Storing files on the backend server's local hard drive works for single-server setups. However, if the server restarts or scales horizontally (spins up a second server), files uploaded to Server A are not accessible by Server B.
* **AWS S3 (Chosen)**: A centralized file warehouse. No matter how many backend servers we spin up, they all read and write from the same S3 bucket.
