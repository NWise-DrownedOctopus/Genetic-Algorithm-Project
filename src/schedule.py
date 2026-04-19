import numpy as np
from dataclasses import dataclass
from constants import ACTIVITIES, ROOM_NAMES, TIMES, FACILITATORS

rng = np.random.default_rng(np.random.PCG64DXSM())

@dataclass
class Assignment:
    """
    Data container for a single scheduled activity assignment.

    Attributes:
        activity (dict): Activity metadata.
        room (str): Assigned room name.
        time (str): Assigned time slot.
        facilitator (str): Assigned facilitator.
    """
    activity: dict
    room: str
    time: str
    facilitator: str

class Schedule:
    """
    Container for a full set of activity assignments representing a schedule.
    """
    def __init__(self, assignments: list[Assignment]):
        """
        Initialize a Schedule.

        Args:
            assignments (list[Assignment]): List of assignment objects.
        """
        self.assignments = assignments

def random_schedule() -> Schedule:
    """
    Generate a random valid schedule by assigning each activity
    a random room, time, and facilitator using the RNG.
    """
    assignments = []
    for activity in ACTIVITIES:
        room = str(rng.choice(ROOM_NAMES))
        time = str(rng.choice(TIMES))
        facilitator = str(rng.choice(FACILITATORS))
        assignments.append(Assignment(activity, room, time, facilitator))
    return Schedule(assignments)

def initialize_population(n=250) -> list[Schedule]:
    """
    Create a population of random schedules.

    Args:
        n (int): Number of schedules to generate.

    Returns:
        list[Schedule]: Generated population.
    """
    return [random_schedule() for _ in range(n)]

if __name__ == "__main__":
    s = random_schedule()
    for a in s.assignments:
        print(a)
    print(f"\nPopulation of 250 generated: {len(initialize_population(250))} schedules")