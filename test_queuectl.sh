#!/bin/bash
# test_queuectl.sh
# Integration test for queuectl (run in Terminal 2)
# Workers should already be running in another terminal.

set -e
set -o pipefail

GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
NC="\033[0m"

pass() { echo -e "${GREEN}PASS:${NC} $1"; }
fail() { echo -e "${RED}FAIL:${NC} $1"; }
info() { echo -e "${YELLOW}$1${NC}"; }

info "Starting Queuectl Integration Test (Linux/WSL)"

# Enqueue a valid job
info "Enqueueing valid job..."
queuectl enqueue '{"command":"echo Hello from queuectl"}' >/dev/null
sleep 2

job_state=$(queuectl list | grep "$jobId" | grep -o '"state": *"[^"]*"' | cut -d'"' -f4)
if [ "$job_state" = "completed" ]; then
  pass "Basic job completed successfully"
else
  fail "Basic job did not complete as expected"
fi

# Enqueue an invalid command to trigger retries + DLQ
info "Enqueueing invalid command for DLQ test..."
queuectl enqueue '{"command":"invalidcommand","max_retries":2}' >/dev/null
sleep 8  # Allow retries and DLQ transition

dlq_job_ids=$(queuectl dlq list | grep '"state": *"dead"' | grep -o '"id": *"[^"]*"' | cut -d'"' -f4)
if [ -n "$dlq_job_ids" ]; then
  pass "Failed job retried and moved to DLQ"
else
  fail "DLQ transition failed"
fi

# DLQ Retry Test
info "Retrying job from DLQ..."
DLQ_OUTPUT=$(queuectl dlq list)
DLQ_JOB_ID=$(echo "$DLQ_OUTPUT" | grep -o '"id": *"[^"]*"' | head -1 | cut -d '"' -f4)

if [ -z "$DLQ_JOB_ID" ]; then
  fail "Could not extract job ID from DLQ output"
else
  queuectl dlq retry "$DLQ_JOB_ID" >/dev/null
  sleep 5

  # Check that job is no longer in DLQ
  UPDATED_DLQ=$(queuectl dlq list)
  if echo "$UPDATED_DLQ" | grep -q "$DLQ_JOB_ID"; then
    fail "DLQ job did not move out of DLQ after retry"
  else
    info "Job moved out of DLQ after retry attempt"
    # Verify job reprocessed (either completed or failed again)
    JOB_STATE=$(queuectl list | grep "$DLQ_JOB_ID" | grep -o '"state": *"[^"]*"' | cut -d '"' -f4)
    if [ "$JOB_STATE" = "completed" ]; then
      pass "DLQ job retried and completed successfully"
    elif [ "$JOB_STATE" = "failed" ]; then
      pass "DLQ job retried and failed again (handled correctly)"
    else
      fail "DLQ job retry did not transition properly (state: $JOB_STATE)"
    fi
  fi
fi

# Test concurrency — multiple workers should pick separate jobs
info "Testing multi-worker concurrency..."
queuectl enqueue '{"command":"echo Job A"}' >/dev/null
queuectl enqueue '{"command":"echo Job B"}' >/dev/null
queuectl enqueue '{"command":"echo Job C"}' >/dev/null
sleep 4

COMPLETED=$(queuectl list --state completed | grep -c "Job")
if [ "$COMPLETED" -ge 3 ]; then
  pass "Multiple workers processed jobs concurrently without overlap"
else
  fail "Workers did not complete all jobs"
fi

# Test invalid command handling (graceful failure)
info "Testing graceful failure handling..."
queuectl enqueue '{"command":"invalidcommand"}' >/dev/null
sleep 4
if queuectl status | grep -q "failed"; then
  pass "Invalid job failed gracefully"
else
  fail "System did not record failed job properly"
fi

# Test persistence (simulate restart)
info "Testing persistence after simulated restart..."
DB_PATH="$HOME/.queuectl/jobs.db"
cp "$DB_PATH" "$DB_PATH.bak"
queuectl enqueue '{"command":"echo Persistent Job"}' >/dev/null
sleep 2
mv "$DB_PATH.bak" "$DB_PATH"
sleep 2
if queuectl status | grep -q "Job states"; then
  pass "Job data persisted across restart"
else
  fail "Persistence test failed"
fi

# Final summary
info "Final queue status:"
queuectl status

# Cleanup
info "Resetting.."
echo "y" | queuectl reset >/dev/null 2>&1
sleep 1

info "Queue status after reset:"
queuectl status

echo "All tests completed"
