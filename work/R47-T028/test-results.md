# Test Results: Split-Second Stopwatch Reference Implementation

- **Total Tests Executed:** 29
- **Passed:** 29
- **Failed:** 0

## Named Test Cases

- **new stopwatch starts in ready state**: `passed`
- **new stopwatch's current lap has no elapsed time**: `passed`
- **new stopwatch's total has no elapsed time**: `passed`
- **new stopwatch does not have previous laps**: `passed`

## All Executed Cases

| Test Case | Status | Named Case |
| :--- | :---: | :---: |
| `lap adds current lap to previous laps` | PASS | No |
| `lap cannot be called from ready state` | PASS | No |
| `lap cannot be called from stopped state` | PASS | No |
| `lap continues time tracking for total` | PASS | No |
| `lap resets current lap and resumes time tracking` | PASS | No |
| `new stopwatch does not have previous laps` | PASS | Yes |
| `new stopwatch starts in ready state` | PASS | Yes |
| `new stopwatch's current lap has no elapsed time` | PASS | Yes |
| `new stopwatch's total has no elapsed time` | PASS | Yes |
| `reset cannot be called from ready state` | PASS | No |
| `reset cannot be called from running state` | PASS | No |
| `reset clears previous laps` | PASS | No |
| `reset from stopped state changes state to ready` | PASS | No |
| `reset resets current lap` | PASS | No |
| `start cannot be called from running state` | PASS | No |
| `start does not change previous laps` | PASS | No |
| `start from ready state changes state to running` | PASS | No |
| `start from stopped state changes state to running` | PASS | No |
| `start from stopped state resumes time tracking for current lap` | PASS | No |
| `start from stopped state resumes time tracking for total` | PASS | No |
| `start initiates time tracking for current lap` | PASS | No |
| `start initiates time tracking for total` | PASS | No |
| `stop cannot be called from ready state` | PASS | No |
| `stop cannot be called from stopped state` | PASS | No |
| `stop does not change previous laps` | PASS | No |
| `stop from running state changes state to stopped` | PASS | No |
| `stop pauses time tracking for current lap` | PASS | No |
| `stop pauses time tracking for total` | PASS | No |
| `supports very long laps` | PASS | No |
