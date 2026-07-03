# Frontend Client Reference Guide

This document outlines the architecture, layout structures, page routing systems, and state management pattern of our React/Vite client application.

---

## 1. Directory Architecture

To keep the codebase maintainable as it grows, we partition our React sources (`src/`) into modular concerns:

```text
frontend/src/
├── components/          # Reusable, stateless visual widgets
│   ├── PrivateRoute.jsx # Router guard preventing access by unauthenticated users
│   ├── CreateFolderModal.jsx
│   ├── UploadFileModal.jsx
│   └── Navbar.jsx
├── context/             # Global application state (Context API)
│   └── AuthContext.jsx  # Tracks login status, tokens, and active user profile
├── pages/               # Main view containers (connected to Router)
│   ├── Login.jsx        # Login & Signup view forms
│   └── Dashboard.jsx    # Cloud storage folder and file explorer
├── utils/               # Logic utilities
│   └── api.js           # Axios instance preconfigured with base url and headers
├── index.css            # Base stylesheet containing Tailwind imports
├── main.jsx             # React framework bootstrap entry point
└── App.jsx              # Root element declaring router tree
```

---

## 2. Router Layout Mappings

Our client is a **Single Page Application (SPA)** that routes URLs client-side using `react-router-dom`:

```text
          [ APP.JSX (Root Router Router) ]
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
   [ /login ]                       [ / (Dashboard) ]
   Public Page                      Private Page (Guarded)
   - Contains Login form            - Lists folders and files
   - Contains Register form         - Handles file actions
```

* **`/login` (Public)**: Public login and registration. If users are already logged in, they are redirected to the Dashboard.
* **`/` (Dashboard, Private)**: Private file manager. Accessing this path requires active credentials.

---

## 3. Global State (AuthContext)

Because multiple components need to know if the user is authenticated (e.g., the Router checks it to grant access, the Dashboard reads it to list folder owners, the Navbar reads it to display the username), we use React's **Context API**:

```text
                  [ AuthProvider (App.jsx Root) ]
                  ┌──────────────┴──────────────┐
                  ▼                             ▼
           [ Login Form ]               [ PrivateRoute ]
           Updates Token key            Checks Token exists
                  │                             │
                  ▼                             ▼
         (Saves to localStorage)       (Allows Dashboard mount)
```

1. **Authentication State**: Holds `user` (profile object) and `token` (40-character DRF token key).
2. **Local Storage Persistence**: When the user logs in, we save the token key in the browser's `localStorage` so that refreshing the browser does not log the user out.
3. **Axios Interceptors**: The API utility automatically extracts this token and appends it to all requests.
