import os
import csv
import datetime

#output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

#create directory if it does not already exist
def _ensure_output_dir():os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_schedule(schedule: list, generation: int, fitness: float, order: str = "time") -> str:
    """
    write best schedule to output/best_schedule.txt
    sorts by time slot index if order='time', or alphabetically if order='activity'
    return absolute path of written file
    """
    _ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, "best_schedule.txt")

    #sort rows by time slot index or alphabetically by name
    from constants import TIMES
    if order == "time":
        schedule = sorted(schedule, key=lambda a: TIMES.index(a["time"]))
    else:
        schedule = sorted(schedule, key=lambda a: a["activity"])

    with open(path, "w") as f:
        f.write(f"Best Schedule - Generation {generation} - Fitness: {fitness:.4f}\n")
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
    """
    write per gen fitness history to output/fitness_history.csv
    accepts list of (best, avg, worst) tuples or dicts
    returns absolute path of the written file
    """
    _ensure_output_dir()
    path = path or os.path.join(OUTPUT_DIR, "fitness_history.csv")

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["generation", "best", "avg", "worst", "improvement_pct"])
        writer.writeheader()
        for i, entry in enumerate(history):
            if isinstance(entry, tuple):
                best, avg, worst = entry
                writer.writerow({
                    "generation":      i + 1,
                    "best":            round(best, 6),
                    "avg":             round(avg, 6),
                    "worst":           round(worst, 6),
                    "improvement_pct": 0.0,
                })
            else:
                writer.writerow({
                    "generation":      entry.get("generation", i + 1),
                    "best":            round(entry.get("best", 0.0), 6),
                    "avg":             round(entry.get("avg", 0.0), 6),
                    "worst":           round(entry.get("worst", 0.0), 6),
                    "improvement_pct": round(entry.get("improvement", 0.0), 6),
                })
    return path

#log writer
def write_log(generation: int, best_fitness: float, schedule: list = None, path: str = None) -> None:
    """
    append one timestamped entry to output/ga_run.log
    if schedule is provided, writes each assignment as a compact row below the entry
    opens in append mode so full run history is preserved
    """
    _ensure_output_dir()
    path = path or os.path.join(OUTPUT_DIR, "ga_run.log")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(path, "a") as f:
        f.write(f"[{timestamp}]  Gen {generation:04d}  Best: {best_fitness:.4f}\n")
        if schedule:
            for row in schedule:
                f.write(f"  {row['activity']:<12} {row['room']:<14} "
                        f"{row['time']:<8} {row['facilitator']}\n")
