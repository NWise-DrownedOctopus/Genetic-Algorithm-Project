import os
import csv
import datetime

#output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

#create directory if it does not already exist
def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_schedule(schedule: list, generation: int, fitness: float,
                  order: str = "time") -> str:
    _ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, "best_schedule.txt")

    #sort rows by time slot index or alphabetically by name
    from constants import TIMES
    if order == "time":
        schedule = sorted(schedule, key=lambda a: TIMES.index(a["time"]))
    else:
        schedule = sorted(schedule, key=lambda a: a["activity"])

    with open(path, "w") as f:
        f.write(f"Best Schedule — Generation {generation} — Fitness: {fitness:.4f}\n")
        f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 70 + "\n")
        f.write(f"{'Activity':<12} {'Room':<14} {'Time':<8} {'Facilitator':<12} {'Score'}\n")
        f.write("-" * 70 + "\n")
        #row per activity assignment
        for row in schedule:
            f.write(f"{row['activity']:<12} {row['room']:<14} {row['time']:<8} "
                    f"{row['facilitator']:<12} {row.get('score', 0.0):+.2f}\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total Fitness: {fitness:.4f}\n")
    return path

def export_csv(history: list, path: str = None) -> str:
    raise NotImplementedError("export_csv() not yet implemented")

#log writer
def write_log(generation: int, best_fitness: float, schedule: list = None,
              path: str = None) -> None:
    raise NotImplementedError("write_log() not yet implemented")

#smoke test
if __name__ == "__main__":
    print("output.py loaded — stub signatures verified")
    print(f"Output directory target: {OUTPUT_DIR}")
    print()

    stubs = [
        ("export_csv",     lambda: export_csv([])),
        ("write_log",      lambda: write_log(0, 0.0)),
    ]

    for name, call in stubs:
        try:
            call()
            print(f"  [WARN] {name}() did not raise NotImplementedError — check stub body")
        except NotImplementedError:
            print(f"  [OK]   {name}() stub confirmed (raises NotImplementedError)")
        except Exception as e:
            print(f"  [WARN] {name}() raised unexpected error: {e}")

    print("[ save_schedule() ]")
    test_schedule = [
        {"activity": "SLA101A", "room": "Roman 201", "time": "10 AM", "facilitator": "Glen", "score": 0.8},
        {"activity": "SLA451", "room": "Frank 119", "time": "3 PM", "facilitator": "Banks", "score": 0.5},
    ]
    path = save_schedule(test_schedule, generation=1, fitness=1.3)
    print(f"  [OK]   written to {path}")
    print()

    print()
    print("_ensure_output_dir() test:")
    _ensure_output_dir()
    if os.path.isdir(OUTPUT_DIR):
        print(f"  [OK]   output/ directory exists at {OUTPUT_DIR}")
    else:
        print(f"  [FAIL] Could not create {OUTPUT_DIR}")

    print()
    print("Interface contract (agreed with Member B on Apr 14):")
    print("  save_schedule() receives list[Assignment|dict], int, float, str")
    print("                  returns  str (file path)")
    print("  export_csv()    receives list[dict|tuple]")
    print("                  returns  str (file path)")
    print("  write_log()     receives int, float, list|None")
    print("                  returns  None (appends to log file)")
    print()
    print("Expected output files:")
    print("  output/best_schedule.txt")
    print("  output/fitness_history.csv")
    print("  output/ga_run.log")