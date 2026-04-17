"""
main.py — CS 461 Program 2: Genetic Algorithm Scheduler
Member C ownership.

Entry point. Wires together the GUI (gui.py), the GA engine (ga.py),
and output (output.py). In the wireframe version, GA and output are
stubbed out — only the GUI runs.

Final architecture:
    main.py owns the game loop and application state.
    gui.py owns all rendering (receives state, draws it).
    ga.py owns the algorithm (called by main, returns updated state).
    output.py owns file export (called by main on user request).
"""

import pygame
from gui import (
    WIN_W, WIN_H, FPS, TITLE,
    render,
    # Wireframe fake data — remove when ga.py is ready
    FAKE_SCHEDULE, FAKE_METRICS, FAKE_HISTORY, _fake_history,
)

# ── Stub imports (replace with real imports when modules are ready) ────────────
# from constants import ROOMS, TIMES, FACILITATORS, ACTIVITIES
# from schedule import initialize_population
# from fitness import compute_fitness
# from ga import run_generation
# from output import save_schedule, export_csv, write_log


# ── Application State ─────────────────────────────────────────────────────────
def make_initial_state():
    """
    Returns the default application state dict.
    This is the single source of truth passed to gui.render() each frame.
    """
    return {
        # UI phase flags
        "populated":    False,   # has initial population been generated?
        "running":      False,   # is the GA currently running generations?
        "converged":    False,   # has stopping condition been met?
        "paused":       False,   # is the GA paused mid-run?

        # Config
        "seed":         42,      # RNG seed
        "run_gens":     100,     # how many generations to run per [Run] press

        # GA state (populated by ga.py in final version)
        "population":   [],      # list of Schedule objects
        "generation":   0,       # current generation count

        # Display data (updated each generation)
        "schedule":     [],      # best schedule — list of activity dicts
        "metrics":      {},      # dict of GA metrics for metrics panel
        "history":      [],      # list of (best, avg, worst) per generation
    }


# ── Stub: Generate initial population ────────────────────────────────────────
def stub_generate_population(state):
    """
    Wireframe stub. In final version, calls:
        pop = initialize_population(N=250, seed=state["seed"])
        scored = [(s, compute_fitness(s)) for s in pop]
        best = max(scored, key=lambda x: x[1])[0]
        ... populate state from best schedule and scored population
    """
    state["populated"] = True
    state["converged"] = False
    state["generation"] = 0
    state["history"] = []
    state["schedule"] = FAKE_SCHEDULE
    state["metrics"] = FAKE_METRICS
    return state


# ── Stub: Run N generations ───────────────────────────────────────────────────
def stub_run_generations(state, n):
    """
    Wireframe stub. In final version, loops n times calling:
        population, metrics = run_generation(population, generation, lam)
        state["history"].append((metrics["best"], metrics["avg"], metrics["worst"]))
        if check_stopping_condition(state): break
    """
    current_len = len(state["history"])
    state["history"] = _fake_history(current_len + n)
    state["metrics"] = {
        **FAKE_METRICS,
        "generation": current_len + n,
        "improvement": max(0.0, 2.47 - (current_len + n) * 0.01),
    }
    # Check stub stopping condition
    if state["metrics"]["generation"] >= 100 and state["metrics"]["improvement"] < 1.0:
        state["converged"] = True
    return state


# ── Stub: Export ──────────────────────────────────────────────────────────────
def stub_export_schedule(state):
    """In final version, calls output.save_schedule(state['schedule'])"""
    print("[STUB] Would export schedule to output/best_schedule.txt")


def stub_export_csv(state):
    """In final version, calls output.export_csv(state['history'])"""
    print("[STUB] Would export fitness history to output/fitness_history.csv")


# ── Event handling ────────────────────────────────────────────────────────────
def handle_events(events, state):
    """
    Process keyboard and window events.
    Returns updated state and a running bool.
    """
    for event in events:
        if event.type == pygame.QUIT:
            return state, False

        if event.type == pygame.KEYDOWN:
            # ESC — quit
            if event.key == pygame.K_ESCAPE:
                return state, False

            # SPACE — pause / resume (only meaningful when GA is running)
            if event.key == pygame.K_SPACE:
                if state["populated"]:
                    state["paused"] = not state["paused"]

            # R — reset to initial state
            if event.key == pygame.K_r:
                state = make_initial_state()

            # T — toggle schedule rows (handled in gui.py in final version)
            # +/- — adjust mutation rate lambda
            if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                if "lam" in state["metrics"]:
                    state["metrics"]["lam"] = min(0.5, state["metrics"]["lam"] * 2)

            if event.key == pygame.K_MINUS:
                if "lam" in state["metrics"]:
                    state["metrics"]["lam"] = max(0.0001, state["metrics"]["lam"] / 2)

        # ── Mouse click handling (button regions) ────────────────────────────
        # TODO: replace with proper Button class hit detection in final version
        # For now, stub actions are triggered by keyboard shortcuts only.
        # In the final version, map each pygame.Rect button from gui.py to
        # its corresponding action here.

    return state, True


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    state = make_initial_state()

    # ── Wireframe demo: auto-populate with fake data so teammates can see
    # the full UI immediately. Remove this block in final version.
    WIREFRAME_DEMO = True
    if WIREFRAME_DEMO:
        state = stub_generate_population(state)
        state = stub_run_generations(state, 42)

    print(f"Launching {TITLE}")
    print("  [R]       Reset to idle state")
    print("  [SPACE]   Pause / resume")
    print("  [+/-]     Adjust mutation rate λ")
    print("  [ESC]     Quit")
    print()
    print("  (Wireframe mode: GA stubs active, no real algorithm running)")

    running = True
    while running:
        events = pygame.event.get()
        state, running = handle_events(events, state)

        render(screen, state)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()