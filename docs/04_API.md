# REST API Reference Specifications

All communication between the React frontend and Django backend occurs via standard JSON HTTP requests. This document outlines the API specifications, status codes, and authentication requirements.

---

## 1. Authentication Headers

Except for the **Register** and **Login** endpoints, all requests to the backend must include the following Authorization header:

```text
Authorization: Token <your_token_key>
```

* **Header Key**: `Authorization`
* **Header Value**: `Token ` followed by the 40-character hex key string generated at login (e.g. `Token a1b2c3d4e5f6...`).

---

## 2. Status Codes Cheat Sheet

Our APIs return standardized HTTP status codes to indicate request outcomes:

| Code | Reason | Meaning |
|---|---|---|
| **200 OK** | Success | Request succeeded. Returning requested data in body. |
| **201 Created** | Success | Resource created successfully (e.g. user registered, folder created). |
| **204 No Content** | Success | Request succeeded. No payload returned (e.g. file deleted). |
| **400 Bad Request** | Client Error | Invalid input data. Returning list of validation errors in JSON. |
| **401 Unauthorized** | Client Error | Missing or invalid Authorization header token. |
| **403 Forbidden** | Client Error | User is authenticated but does not own or have rights to the resource. |
| **404 Not Found** | Client Error | The requested ID or endpoint does not exist. |
| **500 Internal Error** | Server Error | An unhandled exception occurred in Django (e.g., database crash). |

---

## 3. Endpoints Registry

### A. Authentication App (`users/`)

#### 1. Register User
* **Method**: `POST`
* **URL**: `/api/auth/register/`
* **Auth Required**: No
* **Request Body (JSON)**:
  ```json
  {
    "username": "student1",
    "password": "securepassword",
    "email": "student1@example.com"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "token": "79b32c694a1b8d2345e67890f12c34a5b6c7d8e9",
    "user": {
      "id": 1,
      "username": "student1",
      "email": "student1@example.com"
    }
  }
  ```
* **Error Response (400 Bad Request)**:
  ```json
  {
    "username": ["A user with that username already exists."],
    "email": ["Enter a valid email address."]
  }
  ```

#### 2. Login User
* **Method**: `POST`
* **URL**: `/api/auth/login/`
* **Auth Required**: No
* **Request Body (JSON)**:
  ```json
  {
    "username": "student1",
    "password": "securepassword"
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "token": "79b32c694a1b8d2345e67890f12c34a5b6c7d8e9",
    "user": {
      "id": 1,
      "username": "student1",
      "email": "student1@example.com"
    }
  }
  ```
* **Error Response (400 Bad Request)**:
  ```json
  {
    "non_field_errors": ["Unable to log in with provided credentials."]
  }
  ```

---

### B. Folder Management App (`folders/`)

#### 1. List Root Contents (Dashboard)
Returns all folders and files belonging to the user that are stored in their root directory (i.e. parent is `null`).
* **Method**: `GET`
* **URL**: `/api/folders/`
* **Auth Required**: Yes (`Authorization: Token <key>`)
* **Success Response (200 OK)**:
  ```json
  {
    "current_folder": null,
    "subfolders": [
      {
        "id": 1,
        "name": "Work Documents",
        "created_at": "2026-07-03T10:14:00Z"
      }
    ],
    "files": [
      {
        "id": 1,
        "name": "resume.pdf",
        "file": "http://127.0.0.1:8000/media/uploads/resume.pdf",
        "size": 1048576,
        "uploaded_at": "2026-07-03T10:15:00Z"
      }
    ]
  }
  ```

#### 2. View Folder Contents
Returns folder metadata and lists all subfolders and files contained inside it.
* **Method**: `GET`
* **URL**: `/api/folders/<folder_id>/`
* **Auth Required**: Yes (`Authorization: Token <key>`)
* **Success Response (200 OK)**:
  ```json
  {
    "current_folder": {
      "id": 1,
      "name": "Work Documents",
      "parent": null,
      "created_at": "2026-07-03T10:14:00Z"
    },
    "subfolders": [
      {
        "id": 2,
        "name": "Invoices",
        "created_at": "2026-07-03T10:16:00Z"
      }
    ],
    "files": []
  }
  ```
* **Error Response (404 Not Found)**:
  ```json
  {
    "detail": "Not found."
  }
  ```

#### 3. Create Folder
Creates a new directory. If `parent` is `null`, it lives in the root directory. If `parent` is an integer, it is nested inside that folder.
* **Method**: `POST`
* **URL**: `/api/folders/`
* **Auth Required**: Yes (`Authorization: Token <key>`)
* **Request Body (JSON)**:
  ```json
  {
    "name": "Invoices",
    "parent": 1
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "id": 2,
    "name": "Invoices",
    "parent": 1,
    "created_at": "2026-07-03T10:16:00Z"
  }
  ```
* **Error Response (400 Bad Request)**:
  ```json
  {
    "name": ["This field may not be blank."],
    "parent": ["Invalid pk \"99\" - object does not exist."]
  }
  ```

---

### C. File Management App (`files/`)

#### 1. Upload File
Uploads a binary file payload. Request body MUST use `multipart/form-data` encoding.
* **Method**: `POST`
* **URL**: `/api/files/upload/`
* **Auth Required**: Yes (`Authorization: Token <key>`)
* **Request Payload (multipart/form-data)**:
  * `file`: (Binary raw bytes of file)
  * `folder`: (Optional parent folder ID integer. Omit if uploading to root)
* **Success Response (201 Created)**:
  ```json
  {
    "id": 1,
    "name": "resume.pdf",
    "file": "https://driveclone-bucket.s3.amazonaws.com/uploads/resume.pdf?AWSAccessKeyId=AKIA...",
    "size": 1048576,
    "uploaded_at": "2026-07-03T10:15:00Z",
    "folder": null
  }
  ```
* **Error Response (400 Bad Request)**:
  ```json
  {
    "file": ["This field is required."],
    "folder": ["Invalid pk \"99\" - object does not exist."]
  }
  ```

#### 2. Download File
Validates ownership and redirects the client's browser to the temporary presigned download URL on S3.
* **Method**: `GET`
* **URL**: `/api/files/<file_id>/download/`
* **Auth Required**: Yes (`Authorization: Token <key>`)
* **Success Response (302 Found)**:
  * Redirects to the S3 bucket object endpoint.
  * Headers: `Location: https://driveclone-bucket.s3.amazonaws.com/uploads/resume.pdf?AWSAccessKeyId=...`
* **Error Response (404 Not Found)**:
  ```json
  {
    "detail": "Not found."
  }
  ```

#### 3. Delete File
Deletes the file metadata row from the database and removes the physical object from the AWS S3 bucket.
* **Method**: `DELETE`
* **URL**: `/api/files/<file_id>/`
* **Auth Required**: Yes (`Authorization: Token <key>`)
* **Success Response (204 No Content)**:
  * No response body.
* **Error Response (404 Not Found)**:
  ```json
  {
    "detail": "Not found."
  }
  ```



