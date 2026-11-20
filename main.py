import os
import sys
import csv
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Project folders
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"
SCRIPT_DIR = BASE_DIR / "scripts"

for folder in [DATA_DIR, REPORT_DIR, SCRIPT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

LOG_FILE = DATA_DIR / "activity.log"


# ---------------- ACTIVITY LOGGING ----------------

def log_activity(message):
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] {message}\n")


def save_csv(filename, headers, rows):
    path = REPORT_DIR / filename

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"\nReport saved: {path}")


def get_number(message, minimum=0):
    while True:
        try:
            value = int(input(message))
            if value < minimum:
                print(f"Enter a number >= {minimum}.")
                continue
            return value
        except ValueError:
            print("Invalid input. Enter a whole number.")


def get_list(message):
    while True:
        try:
            raw_values = input(message).strip()
            if not raw_values:
                raise ValueError
            values = [int(x.strip()) for x in raw_values.split(",")]
            if any(x < 0 for x in values):
                raise ValueError
            return values
        except ValueError:
            print("Enter non-negative numbers separated by commas.")


# ---------------- CPU TEST HELPER ----------------

def calculate_fcfs(processes):
    """Calculate FCFS finish times and timeline for testing."""
    ordered = sorted(
        processes,
        key=lambda p: (p["arrival"], p["pid"])
    )

    time = 0
    finish = {}
    timeline = []

    for p in ordered:
        time = max(time, p["arrival"])
        start = time
        time += p["burst"]

        finish[p["pid"]] = time
        timeline.append((p["pid"], start, time))

    return finish, timeline


# ---------------- MEMORY ALGORITHM HELPERS ----------------

def simulate_page_replacement(pages, frame_count, algorithm):
    """Run FIFO or LRU and return step rows, hits, and faults."""
    if frame_count < 1:
        raise ValueError("Frame count must be at least 1.")
    if algorithm not in ("FIFO", "LRU"):
        raise ValueError("Algorithm must be FIFO or LRU.")

    memory = []
    last_used = {}
    hits = 0
    faults = 0
    rows = []

    for step, page in enumerate(pages):
        if page in memory:
            hits += 1
            result = "Hit"
        else:
            faults += 1
            result = "Fault"

            if len(memory) < frame_count:
                memory.append(page)
            elif algorithm == "FIFO":
                memory.pop(0)
                memory.append(page)
            else:
                least_recently_used = min(
                    memory,
                    key=lambda item: last_used[item]
                )
                memory.remove(least_recently_used)
                memory.append(page)

        last_used[page] = step
        rows.append([step + 1, page, result, str(memory)])

    return rows, hits, faults


# ---------------- DEADLOCK ALGORITHM HELPER ----------------

def check_bankers_safety(allocation, maximum, available):
    """Return Need matrix, safe sequence, and safety status."""
    process_count = len(allocation)
    resource_count = len(available)

    if process_count == 0 or len(maximum) != process_count:
        raise ValueError("Allocation and Maximum matrices must match.")
    if any(len(row) != resource_count for row in allocation + maximum):
        raise ValueError("Matrix row size does not match resource count.")
    if any(value < 0 for row in allocation + maximum for value in row):
        raise ValueError("Resource values cannot be negative.")
    if any(value < 0 for value in available):
        raise ValueError("Available resources cannot be negative.")

    for i in range(process_count):
        if any(maximum[i][j] < allocation[i][j]
               for j in range(resource_count)):
            raise ValueError("Maximum cannot be less than Allocation.")

    need = [
        [maximum[i][j] - allocation[i][j]
         for j in range(resource_count)]
        for i in range(process_count)
    ]

    work = available.copy()
    finished = [False] * process_count
    sequence = []

    while len(sequence) < process_count:
        progress = False

        for i in range(process_count):
            if not finished[i] and all(
                need[i][j] <= work[j] for j in range(resource_count)
            ):
                work = [
                    work[j] + allocation[i][j]
                    for j in range(resource_count)
                ]
                finished[i] = True
                sequence.append(f"P{i}")
                progress = True

        if not progress:
            break

    return need, sequence, len(sequence) == process_count


# ---------------- DISK ALGORITHM HELPER ----------------

def calculate_disk_order(requests, head, disk_size, algorithm):
    """Return service order and total movement for FCFS, SSTF, or SCAN.

    SCAN moves upward first. If lower requests exist, it reaches the
    highest cylinder (disk_size - 1) before reversing toward lower requests.
    """
    if disk_size < 2:
        raise ValueError("Disk size must be at least 2.")
    if not 0 <= head < disk_size:
        raise ValueError("Head position is outside the disk.")
    if any(request < 0 or request >= disk_size for request in requests):
        raise ValueError("A request is outside the disk.")

    if algorithm == "FCFS":
        order = requests.copy()

    elif algorithm == "SSTF":
        pending = requests.copy()
        order = []
        current = head

        while pending:
            nearest = min(
                pending,
                key=lambda item: abs(item - current)
            )
            order.append(nearest)
            pending.remove(nearest)
            current = nearest

    elif algorithm == "SCAN":
        higher = sorted(request for request in requests if request >= head)
        lower = sorted(
            (request for request in requests if request < head),
            reverse=True
        )
        order = higher.copy()

        if lower:
            if not order or order[-1] != disk_size - 1:
                order.append(disk_size - 1)
            order.extend(lower)

    else:
        raise ValueError("Unknown disk scheduling algorithm.")

    movement = 0
    current = head

    for request in order:
        movement += abs(request - current)
        current = request

    return order, movement


# ---------------- CPU SCHEDULING ----------------

def cpu_scheduling():

    print("\n--- CPU SCHEDULING ---")

    n = get_number("Number of processes: ", 1)

    processes = []

    for i in range(n):
        print(f"\nProcess P{i+1}")

        arrival = get_number("Arrival time: ")
        burst = get_number("Burst time: ", 1)

        processes.append({
            "pid": f"P{i+1}",
            "arrival": arrival,
            "burst": burst
        })

    print("\n1. FCFS")
    print("2. SJF (Non-preemptive)")
    print("3. Round Robin")

    choice = input("Choose algorithm: ")

    if choice not in ["1", "2", "3"]:
        print("Invalid choice.")
        return

    quantum = None

    if choice == "3":
        quantum = get_number("Enter time quantum: ", 1)

    remaining = {p["pid"]: p["burst"] for p in processes}
    finish = {}
    timeline = []
    time = 0

    if choice == "1":

        ordered = sorted(
            processes,
            key=lambda p: (p["arrival"], p["pid"])
        )

        for p in ordered:
            time = max(time, p["arrival"])
            start = time
            time += p["burst"]

            finish[p["pid"]] = time
            timeline.append((p["pid"], start, time))

    elif choice == "2":

        pending = processes.copy()

        while pending:

            available = [
                p for p in pending
                if p["arrival"] <= time
            ]

            if not available:
                time = min(p["arrival"] for p in pending)
                available = [
                    p for p in pending
                    if p["arrival"] <= time
                ]

            p = min(
                available,
                key=lambda x: (x["burst"], x["arrival"])
            )

            start = time
            time += p["burst"]

            finish[p["pid"]] = time
            timeline.append((p["pid"], start, time))

            pending.remove(p)

    else:

        queue = []
        ordered = sorted(processes, key=lambda p: p["arrival"])
        index = 0

        while len(finish) < n:

            while index < n and ordered[index]["arrival"] <= time:
                queue.append(ordered[index]["pid"])
                index += 1

            if not queue:
                time = ordered[index]["arrival"]
                continue

            pid = queue.pop(0)
            start = time

            run_time = min(quantum, remaining[pid])
            time += run_time
            remaining[pid] -= run_time

            timeline.append((pid, start, time))

            while index < n and ordered[index]["arrival"] <= time:
                queue.append(ordered[index]["pid"])
                index += 1

            if remaining[pid] > 0:
                queue.append(pid)
            else:
                finish[pid] = time

    rows = []
    total_wait = 0
    total_turnaround = 0

    print("\nPID  Arrival  Burst  Finish  Turnaround  Waiting")

    for p in processes:

        turnaround = finish[p["pid"]] - p["arrival"]
        waiting = turnaround - p["burst"]

        total_wait += waiting
        total_turnaround += turnaround

        row = [
            p["pid"], p["arrival"], p["burst"],
            finish[p["pid"]], turnaround, waiting
        ]

        rows.append(row)

        print(row)

    print("\nGantt Chart:")
    print(" | ".join(
        f"{pid} ({start}-{end})"
        for pid, start, end in timeline
    ))

    print("\nAverage Waiting Time:", round(total_wait / n, 2))
    print("Average Turnaround Time:", round(total_turnaround / n, 2))

    algorithm = ["FCFS", "SJF", "Round Robin"][int(choice)-1]

    save_csv(
        "cpu_scheduling.csv",
        ["PID", "Arrival", "Burst", "Finish", "Turnaround", "Waiting"],
        rows
    )

    log_activity(f"CPU scheduling: {algorithm}")


# ---------------- MEMORY MANAGEMENT ----------------

def memory_management():

    print("\n--- MEMORY MANAGEMENT ---")

    pages = get_list("Enter page reference string (e.g. 1,2,3,1,2): ")
    frames = get_number("Number of frames: ", 1)

    print("\n1. FIFO")
    print("2. LRU")

    choice = input("Choose algorithm: ")

    if choice not in ["1", "2"]:
        print("Invalid choice.")
        return

    algorithm = "FIFO" if choice == "1" else "LRU"
    rows, hits, faults = simulate_page_replacement(
        pages, frames, algorithm
    )

    for row in rows:
        print(
            f"Page: {row[1]} | {row[2]} | Frames: {row[3]}"
        )

    print("\nTotal Page Hits:", hits)
    print("Total Page Faults:", faults)
    print("Page Fault Rate:", round(faults / len(pages) * 100, 2), "%")

    save_csv(
        f"memory_{algorithm.lower()}.csv",
        ["Step", "Page", "Result", "Frames"],
        rows
    )

    log_activity(f"Memory management: {algorithm}")


# ---------------- DEADLOCK MANAGEMENT ----------------

def bankers_algorithm():

    print("\n--- BANKER'S ALGORITHM ---")

    n = get_number("Number of processes: ", 1)
    m = get_number("Number of resource types: ", 1)

    allocation = []
    maximum = []

    print("\nEnter Allocation Matrix:")

    for i in range(n):
        while True:
            try:
                row = list(map(int, input(f"P{i}: ").split()))

                if len(row) != m or any(x < 0 for x in row):
                    raise ValueError

                allocation.append(row)
                break

            except ValueError:
                print(f"Enter exactly {m} non-negative integers.")

    print("\nEnter Maximum Matrix:")

    for i in range(n):
        while True:
            try:
                row = list(map(int, input(f"P{i}: ").split()))

                if len(row) != m or any(x < 0 for x in row):
                    raise ValueError

                if any(row[j] < allocation[i][j] for j in range(m)):
                    print("Maximum cannot be less than Allocation.")
                    continue

                maximum.append(row)
                break

            except ValueError:
                print(f"Enter exactly {m} non-negative integers.")

    while True:
        try:
            available = list(map(int, input(
                f"Available resources ({m} values): "
            ).split()))

            if len(available) != m or any(x < 0 for x in available):
                raise ValueError

            break

        except ValueError:
            print(f"Enter exactly {m} non-negative integers.")

    need, sequence, safe = check_bankers_safety(
        allocation, maximum, available
    )

    print("\nNeed Matrix:")

    for row in need:
        print(row)

    if safe:
        print("\nSystem is in a SAFE state.")
        print("Safe Sequence:", " -> ".join(sequence))
    else:
        print("\nSystem is NOT in a safe state.")

    log_activity("Banker's Algorithm executed")


# ---------------- DISK SCHEDULING ----------------

def disk_scheduling():

    print("\n--- DISK SCHEDULING ---")

    requests = get_list("Enter disk requests: ")
    head = get_number("Initial head position: ", 0)
    size = get_number("Disk size: ", 2)

    if head >= size or any(request >= size for request in requests):
        print(f"Positions must be between 0 and {size-1}.")
        return

    print("\n1. FCFS")
    print("2. SSTF")
    print("3. SCAN")

    choice = input("Choose algorithm: ")

    if choice not in ["1", "2", "3"]:
        print("Invalid choice.")
        return

    algorithm = ["FCFS", "SSTF", "SCAN"][int(choice) - 1]
    order, movement = calculate_disk_order(
        requests, head, size, algorithm
    )

    print("\nService Order:", order)
    print("Total Head Movement:", movement, "cylinders")

    save_csv(
        "disk_scheduling.csv",
        ["Service Order"],
        [[request] for request in order]
    )

    log_activity(f"Disk scheduling: {algorithm}")


# ---------------- PYTHON AND BASH INTEGRATION ----------------

def system_information():

    print("\n--- SYSTEM INFORMATION ---")

    print("Operating System:", sys.platform)
    print("Python Version:", sys.version.split()[0])
    print("Project Location:", BASE_DIR)

    bash = shutil.which("bash") or r"C:\Program Files\Git\bin\bash.exe"
    script = SCRIPT_DIR / "system_info.sh"

    if not script.is_file():
        print("\nBash script not found:", script)
        log_activity("Bash script missing")
        return

    if not shutil.which("bash") and not Path(bash).is_file():
        print("\nBash not found.")
        print("Install Git Bash or WSL to use Bash integration.")
        log_activity("Bash not found")
        return

    try:
        result = subprocess.run(
            [bash, str(script)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )

        print("\nBASH OUTPUT:")
        if result.stdout:
            print(result.stdout)

        if result.returncode != 0:
            print("Bash exited with error code:", result.returncode)
        if result.stderr:
            print("Bash error output:")
            print(result.stderr)

    except (OSError, subprocess.TimeoutExpired) as error:
        print("Bash error:", error)
        log_activity(f"Bash error: {error}")
        return

    log_activity("System information displayed")


# ---------------- TESTING AND RELIABILITY ----------------

def run_tests():

    print("\n--- RUNNING TEST CASES ---")

    tests = []

    # CPU: test the same FCFS calculation helper used for verification.
    sample_processes = [
        {"pid": "P1", "arrival": 0, "burst": 5},
        {"pid": "P2", "arrival": 1, "burst": 3}
    ]
    finish, timeline = calculate_fcfs(sample_processes)
    tests.append((
        "CPU FCFS finish times",
        finish == {"P1": 5, "P2": 8}
    ))
    tests.append((
        "CPU FCFS timeline",
        timeline == [("P1", 0, 5), ("P2", 5, 8)]
    ))

    # FIFO and LRU: verify page hits/faults from the actual algorithms.
    pages = [1, 2, 3, 1, 4]
    fifo_rows, fifo_hits, fifo_faults = simulate_page_replacement(
        pages, 3, "FIFO"
    )
    lru_rows, lru_hits, lru_faults = simulate_page_replacement(
        pages, 3, "LRU"
    )
    tests.append((
        "Memory FIFO hit/fault count",
        fifo_hits == 1 and fifo_faults == 4
    ))
    tests.append((
        "Memory LRU hit/fault count",
        lru_hits == 1 and lru_faults == 4
    ))
    tests.append((
        "Memory report step count",
        len(fifo_rows) == len(pages) and len(lru_rows) == len(pages)
    ))

    # Banker's Algorithm: standard safe-state example.
    allocation = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1],
        [0, 0, 2]
    ]
    maximum = [
        [7, 5, 3],
        [3, 2, 2],
        [9, 0, 2],
        [2, 2, 2],
        [4, 3, 3]
    ]
    available = [3, 3, 2]
    need, sequence, safe = check_bankers_safety(
        allocation, maximum, available
    )
    tests.append((
        "Banker's Need matrix",
        need[0] == [7, 4, 3] and need[1] == [1, 2, 2]
    ))
    tests.append((
        "Banker's safe-state detection",
        safe and len(sequence) == 5
    ))

    # Disk algorithms: verify service order and movement.
    fcfs_order, fcfs_movement = calculate_disk_order(
        [40, 10], 20, 100, "FCFS"
    )
    sstf_order, sstf_movement = calculate_disk_order(
        [40, 10], 20, 100, "SSTF"
    )
    tests.append((
        "Disk FCFS movement",
        fcfs_order == [40, 10] and fcfs_movement == 50
    ))
    tests.append((
        "Disk SSTF movement",
        sstf_order == [10, 40] and sstf_movement == 40
    ))

    passed = 0

    for name, result in tests:
        if result:
            print("PASS:", name)
            passed += 1
        else:
            print("FAIL:", name)

    print(f"\nPassed {passed}/{len(tests)} tests.")

    log_activity(f"Testing completed: {passed}/{len(tests)} passed")


# ---------------- MAIN MENU ----------------

def main():

    print("\n========================================")
    print("     OS RESOURCE MANAGEMENT SIMULATOR")
    print("========================================")

    while True:

        print("\n1. CPU Scheduling")
        print("2. Memory Management")
        print("3. Deadlock Management")
        print("4. Disk Scheduling")
        print("5. System Information (Python + Bash)")
        print("6. Run Test Cases")
        print("7. Exit")

        choice = input("\nEnter your choice: ").strip()

        try:

            if choice == "1":
                cpu_scheduling()

            elif choice == "2":
                memory_management()

            elif choice == "3":
                bankers_algorithm()

            elif choice == "4":
                disk_scheduling()

            elif choice == "5":
                system_information()

            elif choice == "6":
                run_tests()

            elif choice == "7":
                print("\nThank you for using the simulator!")
                log_activity("Application closed")
                break

            else:
                print("Invalid choice. Select 1-7.")

        except (KeyboardInterrupt, EOFError):
            print("\nInput cancelled.")

        except Exception as error:
            print("Error handled:", error)
            log_activity(f"Error: {error}")


if __name__ == "__main__":
    main()
