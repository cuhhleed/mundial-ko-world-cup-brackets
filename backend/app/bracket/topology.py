R32_SLOTS = [f"R32-{i}" for i in range(1, 17)]
R16_SLOTS = [f"R16-{i}" for i in range(1, 9)]
QF_SLOTS = [f"QF-{i}" for i in range(1, 5)]
SF_SLOTS = ["SF-1", "SF-2"]
LATE_SLOTS = ["FINAL", "TP"]

# Topological order: leaves first, root last
ALL_SLOTS: list[str] = R32_SLOTS + R16_SLOTS + QF_SLOTS + SF_SLOTS + LATE_SLOTS

# Each entry: downstream_slot → ((feeder1, outcome1), (feeder2, outcome2))
# outcome ∈ {"winner", "loser"}
FEEDERS: dict[str, tuple[tuple[str, str], tuple[str, str]]] = {
    "R16-1": (("R32-1", "winner"), ("R32-4", "winner")),
    "R16-2": (("R32-3", "winner"), ("R32-6", "winner")),
    "R16-3": (("R32-2", "winner"), ("R32-5", "winner")),
    "R16-4": (("R32-7", "winner"), ("R32-8", "winner")),
    "R16-5": (("R32-12", "winner"), ("R32-11", "winner")),
    "R16-6": (("R32-10", "winner"), ("R32-9", "winner")),
    "R16-7": (("R32-15", "winner"), ("R32-14", "winner")),
    "R16-8": (("R32-13", "winner"), ("R32-16", "winner")),
    "QF-1": (("R16-1", "winner"), ("R16-2", "winner")),
    "QF-2": (("R16-5", "winner"), ("R16-6", "winner")),
    "QF-3": (("R16-3", "winner"), ("R16-4", "winner")),
    "QF-4": (("R16-7", "winner"), ("R16-8", "winner")),
    "SF-1": (("QF-1", "winner"), ("QF-2", "winner")),
    "SF-2": (("QF-3", "winner"), ("QF-4", "winner")),
    "FINAL": (("SF-1", "winner"), ("SF-2", "winner")),
    "TP": (("SF-1", "loser"), ("SF-2", "loser")),
}

SCORE_BEARING_SLOTS: frozenset[str] = frozenset({"SF-1", "SF-2", "FINAL"})
