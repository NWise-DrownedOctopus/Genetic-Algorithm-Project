from schedule import Schedule, Assignment
from constants import ROOMS

def score_schedule(schedule: Schedule) -> float:
    total = 0.0

    # Rule 1 — Room conflict
    for i in range(len(schedule.assignments)):
        for j in range(i + 1, len(schedule.assignments)):
            a1 = schedule.assignments[i]
            a2 = schedule.assignments[j]
            if a1.room == a2.room and a1.time == a2.time:
                total -= 0.5
                total -= 0.5

    # Rule 2 — Room size
    for a in schedule.assignments:
        capacity = ROOMS[a.room]
        enrollment = a.activity["enrollment"]

        if capacity < enrollment:
            total -= 0.5
        elif capacity > 3 * enrollment:
            total -= 0.4
        elif capacity > 1.5 * enrollment:
            total -= 0.2
        else:
            total += 0.3

    # Rule 3 — Facilitator type
    for a in schedule.assignments:
        facilitator = a.facilitator
        preferred = a.activity["preferred"]
        other = a.activity["other"]

        if facilitator in preferred:
            total += 0.5
        elif facilitator in other:
            total += 0.2
        else:
            total -= 0.1

    return total


if __name__ == "__main__":
    a1 = Assignment(
        activity={"name": "A", "enrollment": 20, "preferred": ["X"], "other": ["Y"]},
        room="Beach 201",  # capacity 18 -> < enrollment => -0.5
        time="10 AM",
        facilitator="X",  # preferred => +0.5
    )

    a2 = Assignment(
        activity={"name": "B", "enrollment": 10, "preferred": ["X"], "other": ["Y"]},
        room="Beach 201",  # same room/time as a1 => conflict
        time="10 AM",
        facilitator="Y",  # other => +0.2
    )

    a3 = Assignment(
        activity={"name": "C", "enrollment": 10, "preferred": ["X"], "other": ["Y"]},
        room="Frank 119",  # capacity 95 -> > 3x => -0.4
        time="11 AM",
        facilitator="Z",  # neither => -0.1
    )

    s = Schedule([a1, a2, a3])

    # Expected calculation:
    # Conflicts: a1 & a2 => -1.0 total
    # Room size: a1 (-0.5), a2 (18 > 1.5*10 => -0.2), a3 (-0.4) => -1.1
    # Facilitator: a1 (+0.5), a2 (+0.2), a3 (-0.1) => +0.6
    # Total: -1.0 + (-1.1) + 0.6 = -1.5

    result = score_schedule(s)
    expected = -1.5

    print(f"Result: {result}, Expected: {expected}")