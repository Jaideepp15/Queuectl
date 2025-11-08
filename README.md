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

## Priority Scheduling & Aging

### Priority

Each job can be assigned a priority from **1** to **10**:

* 1 = **Highest priority**

* 10 = **Lowest priority**

* Default = **5**

Jobs with a lower priority number run first.
If two jobs share the same priority, the earlier created_at job executes first.

### Aging (Anti-Starvation)

To prevent starvation of low-priority jobs:

* Every minute a job remains pending, its priority improves (priority number decreases).

* It won’t drop below priority 1.

* Eventually, long-waiting jobs will bubble up and be executed.

Example:

| **Job Id** | **Initial Priority** | **Wait time(mins)** | **Aged Priority** |
|------------|----------------------|---------------------|-------------------|
| job1 | 9 | 3 | 6 |
| job2 | 5 | 2 | 3 |
| job3 | 2 | 1| 1 |

This ensures fair scheduling while honoring job importance.

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

## Architecture Summary

| Component | Description |
|-----------|-------------|
| Persistence | SQLite DB at `~/.queuectl/jobs.db` |
| Workers | Poll DB, claim pending jobs atomically |
| Priority | Lower numeric priority executes first |
| Aging | Pending jobs automatically gain higher priority over time |
| Concurrency | Managed via SQLite transactions (no race conditions) |
| Retry | Failed jobs rescheduled with exponential backoff |
| DLQ | Jobs exceeding max_retries moved to dead state |
| Job IDs | Auto-generated sequentially (job1, job2, job3...) |
| Config | Stored in config table (backoff base, retries) |
| Storage | Fully persistent between restarts |

---

## System Notes

* Works seamlessly on Linux and Windows  
* Auto-creates SQLite DB on first run  
* Background workers tracked via PID file  
* Thread-safe and crash-safe using SQLite WAL mode  
* Exponential retry logic: delay = base ^ attempts  
* Priority + Aging ensure fairness and responsiveness

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










