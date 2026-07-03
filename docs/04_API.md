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
