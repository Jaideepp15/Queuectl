# Queuectl — A CLI-based background job queue system (Python)

A CLI-based background job queue system built with **SQLite persistence**, **multi-worker support**, **automatic retries with exponential backoff**, and a **Dead Letter Queue (DLQ)**.

It's designed to be compact, readable, and production-like — a great example of how to build a reliable local job processing system using only Python's standard library.

---

## Features

* Persistent job queue using SQLite  
* Multiple concurrent workers  
* Priority scheduling (1–10; lower = higher priority)  
* Automatic aging to prevent starvation  
* Exponential backoff for retries  
* Automatic Dead Letter Queue (DLQ) for failed jobs  
* Configurable retry and backoff values  
* Sequential auto-generated unique job IDs (`job1`, `job2`, …)  
* Cross-platform: works on both Windows and Ubuntu  
* No external dependencies — pure Python standard library  

---

## Project Structure

```
Queuectl/
├──queuectl/
  ├── main.py              # CLI entry point
  ├── db.py                # SQLite DB management
  ├── worker.py            # Worker lifecycle & job execution
  ├── cli_commands.py      # CLI command implementations
  ├── utils.py             # Helpers, PID management, timestamps
  ├── config.py            # Constants and paths
├── pyproject.toml       # Project metadata and install configuration
└── README.md
```

---

## Requirements

- **Python 3.8+**
- No external dependencies
- Works on:
  - Ubuntu / WSL (Linux)
  -  Windows 10/11 (PowerShell or Command Prompt)

---

## Installation

### On Ubuntu / WSL

#### Option 1 - Installing in User Mode

1️. Install `pipx` via apt:
```bash
sudo apt update
sudo apt install -y pipx
python3 -m pipx ensurepath
exec $SHELL
```

2️. Clone and install locally in editable mode:
```bash
git clone https://github.com/<your-username>/queuectl.git
cd queuectl
pipx install --editable .
```

pipx installs your CLI in an isolated environment and links it globally — no need to activate a virtual environment manually.

#### Option 2 - Installing in a Virtual Enviornement

1️. Clone the repository:
```bash
git clone https://github.com/Jaideepp15/queuectl.git
cd queuectl
```

2️. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3️. Install in editable mode:

```bash
pip install -e .
```

Verify installation:

```bash
queuectl --help
```

### On Windows

1️. Clone the repository:

```powershell
git clone https://github.com/Jaideepp15/queuectl.git
cd queuectl
```

2️. (Optional) Create a virtual environment:

```powershell
python -m venv venv
venv\Scripts\activate
```

3️. Install in editable mode:

```powershell
pip install -e .
```

Verify installation:

```powershell
queuectl --help
```

⚠️ If you see `'queuectl' is not recognized`, ensure your Python Scripts folder is in your PATH
(e.g., `%USERPROFILE%\AppData\Local\Programs\Python\Python312\Scripts`).

---

## How the CLI Works

`queuectl` is exposed automatically as a console script via `pyproject.toml`:

```toml
[project.scripts]
queuectl = "queuectl.main:main"
```

After installation (`pip install -e .` or `pipx install --editable .`), you can invoke it directly from any terminal:

```bash
queuectl enqueue '{"command":"echo hello"}'
```

---

## Running Workers

Workers are long-running processes that continuously poll and execute jobs from the queue.

```bash
queuectl worker start --count 3
```

Example output:

```
[worker 0] pid=1102 started
[worker 0] picked job job1: echo hello
hello
[worker 0] job job1 completed
[worker 1] pid=1103 started
[worker 2] pid=1105 started
```

Keep this terminal open — workers will continue polling for jobs.

Open a second terminal to enqueue and inspect jobs:

```bash
queuectl enqueue '{"command":"echo another job"}'
queuectl status
```

---

## Example Commands

| Action | Command |
|--------|---------|
| Enqueue job | `queuectl enqueue '{"command":"echo Hello World"}'` |
| Check status | `queuectl status` |
| List jobs | `queuectl list --state pending` |
| View DLQ | `queuectl dlq list` |
| Retry DLQ job | `queuectl dlq retry job1` |
| Set config values | `queuectl config set backoff_base 2` |
| Clear all jobs | `queuectl reset` |
| Help | `queuectl --help` or `queuectl <command> --help` |

---

## Architecture Overview

Queuectl is designed as a lightweight, production-style background job queue system built entirely with Python's standard library and SQLite.

### 1. System Components

| **Component** | **Description** | 
|---------------|-----------------|
| **CLI Interface (queuectl)** | The entry point for all operations. Users enqueue jobs, start workers, check status, and manage configuration via CLI commands. |
| **SQLite Database (~/.queuectl/jobs.db)** | The central persistent store for all jobs, configurations, and worker state. Ensures data durability across restarts. |
| **Worker** | ProcessesLong-running background processes that continuously fetch pending jobs from the queue and execute their commands. |
| **Configuration Table** | Stores global runtime configurations like max_retries, backoff_base, and backoff delay parameters. |
| **Dead Letter Queue (DLQ)** | Holds jobs that have permanently failed after all retry attempts. Jobs can be retried later manually. |

### 2. Job Lifecycle

Each job moves through well-defined states from creation to completion.
| **State** | **Description** | 
|-----------|-----------------|
| Pending | The job has been enqueued and is waiting to be picked up by a worker. |
| Processing | A worker has claimed the job and is currently executing its command. |
| Completed | The job finished successfully (exit code 0). |
| Failed | The job failed (non-zero exit code) but is still retryable. |
| Dead | The job exceeded its retry limit and was moved to the Dead Letter Queue (DLQ). |

**State Transitions**
```
        ┌────────────┐
        │  pending   │
        └─────┬──────┘
              │ picked by worker
              ▼
        ┌────────────┐
        │ processing │
        └─────┬──────┘
              │ success
    ┌─────────┴─────────┐
    ▼                   ▼
┌──────────┐      ┌──────────┐
│ completed│      │  failed  │
└──────────┘      └─────┬────┘
                        │
              attempts < max_retries
                        │ retry
                        ▼
                  pending again
                        │
              attempts ≥ max_retries
                        ▼
                  ┌──────────┐
                  │   dead   │
                  └──────────┘
```

### 3. Job Execution and Priority Scheduling

Each job record includes:

```json
{
    "id": "job12",
    "command": "echo 'Hello World'",
    "priority": 5,
    "attempts": 0,
    "max_retries": 3,
    "state": "pending",
    "created_at": "...",
    "updated_at": "...",
    "run_at": "...",
    "last_error":"..."
}
```
Jobs are ordered by priority (ascending):

Lower priority value = higher priority.
Default priority is 5 (medium).
Range: 1 (highest) → 10 (lowest).

If two jobs share the same priority, the earlier-created job is executed first (FIFO order).
Aging is implemented to prevent starvation:
- Every minute a job remains pending, its priority improves (priority number decreases).
- Eventually, long-waiting jobs will bubble up and be executed.

### 4. Retry Mechanism and Backoff Strategy

When a job fails, it is retried automatically with exponential backoff, calculated as:
delay = backoff_base ^ attempts
For example, if backoff_base=2 and the job failed twice:

Attempt 1 → retry after 2 seconds
Attempt 2 → retry after 4 seconds
Attempt 3 → moved to DLQ (if max_retries=3)

If a job exceeds its retry count, it transitions from failed → dead, and becomes visible in the Dead Letter Queue.

### 5. Data Persistence (SQLite)

All jobs, configs, and metadata are persisted in SQLite at:
Linux:
```bash
~/.queuectl/jobs.db
```
Windows:
```cmd
%USERPROFILE%\.queuectl\jobs.db
```
Tables:
jobs — stores all job records with states, timestamps, and retry data.
config — stores runtime configuration values (backoff_base, default_max_retries, etc.).

Persistence ensures:
* Jobs survive process restarts or system shutdowns.
* DLQ entries can be retried across sessions.
* Workers can safely resume after crashes.

SQLite is configured in WAL (Write-Ahead Logging) mode for better concurrency and performance:
```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```
This allows multiple workers to read and write concurrently without corruption or blocking.

### 6. Worker Logic

Workers are implemented as independent background processes (multiprocessing).
Each worker repeatedly:
1. Connects to the shared SQLite DB.
2. Atomically fetches the next highest-priority pending job:
```sql
SELECT * FROM jobs
WHERE state='pending' AND run_after <= current_timestamp
ORDER BY priority ASC, created_at ASC
LIMIT 1;
```
3. Marks it as processing inside a transaction.
4. Executes the job's shell command via subprocess.run().
5. Updates the job record with:
  * state='completed' if success
  * state='failed' if non-zero exit code
  * attempts++, run_after set to next backoff delay
6. If retries exceed max_retries, marks job as dead (DLQ).
7. Sleeps for a short polling interval (e.g., 1 second) and repeats.

This ensures:
* No two workers ever process the same job (atomic SQL claim).
* Concurrency is safely handled by SQLite transactions.
* Crash-safe operation: in-progress jobs remain recoverable.

### 7. Concurrency and Locking

* SQLite provides built-in row-level atomicity for write transactions.
* When a worker “claims” a job, it executes:
```sql
UPDATE jobs
SET state='processing'
WHERE id=? AND state='pending';
```
Only **one** worker can successfully update this row — others see no match.
* This prevents duplicate processing and race conditions.
* Enabling WAL mode further increases read concurrency, allowing multiple workers to poll simultaneously without blocking each other.

### 8. Dead Letter Queue (DLQ)

Jobs that exceed their retry limits are marked state='dead' and appear in the DLQ.

The DLQ is not a separate database or table, but a logical partition within the jobs table.
This design:
* Simplifies querying and persistence.
* Allows unified indexing and reporting.
* Preserves full job history (creation, failures, final state) in one place.

You can:
  * List failed jobs:
  ```bash
  queuectl dlq list
  ```
  * Retry them:
  ```bash
  queuectl dlq retry job7
  ```
  This moves the job back to the pending state for reprocessing.

---

## Tradeoffs / Assumptions

| Area | Description |
|------|-------------|
| Scope | Single-machine queue using SQLite |
| Scaling | For distributed queues, replace DB with PostgreSQL or Redis |
| Polling | Could be improved with event-driven triggers |
| Background mode | PID files work locally; use systemd/supervisor for production |
| Extensions | Could add job dependencies, scheduling, or a web dashboard |

---

## Example Workflow

**Terminal 1 (start workers)**
```bash
queuectl worker start --count 3
```

**Terminal 2 (enqueue jobs)**
```bash
queuectl enqueue '{"command":"echo Job test"}'
queuectl status
queuectl list
queuectl dlq list
```

---

## Installation Summary

| Platform | Command |
|----------|---------|
| Ubuntu (user mode) | `sudo apt install -y pipx && python3 -m pipx ensurepath && pipx install --editable .` |
| Ubuntu (venv) | `python3 -m venv .venv && source .venv/bin/activate && pip install -e .` |
| Windows (user mode) | `pip install -e .` |
| Windows (venv) | `python -m venv venv && venv\Scripts\activate && pip install -e .` |

---

## Author

**Jaideep Palaniselvan**  
Amrita Vishwa Vidyapeetham, Coimbatore  

📧 jaideepp15@gmail.com
















