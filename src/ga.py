#placeholder
# from schedule import Schedule, Assignment, initialize_population
# from fitness import score_schedule
# from constants import ROOM_NAMES, TIMES, FACILITATORS
import numpy as np

#selection
def select(population: list, scores: list[float]) -> tuple:
    raise NotImplementedError("select() not yet implemented")

#crossover
def crossover(parent_a, parent_b):
    raise NotImplementedError("crossover() not yet implemented")

#mutation
def mutate(schedule, lam: float = 0.01):
    raise NotImplementedError("mutate() not yet implemented")

#generational loop
def run_generation(population: list, scores: list[float], lam: float = 0.01) -> tuple:
    raise NotImplementedError("run_generation() not yet implemented")

#stop condition
def check_stopping_condition(generation: int, improvement_pct: float,
                              min_generations: int = 100,
                              improvement_threshold: float = 1.0) -> bool:
    raise NotImplementedError("check_stopping_condition() not yet implemented")

#mutation rate scheduler
def halve_mutation_rate(lam: float, min_lam: float = 0.0001) -> float:
    return max(min_lam, lam / 2)

#smoke test
if __name__ == "__main__":
    print("ga.py loaded — stub signatures verified")
    print()

    stubs = [
        ("select",                   lambda: select([], [])),
        ("crossover",                lambda: crossover(None, None)),
        ("mutate",                   lambda: mutate(None)),
        ("run_generation",           lambda: run_generation([], [])),
        ("check_stopping_condition", lambda: check_stopping_condition(0, 0.0)),
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
    print("halve_mutation_rate() tests:")
    print(f"  0.01  -> {halve_mutation_rate(0.01):.6f}  (expect 0.005000)")
    print(f"  0.001 -> {halve_mutation_rate(0.001):.6f}  (expect 0.000500)")
    print(f"  0.0001-> {halve_mutation_rate(0.0001):.6f}  (expect 0.000100, floor)")
    print(f"  0.00005->{halve_mutation_rate(0.00005):.6f}  (expect 0.000100, floor)")
    print()
    print("Interface contract (agreed with Member A on Apr 14):")
    print("  select()       receives list[Schedule], list[float]")
    print("  crossover()    receives Schedule, Schedule — returns Schedule")
    print("  mutate()       receives Schedule, float    — returns Schedule")
    print("  run_generation receives list[Schedule], list[float], float")
    print("                 returns  list[Schedule], dict")
    print("  Schedule.assignments is list[Assignment]")
    print("  Assignment fields: .activity (dict), .room (str), .time (str), .facilitator (str)")