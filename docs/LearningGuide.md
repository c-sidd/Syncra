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

---

# Step 7: Configure PostgreSQL

## Goal
Install the PostgreSQL database adapter (`psycopg2-binary`) inside our virtual environment, configure Django settings to link with a local PostgreSQL server, and test the database connection socket.

---

## Why
Django scaffolds default projects to use **SQLite** (represented as a single local file `db.sqlite3` in the workspace). While SQLite is fast for tiny apps, it has a single-writer constraint: if one user is uploading a file metadata record, other user connection write queries are blocked. To build a multi-user Google Drive Clone, we require a robust client-server database like **PostgreSQL** that supports high concurrency, row-level locking, and strict relational integrity constraints. We modify `settings.py` so that instead of referencing a local SQLite file, Django connects to a running PostgreSQL database service over the network.

---

## Commands

```powershell
# Install the PostgreSQL database driver binary
.\venv\Scripts\pip.exe install psycopg2-binary
```

### Explanations:
* `.\venv\Scripts\pip.exe`: Runs our isolated package manager.
* `install`: Tells pip to fetch packages.
* `psycopg2-binary`: A pre-compiled version of the PostgreSQL database driver for Python. It contains pre-built C binaries so it can be installed instantly without requiring Visual Studio or external C compiler libraries on your host operating system.

---

## Files Created/Modified

| File Name | Change Type | Purpose |
|---|---|---|
| `docs/05_Database.md` | **[NEW]** | Conceptual guide file explaining relational databases, SQLite vs PostgreSQL, and driver connection lifecycles. |
| `backend/config/settings.py` | **[MODIFY]** | Updated `DATABASES` settings dict to redirect database routing from SQLite to PostgreSQL. |

---

## Folder Structure
Our updated structure at the end of Step 7:

```text
DriveClone/
├── .gitignore
├── backend/
│   ├── config/
│   │   ├── settings.py (Modified)
│   │   └── ...
│   └── ...
├── frontend/
├── venv/
└── docs/
    ├── 00_HowGoogleDriveWorks.md
    ├── 01_ProjectOverview.md
    ├── 02_Architecture.md
    ├── 05_Database.md (New)
    ├── 08_Git.md
    ├── 09_Glossary.md
    ├── LearningGuide.md
    └── Progress.md
```

---

## Code Explanation

We must modify the `DATABASES` block inside `backend/config/settings.py`. Open settings.py and locate this default block:

```python
# Default SQLite Configuration (We will replace this)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Replace it with the following PostgreSQL configuration:

```python
# PostgreSQL Configuration
DATABASES = {
    'default': {
        # 1. Connect Django's ORM compiler to the PostgreSQL backend engine
        'ENGINE': 'django.db.backends.postgresql',
        # 2. Define the name of the database we created on our PG server
        'NAME': 'driveclone',
        # 3. Specify the username for database authentication
        'USER': 'postgres',
        # 4. Specify the password for database authentication
        'PASSWORD': 'password',
        # 5. Define where PostgreSQL is running (localhost means this same machine)
        'HOST': '127.0.0.1',
        # 6. Specify the network port PostgreSQL listens on (default is 5432)
        'PORT': '5432',
    }
}
```

### Breakdown of Keys:
* **`ENGINE`**: Instructs Django which database translator to use. `django.db.backends.postgresql` compiles our Python model commands into PostgreSQL-compatible dialect SQL.
* **`NAME`**: The specific logical catalog inside your PostgreSQL server where our tables will be stored. You must create this database inside your server before running Django.
* **`USER`**: The role name accessing the database. `postgres` is the default superuser created by PostgreSQL installers.
* **`PASSWORD`**: Password set during PostgreSQL installation.
* **`HOST`**: Network address. `127.0.0.1` (localhost) means the database is running on the same machine as the Django server.
* **`PORT`**: Network port. `5432` is the standard port reserved for PostgreSQL.

---

## Request Lifecycle / Internals

When Django boots or runs a query, it opens a network socket to PostgreSQL:

```text
  [ Django Server (python manage.py runserver) ]
                     │
         ├── 1. Reads config/settings.py DATABASES dict
         ├── 2. Loads psycopg2-binary driver adapter
         ▼
  [ Socket Connection Request ]
         ├── Opens TCP connection to 127.0.0.1:5432
         ▼
  [ PostgreSQL Server ]
         ├── 3. Verifies credentials (USER: postgres, PASSWORD: password)
         ├── 4. Verifies database exists (NAME: driveclone)
         ▼
  [ Handshake Succeeded ]
         └── Connection socket is established. Query operations are now ready.
```

---

## How to Debug

If you misconfigure parameters or your server is stopped, Django will raise database connection errors. Learn how to read and solve them:

### Error 1: Connection Refused
```text
django.db.utils.OperationalError: connection to server at "127.0.0.1", port 5432 failed: Connection refused
```
* **What it means**: Django tried to talk to port 5432 on your machine, but nothing answered. The PostgreSQL service is either not running, or is listening on a different port.
* **How to fix it**: Start your PostgreSQL service:
  * On Windows: Open the "Services" app (`services.msc`), find `postgresql`, and click **Start**.

### Error 2: Database Does Not Exist
```text
django.db.utils.OperationalError: FATAL: database "driveclone" does not exist
```
* **What it means**: Django successfully connected to your PostgreSQL server, but couldn't find a database named `driveclone`.
* **How to fix it**: You must create the database:
  * Open pgAdmin (or run `psql` in command line).
  * Right-click "Databases" -> Create -> Database...
  * Name it `driveclone` and save.

### Error 3: Authentication Failed
```text
django.db.utils.OperationalError: FATAL: password authentication failed for user "postgres"
```
* **What it means**: The username or password in `settings.py` is incorrect.
* **How to fix it**: Check what password you set during the PostgreSQL database installation and write it exactly in `settings.py`.

---

## Try It Yourself / Exercises
* **Task 1**: Install the `psycopg2-binary` driver.
* **Task 2**: Connect to your PostgreSQL server using pgAdmin or the Command Line, and execute the SQL script:
  ```sql
  CREATE DATABASE driveclone;
  ```
* **Task 3**: Edit your `backend/config/settings.py` with your database credentials. Run `..\venv\Scripts\python.exe manage.py check` to verify that Django successfully loads without settings syntax errors.

---

## Knowledge Check
1. **Why does Django need the `psycopg2-binary` library to talk to PostgreSQL?**
2. **What does the `Connection refused` error message tell you about the state of your PostgreSQL service?**
3. **If you change the value of `PASSWORD` in `settings.py` to a wrong password, which component throws the authentication error: Django, psycopg2, or PostgreSQL?**

---

## Next Step
We will move to **Step 8: Install DRF** to install Django REST Framework to enable JSON-based API creation.

---

# Step 8: Install Django REST Framework (DRF)

## Goal
Install Django REST Framework (DRF) inside our virtual environment.

---

## Why
1. **API Serialization**: Classical Django views are built to return HTML templates to the browser. However, our decoupled React frontend is responsible for rendering the UI; it only wants raw data from the server. DRF provides **Serializers** that convert complex database model objects into clean JSON payloads (and vice-versa).
2. **Request Validation**: DRF automatically validates incoming JSON request payloads against defined model types, returning standard error messages and HTTP status codes (like `400 Bad Request`) if inputs are invalid.
3. **Stateless Authentication**: DRF provides built-in modules for Token-based security, which is perfect for building RESTful APIs.

---

## Package Breakdown

### 1. `djangorestframework`
* **Purpose**: Web API toolkit for Django.
* **Without it**: We would have to manually parse raw JSON request bodies, write complex logic to serialize database objects to dictionaries, and construct JSON responses by hand for every single view.
* **When it runs / Where used**: Runs inside Django view handlers whenever an API endpoint is hit.

---

## Commands

```powershell
# Install Django REST Framework using pip
.\venv\Scripts\pip.exe install djangorestframework
```

### Explanations:
* `.\venv\Scripts\pip.exe`: Runs our isolated virtual environment package installer.
* `install`: Subcommand telling pip to download packages.
* `djangorestframework`: The package library name on PyPI.

---

## Files Created/Modified
This step does not edit workspace files. It downloads libraries to the virtual environment folder:
* **`venv/Lib/site-packages/rest_framework/`**: Contains DRF's code (views, serializers, authentication filters, routing utilities).

---

## Folder Structure
Our folder structure remains unchanged.

---

## Code Explanation
No code files were written in this step. The libraries are installed to local directories.

---

## Request Lifecycle / Internals

Here is how DRF wraps a standard Django request to handle JSON APIs:

```text
  [ Client Browser (Axios POST) ]
             │
             ├── 1. Send JSON payload (e.g. {"name": "New Folder", "parent": 2})
             ▼
  [ Django URL Router ]
             │
             ├── 2. Routes request path to a DRF APIView
             ▼
  [ DRF APIView / ViewSet ]
             ├── 3. Wraps raw Django request in a DRF "Request" object
             ├── 4. Runs Authentication filters (Checks token key)
             ├── 5. Passes request.data to Serializer for validation
             │
             ├── 6. (If Valid) Saves model: Folder.objects.create(...)
             │
             ├── 7. Serializer converts newly saved model object back into a Python dict
             ▼
  [ DRF Response Handler ]
             ├── 8. Renders dict to JSON string and returns HTTP 201 Created
             ▼
  [ Client Browser (Axios) ]
             <── 9. Receives JSON output: {"id": 15, "name": "New Folder", "parent": 2}
```

---

## How to Debug

### How to check if this step worked:
1. Run this command in your terminal:
   ```powershell
   .\venv\Scripts\python.exe -c "import rest_framework; print(rest_framework.__version__)"
   ```
2. **Success Output**: Prints the installed DRF version number (e.g. `3.x.x`).
3. **Failure Output**:
   * If it raises `ImportError: No module named 'rest_framework'`, the package installer ran outside the virtual environment. Verify you used the correct pip.

---

## Try It Yourself / Exercises
* **Task**: Run `.\venv\Scripts\pip list` in your terminal.
* Observe that `djangorestframework` now appears in the list alongside `django`. Note how clean this virtual environment is—there are no unrelated packages!

---

## Knowledge Check
1. **Why does React need Django REST Framework (DRF) instead of classical Django MTV views?**
2. **What are the two primary tasks that a Serializer performs?**
3. **If you send invalid data (e.g. text in an integer field) to a serializer, what does the serializer do?**

---

## Next Step
We will move to **Step 9: Configure settings.py** to register our apps, configure DRF settings, and enable CORS to allow the React app to communicate with our server.

---

# Step 9: Configure settings.py

## Goal
Install the CORS headers package, register all local applications and third-party frameworks in `settings.py`, set up cross-origin request headers, and define our global Django REST Framework authentication policy.

---

## Why
1. **App Registration**: Django cannot run database operations or discover models in our sub-apps unless they are declared in the `INSTALLED_APPS` registry.
2. **CORS Security**: Web browsers block Javascript (React) requests loaded from origin `http://localhost:3000` from reading data from another origin `http://localhost:8000` (our Django backend) due to the **Same-Origin Policy**. To permit this interaction, the backend must return the header `Access-Control-Allow-Origin: http://localhost:3000`. We install `django-cors-headers` to manage these security headers automatically.
3. **Authentication Default**: We configure Django REST Framework to use **Token Authentication**. This tells the API to check every request for a valid security token in the header and automatically match it to the requesting database User.

---

## Package Breakdown

### 1. `django-cors-headers`
* **Purpose**: A Django application for adding Cross-Origin Resource Sharing (CORS) headers to responses.
* **Without it**: React will fail to read responses from our API endpoints. The browser console will block the request and show CORS errors.
* **When it runs**: Runs as early-stage middleware on every incoming HTTP request.

---

## Commands

```powershell
# Install the CORS headers helper package
.\venv\Scripts\pip.exe install django-cors-headers
```

### Explanations:
* `pip.exe install`: Instructs pip to fetch the package.
* `django-cors-headers`: The library name to download.

---

## Files Created/Modified

| File Name | Change Type | Purpose |
|---|---|---|
| `backend/config/settings.py` | **[MODIFY]** | Registered `rest_framework`, `corsheaders`, `users`, `folders`, `files` apps. Inserted CORS middleware, and added CORS lists and DRF authentication blocks. |

---

## Folder Structure
No new directories are created. The libraries live in `venv/Lib/site-packages/`.

---

## Code Explanation

Here are the changes we must implement in `backend/config/settings.py`:

### 1. Register Applications in `INSTALLED_APPS`
Locate the `INSTALLED_APPS` list and update it:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-Party Libraries
    'rest_framework',                  # Load Django REST Framework core
    'rest_framework.authtoken',        # Load DRF Token Database tables
    'corsheaders',                     # Load CORS headers middleware app
    
    # Local Apps
    'users.apps.UsersConfig',          # Load local registration & login app
    'folders.apps.FoldersConfig',      # Load nested directories manager app
    'files.apps.FilesConfig',          # Load file manager & S3 sync app
]
```

### 2. Configure CORS Middleware
Locate the `MIDDLEWARE` list. **`CorsMiddleware` must be placed as high as possible**, especially before `CommonMiddleware` or any response-generating middleware:

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',          # CORS headers intercept filter (MUST be at the top)
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### 3. Add CORS Allowed Origins & DRF Configurations
Scroll to the bottom of `settings.py` and append these configurations:

```python
# CORS Configuration: Tell Django which external client origins are allowed to connect
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",       # React development server (default host)
    "http://127.0.0.1:3000",       # Alternate localhost IP
]

# Django REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Configure DRF to use token authentication by default for all API endpoints
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

---

## Request Lifecycle / Internals

How CORS and Authentication intercept requests inside settings:

```text
  [ Client Browser (React: http://localhost:3000) ]
             │
             ├── 1. POST /api/folders/ (Headers: Authorization: Token abc123xyz)
             ▼
  [ Django Server Middleware Layer ]
         │
         ├── 2. CorsMiddleware: Intercepts request. Checks origin against CORS_ALLOWED_ORIGINS.
         ├──    Origin matches! Appends Access-Control-Allow-Origin headers.
         ▼
  [ DRF Request Parser ]
         │
         ├── 3. TokenAuthentication checks header: "Token abc123xyz"
         ├── 4. Queries Postgres table: rest_framework_authtoken
         ├──    Matches token to User #1 database row.
         ├── 5. Populates request.user = User(id=1, username="alex")
         ▼
  [ Django View Handler ]
         └── 6. Executes code knowing exactly which authenticated user sent the request.
```

---

## How to Debug

### Common Pitfalls:
* **Preflight CORS failure**: If you run React and call APIs but see CORS console blockers, check that:
  1. `'corsheaders.middleware.CorsMiddleware'` is listed **first** in the `MIDDLEWARE` block. If listed below `CommonMiddleware`, Django might redirect or return standard page configurations before the CORS headers are attached.
  2. The URL includes the correct protocol (`http://` vs `https://`). `localhost:3000` is invalid in CORS; it must be `"http://localhost:3000"`.

---

## Try It Yourself / Exercises
* **Task**: Install the package. Add the configurations to `settings.py`.
* Run `..\venv\Scripts\python.exe manage.py check` to make sure there are no typos. If Django raises errors like `ModuleNotFoundError: No module named 'corsheaders'`, verify the pip install finished successfully.

---

## Knowledge Check
1. **Why must `CorsMiddleware` be placed above `CommonMiddleware` inside settings?**
2. **What does the `rest_framework.authtoken` app do when registered inside `INSTALLED_APPS`?**
3. **If React runs on port 5173 instead of 3000, what setting must you modify in settings.py?**

---

## Next Step
We will move to **Step 10: Create Models** (Milestone 2) to build our relational database representations for User, Folder, and File entities.

---

# Step 10: Create Models

## Goal
Define the relational database tables for our Google Drive Clone using Python classes in `folders/models.py` and `files/models.py`.

---

## Why
Rather than writing raw SQL tables manually (e.g. `CREATE TABLE folders (...)`), we use Django's **Object-Relational Mapper (ORM)**. The ORM lets us write Python classes called **Models** which represent database tables.
1. **`User` (Built-in)**: We use Django's default built-in user authentication model. It contains fields for usernames, emails, and securely hashed passwords using PBKDF2.
2. **`Folder`**: Stores directory catalogs. It uses a self-referential foreign key (`parent = ForeignKey('self')`) to implement the Adjacency List pattern. This allows a folder to contain other folders, creating a nested tree hierarchy.
3. **`File`**: Tracks metadata for uploaded objects. It holds the file name, size, upload date, a foreign key linking it to a parent `Folder` (or `null` if it resides in the root directory), and a `FileField` that points to S3 storage.

---

## Files Created/Modified

| File Name | Change Type | Purpose |
|---|---|---|
| `backend/folders/models.py` | **[MODIFY]** | Created the `Folder` database model class. |
| `backend/files/models.py` | **[MODIFY]** | Created the `File` database model class linking to User and Folder. |
| `docs/05_Database.md` | **[MODIFY]** | Appended visual database schemas, column definitions, and cascading deletes documentation. |

---

## Folder Structure
Our file tree remains unchanged; models are defined inside local app folders.

---

## Code Explanation

We will modify three files.

### 1. Update `backend/folders/models.py`
Open `backend/folders/models.py` and add this code:

```python
from django.db import models
# Import the standard User model provided by Django's auth system
from django.contrib.auth.models import User

class Folder(models.Model):
    # 1. Store the display name of the folder
    name = models.CharField(max_length=255)
    
    # 2. Link this folder to a User record in the database
    # If the user is deleted, automatically delete all their folders
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    
    # 3. Create parent-child link (Adjacency List Pattern)
    # 'self' allows a folder to point to another folder ID.
    # null=True & blank=True allows a folder to be in the "Root" directory (no parent).
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subfolders'
    )
    
    # 4. Stamp when this folder was created
    created_at = models.DateTimeField(auto_now_add=True)

    # String representation: return folder name when printed in logs
    def __str__(self):
        return self.name
```

#### Why these parameters?
* **`on_delete=models.CASCADE`**: Enforces referential integrity. If you delete a user, you don't want their folders orphaned in the database. `CASCADE` automatically deletes all subfolders and files belonging to that user.
* **`related_name='subfolders'`**: Allows you to perform backwards lookup queries easily. For example, if you have a folder object `docs`, you can run `docs.subfolders.all()` to find all folders nested inside it.

---

### 2. Update `backend/files/models.py`
Open `backend/files/models.py` and add this code:

```python
from django.db import models
from django.contrib.auth.models import User
# Import Folder from our folders app
from folders.models import Folder

class File(models.Model):
    # 1. The visual display name of the file (e.g. "resume.pdf")
    name = models.CharField(max_length=255)
    
    # 2. The physical file handler column.
    # Under the hood, Django's FileField stores a string path pointing to S3.
    file = models.FileField(upload_to='uploads/')
    
    # 3. Link file to the user who uploaded it
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    
    # 4. Link file to a parent folder
    # null=True & blank=True allows a file to live in the root directory (outside any folder)
    folder = models.ForeignKey(
        Folder, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='files'
    )
    
    # 5. Store file size in bytes
    # BigIntegerField handles files larger than 2GB safely
    size = models.BigIntegerField(null=True, blank=True)
    
    # 6. Stamp when this file was uploaded
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
```

#### Why these parameters?
* **`upload_to='uploads/'`**: Django prefix prepended to the S3 object key. When saving `resume.pdf`, it will be stored inside the S3 bucket under the path `uploads/resume.pdf`.
* **`BigIntegerField`**: Standard integer fields (32-bit) can only store numbers up to 2.14 billion. Since file size is calculated in bytes, a 2.14GB file would cause integer overflow errors. `BigIntegerField` uses a 64-bit integer, safely accommodating file sizes up to 9.22 Exabytes.

---

### 3. Update `docs/05_Database.md`
Let's add our concrete schema designs to our database guide so we have a clear map. We will append the following schema table designs.

---

## Database Internals: Python to PostgreSQL Conversion

How Django maps model definitions to PostgreSQL column types:

| Django Model Field | PostgreSQL Column Type | SQL Attributes |
|---|---|---|
| `CharField(max_length=255)` | `VARCHAR(255)` | Enforces character limit. |
| `BigIntegerField()` | `BIGINT` | Stores 64-bit integers. |
| `DateTimeField(auto_now_add=True)` | `TIMESTAMP WITH TIME ZONE` | Stamped automatically on row creation. |
| `ForeignKey(User, on_delete=models.CASCADE)` | `BIGINT` | References `auth_user(id)` with a `FOREIGN KEY` constraint. |

---

## How to Debug

### Common Pitfalls:
* **Circular Imports**: If the `folders` app imports a model from `files` and the `files` app imports a model from `folders` using standard python imports, the compiler crashes: `ImportError: cannot import name...`.
  * *How to solve*: Avoid circular imports by referencing model classes as strings in relations (e.g. `models.ForeignKey('folders.Folder', on_delete=models.CASCADE)`).
* **Missing Related Name Conflicts**: If you define multiple foreign keys to the same model without setting unique `related_name` values, Django will fail validation checks because it cannot determine unique reverse relationship names.

---

## Try It Yourself / Exercises
* **Task 1**: Write the model code inside `backend/folders/models.py` and `backend/files/models.py`.
* Run `..\venv\Scripts\python.exe manage.py check` to confirm there are no database design configuration errors.

---

## Knowledge Check
1. **Why do we use `models.BigIntegerField` instead of `models.IntegerField` for file sizes?**
2. **What does `on_delete=models.CASCADE` do if a user deletes a parent folder containing 10 nested files?**
3. **What database data type is generated in PostgreSQL for a Django `CharField(max_length=255)` field?**

---

## Next Step
We will move to **Step 11: Run Migrations** (Milestone 2) to compile our models into SQL instructions and create the physical tables in PostgreSQL.

---

# Step 11: Run Migrations

## Goal
Generate database migration blueprint files for our local apps and apply all migrations (including Django's core authentication tables) to our PostgreSQL server.

---

## Why
PostgreSQL tables do not magically update when you save Python files. The database needs explicit DDL (Data Definition Language) SQL instructions (such as `CREATE TABLE`, `ALTER TABLE`) to build tables and columns. Django uses a two-phase process called **Migrations** to keep the database schema in sync with your models:
1. **`makemigrations`**: Inspects your Python models and compares them against your app's existing migrations. It writes a declarative, version-controlled Python blueprint file (e.g. `0001_initial.py`) describing what changed.
2. **`migrate`**: Checks which blueprint files have not yet been applied, compiles them into PostgreSQL-specific SQL code, connects to the database, executes the SQL commands to create/modify tables, and logs completion.

---

## Commands

```powershell
# 1. Compile model blueprints into Python migration files
..\venv\Scripts\python.exe manage.py makemigrations

# 2. Connect to PostgreSQL and execute the migration blueprints
..\venv\Scripts\python.exe manage.py migrate
```

### Explanations:
* `makemigrations`: Compiles database version blueprints.
* `migrate`: Connects to PostgreSQL, executes SQL DDL schemas, and logs success.

---

## Files Created/Modified

| File Name | Change Type | Purpose |
|---|---|---|
| `backend/folders/migrations/0001_initial.py` | **[NEW]** | Python blueprint declaring how to build the `folders_folder` table in PostgreSQL. |
| `backend/files/migrations/0001_initial.py` | **[NEW]** | Python blueprint declaring how to build the `files_file` table in PostgreSQL. |

---

## Folder Structure
Our updated structure showing initial migrations generated inside local apps:

```text
DriveClone/
├── backend/
│   ├── files/
│   │   └── migrations/
│   │       ├── 0001_initial.py (New)
│   │       └── ...
│   ├── folders/
│   │   └── migrations/
│   │       ├── 0001_initial.py (New)
│   │       └── ...
│   └── ...
└── ...
```

---

## Code Explanation

Let's dissect the generated file `backend/folders/migrations/0001_initial.py` to see what Django builds for us:

```python
# Generated by Django 4.2.x
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # Tells Django this migration depends on core Django User auth tables being built first
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Action to create a table named folders_folder
        migrations.CreateModel(
            name='Folder',
            fields=[
                # Auto-incrementing BigInt Primary Key
                ('id', models.BigAutoField(auto_now_add=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                # Self-referential parent link
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subfolders', to='folders.folder')),
                # Link referencing the User table (auth_user)
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='folders', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
```

* **`dependencies`**: Prevents database errors. Since `Folder` references a `User` (a foreign key relationship), the `User` table *must* exist before PostgreSQL can create the `Folder` table. Django ensures tables are created in the correct sequence.
* **`operations`**: A list of structural changes. `migrations.CreateModel` compiles internally to:
  ```sql
  CREATE TABLE folders_folder (
      id BIGSERIAL PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE NOT NULL,
      parent_id BIGINT REFERENCES folders_folder(id) ON DELETE CASCADE,
      user_id BIGINT REFERENCES auth_user(id) ON DELETE CASCADE
  );
  ```

---

## Request Lifecycle / Internals

What happens behind the scenes when you run `python manage.py migrate`:

```text
  [ Terminal Command: python manage.py migrate ]
                         │
                         ▼
  [ Reads database table: django_migrations ]
         ├── Checks which migration files are marked as applied
         ▼
  [ Scans migration folders for unapplied files ]
         ├── Finds auth initial migrations (Django core tables)
         ├── Finds authtoken initial migrations (DRF token tables)
         ├── Finds folders initial migrations (folders app tables)
         └── Finds files initial migrations (files app tables)
                         │
                         ▼
  [ Connects via psycopg2: Opens PostgreSQL Transaction ]
         ├── 1. Translates Python instructions to PostgreSQL dialect SQL
         ├── 2. Executes SQL statements sequentially
         ├── 3. Creates SQL Tables and constraints
         ├── 4. INSERTS rows into django_migrations (logging completion)
         ▼
  [ Transaction committed successfully! SQL Tables ready for queries. ]
```

---

## How to Debug

### Common Pitfalls:
* **"FATAL: database does not exist"**:
  * *Fix*: Ensure you created the PostgreSQL database named `driveclone` as described in Step 7.
* **Locked Database / Column Mismatches**: If you edit models after running migrations, do not write modifications manually in pgAdmin. If your Python code disagrees with PostgreSQL's actual schemas, Django will crash with `ProgrammingError: column X of relation Y does not exist`. Always use `makemigrations` and `migrate` to modify schemas.

---

## Try It Yourself / Exercises
* **Task 1**: Run the migration commands:
  ```powershell
  ..\venv\Scripts\python.exe manage.py makemigrations
  ..\venv\Scripts\python.exe manage.py migrate
  ```
* **Task 2**: Connect to PostgreSQL using pgAdmin. Expand databases -> driveclone -> Schemas -> public -> Tables.
* Count how many tables are present. Note that Django created its core system tables (`auth_user`, `django_session`, `django_migrations`) alongside our application tables (`folders_folder`, `files_file`, `authtoken_token`).

---

## Knowledge Check
1. **What is the difference between `makemigrations` and `migrate`?**
2. **What database table is created by Django to track which migration files have been applied?**
3. **Why does `folders/migrations/0001_initial.py` declare a dependency on `auth` migrations?**

---

## Next Step
We will move to **Step 12: Authentication** (Milestone 3) to implement our secure registration and login endpoints.











