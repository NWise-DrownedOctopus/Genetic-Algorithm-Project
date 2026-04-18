import numpy as np
from scipy.special import softmax
from copy import deepcopy
from schedule import Schedule, Assignment, initialize_population
from fitness import score_schedule
from constants import ROOM_NAMES, TIMES, FACILITATORS

rng = np.random.default_rng(np.random.PCG64DXSM())

#selection
def select(population: list, scores: list[float]) -> tuple:
    raise NotImplementedError("select() not yet implemented")

#crossover
def crossover(parent_a, parent_b):
    n = len(parent_a.assignments)
    k = int(rng.integers(1, n))
    child_assignments = (deepcopy(parent_a.assignments[:k])
                         + deepcopy(parent_b.assignments[k:]))
    return Schedule(child_assignments)

#mutation
def mutate(schedule, lam: float = 0.01):
    for a in schedule.assignments:
        if rng.random() < lam:
            field = int(rng.integers(0, 3))
            if field == 0:
                a.room = str(rng.choice(ROOM_NAMES))
            elif field == 1:
                a.time = str(rng.choice(TIMES))
            else:
                a.facilitator = str(rng.choice(FACILITATORS))
    return schedule

#generational loop
def run_generation(population: list, scores: list[float], lam: float = 0.01, generation: int = 0, prev_avg: float = None) -> tuple:
    N = len(population)
    next_gen = []

    while len(next_gen) < N:
        a, b = select(population, scores)
        child = crossover(a, b)
        mutate(child, lam)
        next_gen.append(child)

    new_scores = [score_schedule(s) for s in next_gen]

    best = float(max(new_scores))
    avg = float(sum(new_scores) / N)
    worst = float(min(new_scores))

    if prev_avg is not None and prev_avg != 0.0:
        improvement = ((avg - prev_avg) / abs(prev_avg)) * 100
    else:
        improvement = 0.0

    metrics = {
        "best": best,
        "avg": avg,
        "worst": worst,
        "improvement": improvement,
        "lam": lam,
        "generation": generation,
    }
    return next_gen, metrics

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
    print("=" * 60)
    print("ga.py — April 15 interface verification")
    print("=" * 60)
    print()

    #confirm imports resolve against real Member A modules
    print("[ Import check ]")
    try:
        from schedule import Schedule, Assignment, initialize_population

        print("  [OK] schedule.py  — Schedule, Assignment, initialize_population")
    except ImportError as e:
        print(f"  [FAIL] schedule.py: {e}")

    try:
        from fitness import score_schedule

        print("  [OK] fitness.py   — score_schedule")
    except ImportError as e:
        print(f"  [FAIL] fitness.py: {e}")

    try:
        from constants import ROOM_NAMES, TIMES, FACILITATORS

        print(f"  [OK] constants.py — {len(ROOM_NAMES)} rooms, "
              f"{len(TIMES)} time slots, {len(FACILITATORS)} facilitators")
    except ImportError as e:
        print(f"  [FAIL] constants.py: {e}")

    print()

    #confirm Schedule / Assignment fields match
    print("[ Interface contract — Member A data structures ]")
    pop = initialize_population(1)
    s = pop[0]
    a = s.assignments[0]

    checks = [
        (hasattr(s, "assignments"), "Schedule.assignments exists"),
        (isinstance(s.assignments, list), "Schedule.assignments is list"),
        (hasattr(a, "activity"), "Assignment.activity exists"),
        (hasattr(a, "room"), "Assignment.room exists"),
        (hasattr(a, "time"), "Assignment.time exists"),
        (hasattr(a, "facilitator"), "Assignment.facilitator exists"),
        (isinstance(a.activity, dict), "Assignment.activity is dict"),
        ("name" in a.activity, "activity has 'name'"),
        ("enrollment" in a.activity, "activity has 'enrollment'"),
        ("preferred" in a.activity, "activity has 'preferred'"),
        ("other" in a.activity, "activity has 'other'"),
        (a.room in ROOM_NAMES, f"room '{a.room}' in ROOM_NAMES"),
        (a.time in TIMES, f"time '{a.time}' in TIMES"),
        (a.facilitator in FACILITATORS, f"facilitator '{a.facilitator}' in FACILITATORS"),
    ]
    for passed, label in checks:
        print(f"  {'[OK]  ' if passed else '[FAIL]'} {label}")

    print()

    #confirm score_schedule accepts Schedule and returns float
    print("[ score_schedule() interface ]")
    score = score_schedule(s)
    ok = isinstance(score, float)
    print(f"  {'[OK]  ' if ok else '[FAIL]'} score_schedule(Schedule) -> float  "
          f"(sample: {score:.4f})")
    print()

    #stub confirmation
    print("[ Stub confirmation ]")
    stubs = [
        ("select", lambda: select([], [])),
        ("crossover", lambda: crossover(None, None)),
        ("mutate", lambda: mutate(None)),
        ("run_generation", lambda: run_generation([], [])),
        ("check_stopping_condition", lambda: check_stopping_condition(0, 0.0)),
    ]
    for name, call in stubs:
        try:
            call()
            print(f"  [WARN] {name}() did not raise NotImplementedError")
        except NotImplementedError as e:
            print(f"  [OK]   {name}() stub — {e}")
        except Exception as e:
            print(f"  [WARN] {name}() unexpected error: {e}")
    print()

    #halve mutation rate
    print("[ halve_mutation_rate() ]")
    cases = [
        (0.01, 0.005, "normal halve"),
        (0.001, 0.0005, "normal halve"),
        (0.0001, 0.0001, "at floor"),
        (0.00005, 0.0001, "below floor — clamp"),
    ]
    for lam_in, expected, label in cases:
        result = halve_mutation_rate(lam_in)
        ok = abs(result - expected) < 1e-10
        print(f"  {'[OK]  ' if ok else '[FAIL]'} {lam_in:.5f} -> {result:.6f}  ({label})")
    print()

    #population scale fitness check
    print("[ Population fitness check (N=10) ]")
    small_pop = initialize_population(10)
    small_scores = [score_schedule(s) for s in small_pop]
    print(f"  [OK]   Scored 10 schedules")
    print(f"         best={max(small_scores):.4f}  "
          f"avg={sum(small_scores) / len(small_scores):.4f}  "
          f"worst={min(small_scores):.4f}")
    print()
