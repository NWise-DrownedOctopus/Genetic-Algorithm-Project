from constants import ACTIVITIES, ROOMS

for activity in ACTIVITIES:
    print(f"{activity['name']}:")
    print(f"  Enrollment: {activity['enrollment']}")
    print(f"  Preferred: {', '.join(activity['preferred'])}")
    print(f"  Other: {', '.join(activity['other'])}")
    print()

for room, capacity in ROOMS.items():
    print(f"{room}: {capacity}")