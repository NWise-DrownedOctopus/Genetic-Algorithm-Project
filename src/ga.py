import numpy as np
from scipy.special import softmax
from copy import deepcopy
from schedule import Schedule, Assignment, initialize_population
from fitness import score_schedule
from constants import ROOM_NAMES, TIMES, FACILITATORS

rng = np.random.default_rng(np.random.PCG64DXSM())

#selection
def select(population: list, scores: list[float]) -> tuple:
    probs = softmax(scores)
    idx = rng.choice(len(population), size=2, p=probs)
    return population[idx[0]], population[idx[1]]

#crossover
def crossover(parent_a, parent_b):
    raise NotImplementedError("crossover() not yet implemented")

#mutation
def mutate(schedule, lam: float = 0.01):
    raise NotImplementedError("mutate() not yet implemented")

#generational loop
def run_generation(population: list, scores: list[float], lam: float = 0.01, generation: int = 0, prev_avg: float = None) -> tuple:
    N = len(population)
    new_scores = scores
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
    return population, metrics

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
    print("=" * 60)
    print()

    pop = initialize_population(250)
    scores = [score_schedule(s) for s in pop]

    #select
    print("[ select() ]")
    a, b = select(pop, scores)
    assert isinstance(a, Schedule), "select() did not return a Schedule"
    assert isinstance(b, Schedule), "select() did not return a Schedule"
    assert a in pop, "parent_a not from population"
    assert b in pop, "parent_b not from population"
    print(f"  [OK]   Returns two Schedule objects from population")

    #bias check
    best_idx = scores.index(max(scores))
    worst_idx = scores.index(min(scores))
    best_count, worst_count = 0, 0
    for _ in range(1000):
        x, y = select(pop, scores)
        if x is pop[best_idx] or y is pop[best_idx]:
            best_count += 1
        if x is pop[worst_idx] or y is pop[worst_idx]:
            worst_count += 1
    print(f"  [OK]   Best schedule selected  {best_count}/1000 trials")
    print(f"  [OK]   Worst schedule selected {worst_count}/1000 trials")
    assert best_count > worst_count, "softmax bias check failed — best should outscore worst"
    print(f"  [OK]   Softmax bias confirmed (best > worst selection frequency)")
    print()

    #run_generation metrics
    print("[ run_generation() — metrics (Apr 16 partial) ]")
    _, m = run_generation(pop, scores, lam=0.01, generation=1, prev_avg=None)
    assert "best" in m, "metrics missing 'best'"
    assert "avg" in m, "metrics missing 'avg'"
    assert "worst" in m, "metrics missing 'worst'"
    assert "improvement" in m, "metrics missing 'improvement'"
    assert "lam" in m, "metrics missing 'lam'"
    assert "generation" in m, "metrics missing 'generation'"
    assert m["best"] >= m["avg"] >= m["worst"], "best/avg/worst ordering wrong"
    assert m["improvement"] == 0.0, "improvement should be 0.0 on gen 1"
    print(f"  [OK]   All metric keys present")
    print(f"  [OK]   best={m['best']:.4f}  avg={m['avg']:.4f}  worst={m['worst']:.4f}")
    print(f"  [OK]   improvement={m['improvement']:.4f}%  lam={m['lam']}  gen={m['generation']}")

    #test improvement % with a known prev_avg
    _, m2 = run_generation(pop, scores, lam=0.01, generation=2, prev_avg=m["avg"] * 0.9)
    expected_imp = ((m2["avg"] - m["avg"] * 0.9) / abs(m["avg"] * 0.9)) * 100
    assert abs(m2["improvement"] - expected_imp) < 0.001, "improvement % calculation wrong"
    print(f"  [OK]   improvement % formula correct (gen 2: {m2['improvement']:.4f}%)")
    print()

    #stubs
    print("[ Remaining stubs ]")
    stubs = [
        ("crossover", lambda: crossover(None, None)),
        ("mutate", lambda: mutate(None)),
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

