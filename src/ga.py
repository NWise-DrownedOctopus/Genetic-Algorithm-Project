import numpy as np
from scipy.special import softmax
from copy import deepcopy
from schedule import Schedule
from fitness import score_schedule
from constants import ROOM_NAMES, TIMES, FACILITATORS

rng = np.random.default_rng(np.random.PCG64DXSM())

#selection
def select(population: list, scores: list[float]) -> tuple:
    """
    select two parent schedules using softmax
    higher fitness scores are more likely to be selected
    """
    probs = softmax(scores)
    idx = rng.choice(len(population), size=2, p=probs)
    return population[idx[0]], population[idx[1]]

#crossover
def crossover(parent_a, parent_b):
    """
    produce one offspring via crossover
    split both parent assignment lists at random index and combine them
    parents never modified, assignments deepcopied
    """
    n = len(parent_a.assignments)
    k = int(rng.integers(1, n))
    child_assignments = (deepcopy(parent_a.assignments[:k])
                         + deepcopy(parent_b.assignments[k:]))
    return Schedule(child_assignments)

#mutation
def mutate(schedule, lam: float = 0.01):
    """
    apply per activity mutation to a schedule at rate lambda
    each assignment has a lambda probability of having 1 field
    (room, time, or facilitator) randomly replaced from valid domain
    """
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
    """
    execute one full generational step of the genetic algo
    produce N offspring via selection, crossover and mutation
    scores them and returns new population with metrics
    returns (new_population, metrics_dict)
    """
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
def check_stopping_condition(generation: int, improvement_pct: float, min_generations: int = 100, improvement_threshold: float = 1.0) -> bool:
    """
    return true when both stopping criteria are met:
    1. at least 100 generations have been completed
    2. improvement in average fitness is less than 1%
    """
    return generation >= min_generations and improvement_pct < improvement_threshold

#mutation rate scheduler
def halve_mutation_rate(lam: float, min_lam: float = 0.0001) -> float:
    return max(min_lam, lam / 2)


