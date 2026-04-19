from schedule import Schedule, Assignment, initialize_population
from constants import ROOMS, TIMES

def score_schedule(schedule: Schedule) -> float:
    """Compute total fitness score for a schedule.

    Applies rules for room conflicts, room size, facilitator type,
    facilitator load, consecutive assignments, and SLA constraints.

    Args:
        schedule (Schedule): Schedule to evaluate.

    Returns:
        float: Total fitness score.
    """
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
        used_space_rate = enrollment / capacity

        if used_space_rate > 1.0:
            total -= 1.0
        elif 0.83 <= used_space_rate <= 1.0:
            total += 0.8
        elif 0.75 <= used_space_rate < 0.83:
            total += 0.5
        elif 0.67 <= used_space_rate < 0.75:
            total += 0.2
        elif 0.50 <= used_space_rate < 0.67:
            total -= 0.3
        else:
            total -= 0.6

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
        """Check if a room is in Roman or Beach buildings."""
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
        """Find assignment by activity name."""
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

def count_violations(schedule):
    room_conflicts = 0
    facilitator_counts = {}
    fac_time_counts = {}  #Added
    size_violations = 0

    assignments = schedule.assignments

    # Room conflicts
    for i in range(len(assignments)):
        for j in range(i + 1, len(assignments)):
            a1 = assignments[i]
            a2 = assignments[j]
            if a1.room == a2.room and a1.time == a2.time:
                room_conflicts += 1

    # Facilitator counts
    for a in assignments:
        facilitator_counts[a.facilitator] = facilitator_counts.get(a.facilitator, 0) + 1
        fac_time_counts[(a.facilitator, a.time)] = fac_time_counts.get((a.facilitator, a.time), 0) + 1

    overload_double = sum(1 for count in fac_time_counts.values() if count > 1)  # NEW
    facilitator_overload = sum(1 for count in facilitator_counts.values() if count > 4) + overload_double
    # Size violations
    for a in assignments:
        if ROOMS[a.room] < a.activity["enrollment"]:
            size_violations += 1

    return {
        "room_conflicts": room_conflicts,
        "facilitator_overload": facilitator_overload,
        "size_violations": size_violations
    }


if __name__ == "__main__":
    def check(name, result, expected):
        """Compare result to expected and print PASS/FAIL."""
        print(f"{name}: Result: {result}  Expected: {expected}  {'PASS' if abs(result - expected) < 1e-6 else 'FAIL'}")

    def act(name, enrollment=40, preferred=None, other=None):
        """Create activity dictionary."""
        return {"name": name, "enrollment": enrollment,
                "preferred": preferred or [], "other": other or []}

    # Rule 1 (room conflict)
    # Rule1: -0.5 per assignment pair = -1.0
    # Rule2: A +0.8, B +0.8 = +1.6
    # Rule3: A -0.1, B -0.1 = -0.2
    # Rule4: ft=1 each +0.2+0.2=+0.4, total<3 -0.4-0.4=-0.8
    # Total: 0.0
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Roman 201", "10 AM", "F2")
    s = Schedule([a1, a2])
    check("Rule 1", score_schedule(s), 0.0)

    # Rule 2a (room too small)
    # Rule2: 50/40=1.25 => -1.0
    # Rule3: -0.1
    # Rule4: +0.2 -0.4 = -0.2
    # Total: -1.3
    a1 = Assignment(act("A", enrollment=50), "Roman 201", "10 AM", "F1")
    s = Schedule([a1])
    check("Rule 2a", score_schedule(s), -1.3)

    # Rule 2b (>3x)
    # Rule2: 10/95<0.5 => -0.6
    # Rule3: -0.1
    # Rule4: +0.2 -0.4
    # Total: -0.9
    a1 = Assignment(act("A", enrollment=10), "Frank 119", "10 AM", "F1")
    s = Schedule([a1])
    check("Rule 2b", score_schedule(s), -0.9)

    # Rule 2c
    # Rule2: 40/95<0.5 => -0.6
    # Rule3: -0.1
    # Rule4: +0.2 -0.4
    # Total: -0.9
    a1 = Assignment(act("A"), "Frank 119", "10 AM", "F1")
    s = Schedule([a1])
    check("Rule 2c", score_schedule(s), -0.9)

    # Rule 2d
    # Rule2: 40/40=1.0 => +0.8
    # Rule3: -0.1
    # Rule4: +0.2 -0.4
    # Total: 0.5
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    s = Schedule([a1])
    check("Rule 2d", score_schedule(s), 0.5)

    # Rule 3a
    # Rule2 +0.8, Rule3 +0.5, Rule4 +0.2 -0.4
    # Total: 1.1
    a1 = Assignment(act("A", preferred=["F1"]), "Roman 201", "10 AM", "F1")
    s = Schedule([a1])
    check("Rule 3a", score_schedule(s), 1.1)

    # Rule 3b
    # Total: 0.8
    a1 = Assignment(act("A", other=["F1"]), "Roman 201", "10 AM", "F1")
    s = Schedule([a1])
    check("Rule 3b", score_schedule(s), 0.8)

    # Rule 3c
    # Total: 0.5
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    s = Schedule([a1])
    check("Rule 3c", score_schedule(s), 0.5)

    # Rule 4a
    # A: 0.1, B: 0.1 => 0.2
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Loft 310", "10 AM", "F1")
    s = Schedule([a1, a2])
    check("Rule 4a", score_schedule(s), 0.2)

    # Rule 4b
    # Total: 0.9
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "Tyler")
    s = Schedule([a1])
    check("Rule 4b", score_schedule(s), 0.9)

    # Rule 4c
    # Total: 4.0
    times = ["10 AM","11 AM","12 PM","1 PM","2 PM"]
    assigns = [Assignment(act(f"A{i}"), "Roman 201", times[i], "F1") for i in range(5)]
    s = Schedule(assigns)
    check("Rule 4c", score_schedule(s), 4.0)

    # Rule 4d
    # Total: 1.0
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Loft 310", "12 PM", "F1")
    s = Schedule([a1, a2])
    check("Rule 4d", score_schedule(s), 1.0)

    # Rule 5a
    # Total: 1.5
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Roman 201", "11 AM", "F1")
    s = Schedule([a1, a2])
    check("Rule 5a", score_schedule(s), 1.5)

    # Rule 5b
    # Total: 1.1
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Loft 310", "11 AM", "F1")
    s = Schedule([a1, a2])
    check("Rule 5b", score_schedule(s), 1.1)

    # Rule 6a
    # Total: 0.5
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA101B"), "Loft 310", "10 AM", "F2")
    s = Schedule([a1, a2])
    check("Rule 6a", score_schedule(s), 0.5)

    # Rule 6b
    # Total: 1.5
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA101B"), "Loft 310", "3 PM", "F2")
    s = Schedule([a1, a2])
    check("Rule 6b", score_schedule(s), 1.5)

    # Rule 7a
    # Total: 0.5
    a1 = Assignment(act("SLA191A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191B"), "Loft 310", "10 AM", "F2")
    s = Schedule([a1, a2])
    check("Rule 7a", score_schedule(s), 0.5)

    # Rule 7b
    # Total: 1.5
    a1 = Assignment(act("SLA191A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191B"), "Loft 310", "3 PM", "F2")
    s = Schedule([a1, a2])
    check("Rule 7b", score_schedule(s), 1.5)

    # Rule 8a
    # Total: 1.5
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191A"), "Roman 201", "11 AM", "F2")
    s = Schedule([a1, a2])
    check("Rule 8a", score_schedule(s), 1.5)

    # Rule 8b
    # Total: 1.1
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191A"), "Loft 310", "11 AM", "F2")
    s = Schedule([a1, a2])
    check("Rule 8b", score_schedule(s), 1.1)

    # Rule 8c
    # Total: 1.25
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191A"), "Loft 310", "12 PM", "F2")
    s = Schedule([a1, a2])
    check("Rule 8c", score_schedule(s), 1.25)

    # Rule 8d
    # Total: 0.75
    a1 = Assignment(act("SLA101A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("SLA191A"), "Loft 310", "10 AM", "F2")
    s = Schedule([a1, a2])
    check("Rule 8d", score_schedule(s), 0.75)

    pop = initialize_population(250)
    scores = [score_schedule(s) for s in pop]
    print(f"Min: {min(scores)}  Max: {max(scores)}  Avg: {sum(scores)/len(scores)}")

    # Test 1 — Empty schedule
    # Rule2 = 0
    # Rule3 = 0
    # Rule4 = 0
    # Total = 0.0
    s = Schedule([])
    check("Edge 1", score_schedule(s), 0.0)

    # Test 2 — Ratio 0.50
    # Rule2 = -0.3
    # Rule3 = -0.1
    # Rule4 = +0.2 - 0.4 = -0.2
    # Total = -0.6
    a1 = Assignment(act("A", enrollment=9), "Beach 201", "10 AM", "F1")
    s = Schedule([a1])
    check("Edge 2", score_schedule(s), -0.6)

    # Test 3 — Ratio 0.67-0.75
    # Rule2 = +0.2
    # Rule3 = -0.1
    # Rule4 = +0.2 - 0.4 = -0.2
    # Total = -0.1
    a1 = Assignment(act("A", enrollment=64), "Frank 119", "10 AM", "F1")
    s = Schedule([a1])
    check("Edge 3", score_schedule(s), -0.1)

    # Test 4 — Ratio 0.75
    # Rule2 = +0.5
    # Rule3 = -0.1
    # Rule4 = +0.2 - 0.4 = -0.2
    # Total = 0.2
    a1 = Assignment(act("A", enrollment=30), "Roman 201", "10 AM", "F1")
    s = Schedule([a1])
    check("Edge 4", score_schedule(s), 0.2)

    # Test 5 — Ratio 0.83-1.0
    # Rule2 = +0.8
    # Rule3 = -0.1
    # Rule4 = +0.2 - 0.4 = -0.2
    # Total = 0.5
    a1 = Assignment(act("A", enrollment=73), "Roman 216", "10 AM", "F1")
    s = Schedule([a1])
    check("Edge 5", score_schedule(s), 0.5)

    # Test 6 — Ratio 1.0
    # Rule2 = +0.8
    # Rule3 = -0.1
    # Rule4 = +0.2 - 0.4 = -0.2
    # Total = 0.5
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    s = Schedule([a1])
    check("Edge 6", score_schedule(s), 0.5)

    # Test 7 — Tyler 1 activity
    # Rule2 = +0.8
    # Rule3 = -0.1
    # Rule4 = +0.2 (no <3 penalty)
    # Total = 0.9
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "Tyler")
    s = Schedule([a1])
    check("Edge 7", score_schedule(s), 0.9)

    # Test 8 — Tyler 2 non-consecutive
    # Rule2 = +1.6
    # Rule3 = -0.2
    # Rule4 = +0.4
    # Rule5 = 0
    # Total = 1.8
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "Tyler")
    a2 = Assignment(act("B"), "Roman 201", "12 PM", "Tyler")
    s = Schedule([a1, a2])
    check("Edge 8", score_schedule(s), 1.0)

    # Test 9 — F1 3 activities
    # Rule2 = +2.4
    # Rule3 = -0.3
    # Rule4 = +0.6
    # Rule5 = 0
    # Total = 2.7
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Roman 201", "12 PM", "F1")
    a3 = Assignment(act("C"), "Roman 201", "2 PM", "F1")
    s = Schedule([a1, a2, a3])
    check("Edge 9", score_schedule(s), 2.7)

    # Test 10 — F1 4 activities
    # Rule2 = +3.2
    # Rule3 = -0.4
    # Rule4 = +0.8
    # Rule5 = +0.5
    # Total = 4.1
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Roman 201", "12 PM", "F1")
    a3 = Assignment(act("C"), "Roman 201", "2 PM", "F1")
    a4 = Assignment(act("D"), "Roman 201", "3 PM", "F1")
    s = Schedule([a1, a2, a3, a4])
    check("Edge 10", score_schedule(s), 4.1)

    # Test 11 — F1 5 activities
    # Rule2 = +4.0
    # Rule3 = -0.5
    # Rule4 = +1.0 - 2.5
    # Rule5 = +1.5
    # Total = 3.5
    a1 = Assignment(act("A"), "Roman 201", "10 AM", "F1")
    a2 = Assignment(act("B"), "Roman 201", "11 AM", "F1")
    a3 = Assignment(act("C"), "Roman 201", "12 PM", "F1")
    a4 = Assignment(act("D"), "Roman 201", "1 PM", "F1")
    a5 = Assignment(act("E"), "Roman 201", "3 PM", "F1")
    s = Schedule([a1, a2, a3, a4, a5])
    check("Edge 11", score_schedule(s), 3.5)

    # count_violations test
    a1 = Assignment({"name": "A", "enrollment": 50}, "Roman 201", "10 AM", "F1")
    a2 = Assignment({"name": "B", "enrollment": 10}, "Roman 201", "10 AM", "F2")
    a3 = Assignment({"name": "C", "enrollment": 10}, "Frank 119", "11 AM", "F1")
    s = Schedule([a1, a2, a3])
    v = count_violations(s)
    print(f"room_conflicts: {v['room_conflicts']}  expected: 1")
    print(f"facilitator_overload: {v['facilitator_overload']}  expected: 0")
    print(f"size_violations: {v['size_violations']}  expected: 1")

    a1 = Assignment({"name": "A", "enrollment": 10}, "Roman 201", "10 AM", "Glen")
    a2 = Assignment({"name": "B", "enrollment": 10}, "Loft 310", "10 AM", "Glen")
    s = Schedule([a1, a2])
    v = count_violations(s)
    print(f"facilitator_overload (double-booked): {v['facilitator_overload']}  expected: 1")