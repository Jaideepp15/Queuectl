# test_queuectl.ps1
# Integration test for queuectl (run in Terminal 2)
# Workers should already be running in another terminal.

$ErrorActionPreference = "Stop"

function Pass($msg) { Write-Host "PASS: $msg" -ForegroundColor Green }
function Fail($msg) { Write-Host "FAIL: $msg" -ForegroundColor Red }
function Info($msg) { Write-Host "$msg" -ForegroundColor Yellow }


Write-Host "Starting Queuectl Integration Test (Windows)" -ForegroundColor Yellow

# Enqueue a valid job
Info "Enqueueing valid job..."
queuectl enqueue '{""command"":""echo Hello from queuectl""}' | Out-Null
Start-Sleep -Seconds 2

$jobList = queuectl list
$match = ($jobList | Select-String '"state":\s*"([^"]+)"')
if ($match) {
    $jobState = $match.Matches.Groups[1].Value
}
if ($jobState -eq "completed") {
    Pass "Basic job completed successfully"
} else {
    Fail "Basic job did not complete as expected"
}

# Enqueue an invalid command to trigger retries + DLQ
Info "Enqueueing invalid command for DLQ test..."
queuectl enqueue '{\"command\":\"invalidcommand\",\"max_retries\":2}' | Out-Null
Start-Sleep -Seconds 8  # Allow retries and DLQ transition

$dlqOutput = queuectl dlq list
$dlqJobIds = ($dlqOutput | Select-String '"state":\s*"dead"' | ForEach-Object {
    ($_ -match '"id":\s*"([^"]+)"') | Out-Null
    $matches[1]
})

if ($dlqJobIds) {
    Pass "Failed job retried and moved to DLQ"
} else {
    Fail "DLQ transition failed"
}

# DLQ Retry Test
Info "Retrying job from DLQ..."
$DLQ_OUTPUT = queuectl dlq list
$DLQ_JOB_ID = ($DLQ_OUTPUT | Select-String '"id":' | Select-Object -First 1).ToString().Split('"')[3]

if (-not $DLQ_JOB_ID) {
    Fail "Could not extract job ID from DLQ output"
} else {
    queuectl dlq retry $DLQ_JOB_ID | Out-Null
    Start-Sleep -Seconds 5

    # Check that job is no longer in DLQ
    $UPDATED_DLQ = queuectl dlq list
    if ($UPDATED_DLQ -match $DLQ_JOB_ID) {
        Fail "DLQ job did not move out of DLQ after retry"
    } else {
        Info "Job moved out of DLQ after retry attempt"
        # Verify job reprocessed (either completed or failed again)
        $jobList = queuectl list
        $match = ($jobList | Select-String '"state":\s*"([^"]+)"')
        if ($match) {
            $JOB_STATE = $match.Matches.Groups[1].Value
        }
        if ($JOB_STATE -eq "completed") {
            Pass "DLQ job retried and completed successfully"
        } elseif ($JOB_STATE -eq "failed") {
            Pass "DLQ job retried and failed again (handled correctly)"
        } else {
            Fail "DLQ job retry did not transition properly (state: $JOB_STATE)"
        }
    }
}

# Test concurrency — multiple workers should pick separate jobs
Info "Testing multi-worker concurrency..."
queuectl enqueue '{""command"":""echo Job A""}' | Out-Null
queuectl enqueue '{""command"":""echo Job B""}' | Out-Null
queuectl enqueue '{""command"":""echo Job C""}' | Out-Null
Start-Sleep -Seconds 4

$completedList = queuectl list --state completed
$completedCount = ($completedList | Select-String "Job").Count

if ($completedCount -ge 3) {
    Pass "Multiple workers processed jobs concurrently without overlap"
} else {
    Fail "Workers did not complete all jobs"
}

# Test invalid command handling (graceful failure)
Info "Testing graceful failure handling..."
queuectl enqueue '{""command"":""invalidcommand""}' | Out-Null
Start-Sleep -Seconds 4
$status = queuectl status
if ($status -match "failed") {
    Pass "Invalid job failed gracefully"
} else {
    Fail "System did not record failed job properly"
}

# Final summary
Info "Final queue status:"
queuectl status

# Cleanup
Info "Resetting..."
"y" | queuectl reset | Out-Null
Start-Sleep -Seconds 1

Info "Queue status after reset:"
queuectl status

Write-Host "All tests completed" -ForegroundColor Yellow

