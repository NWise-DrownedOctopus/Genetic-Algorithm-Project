import numpy as np
from dataclasses import dataclass
from constants import ACTIVITIES, ROOM_NAMES, TIMES, FACILITATORS

rng = np.random.default_rng(np.random.PCG64DXSM())

@dataclass
class Assignment:
    activity: dict
    room: str
    time: str
    facilitator: str

class Schedule:
    def __init__(self, assignments: list[Assignment]):
        self.assignments = assignments

def random_schedule() -> Schedule:
    assignments = []
    for activity in ACTIVITIES:
        room = str(rng.choice(ROOM_NAMES))
        time = str(rng.choice(TIMES))
        facilitator = str(rng.choice(FACILITATORS))
        assignments.append(Assignment(activity, room, time, facilitator))
    return Schedule(assignments)

def initialize_population(n=250) -> list[Schedule]:
    return [random_schedule() for _ in range(n)]

if __name__ == "__main__":
    s = random_schedule()
    for a in s.assignments:
        print(a)
    print(f"\nPopulation of 250 generated: {len(initialize_population(250))} schedules")