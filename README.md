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

## Demo Video

* CLI-Demo : https://drive.google.com/file/d/1SqgSm1dhbjy77RwBblvErlQZOqsLDman/view?usp=sharing
* Persistence Demo : https://drive.google.com/file/d/1mWOe_xZo9w9RGfykYU1Yu2hvIFYaiFif/view?usp=sharing
* Testing Demo : https://drive.google.com/file/d/17RQi3t8vtI3H6QTozbAA4yBZvsEqt42g/view?usp=sharing

---

## Requirements

- **Python 3.8+**
- No external dependencies
- Works on:
  - Ubuntu / WSL (Linux)
  -  Windows 10/11 (PowerShell or Command Prompt)

---

## Installation

### On Linux (Recommended OS)

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
git clone https://github.com/Jaideepp15/queuectl.git
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

**Note**
The format for providing the job as a JSON document varies depending on the terminal you are using to run queuectl
* **Powershell**
  ```powershell
  queuectl enqueue '{""command"":""echo hello"",""max-retries"":2}'
  ```
* **Command Prompt (CMD)**
  ```cmd
  queuectl enqueue "{""command"":""echo hello"",""max-retries"":2}"
  ```
* **Linux shell / WSL Shell**
  ```bash
  queuectl enqueue '{"command":"echo hello","max-retries":2}'
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

## Commands

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

## Example Usage

### 1. View default configuration

Command:
```bash
queuectl config get default_max_retries
queuectl config get backoff_base
```
Output:
```bash
3
2
```

### 2. Modify configuration values

Command:
```bash
queuectl config set backoff_base 3
queuectl config set default_max_retries 4
```
Output:
```bash
OK
OK
```
Verify the changes:
```bash
queuectl config get default_max_retries
queuectl config get backoff_base
```
Output:
```bash
4
3
```

### 3. Enqueue a simple job

Command:
```bash
queuectl enqueue '{"command":"echo Hello World"}'
```
Output:
```bash
Enqueued job job1
```

### 4. Start workers

**Note:** Execute this command in a new terminal
Command:
```bash
queuectl worker start --count 2
```
Output:
```bash
Started worker pid=4408
[worker 0] pid=4408 started
Started worker pid=4409
Saved PIDs to /home/jaide/.queuectl/pids.json
[worker 0] picked job job1: echo Hello World
Hello World
[worker 0] job job1 completed
[worker 1] pid=4409 started
```

### 5. Verify job completion

Command:
```bash
queuectl status
```
Output:
```bash
Job states:
  pending: 0
  processing: 0
  failed: 0
  completed: 1
  dead: 0
Background worker PIDs: [4408, 4409]
```
The job executed successfully and moved to the completed state.

### 6. Test job priorities

Command:
```bash
queuectl enqueue '{"command":"echo High Priority Job","priority":1}'
queuectl enqueue '{"command":"echo Medium Priority Job","priority":5}'
queuectl enqueue '{"command":"echo Low Priority Job","priority":9}'
```
Expected Output:
```bash
Enqueued job job2
Enqueued job job3
Enqueued job job4
```

Command:
```bash
queuectl list
```
Output:
```bash
{"id": "job2", "command": "echo High Priority Job", "state": "completed", "attempts": 0, "max_retries": 3, "priority": 1, "created_at": "2025-11-08T12:35:50.089525+00:00", "updated_at": "2025-11-08T12:35:50.982301+00:00", "run_after": 1762605350, "last_error": null}
{"id": "job1", "command": "echo Hello World", "state": "completed", "attempts": 0, "max_retries": 3, "priority": 5, "created_at": "2025-11-08T12:33:02.155330+00:00", "updated_at": "2025-11-08T12:33:56.393488+00:00", "run_after": 1762605182, "last_error": null}
{"id": "job3", "command": "echo Medium Priority Job", "state": "completed", "attempts": 0, "max_retries": 3, "priority": 5, "created_at": "2025-11-08T12:35:58.310338+00:00", "updated_at": "2025-11-08T12:35:58.973965+00:00", "run_after": 1762605358, "last_error": null}
{"id": "job4", "command": "echo Low Priority Job", "state": "completed", "attempts": 0, "max_retries": 3, "priority": 9, "created_at": "2025-11-08T12:36:06.510093+00:00", "updated_at": "2025-11-08T12:36:08.165250+00:00", "run_after": 1762605366, "last_error": null}
```
This demonstrates priority-based scheduling.

### 7. Enqueue a failing job

Command:
```bash
queuectl enqueue '{"command":"invalidcommand","max_retries":2}'
```
Output:
```bash
Enqueued job job5
```

### 8. Verify dead and DLQ jobs

Command:
```bash
queuectl list --state dead
```
Expected Output:
```bash
{"id": "job5", "command": "invalidcommand", "state": "dead", "attempts": 3, "max_retries": 2, "priority": 5, "created_at": "2025-11-08T12:37:51.770491+00:00", "updated_at": "2025-11-08T12:37:58.624076+00:00", "run_after": 1762605478, "last_error": "exit:127"}
```

Command:
```bash
queuectl dlq list
```
Expected Output:
```bash
{"id": "job5", "command": "invalidcommand", "state": "dead", "attempts": 3, "max_retries": 2, "priority": 5, "created_at": "2025-11-08T12:37:51.770491+00:00", "updated_at": "2025-11-08T12:37:58.624076+00:00", "run_after": 1762605478, "last_error": "exit:127"}
```

### 9. Retry a DLQ job

Command:
```bash
queuectl dlq retry job5
```
Output (Worker terminal):
```bash
[worker 0] job job5 failed -> failed (exit:127)
[worker 0] picked job job5: invalidcommand
/bin/sh: 1: invalidcommand: not found
[worker 0] job job5 failed -> failed (exit:127)
[worker 0] picked job job5: invalidcommand
/bin/sh: 1: invalidcommand: not found
[worker 0] job job5 failed -> failed (exit:127)
[worker 0] picked job job5: invalidcommand
/bin/sh: 1: invalidcommand: not found
[worker 0] job job5 failed -> dead (exit:127)
```

* The retried job will attempted execution again.
* It failed again and re-entered DLQ — this is expected behavior.

### 10. Check all current jobs

Command:
```bash
queuectl list
```
Output:
```bash
{"id": "job2", "command": "echo High Priority Job", "state": "completed", "attempts": 0, "max_retries": 3, "priority": 1, "created_at": "2025-11-08T12:35:50.089525+00:00", "updated_at": "2025-11-08T12:35:50.982301+00:00", "run_after": 1762605350, "last_error": null}
{"id": "job1", "command": "echo Hello World", "state": "completed", "attempts": 0, "max_retries": 3, "priority": 5, "created_at": "2025-11-08T12:33:02.155330+00:00", "updated_at": "2025-11-08T12:33:56.393488+00:00", "run_after": 1762605182, "last_error": null}
{"id": "job3", "command": "echo Medium Priority Job", "state": "completed", "attempts": 0, "max_retries": 3, "priority": 5, "created_at": "2025-11-08T12:35:58.310338+00:00", "updated_at": "2025-11-08T12:35:58.973965+00:00", "run_after": 1762605358, "last_error": null}
{"id": "job5", "command": "invalidcommand", "state": "dead", "attempts": 3, "max_retries": 2, "priority": 5, "created_at": "2025-11-08T12:37:51.770491+00:00", "updated_at": "2025-11-08T12:40:16.226945+00:00", "run_after": 1762605616, "last_error": "exit:127"}
{"id": "job4", "command": "echo Low Priority Job", "state": "completed", "attempts": 0, "max_retries": 3, "priority": 9, "created_at": "2025-11-08T12:36:06.510093+00:00", "updated_at": "2025-11-08T12:36:08.165250+00:00", "run_after": 1762605366, "last_error": null}
```

### 11. Reset the queue

Command:
```bash
queuectl reset
```
If workers are running, you’ll be prompted:
```bash
This will stop all workers and delete all jobs. Continue? (y/N):
```
Type:
```bash
y
```
Output:
```bash
Sent SIGTERM to pid 4408
Sent SIGTERM to pid 4409
Queue reset successful: all jobs and configurations cleared.
```

### Step 12. Verify clean state

Command:
```bash
queuectl status
```
Output:
```bash
Job states:
  pending: 0
  processing: 0
  failed: 0
  completed: 0
  dead: 0
Background worker PIDs: []
```

### 13. Stop background workers (optional)

Command (After starting workers in a different terminal):
```bash
queuectl worker stop
```
Output (In the workers terminal):
```bash
[worker 0] received stop signal, will exit after current job
[worker 1] received stop signal, will exit after current job
[worker 0] exiting
[worker 1] exiting
```
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
* jobs — stores all job records with states, timestamps, and retry data.
* config — stores runtime configuration values (backoff_base, default_max_retries, etc.).

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

## Testing Instructions

This project includes automated integration tests that verify all core functionalities of queuectl, including job execution, retries, DLQ handling, concurrency, graceful failures, and data persistence.

Before running any test script, ensure you have at least one terminal running workers:
```bash
queuectl worker start --count 3 --daemon
```
Then, open another terminal to execute the tests.

### On Linux

1. Set Execution Permissions
Before running the test script for the first time:
```bash
chmod +x test_queuectl.sh
```

2. Run the Test Script
```bash
./test_queuectl.sh
```

This script performs the following verifications:
* Basic job execution — ensures a simple job runs and completes successfully.
* Retry and DLQ logic — failed jobs are retried with exponential backoff and moved to the Dead Letter Queue after exceeding max_retries.
* DLQ retry — ensures jobs from the DLQ can be retried and either succeed or fail gracefully.
* Worker concurrency — multiple workers process jobs simultaneously without overlap.
* Graceful failure — invalid commands are correctly marked as failed.
* Persistence test — simulates a restart by removing and restoring the database, ensuring job data persists.
* Reset test — clears all jobs and verifies the queue is empty.

### On Windows (PowerShell)

1. Allow Script Execution
PowerShell blocks custom scripts by default.
To enable it temporarily for your session, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```
This allows PowerShell to run local scripts without changing global security settings.

2. Run the Test Script
```powershell
.\test_queuectl.ps1
```

This PowerShell test validates:
* Basic job execution — ensures a simple job runs and completes successfully.
* Retry and DLQ logic — failed jobs are retried with exponential backoff and moved to the Dead Letter Queue after exceeding max_retries.
* DLQ retry — ensures jobs from the DLQ can be retried and either succeed or fail gracefully.
* Worker concurrency — multiple workers process jobs simultaneously without overlap.
* Graceful failure — invalid commands are correctly marked as failed.
* Reset test — clears all jobs and verifies the queue is empty.

**Note on Persistence Test (Windows)**
* The persistence test is not automated on Windows because of NTFS file-locking rules —
SQLite keeps the database file open while workers are running, preventing file replacement.
* However, you can verify persistence manually:
  1. Run a few jobs:
  ```powershell
  queuectl enqueue '{""command"":""echo Persistent test""}'
  ```
  2. Close the PowerShell window entirely.
  3. Open a new PowerShell window and run:
  ```powershell
  queuectl list
  ```
  4. You should still see your previously enqueued jobs
* That confirms persistent storage is working correctly on Windows.

---

## Test Output

### Linux

<img width="1205" height="897" alt="image" src="https://github.com/user-attachments/assets/1a44813b-bcf5-466e-bb4b-a16be2095095" />

### Windows (PowerShell)

<img width="1199" height="860" alt="image" src="https://github.com/user-attachments/assets/87b3c121-7bcc-43f2-9e89-8e1502cfb0d3" />





