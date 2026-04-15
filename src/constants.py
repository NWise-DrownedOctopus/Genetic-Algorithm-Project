TIMES = ["10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM"]

ROOMS = {
    "Beach 201": 18,
    "Beach 301": 25,
    "Frank 119": 95,
    "Loft 206": 55,
    "Loft 310": 48,
    "James 325": 110,
    "Roman 201": 40,
    "Roman 216": 80,
    "Slater 003": 32,
}

FACILITATORS = [
    "Lock", "Glen", "Banks", "Richards", "Shaw",
    "Singer", "Uther", "Tyler", "Numen", "Zeldin"
]

ACTIVITIES = [
    {
        "name": "SLA101A",
        "enrollment": 40,
        "preferred": ["Glen", "Lock", "Banks"],
        "other": ["Numen", "Richards", "Shaw", "Singer"],
    },
    {
        "name": "SLA101B",
        "enrollment": 35,
        "preferred": ["Glen", "Lock", "Banks"],
        "other": ["Numen", "Richards", "Shaw", "Singer"],
    },
    {
        "name": "SLA191A",
        "enrollment": 45,
        "preferred": ["Glen", "Lock", "Banks"],
        "other": ["Numen", "Richards", "Shaw", "Singer"],
    },
    {
        "name": "SLA191B",
        "enrollment": 40,
        "preferred": ["Glen", "Lock", "Banks"],
        "other": ["Numen", "Richards", "Shaw", "Singer"],
    },
    {
        "name": "SLA201",
        "enrollment": 60,
        "preferred": ["Glen", "Banks", "Zeldin", "Lock", "Singer"],
        "other": ["Richards", "Uther", "Shaw"],
    },
    {
        "name": "SLA291",
        "enrollment": 50,
        "preferred": ["Glen", "Banks", "Zeldin", "Lock", "Singer"],
        "other": ["Richards", "Uther", "Shaw"],
    },
    {
        "name": "SLA303",
        "enrollment": 25,
        "preferred": ["Glen", "Zeldin"],
        "other": ["Banks"],
    },
    {
        "name": "SLA304",
        "enrollment": 20,
        "preferred": ["Singer", "Uther"],
        "other": ["Richards"],
    },
    {
        "name": "SLA394",
        "enrollment": 15,
        "preferred": ["Tyler", "Singer"],
        "other": ["Richards", "Zeldin"],
    },
    {
        "name": "SLA449",
        "enrollment": 30,
        "preferred": ["Tyler", "Zeldin", "Uther"],
        "other": ["Zeldin", "Shaw"],
    },
    {
        "name": "SLA451",
        "enrollment": 90,
        "preferred": ["Lock", "Banks", "Zeldin"],
        "other": ["Tyler", "Singer", "Shaw", "Glen"],
    },
]

ROOM_NAMES = list(ROOMS.keys())