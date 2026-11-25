
import sys
from itertools import combinations

SAMPLE = """Aarav: Maths, Physics, Chemistry
Diya: Maths, Physics, CS
Kabir: Chemistry, Biology, English
Meera: Biology, English, Economics
Ishaan: CS, Economics, Maths
Sara: Physics, English, History
Rohan: History, Economics, Biology
Anya: CS, History, Chemistry"""

SESSIONS = ["morning", "afternoon", "evening"]



def read_students(text):
    students = {}
    for line in text.strip().splitlines():
        if ":" in line:
            name, subs = line.split(":", 1)
            students[name.strip()] = list(dict.fromkeys(s.strip() for s in subs.split(",") if s.strip()))
    return students



def build_graph(students):
    subjects = sorted({s for subs in students.values() for s in subs})
    adj = {s: set() for s in subjects}
    for subs in students.values():
        for a, b in combinations(subs, 2):
            adj[a].add(b)
            adj[b].add(a)
    return subjects, adj



def color_with_k(order, adj, k, stats, trace=False):
    color = {}

    def place(i, used):
        if i == len(order):
            return True
        v = order[i]
        stats["nodes"] += 1
        for c in range(min(k - 1, used + 1) + 1):          # never open a new slot early
            clash = next((u for u in adj[v] if color.get(u) == c), None)
            if clash is None:                               # safe: no neighbour has slot c
                color[v] = c
                if trace: print(f"    assign  {v} -> Slot {c + 1}")
                if place(i + 1, max(used, c)):
                    return True
                del color[v]                                # dead end: undo (backtrack)
                stats["backtracks"] += 1
                if trace: print(f"    undo    {v}")
            elif trace:
                print(f"    reject  {v} in Slot {c + 1} (clashes with {clash})")
        return False

    return color if place(0, -1) else None



def min_slots(adj, trace=False):
    order = sorted(adj, key=lambda v: -len(adj[v]))         # busiest subject first
    stats = {"nodes": 0, "backtracks": 0}
    for k in range(1, len(adj) + 1):
        if trace: print(f"Round k = {k}")
        result = color_with_k(order, adj, k, stats, trace)
        if result:
            return k, result, stats
        if trace: print(f"  {k} slot(s) not enough")



def greedy(adj):
    color = {}
    for v in adj:
        c = 0
        while any(color.get(u) == c for u in adj[v]):
            c += 1
        color[v] = c
    return max(color.values()) + 1


def verify(students, color):
    return all(len({color[s] for s in subs}) == len(subs) for subs in students.values())


def print_timetable(subjects, color, k, per_day):
    print(f"\nTimetable ({per_day} exams per day):")
    for slot in range(k):
        day, ses = divmod(slot, per_day)
        exams = ", ".join(s for s in subjects if color[s] == slot)
        print(f"  Day {day + 1} {SESSIONS[ses]:<9} Slot {slot + 1}: {exams}")


def draw_graph(adj, color, k):
    try:
        import networkx as nx, matplotlib.pyplot as plt
    except ImportError:
        print("Install first:  pip install networkx matplotlib"); return
    G = nx.Graph([(a, b) for a in adj for b in adj[a]])
    palette = plt.cm.Set3.colors
    nx.draw_circular(G, with_labels=True, node_size=1800, font_size=8,
                     node_color=[palette[color[v] % len(palette)] for v in G.nodes])
    plt.title(f"Conflict graph colored with {k} slots")
    plt.savefig("graph.png", dpi=150, bbox_inches="tight")
    print("Saved graph.png")



if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    text = open(args[0]).read() if args else SAMPLE
    students = read_students(text)
    subjects, adj = build_graph(students)
    edges = sum(len(n) for n in adj.values()) // 2
    print(f"{len(subjects)} subjects, {len(students)} students, {edges} conflicts\n")

    k, color, stats = min_slots(adj, trace="--trace" in sys.argv)
    print(f"Minimum exam slots: {k}")
    print(f"Placements tried: {stats['nodes']}, backtracks: {stats['backtracks']}")
    print(f"Greedy (no backtracking) would use: {greedy(adj)} slots")
    print_timetable(subjects, color, k, per_day=2)
    print("\nNo student has two exams at once:", verify(students, color))
    if "--draw" in sys.argv:
        draw_graph(adj, color, k)