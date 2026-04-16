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
            if 2 <= total_count < 3:
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
    def check(name, result, expected):
        print(f"{name}: Result: {result}  Expected: {expected}  {'PASS' if abs(result - expected) < 1e-6 else 'FAIL'}")

    def act(name, enrollment=40, preferred=None, other=None):
        return {"name": name, "enrollment": enrollment,
                "preferred": preferred or [], "other": other or []}

    # Rule 1 (room conflict)
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Roman 201", "10 AM", "F2")
    # Rule 1: -1.0 total, baselines 0.0 each
    s = Schedule([a1, a2])
    check("Rule 1", score_schedule(s), -1.0)

    # Rule 2a (room too small)
    a1 = Assignment(act("A", enrollment=50), "Roman 201", "10 AM", "F1")
    # -0.5 -0.1 +0.2 -0.4 = -0.8
    s = Schedule([a1])
    check("Rule 2a", score_schedule(s), -0.8)

    # Rule 2b (>3x)
    a1 = Assignment(act("A", enrollment=10), "Frank 119", "10 AM", "F1")
    # -0.4 -0.1 +0.2 -0.4 = -0.7
    s = Schedule([a1])
    check("Rule 2b", score_schedule(s), -0.7)

    # Rule 2c (>1.5x)
    a1 = Assignment(act("A"), "Frank 119", "10 AM", "F1")
    # -0.2 -0.1 +0.2 -0.4 = -0.5
    s = Schedule([a1])
    check("Rule 2c", score_schedule(s), -0.5)

    # Rule 2d (good fit)
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    # +0.3 -0.1 +0.2 -0.4 = 0.0
    s = Schedule([a1])
    check("Rule 2d", score_schedule(s), 0.0)

    # Rule 3a (preferred)
    a1 = Assignment(act("A", preferred=["F1"]), "Roman 201", "10 AM", "F1")
    # +0.3 +0.5 +0.2 -0.4 = +0.6
    s = Schedule([a1])
    check("Rule 3a", score_schedule(s), 0.6)

    # Rule 3b (other)
    a1 = Assignment(act("A", other=["F1"]), "Roman 201", "10 AM", "F1")
    # +0.3 +0.2 +0.2 -0.4 = +0.3
    s = Schedule([a1])
    check("Rule 3b", score_schedule(s), 0.3)

    # Rule 3c (unlisted)
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    # 0.0
    s = Schedule([a1])
    check("Rule 3c", score_schedule(s), 0.0)

    # Rule 4a (double-booked slot)
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Loft 310", "10 AM", "F1")
    # +0.6 -0.2 -0.4 -0.8 = -0.8
    s = Schedule([a1, a2])
    check("Rule 4a", score_schedule(s), -0.8)

    # Rule 4b (Tyler exception)
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "Tyler")
    # +0.4
    s = Schedule([a1])
    check("Rule 4b", score_schedule(s), 0.4)

    # Rule 4c (>4 total)
    times = ["10 AM","11 AM","12 PM","1 PM","2 PM"]
    assigns = [Assignment(act(f"A{i}"), "Roman 201", times[i], "F1") for i in range(5)]
    # +1.5 -0.5 +1.0 -2.5 +2.0 = +1.5
    s = Schedule(assigns)
    check("Rule 4c", score_schedule(s), 1.5)

    # Rule 4d (<3 total)
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Loft 310", "12 PM", "F1")
    # +0.6 -0.2 +0.4 -0.8 = 0.0
    s = Schedule([a1, a2])
    check("Rule 4d", score_schedule(s), 0.0)

    # Rule 5a (consecutive no mismatch)
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Roman 201", "11 AM", "F1")
    # +0.6 -0.2 +0.4 -0.8 +0.5 = +0.5
    s = Schedule([a1, a2])
    check("Rule 5a", score_schedule(s), 0.5)

    # Rule 5b (consecutive mismatch)
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Loft 310", "11 AM", "F1")
    # +0.6 -0.2 +0.4 -0.8 +0.5 -0.4 = +0.1
    s = Schedule([a1, a2])
    check("Rule 5b", score_schedule(s), 0.1)

    # Rule 6a (SLA101 same)
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA101B"), "Loft 310", "10 AM", "F2")
    # -0.5
    s = Schedule([a1, a2])
    check("Rule 6a", score_schedule(s), -0.5)

    # Rule 6b (SLA101 far)
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA101B"), "Loft 310", "3 PM", "F2")
    # +0.5
    s = Schedule([a1, a2])
    check("Rule 6b", score_schedule(s), 0.5)

    # Rule 7a (SLA191 same)
    a1 = Assignment(act("SLA191A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191B"), "Loft 310", "10 AM", "F2")
    # -0.5
    s = Schedule([a1, a2])
    check("Rule 7a", score_schedule(s), -0.5)

    # Rule 7b (SLA191 far)
    a1 = Assignment(act("SLA191A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191B"), "Loft 310", "3 PM", "F2")
    # +0.5
    s = Schedule([a1, a2])
    check("Rule 7b", score_schedule(s), 0.5)

    # Rule 8a (consecutive no mismatch)
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191A"), "Roman 201", "11 AM", "F2")
    # +0.6 -0.2 -0.4 +0.5 = +0.5
    s = Schedule([a1, a2])
    check("Rule 8a", score_schedule(s), 0.5)

    # Rule 8b (consecutive mismatch)
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191A"), "Loft 310", "11 AM", "F2")
    # +0.6 -0.2 -0.4 +0.5 -0.4 = +0.1
    s = Schedule([a1, a2])
    check("Rule 8b", score_schedule(s), 0.1)

    # Rule 8c (gap 2)
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191A"), "Loft 310", "12 PM", "F2")
    # +0.25
    s = Schedule([a1, a2])
    check("Rule 8c", score_schedule(s), 0.25)

    # Rule 8d (same slot)
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191A"), "Loft 310", "10 AM", "F2")
    # -0.25
    s = Schedule([a1, a2])
    check("Rule 8d", score_schedule(s), -0.25)

    pop = initialize_population(250)
    scores = [score_schedule(s) for s in pop]
    print(f"Min: {min(scores)}  Max: {max(scores)}  Avg: {sum(scores)/len(scores)}")