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
    raise NotImplementedError("save_schedule() not yet implemented")

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
        ("save_schedule",  lambda: save_schedule([], 0, 0.0)),
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