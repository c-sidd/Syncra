# Learning Guide: Google Drive Clone Full Curriculum

Welcome to your master notebook! This file is your primary learning log. For every step of this project, we will document the goal, rationale, commands, file details, code breakdowns, internal lifecycles, debugging methods, exercises, and knowledge checks.

---

# Step 0: Understand the Project

## Goal
Understand the full stack client-server architecture, database decoupling, and AWS cloud storage logic before creating folders or running commands.

---

## Why
Building without understanding leads to copy-pasting code and failing to debug issues. By mapping out the data flow first, we establish:
1. **Separation of Concerns**: Why React only handles display, Django handles business decisions, PostgreSQL stores index metadata, and AWS S3 stores raw bytes.
2. **Resource Optimization**: Why storing big binary files in databases slows down SQL queries and degrades server RAM.
3. **Decoupled Architecture**: How signed URLs let client browsers stream files directly from AWS S3 without overloading our backend Django server.

---

## Commands
*There are no code or command executions in this conceptual step. Our workspace remains empty as we define the plan.*

---

## Files & Folders Created
We created the initial conceptual guides under the `docs/` folder in our project root:

| File Name | Purpose | What it Teaches | Created By |
|---|---|---|---|
| `docs/00_HowGoogleDriveWorks.md` | Explains high-level cloud storage concepts. | Why we decouple storage, flat S3 structure, signed URLs. | AI (Antigravity) |
| `docs/01_ProjectOverview.md` | Details the tech stack and project scope boundaries. | Pros/cons of Django, React, Postgres, S3 vs alternatives. | AI (Antigravity) |
| `docs/02_Architecture.md` | Maps out technical components and interaction layers. | System architecture boundaries and details on request flow. | AI (Antigravity) |
| `docs/08_Git.md` | Git version control quick-reference. | Git states (working, staging, repo) and milestone plan. | AI (Antigravity) |
| `docs/09_Glossary.md` | Dynamic dictionary of technical terms. | Terms like CORS, ORM, REST, SPA, Serialization, Hooks. | AI (Antigravity) |
| `docs/Progress.md` | Checklist of features. | Course roadmap visual tracker. | AI (Antigravity) |

---

## Folder Structure
This is our directory structure at the end of Step 0:

```text
DriveClone/
└── docs/
    ├── 00_HowGoogleDriveWorks.md
    ├── 01_ProjectOverview.md
    ├── 02_Architecture.md
    ├── 08_Git.md
    ├── 09_Glossary.md
    ├── LearningGuide.md
    └── Progress.md
```

---

## Code Explanation
In this step, we did not write application source code, but we defined our structural rules. Here is the critical takeaway regarding the **Adjacency List Pattern** we will write later:
```python
# Conceptual Schema for Folder Nesting
class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
```
* **Why `self`?**: It allows a Folder row to point to another row in the *same* Folder table. This creates a parent-child hierarchy.
* **Why `on_delete=models.CASCADE`?**: If a parent folder is deleted, database integrity rules dictate that all nested child folders must be deleted too, preventing "orphaned" folders.

---

## Request Lifecycle / Internals
Let's trace how the browser and backend coordinate during a simple folder listing request:

```text
Browser/React                       Django REST API (DRF)                PostgreSQL
      │                                       │                              │
      │── 1. GET /api/folders/5/ ────────────>│                              │
      │   (Authorization: Token <key>)        │── 2. Authenticate token ────>│ (Verify user)
      │                                       │<─ 3. Token valid, user is 1 ─│
      │                                       │                              │
      │                                       │── 4. Fetch folders & files ─>│ (WHERE parent_id=5)
      │                                       │   (SQL query)                │
      │                                       │<─ 5. Return database rows ───│
      │                                       │                              │
      │                                       │── 6. Serialize rows to JSON  │
      │<─ 7. Return 200 OK & JSON data ───────│                              │
      ▼
[React updates UI state:
 renders files and subfolders]
```

---

## How to Debug
Since this is a design phase, debugging involves validating your mental model.
* **Conceptual Check**: If S3 crashes, does the user lose the file name?
  * *Answer*: No. The file name is stored in PostgreSQL. The user won't be able to download the file contents, but the catalog (dashboard list) remains visible.
* **Security Check**: What happens if a user guesses another user's folder ID in the URL?
  * *Answer*: The backend must check ownership. Django queries `Folder.objects.filter(id=folder_id, user=request.user)`. If it returns empty, Django returns HTTP `403 Forbidden` or `404 Not Found` to prevent data leakage.

---

## Try It Yourself / Exercises
* **Task**: Open your `docs/Progress.md` file and mark **Step 0** as complete by changing `[ ] **Step 0**` to `[x] **Step 0**`. Repeat for the sub-files listed under Milestone 0. This is your first official action!

---

## Knowledge Check
Answer these questions mentally (or write them down in a notebook) before moving forward:
1. **Why don't we store file bytes in PostgreSQL columns?**
2. **What is a "Signed URL" and what resource does it save on the Django backend?**
3. **How does the Adjacency List pattern represent a subfolder inside a parent folder?**
4. **Why is it important to have stateless API backend servers instead of servers holding session memories in multiple instances?**

---

# Step 1: Create Folders and Initialize Git Repository

## Goal
Create the project folder structure for decoupled development and initialize a Git repository to track code versions from day one.

---

## Why
1. **Decoupled Folder Structure**: We place backend and frontend code in separate directories (`backend/` and `frontend/`). This keeps Python dependencies, virtual environments, and configuration files isolated from node packages, styling tools, and static React source files.
2. **Git Version Control**: Version control allows us to capture snapshots of our work. If we write broken code later, we can compare changes and roll back safely.
3. **Ignoring Secrets and Bloat (`.gitignore`)**: Systems compile intermediate cache files (like Python's `.pyc` files or Node's build outputs) and store packages locally (like `node_modules/` or Python's `venv/`). Storing these in Git bloats the repository. More importantly, files containing keys (like `.env`) must be ignored to prevent security leaks.

---

## Commands

```powershell
# 1. Create backend and frontend directories
mkdir backend, frontend

# 2. Initialize a local Git repository
git init
```

### Explanations:
* `mkdir`: Short for "make directory". It commands the operating system filesystem manager to create catalog nodes for `backend` and `frontend`.
* `git`: The Version Control System application.
* `init`: The subcommand that initializes a new Git repository. It creates a hidden directory called `.git` inside the root workspace folder, setting up databases for objects, refs, and history log configuration.

---

## Files & Folders Created

| File/Folder Name | Purpose | Why it Exists / Created By |
|---|---|---|
| `backend/` | Folder containing all Django files. | Keeps python backend isolated from frontend. (Created manually) |
| `frontend/` | Folder containing all React files. | Keeps javascript frontend isolated from backend. (Created manually) |
| `.git/` | Hidden folder containing Git's configuration databases. | Track changes, branch logs, commit pointers. (Created by `git init`) |
| `.gitignore` | Configuration text file listing file patterns for Git to ignore. | Prevents committing heavy caches and passwords. (Created manually) |

---

## Folder Structure
Our updated structure at the end of Step 1:

```text
DriveClone/
├── .gitignore
├── backend/
├── frontend/
└── docs/
    ├── 00_HowGoogleDriveWorks.md
    ├── 01_ProjectOverview.md
    ├── 02_Architecture.md
    ├── 08_Git.md
    ├── 09_Glossary.md
    ├── LearningGuide.md
    └── Progress.md
```

---

## Code Explanation

Here is the `.gitignore` file we will create in the root `DriveClone/` directory:

```text
# Python bytecode caches
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
.venv/
env/

# Operating system files
.DS_Store
Thumbs.db

# IDE configuration folders
.vscode/
.idea/

# Environment configurations containing passwords and credentials
.env
*.env.local

# Frontend packages and build targets
node_modules/
dist/
build/
```

### Why do we ignore these specifically?
* `__pycache__/` and `*.py[cod]`: Python compiles source code (`.py`) into bytecode (`.pyc`) for faster execution on subsequent runs. These are compiled automatically and vary by Python version; committing them creates constant code diff noise.
* `venv/`: Python virtual environments contain hundreds of megabytes of third-party package code (like Django). We only commit list definitions of these packages (e.g. `requirements.txt`), allowing anyone to download them on demand rather than storing them in git.
* `.env`: Contains PostgreSQL passwords and AWS keys. Committing this exposes keys to anyone viewing the repository.

---

## Request Lifecycle / Internals

When you initialize a repository, Git creates a hidden directory called `.git/`. Here is what happens behind the scenes inside that folder:

```text
.git/
├── HEAD          # Points to the active branch (currently refs/heads/master)
├── config        # Contains repository-specific settings (like URL links)
├── description   # Used by GitWeb (default project name placeholder)
├── hooks/        # Script templates that Git can run before commits/pushes
├── info/         # Holds exclude file for repository-specific ignore rules
├── objects/      # Git database containing files hashed as "blobs"
└── refs/         # Pointers to commits (branches and tags)
```

---

## How to Debug

### How to know if this step worked:
1. Run `git status` in the terminal.
2. **Success Output**:
   ```text
   On branch master (or main)
   No commits yet
   Untracked files:
     (use "git add <file>..." to include in what will be committed)
           docs/
   ```
3. **Failure Output**:
   If it returns `git : The term 'git' is not recognized as the name of a cmdlet...`, Git is not installed on your system. Install Git and restart your shell.

---

## Try It Yourself / Exercises
* **Task**: Create a temporary file named `secret.txt` inside your project root.
* Run `git status` in the terminal. Note that `secret.txt` appears under "Untracked files".
* Now, add `secret.txt` as a new line in `.gitignore`.
* Run `git status` again. Note that `secret.txt` is no longer visible to Git.
* Remove `secret.txt` from the filesystem and from `.gitignore` when finished.

---

## Knowledge Check
1. **What hidden folder does `git init` create, and what is its role?**
2. **Why should you never commit the `venv/` folder to Git?**
3. **If you commit a file named `db.sqlite3` and then add `*.sqlite3` to your `.gitignore`, will Git stop tracking it? Why or why not?**

---

## Next Step
We will proceed to **Step 2: Create Virtual Environment** to build an isolated sandbox for Python packages.

---

# Step 2: Create Virtual Environment

## Goal
Create an isolated Python environment for our Google Drive Clone project to ensure package versions do not conflict with other Python projects on the machine.

---

## Why
1. **Dependency Isolation**: In Python, packages are installed by default into a global "site-packages" directory. If one project on your machine requires Django 4.x and another requires Django 5.x, they will overwrite each other. Virtual environments create local sandboxes.
2. **Reproducibility**: By locking packages within a local `venv/` folder, we can export a clean list of requirements (using `pip freeze`). Another developer can then install exact copies without including any global system clutter.
3. **No Root/Admin Privileges Required**: Installing packages globally often requires administrative access (e.g. `sudo` on Unix, admin prompt on Windows). Virtual environments let you install packages into a folder inside your own workspace without permission restrictions.

---

## Commands

```powershell
# Run the built-in venv module to create a virtual environment named 'venv'
python -m venv venv
```

### Explanations:
* `python`: Runs the global Python interpreter installed on your OS.
* `-m`: Stands for "module-name". It tells Python to locate and execute a library module as a script (running its internal `__main__.py` entrypoint).
* `venv` (first): The name of the built-in Python module responsible for creating virtual environments.
* `venv` (second): The directory path name where the environment files and binaries will be written. We call it `venv` by convention, which matches the ignore rule in `.gitignore`.

---

## Files & Folders Created

When Python runs `python -m venv venv`, it populates the new directory with these items:

| File/Folder Name | Purpose | What it Does |
|---|---|---|
| `venv/` | Root directory of the virtual environment. | Holds all isolated scripts, interpreters, and libraries. |
| `venv/pyvenv.cfg` | Configuration settings file. | Contains reference paths pointing back to the base system Python installation. |
| `venv/Include/` | Header files folder. | Empty directory used if you compile C-extension Python libraries locally. |
| `venv/Lib/site-packages/` | Third-party packages store. | The directory where pip installs packages (like Django) for this project. |
| `venv/Scripts/` | Executables and scripts folder. | Holds the local `python.exe`, `pip.exe`, and activation shell scripts. |

---

## Folder Structure
Our updated structure at the end of Step 2:

```text
DriveClone/
├── .gitignore
├── backend/
├── frontend/
├── venv/                 <-- [NEW]
│   ├── Include/
│   ├── Lib/site-packages/
│   ├── Scripts/
│   └── pyvenv.cfg
└── docs/
    ├── 00_HowGoogleDriveWorks.md
    ├── 01_ProjectOverview.md
    ├── 02_Architecture.md
    ├── 08_Git.md
    ├── 09_Glossary.md
    ├── LearningGuide.md
    └── Progress.md
```

---

## Code Explanation

### Understanding `venv/pyvenv.cfg`
Inside the generated `pyvenv.cfg` configuration file, you will find settings similar to this:

```text
home = C:\Users\CS\AppData\Local\Programs\Python\Python310
include-system-site-packages = false
version = 3.10.11
```

* **`home`**: Tracks the absolute path of the physical Python installation that created this environment. When you run `venv/Scripts/python.exe`, it references this folder to load core library files.
* **`include-system-site-packages = false`**: Enforces strict isolation. When set to `false`, Python will *not* scan your system's global environment for packages. It will *only* look inside your local `venv/Lib/site-packages/`.

---

## Request Lifecycle / Internals

### The Activation Mechanism
How does activating a virtual environment change which python runs?

```text
                  [ Terminal Shell (PowerShell) ]
                                 │
                   (User runs: .\venv\Scripts\Activate.ps1)
                                 │
                                 ▼
                     [ PATH Environment Variable ]
       Before: C:\Windows; C:\Program Files\Python310
       After:  D:\my_drive\DriveClone\venv\Scripts; C:\Windows; C:\Program Files\Python310
                                 │
               (User runs: "python" or "pip install django")
                                 │
                                 ▼
             [ OS scans PATH directories sequentially ]
     - Finds python.exe in D:\my_drive\DriveClone\venv\Scripts FIRST!
     - Runs the isolated local Python environment.
```

When you run the activation script, PowerShell does **not** modify Python. Instead, it prepends the path to `DriveClone/venv/Scripts/` to the beginning of the OS `PATH` environment variable. When you write commands, the OS searches path folders from left to right. Finding our local venv folder first, it runs our isolated executable.

---

## How to Debug

### How to know if this step worked:
1. Run `.\venv\Scripts\Activate.ps1` in PowerShell.
2. Check if `(venv)` is prepended to your command prompt line:
   ```text
   (venv) PS D:\my_drive\DriveClone>
   ```
3. Run `where.exe python`.
   * **Correct Output**: `D:\my_drive\DriveClone\venv\Scripts\python.exe`
   * **Incorrect Output**: `C:\Users\...\Python310\python.exe` (indicates environment is NOT active).

### Common Error: PowerShell Script Execution Policies
If you get this error:
```text
File D:\my_drive\DriveClone\venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.
```
* **Why it happens**: Windows disables script execution by default to protect users from malicious shell files.
* **How to fix it**: Run this command to change the policy for your current terminal session only:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
  ```
  Then re-run `.\venv\Scripts\Activate.ps1`.

---

## Try It Yourself / Exercises
* **Task**: Open PowerShell, navigate to `D:\my_drive\DriveClone` (if not already there), and run `where.exe python`.
* Now, run `.\venv\Scripts\Activate.ps1` (apply the execution policy fix if needed).
* Run `where.exe python` again. Compare the printed path lists. Notice how the virtual environment path has moved to the top!
* Deactivate the environment by typing `deactivate`. See how `(venv)` disappears from your prompt.

---

## Knowledge Check
1. **What is the exact purpose of the `venv/pyvenv.cfg` file?**
2. **If you open a new terminal window, is the virtual environment automatically activated? Why or why not?**
3. **What does the command `deactivate` do behind the scenes?**

---

## Next Step
We will move to **Step 3: Upgrade pip** to ensure our isolated package manager is updated to avoid installation errors.

---

# Step 3: Upgrade pip

## Goal
Upgrade the Python package manager (`pip`) to the latest version inside our virtual environment.

---

## Why
1. **Security & Fixes**: `pip` is updated frequently to patch security issues and fix bugs.
2. **Speed & Reliability**: Newer versions of `pip` feature better caching algorithms (meaning faster subsequent library downloads) and a robust dependency resolver (helping it figure out conflicting packages when installing libraries like Django REST Framework).
3. **Avoid Deprecation Warnings**: Older `pip` versions print warning banners when downloading modern library package wheels (`.whl`), which can confuse developers.
4. **Prevent Windows Access Locks**: Upgrading `pip` by running `pip install --upgrade pip` directly can cause access violations on Windows because the `pip.exe` binary locks itself while trying to overwrite itself. Executing through `python -m pip` bypasses this by using Python to execute the underlying scripts directly, freeing the binary executable from file lock.

---

## Commands

```powershell
# Run python within the virtual environment script directory to self-upgrade pip
.\venv\Scripts\python.exe -m pip install --upgrade pip
```

### Explanations:
* `.\venv\Scripts\python.exe`: Directs the shell to execute the local Python interpreter inside our virtual environment, guaranteeing we do not modify the global system Python packages.
* `-m pip`: Run the built-in package installation manager module.
* `install`: The subcommand to fetch and set up external Python modules.
* `--upgrade`: Instructs pip to retrieve and overwrite any older packages with the latest stable version.
* `pip`: The target library to install (upgrading itself).

---

## Files & Folders Created
This step does not create new directories. It modifies existing files inside the virtual environment:
* Modifies: `venv/Scripts/pip.exe`, `venv/Scripts/pip3.exe`, and libraries inside `venv/Lib/site-packages/pip-*.dist-info/` and `venv/Lib/site-packages/pip/`.

---

## Folder Structure
Our folder structure remains unchanged from Step 2.

---

## Code Explanation
No code files were written in this step. The command executes binaries and updates library caches in the background.

---

## Request Lifecycle / Internals

When you upgrade pip, it runs through the following request pipeline:

```text
  [ Local pip CLI ]
         │
         ├── 1. HTTPS GET request (Check packages)
         ▼
  [ PyPI Package Server (pypi.org) ]
         │
         ├── 2. Return list of available packages (JSON response)
         ▼
  [ Local pip CLI ]
         │
         ├── 3. Choose latest wheel (.whl) & download stream
         ▼
  [ PyPI Package Server (pypi.org) ]
         │
         ├── 4. Streams bytes to local venv temp directory
         ▼
  [ Local site-packages cleanup ]
         - Unpacks downloaded files.
         - Deletes older pip folder from venv/Lib/site-packages/.
         - Replaces files with new versions.
         - Compiles new scripts inside venv/Scripts/.
```

---

## How to Debug

### How to check if this step worked:
1. Run `.\venv\Scripts\pip --version` in your terminal.
2. Check that the output prints the updated version number. It will look like:
   ```text
   pip 26.x.x from D:\my_drive\DriveClone\venv\lib\site-packages\pip (python 3.10)
   ```

### Common Errors:
* **`python: The term '.\venv\Scripts\python.exe' is not recognized...`**: This means you are running the command from the wrong folder or the virtual environment was not created properly in Step 2. Run `pwd` to verify you are inside the `D:\my_drive\DriveClone` directory.
* **Network / SSL Connection Failure**: Pip requires internet access to connect to `pypi.org`. If your firewall blocks it, you may see SSL/TLS errors. Ensure you are connected to the internet.

---

## Try It Yourself / Exercises
* **Task**: Run `.\venv\Scripts\pip list` in the terminal.
* Check which packages are currently installed in your virtual environment. You should only see `pip` and `setuptools`. This shows how clean the virtual environment is compared to your global Python environment!

---

## Knowledge Check
1. **What is PyPI, and how does `pip` interact with it?**
2. **Why do we prepend `.\venv\Scripts\python.exe -m` to the command instead of just running `pip install --upgrade pip`?**
3. **If you upgrade `pip` in this virtual environment, does it upgrade the `pip` program globally on your computer? Why or why not?**

---

## Next Step
We will move to **Step 4: Install Django** to set up our main Python web framework.

---

# Step 4: Install Django

## Goal
Install the Django web framework inside our virtual environment.

---

## Why
1. **The Web Framework Core**: Django serves as our application server. It manages incoming network routes, translates URL requests, communicates with the PostgreSQL database using an ORM, and outputs API payloads.
2. **Batteries-Included**: Django provides pre-made security protections (for CSRF, SQL injection, and clickjacking), a comprehensive middleware engine, and database schema version-control (migrations) out of the box.

---

## Package Breakdown

When you run `pip install django`, pip installs the core framework along with its necessary system dependencies:

### 1. `django`
* **Purpose**: Web framework foundation.
* **Without it**: We would have to manually code TCP sockets, HTTP parsing, router functions, and SQL query compilation.
* **When it runs / Where used**: Runs continuously on the backend server to process client HTTP requests.

### 2. `asgiref` (Dependency)
* **Purpose**: ASGI (Asynchronous Server Gateway Interface) standard helper library.
* **Without it**: Django cannot run asynchronous functions or route async websocket requests.
* **When it runs / Where used**: Used by Django's execution runner to run code asynchronously or run sync database operations in async contexts.

### 3. `sqlparse` (Dependency)
* **Purpose**: Non-validating SQL formatting and parsing utility.
* **Without it**: Django cannot pretty-print SQL commands in database debugging logs or compile structured migration commands.
* **When it runs / Where used**: Runs inside management command engines when compiling model changes to SQL.

### 4. `tzdata` (Dependency)
* **Purpose**: Provides time zone databases (IANA database).
* **Without it**: Django cannot calculate localized timestamps for file creation dates on OS environments lacking timezone databases (like Windows).
* **When it runs / Where used**: Used by Django datetime configurations to localize database timestamps.

---

## Commands

```powershell
# Run the local pip executable inside venv to install Django
.\venv\Scripts\pip.exe install django
```

### Explanations:
* `.\venv\Scripts\pip.exe`: Instructs the terminal to execute the isolated pip manager we just upgraded in Step 3.
* `install`: Tells pip to fetch packages.
* `django`: The target web framework package package to retrieve from PyPI.

---

## Files & Folders Created
This command downloads packages into the local virtual environment folder:
* **`venv/Lib/site-packages/django/`**: Contains Django's core python libraries (ORM, router, middleware, views, admin, forms).
* **`venv/Lib/site-packages/asgiref/`, `sqlparse/`, `tzdata/`**: Dependency library folders.
* **`venv/Scripts/django-admin.exe`**: A command line utility added to the local scripts folder. We will use this in the next step to scaffold our project template.

---

## Folder Structure
Root structure remains unchanged; libraries exist inside `venv/Lib/site-packages/`.

---

## Code Explanation
No code files were written in this step. The libraries are installed to local folders.

---

## Request Lifecycle / Internals

Here is how a request travels through Django's architecture at a high level:

```text
  [ Client Browser (React) ]
             │
             ├── 1. HTTP Request (e.g. GET /api/folders/5/)
             ▼
  [ Web Server Gateway (WSGI/ASGI) ]
             │
             ├── 2. Wraps raw HTTP headers & body into Django "HttpRequest" object
             ▼
  [ Middleware Engine ]
             │
             ├── 3. Applies security checks, CORS validations, and authentication headers
             ▼
  [ URL Router (urls.py) ]
             │
             ├── 4. Maps route path "/api/folders/5/" to the matched View function
             ▼
  [ View Logic (views.py) ]
             │
             ├── 5. Queries PostgreSQL using ORM (Folder.objects.get(id=5))
             ├── 6. Serializes data into a JSON string
             ▼
  [ Middleware Engine (Response phase) ]
             │
             ├── 7. Appends headers (like Content-Type: application/json)
             ▼
  [ Client Browser (React) ]
             <── 8. Streams JSON response with HTTP 200 OK status
```

---

## How to Debug

### How to check if this step worked:
1. Run this command in your terminal:
   ```powershell
   .\venv\Scripts\python.exe -c "import django; print(django.__version__)"
   ```
2. **Success Output**: It prints the installed version number (e.g. `5.x.x` or `4.x.x`).
3. **Failure Output**:
   * If it raises `ImportError: No module named 'django'`, the installation did not run inside this virtual environment. Verify you ran `.\venv\Scripts\pip.exe install django` and not a global `pip`.

---

## Try It Yourself / Exercises
* **Task**: Open your file explorer and navigate to `D:\my_drive\DriveClone\venv\Lib\site-packages\`.
* Find the `django` folder.
* Inside `django/bin/`, observe the `django-admin.py` script. This is the script responsible for bootstrapping new websites.

---

## Knowledge Check
1. **Why do we install Django inside the virtual environment instead of globally on our machine?**
2. **What utility script is placed inside `venv/Scripts/` after installing Django, and what is its purpose?**
3. **Name the three dependencies that pip automatically installs alongside Django.**

---

## Next Step
We will move to **Step 5: Create Django Project** to scaffold our initial server files.

---

# Step 5: Create Django Project

## Goal
Scaffold the base configuration files and entrypoint files for our Django server.

---

## Why
Every Django backend requires standard entry points to manage settings, load route parameters, process incoming HTTP requests, and handle tasks like database migrations. We run Django's bootstrapping utility `django-admin` to generate standard configuration templates. We name our project directory `config` instead of the project name to clarify that this directory acts as the central control room for the entire backend application, separating it from individual feature components (apps).

---

## Commands

```powershell
# Create the Django project directly inside the backend directory
# (Run this with your working directory set to D:\my_drive\DriveClone\backend)
..\venv\Scripts\django-admin.exe startproject config .
```

### Explanations:
* `..\venv\Scripts\django-admin.exe`: Calls the bootstrapping command-line script created in Step 4. We navigate up one folder relative to `backend/` to run it.
* `startproject`: Subcommand telling Django to create a new website structure template.
* `config`: The name we give to our primary settings directory.
* `.` (The dot): **CRITICAL FLAG**. Instructs Django to generate `manage.py` and the `config` files directly inside the current working directory (`backend/`). If omitted, Django generates an extra wrapping parent folder, nesting our files deep inside `backend/config/config/`, creating redundant file paths.

---

## Files & Folders Created
The following files are generated automatically. We explain every single one:

| File/Folder Name | Purpose | What it Does Internally |
|---|---|---|
| `backend/manage.py` | Wrapper management script. | Exposes command-line hooks. Sets environment settings and calls Django's core executing tools to run migrations, start the server, or run custom scripts. |
| `backend/config/` | Primary configuration folder. | Holds the configuration apps and settings modules. |
| `backend/config/__init__.py` | Empty Python entry file. | Flags the `config` folder as a Python package, allowing settings and urls to be imported elsewhere. |
| `backend/config/settings.py` | Core settings module. | The master panel. Holds database connections, active apps lists, middleware filters, security keys, and resource paths. |
| `backend/config/urls.py` | Root URL routing module. | The directory map. Matches the URL paths of incoming requests to their corresponding python View functions. |
| `backend/config/wsgi.py` | WSGI server configuration. | Stands for "Web Server Gateway Interface". Standard entrypoint file for synchronous production web servers (e.g. Gunicorn) to interface with Django. |
| `backend/config/asgi.py` | ASGI server configuration. | Stands for "Asynchronous Server Gateway Interface". Entrypoint file for async-compatible web servers (e.g. Uvicorn) to run chat or streaming applications. |

---

## Folder Structure
Our updated structure at the end of Step 5:

```text
DriveClone/
├── .gitignore
├── backend/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── manage.py
├── frontend/
├── venv/
└── docs/
    ├── 00_HowGoogleDriveWorks.md
    ├── 01_ProjectOverview.md
    ├── 02_Architecture.md
    ├── 08_Git.md
    ├── 09_Glossary.md
    ├── LearningGuide.md
    └── Progress.md
```

---

## Code Explanation

Let's dissect the primary code inside `backend/manage.py`:

```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    # 1. Map Django to the config folder's settings file
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        # 2. Load Django's CLI parser
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # 3. Route terminal arguments to the parser
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
```

* **`os.environ.setdefault(...)`**: Links the execution command to our configuration file in `config/settings.py`. Whenever we run `manage.py`, it knows exactly what database, apps, and keys to load.
* **`execute_from_command_line(sys.argv)`**: Captures the arguments you typed in the shell (e.g., `runserver`, `migrate`) and forwards them to Django's internal system scripts to execute the requested program.

---

## Request Lifecycle / Internals

When you run `python manage.py runserver`, the boot sequence follows this path:

```text
  [ Shell: "python manage.py runserver" ]
                     │
                     ▼
  [ manage.py: Sets DJANGO_SETTINGS_MODULE = "config.settings" ]
                     │
                     ▼
  [ django.core.management: execute_from_command_line() ]
                     │
                     ▼
  [ Django Core Initializer ]
         ├── Reads settings.py (Loads key configurations)
         ├── Verifies database parameters
         ├── Installs INSTALLED_APPS into Python runtime memory
         ├── Compiles URL Router lists from config/urls.py
         ▼
  [ Development HTTP Server spins up on http://127.0.0.1:8000/ ]
```

---

## How to Debug

### How to check if this step worked:
1. Navigate your shell into the `D:\my_drive\DriveClone\backend` directory.
2. Run this command:
   ```powershell
   ..\venv\Scripts\python.exe manage.py check
   ```
3. **Success Output**:
   ```text
   System check identified no issues (0 silenced).
   ```
4. **Failure Output**:
   * If it raises an error like `ImproperlyConfigured` or syntax exceptions, check if you accidentally modified the settings file or if you are in the wrong working directory.
   * If it says `python : The term '..\venv\Scripts\python.exe' is not recognized...`, double check your relative path. The venv directory is up one level (`..`) relative to the `backend/` folder.

---

## Try It Yourself / Exercises
* **Task**: Open `backend/config/settings.py` in your editor.
* Scroll down to find the `BASE_DIR` variable definition. Think about what this variable calculates.
  * *Answer*: It resolves the parent folder path of our settings file, helping Django build relative paths for logs, local databases, or static folders regardless of where the project is placed on your drive.

---

## Knowledge Check
1. **What does the trailing dot `.` represent in the command `django-admin startproject config .`?**
2. **What setting does `manage.py` set inside the operating system environment before loading Django?**
3. **What is the purpose of `__init__.py` inside the `config` folder?**

---

## Next Step
We will move to **Step 6: Create Apps** to build individual feature modules (`users`, `folders`, `files`) for our clone.

---

# Step 6: Create Apps

## Goal
Create three modular Django applications inside our backend codebase: `users`, `folders`, and `files` to separate our core features cleanly.

---

## Why
Django projects are structured as collections of independent, modular **Apps**. Each app should have a singular responsibility (a "Separation of Concerns").
1. **`users`**: Responsible only for user registration, user authentication records, and secure tokens.
2. **`folders`**: Responsible only for modeling nested folder trees, creating, naming, and listing logical directories.
3. **`files`**: Responsible for storing file upload details (name, size, type), connecting to AWS S3, downloading streams, and deleting files.

By splitting features into distinct apps, we keep settings, views, database schemas, and unit tests isolated. This makes debugging easier, avoids files with thousands of lines of mixed code, and enables code reusability.

---

## Commands

```powershell
# Create the users app
..\venv\Scripts\python.exe manage.py startapp users

# Create the folders app
..\venv\Scripts\python.exe manage.py startapp folders

# Create the files app
..\venv\Scripts\python.exe manage.py startapp files
```

### Explanations:
* `..\venv\Scripts\python.exe manage.py`: Runs our local virtual environment's Python interpreter to execute our project control script (`manage.py`).
* `startapp`: Subcommand instructing Django to generate a new application folder structure boilerplate.
* `users`, `folders`, `files`: The respective folder directory names and namespaces we assign to each application.

---

## Files & Folders Created
For each app generated, Django automatically creates a directory containing these files. We explain what each generated file does:

| File/Folder Name | Purpose | What it Does Internally |
|---|---|---|
| `admin.py` | Admin panel registrar. | Used to register your models (e.g. Folder, File) with Django's built-in Admin dashboard so you can view and edit records. |
| `apps.py` | App configuration registry. | Declares configuration parameters for the app, such as the subclass of `AppConfig` and its naming namespace. |
| `models.py` | Database tables design. | The blueprints. This is where we write Python classes that define our database tables, column names, column data types, constraints, and relationships. |
| `tests.py` | Testing sandbox. | Container for writing automated unit tests and assertions to verify that our code runs correctly. |
| `views.py` | Request handler controller. | Contains logic for receiving HTTP Requests, processing parameters, querying models, talking to S3, and returning HTTP Responses. |
| `migrations/` | Database instructions log. | Folder containing autogenerated migration files that translate Python model classes into database schema modifications (SQL). |
| `migrations/__init__.py` | Package marker file. | Identifies the `migrations/` folder as a Python package. |

---

## Folder Structure
Our updated structure at the end of Step 6:

```text
DriveClone/
├── .gitignore
├── backend/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── files/
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   └── views.py
│   ├── folders/
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   └── views.py
│   ├── users/
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   └── views.py
│   └── manage.py
├── frontend/
├── venv/
└── docs/
    ├── 00_HowGoogleDriveWorks.md
    ├── 01_ProjectOverview.md
    ├── 02_Architecture.md
    ├── 08_Git.md
    ├── 09_Glossary.md
    ├── LearningGuide.md
    └── Progress.md
```

---

## Code Explanation

Let's look inside `backend/users/apps.py` (which is identical in structure for `folders` and `files`):

```python
from django.apps import AppConfig

class UsersConfig(AppConfig):
    # 1. Define the default primary key field type for tables
    default_auto_field = 'django.db.models.BigAutoField'
    # 2. Define the namespace identifier for the app
    name = 'users'
```

* **`default_auto_field = 'django.db.models.BigAutoField'`**: Tells Django that by default, any database table created in this app should use a 64-bit integer auto-incrementing ID (`BigAutoField`). This is ideal for large datasets because a 64-bit ID can store up to $9.22 \times 10^{18}$ records.
* **`name = 'users'`**: Defines the absolute package path and namespace name of this module. Django references this name when linking models and settings.

---

## Request Lifecycle / Internals

How Django discovers and runs applications:

```text
  [ Run Server: python manage.py runserver ]
                      │
                      ▼
  [ django.core: Loads settings.INSTALLED_APPS ]
         ├── Imports 'users.apps.UsersConfig'
         ├── Imports 'folders.apps.FoldersConfig'
         └── Imports 'files.apps.FilesConfig'
                      │
                      ▼
  [ App Config Registry ]
         ├── Executes .ready() lifecycle methods
         └── Maps models inside <app>/models.py to ORM Registry
                      │
                      ▼
  [ Django fully active with all Apps loaded ]
```

---

## How to Debug

### Common Pitfall: Missing Registration
If you write model relations pointing to the `users` or `folders` app but forget to register them in settings, Django will crash with:
```text
LookupError: No installed app with label 'users'
```
* **Why**: The `startapp` command only creates folders on your hard drive. Django does not scan files arbitrarily; it only loads apps explicitly specified in `INSTALLED_APPS` inside `backend/config/settings.py`. We will configure this in Step 9.

---

## Try It Yourself / Exercises
* **Task**: Create the three applications by executing the terminal commands.
* Navigate inside `backend/files/models.py`. See that it contains only template code:
  ```python
  from django.db import models
  # Create your models here.
  ```
* Open `backend/folders/apps.py` and inspect how `name = 'folders'` matches the directory name.

---

## Knowledge Check
1. **What is the difference between a Django Project and a Django App?**
2. **What does the `default_auto_field` parameter inside `apps.py` define?**
3. **If you generate a new app called `analytics`, what files does Django create inside that folder?**

---

## Next Step
We will move to **Step 7: Configure PostgreSQL** (Milestone 2) to hook up our database and replace the default SQLite developer database.






