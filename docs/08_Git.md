# Git Version Control Reference Guide

Git is a distributed version control system. It tracks changes in your source files over time, allowing you to see history, revert mistakes, and collaborate.

---

## 1. Core Concepts: The Three States

Git works by tracking files in three distinct areas of your local environment:

```text
[ Working Directory ] ──( git add )──> [ Staging Area ] ──( git commit )──> [ Local Repository ]
  (Actual files you                                                          (Snapshot history
   are editing)                                                               saved in .git folder)
```

1. **Working Directory**: The actual folder on your computer containing files. Changes here are "untracked" or "modified" until you staging them.
2. **Staging Area**: A preview sandbox. It holds the modifications you want to package into your next snapshot (commit).
3. **Local Repository**: The safe database where Git stores your committed snapshots permanently in the hidden `.git/` folder.

---

## 2. Fundamental Git Commands Explained

| Command | Action | Behind the Scenes |
|---|---|---|
| `git init` | Initializes a new repository | Creates a hidden `.git` folder in your project root. This folder contains database files that track configuration, commits, refs, and file blobs. |
| `git status` | Shows current workspace state | Compares your working directory with the current index/staging area to list files that are modified, staged, or untracked. |
| `git add <file>` | Adds file to the staging area | Reads the file, hashes its content, copies it into Git's object database as a blob, and updates the staging index file with the hash. |
| `git add .` | Stages all current changes | Recursively scans the directory, staging every new, modified, or deleted file. |
| `git commit -m "msg"` | Commits staged changes | Creates a new commit object. This object holds a pointer to the snapshot tree, the author metadata, parent commit pointer, and the message string. |
| `git log` | Displays commit history | Iterates backwards through commit pointers starting from `HEAD` and prints their authors, hashes, dates, and messages. |

---

## 3. Git Commit Milestones for this Course

We will run git commits at specific milestones. Do not commit messy code; commit complete, working states:

| Step / Milestone | Recommended Commit Message | Milestone Description |
|---|---|---|
| Milestone 1 | `"feat: create project directories and configure virtual environment"` | Setting up raw directories, `.gitignore`, and the Python virtual environment. |
| Milestone 1 | `"feat: initialize django project and create user, folders, and files apps"` | Running `django-admin startproject` and starting the app structures. |
| Milestone 2 | `"feat: configure postgresql database settings and install drf"` | Connecting Django to PostgreSQL and confirming connection tests. |
| Milestone 2 | `"feat: define user, folder, and file models and generate migrations"` | Creating models and applying migrations in PostgreSQL. |
| Milestone 3 | `"feat: implement token registration and login endpoints"` | Secure REST authentication handlers completed. |
| Milestone 4 | `"feat: implement folder CRUD endpoints with nesting support"` | Folder models fully operational via REST APIs. |
| Milestone 5 | `"feat: implement AWS S3 file upload, download, and delete endpoints"` | Successful integration of file actions with AWS storage buckets. |
| Milestone 6 | `"feat: scaffold react app with vite and setup tailwind css"` | Frontend project structure initialized. |
| Milestone 7 | `"feat: integrate full stack login, dashboard, folder management and file workflows"` | End-to-end frontend to backend interaction complete. |
