# 🧰 queuectl — Minimal Production-Grade Job Queue (Python)

A CLI-based background job queue system built with **SQLite persistence**, **multi-worker support**, **automatic retries with exponential backoff**, and a **Dead Letter Queue (DLQ)**.

It's designed to be compact, readable, and production-like — a great example of how to build a reliable local job processing system using only Python's standard library.

---

## 🚀 Features

✅ Persistent job queue using SQLite  
✅ Multiple concurrent workers  
✅ Exponential backoff for retries  
✅ Automatic Dead Letter Queue (DLQ) for failed jobs  
✅ Configurable retry and backoff values  
✅ Sequential auto-generated unique job IDs (`job1`, `job2`, …)  
✅ Cross-platform: works on both Windows and Ubuntu  
✅ No external dependencies — pure Python standard library  

---

## 🧩 Project Structure

```
queuectl/
├── __init__.py
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

## 🐍 Requirements

- **Python 3.8+**
- No external dependencies
- Works on:
  - ✅ Ubuntu / WSL (Linux)
  - ✅ Windows 10/11 (PowerShell or Command Prompt)

---

## ⚙️ Installation

### 🟩 On Ubuntu / WSL

1️⃣ Clone the repository:
```bash
git clone https://github.com/<your-username>/queuectl.git
cd queuectl
```

2️⃣ (Recommended) Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3️⃣ Install in editable mode:

```bash
pip install -e .
```

✅ Verify installation:

```bash
queuectl --help
```

### 🟦 On Windows

1️⃣ Clone the repository:

```powershell
git clone https://github.com/<your-username>/queuectl.git
cd queuectl
```

2️⃣ (Optional but recommended) Create a virtual environment:

```powershell
python -m venv venv
venv\Scripts\activate
```

3️⃣ Install in editable mode:

```powershell
pip install -e .
```

✅ Verify installation:

```powershell
queuectl --help
```

⚠️ If you see `'queuectl' is not recognized`, ensure your Python Scripts folder is in your PATH
(e.g., `%USERPROFILE%\AppData\Local\Programs\Python\Python312\Scripts`).

---

## 🧠 How the CLI Works

`queuectl` is exposed automatically as a console script via `pyproject.toml`:

```toml
[project.scripts]
queuectl = "queuectl.main:main"
```

After installation (`pip install -e .`), you can invoke it directly from any terminal:

```bash
queuectl enqueue '{"command":"echo hello"}'
```

---

## 🧩 Example Commands

| Action | Command |
|--------|---------|
| Enqueue job | `queuectl enqueue '{"command":"echo Hello World"}'` |
| Check status | `queuectl status` |
| List jobs | `queuectl list --state pending` |
| View DLQ | `queuectl dlq list` |
| Retry DLQ job | `queuectl dlq retry job1` |
| Set config values | `queuectl config set backoff_base 2` |
| Clear all jobs | `queuectl reset` |

---

## ⚙️ Running Workers

Workers are long-running processes that continuously poll and execute jobs from the queue.

### 🧩 On Linux / Ubuntu / WSL

#### ▶ Option 1 — Foreground Workers (Interactive)
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

#### ▶ Option 2 — Background (Daemon) Workers

Run workers as background services:

```bash
queuectl worker start --count 3 --daemon
```

Example output:

```
Started worker pid=1234
Started worker pid=1235
Started worker pid=1236
Saved PIDs to ~/.queuectl/pids.json
```

Stop workers gracefully:

```bash
queuectl worker stop
```

### 🟦 On Windows

#### ▶ Option 1 — Foreground Workers (Interactive)
```powershell
queuectl worker start --count 3
```

Example output:

```
[worker 0] pid=5012 started
[worker 0] picked job job1: echo hello
hello
[worker 0] job job1 completed
[worker 1] pid=5013 started
[worker 2] pid=5015 started
```

Keep this terminal open for active workers.
Open another terminal for management commands:

```powershell
queuectl enqueue '{"command":"echo another job"}'
queuectl status
```

#### ▶ Option 2 — Background via New Window

Create a `.bat` file named `start_workers.bat` in your project folder:

```bat
@echo off
start "Queue Workers" cmd /c "queuectl worker start --count 3"
```

Run it by double-clicking or typing:

```bat
start_workers.bat
```

To stop:

```powershell
queuectl worker stop
```

Or close the "Queue Workers" window.

#### ▶ Option 3 — PowerShell Background Job

```powershell
Start-Job { queuectl worker start --count 3 }
```

List running jobs:

```powershell
Get-Job
```

Stop all background jobs:

```powershell
Stop-Job *
```

---

## 🧠 Architecture Summary

| Component | Description |
|-----------|-------------|
| Persistence | SQLite DB at `~/.queuectl/jobs.db` |
| Workers | Poll DB, claim pending jobs atomically |
| Concurrency | Managed via SQLite transactions (no race conditions) |
| Retry | Failed jobs rescheduled with exponential backoff |
| DLQ | Jobs exceeding max_retries moved to dead state |
| Job IDs | Auto-generated sequentially (job1, job2, job3...) |
| Config | Stored in config table (backoff base, retries) |
| Storage | Fully persistent between restarts |

---

## ⚙️ System Notes

✅ Works seamlessly on Linux and Windows  
✅ Auto-creates SQLite DB on first run  
✅ Background workers tracked via PID file  
✅ Thread-safe and crash-safe using SQLite WAL mode  
✅ Exponential retry logic: delay = base ^ attempts  

---

## 🧱 Tradeoffs & Future Improvements

| Area | Description |
|------|-------------|
| Scope | Single-machine queue using SQLite |
| Scaling | For distributed queues, replace DB with PostgreSQL or Redis |
| Polling | Could be improved with event-driven triggers |
| Background mode | PID files work locally; use systemd/supervisor for production |
| Extensions | Could add priorities, scheduled jobs, or a web dashboard |

---

## 🧪 Example Workflow

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

## 📦 Installation Summary

| Platform | Command |
|----------|---------|
| Ubuntu (venv) | `python3 -m venv .venv && source .venv/bin/activate && pip install -e .` |
| Windows (venv) | `python -m venv venv && venv\Scripts\activate && pip install -e .` |
| Ubuntu (user mode) | `python3 -m pip install --user -e . && export PATH="$HOME/.local/bin:$PATH"` |
| Global (unsafe) | `sudo python3 -m pip install -e . --break-system-packages` (not recommended) |

---

## 🧾 License

MIT License — feel free to modify and extend.

---

## 👨‍💻 Author

**Jaideep**  
Amrita Vishwa Vidyapeetham University, Coimbatore  
📧 your.email@example.com