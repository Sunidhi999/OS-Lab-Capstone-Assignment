# OS Resource Management Simulator

## Project Overview

This project is an integrated Python and Bash application that simulates important Operating System resource management functions through an interactive menu.

## Modules

1. **CPU Scheduling**
   - First Come First Serve (FCFS)
   - Shortest Job First (SJF - Non-preemptive)
   - Round Robin

2. **Memory Management**
   - FIFO Page Replacement
   - LRU Page Replacement

3. **Deadlock Management**
   - Banker's Algorithm
   - Need Matrix Calculation
   - Safe State Detection

4. **Disk Scheduling**
   - FCFS
   - SSTF
   - SCAN (upward direction first)

5. **System Information**
   - Python system information
   - Bash script integration

6. **Testing and Reliability**
   - Built-in algorithm test cases
   - Input validation
   - Error handling
   - Activity logging

## Technologies Used

- Python
- Bash Shell
- CSV
- Visual Studio Code

## Requirements

- Python 3.9 or above
- Git Bash or WSL for Bash integration on Windows

## Project Structure

```text
OS_Resource_Management_Simulator/
├── main.py
├── README.md
├── scripts/
│   └── system_info.sh
├── reports/
└── data/
```

The `reports` and `data` folders are created automatically when the application runs.

## Execution Steps

1. Open the project folder in VS Code.
2. Open the integrated terminal.
3. Run:

   ```bash
   python main.py
   ```

4. Select an option from the main menu.
5. Follow the instructions displayed.

## Output

The application generates:

- CPU scheduling report: `reports/cpu_scheduling.csv`
- FIFO memory report: `reports/memory_fifo.csv`
- LRU memory report: `reports/memory_lru.csv`
- Disk scheduling report: `reports/disk_scheduling.csv`
- Activity log: `data/activity.log`

Reports are overwritten when the same module is run again.

## Algorithm Analysis and Comparison

### 1. CPU Scheduling

| Algorithm | Working Principle | Advantage | Limitation |
|---|---|---|---|
| FCFS | Executes processes in arrival order | Simple to implement | Can cause long waiting times |
| SJF | Executes the shortest available job first | Can reduce average waiting time | Long jobs may starve |
| Round Robin | Gives each process a fixed time quantum | Fair CPU allocation | Performance depends on time quantum |

### 2. Memory Management

| Algorithm | Working Principle | Advantage | Limitation |
|---|---|---|---|
| FIFO | Replaces the oldest loaded page | Simple implementation | May suffer from Belady's anomaly |
| LRU | Replaces the least recently used page | Uses recent page usage history | Requires tracking page usage |

### 3. Disk Scheduling

| Algorithm | Working Principle | Advantage | Limitation |
|---|---|---|---|
| FCFS | Serves requests in arrival order | Simple and fair | May cause more head movement |
| SSTF | Selects the nearest disk request | Reduces head movement in many cases | Distant requests may starve |
| SCAN | Disk head moves in one direction and then reverses | Provides more balanced service | May cause extra movement at disk ends |

### 4. Deadlock Management

Banker's Algorithm calculates the Need Matrix and checks whether the system can complete all processes in a safe sequence with the currently available resources. It avoids granting a resource request that would leave the system in an unsafe state.

### 5. Overall Analysis

Different algorithms provide different advantages depending on system requirements. CPU scheduling focuses on process execution, memory management handles page replacement, disk scheduling manages request order and head movement, and Banker's Algorithm checks safe resource allocation.

## Conclusion

The project demonstrates major Operating System resource management algorithms through an interactive Python and Bash application. It also generates CSV reports and activity logs to support testing and observation.
