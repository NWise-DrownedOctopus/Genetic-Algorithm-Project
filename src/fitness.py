from schedule import Schedule, Assignment, initialize_population
from constants import ROOMS, TIMES

def score_schedule(schedule: Schedule) -> float:
    total = 0.0

    assignments = schedule.assignments

    # Rule 1 — Room conflict
    for i in range(len(assignments)):
        for j in range(i + 1, len(assignments)):
            a1 = assignments[i]
            a2 = assignments[j]
            if a1.room == a2.room and a1.time == a2.time:
                total -= 0.5
                total -= 0.5

    # Rule 2 — Room size
    for a in assignments:
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
    for a in assignments:
        facilitator = a.facilitator
        preferred = a.activity["preferred"]
        other = a.activity["other"]

        if facilitator in preferred:
            total += 0.5
        elif facilitator in other:
            total += 0.2
        else:
            total -= 0.1

    # Precompute counts for Rule 4 and 5
    fac_time_count = {}
    fac_total_count = {}

    for a in assignments:
        key = (a.facilitator, a.time)
        fac_time_count[key] = fac_time_count.get(key, 0) + 1
        fac_total_count[a.facilitator] = fac_total_count.get(a.facilitator, 0) + 1

    time_index = {t: i for i, t in enumerate(TIMES)}

    # Rule 4 — Facilitator load
    for a in assignments:
        ft = fac_time_count[(a.facilitator, a.time)]
        total_count = fac_total_count[a.facilitator]

        if ft == 1:
            total += 0.2
        elif ft > 1:
            total -= 0.2

        if total_count > 4:
            total -= 0.5
        elif a.facilitator == "Tyler":
            if total_count < 2:
                total -= 0.4
        else:
            if total_count < 3:
                total -= 0.4

    # Rule 5 — Consecutive time slot penalty for facilitators
    def is_rb(room):
        return room.startswith("Roman") or room.startswith("Beach")

    for i in range(len(assignments)):
        for j in range(i + 1, len(assignments)):
            a1 = assignments[i]
            a2 = assignments[j]
            if a1.facilitator == a2.facilitator:
                if abs(time_index[a1.time] - time_index[a2.time]) == 1:
                    total += 0.5
                    if is_rb(a1.room) != is_rb(a2.room):
                        total -= 0.4

    # Helper to find assignments by activity name
    def find(name):
        for a in assignments:
            if a.activity["name"] == name:
                return a
        return None

    # Rule 6 — SLA101A/B
    a101a = find("SLA101A")
    a101b = find("SLA101B")
    if a101a and a101b:
        diff = abs(time_index[a101a.time] - time_index[a101b.time])
        if diff == 0:
            total -= 0.5
        elif diff >= 5:
            total += 0.5

    # Rule 7 — SLA191A/B
    a191a = find("SLA191A")
    a191b = find("SLA191B")
    if a191a and a191b:
        diff = abs(time_index[a191a.time] - time_index[a191b.time])
        if diff == 0:
            total -= 0.5
        elif diff >= 5:
            total += 0.5

    # Rule 8 — Cross-section rules

    pairs = [
        (a101a, a191a),
        (a101a, a191b),
        (a101b, a191a),
        (a101b, a191b),
    ]

    for p1, p2 in pairs:
        if p1 and p2:
            diff = abs(time_index[p1.time] - time_index[p2.time])

            if diff == 0:
                total -= 0.25
            elif diff == 1:
                total += 0.5
                if is_rb(p1.room) != is_rb(p2.room):
                    total -= 0.4
            elif diff == 2:
                total += 0.25

    return total


if __name__ == "__main__":
    s = initialize_population(1)[0]
    print(f"Single schedule score: {score_schedule(s)}")

    population = initialize_population(250)
    scores = [score_schedule(s) for s in population]

    print(f"Min: {min(scores)}")
    print(f"Max: {max(scores)}")
    print(f"Avg: {sum(scores)/len(scores)}")