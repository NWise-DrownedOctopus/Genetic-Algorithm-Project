"""
main.py — CS 461 Program 2: Genetic Algorithm Scheduler
Member C ownership.

Entry point. Wires together the GUI (gui.py), the GA engine (ga.py),
and output (output.py).

Final architecture:
    main.py owns the game loop and application state.
    gui.py owns all rendering (receives state, draws it).
    ga.py owns the algorithm (called by main, returns updated state).
    output.py owns file export (called by main on user request).
"""

import pygame
from gui import (
    WIN_W, WIN_H, FPS, TITLE,
    render, BUTTONS, INPUTS,
)
from schedule import initialize_population
from fitness import score_schedule
from ga import run_generation, halve_mutation_rate


# ── Application State ──────────────────────────────────────────────────────────
def make_initial_state(seed=42):
    """
    Returns the default application state dict.
    This is the single source of truth passed to gui.render() each frame.
    """
    return {
        # UI phase flags
        "populated":           False,   # has initial population been generated?
        "running":             False,   # is the GA currently running?
        "converged":           False,   # has stopping condition been met?
        "paused":              False,   # is the GA paused mid-run?

        # Input field state
        "input_focus":         None,    # "seed" | "gens" | None
        "seed_draft":          str(seed),    # string currently displayed in seed field
        "gens_draft":          "100",   # string currently displayed in gens field

        # Config
        "seed":                seed,      # committed RNG seed value
        "run_gens":            100,     # committed generations value
        "show_all_activities": False,   # T toggles 6 vs all 11 in schedule panel

        # GA state
        "population":          [],      # list of Schedule objects
        "scores":              [],      # fitness scores, parallel to population
        "generation":          0,       # current generation count
        "lam":                 0.01,    # mutation rate — single source of truth

        # Display data (updated each generation)
        "schedule":            [],      # best schedule — list of activity dicts
        "metrics":             {},      # GA metrics for metrics panel
        "history":             [],      # list of (best, avg, worst) per generation
    }


# ── Input commit ───────────────────────────────────────────────────────────────
def _commit_input(state):
    """
    Parse whichever draft field is currently focused and write its value
    back to the real state entry. Reverts the draft to the last valid value
    if the input is empty or non-numeric. Clears focus after committing.
    """
    focus = state["input_focus"]

    if focus == "seed":
        val = state["seed_draft"].strip()
        if val.isdigit():
            state["seed"] = int(val)
        else:
            state["seed_draft"] = str(state["seed"])   # revert to last valid

    elif focus == "gens":
        val = state["gens_draft"].strip()
        if val.isdigit() and int(val) >= 1:
            state["run_gens"] = int(val)
        else:
            state["gens_draft"] = str(state["run_gens"])  # revert to last valid

    state["input_focus"] = None   # release focus


# ── Generate initial population ────────────────────────────────────────────────
def generate_population(state):
    """Generate 250 random schedules and score them. Populates state."""
    population    = initialize_population()
    scores        = [score_schedule(s) for s in population]
    best_idx      = scores.index(max(scores))
    best_schedule = population[best_idx]
    average_score = sum(scores) / len(scores)

    schedule_display = [
        {
            "activity":    a.activity["name"],
            "room":        a.room,
            "time":        a.time,
            "facilitator": a.facilitator,
            "score":       0.0,
        }
        for a in best_schedule.assignments
    ]

    metrics = {
        "generation":           0,
        "population":           len(population),
        "lam":                  state["lam"],
        "best":                 max(scores),
        "avg":                  average_score,
        "worst":                min(scores),
        "improvement":          0.0,
        "room_conflicts":       0,
        "facilitator_overload": 0,
        "size_violations":      0,
    }

    state["population"]  = population
    state["scores"]      = scores
    state["populated"]   = True
    state["converged"]   = False
    state["generation"]  = 0
    state["history"]     = [(max(scores), average_score, min(scores))]
    state["schedule"]    = schedule_display
    state["metrics"]     = metrics

    return state


# ── Advance one generation ─────────────────────────────────────────────────────
def advance_generation(state):
    """
    Calls Member B's run_generation() with the correct signature and
    unpacks its return value back into the shared state dict.

    Member B's signature:
        run_generation(
            population : list[Schedule],
            scores     : list[float],
            lam        : float = 0.01,
            generation : int   = 0,
            prev_avg   : float = None,
        ) -> tuple[list[Schedule], dict]

    The returned metrics dict contains: best, avg, worst, improvement, lam, generation
    """
    prev_avg = state["metrics"].get("avg") if state["metrics"] else None

    next_gen, metrics = run_generation(
        population=state["population"],
        scores=state["scores"],
        lam=state["lam"],
        generation=state["generation"] + 1,
        prev_avg=prev_avg,
    )

    new_scores    = [score_schedule(s) for s in next_gen]
    best_idx      = new_scores.index(max(new_scores))
    best_schedule = next_gen[best_idx]

    schedule_display = [
        {
            "activity":    a.activity["name"],
            "room":        a.room,
            "time":        a.time,
            "facilitator": a.facilitator,
            "score":       0.0,
        }
        for a in best_schedule.assignments
    ]

    # Check stopping condition: >= 100 gens AND improvement < 1%
    gen         = state["generation"] + 1
    improvement = metrics.get("improvement", 0.0)
    converged   = gen >= 100 and abs(improvement) < 1.0

    # Halve mutation rate exactly once on the generation convergence is reached
    if converged and not state["converged"]:
        state["lam"] = halve_mutation_rate(state["lam"])

    # Merge in fields that run_generation doesn't track
    prev_metrics = state.get("metrics", {})
    metrics.update({
        "population":           len(next_gen),
        "lam":                  state["lam"],
        "room_conflicts":       prev_metrics.get("room_conflicts", 0),
        "facilitator_overload": prev_metrics.get("facilitator_overload", 0),
        "size_violations":      prev_metrics.get("size_violations", 0),
    })

    state["population"]  = next_gen
    state["scores"]      = new_scores
    state["generation"]  = gen
    state["converged"]   = converged
    state["schedule"]    = schedule_display
    state["metrics"]     = metrics
    state["history"].append((metrics["best"], metrics["avg"], metrics["worst"]))

    return state


# ── Export stubs (replace when Member B ships output.py) ──────────────────────
def stub_export_schedule(state):
    """Placeholder — final version calls output.save_schedule(state['schedule'])."""
    print("[STUB] Would export schedule to output/best_schedule.txt")


def stub_export_csv(state):
    """Placeholder — final version calls output.export_csv(state['history'])."""
    print("[STUB] Would export fitness history to output/fitness_history.csv")


# ── Event handling ─────────────────────────────────────────────────────────────
def handle_events(events, state):
    """
    Process all keyboard and mouse events each frame.

    Input field focus model:
      - Clicking an input field gives it focus and loads its current value
        into the corresponding draft string for editing.
      - Digits are appended to the draft; Backspace trims it.
      - Enter commits the draft to real state and releases focus.
      - Escape cancels the edit (reverts draft) and releases focus.
        If no field is focused, Escape quits the app.
      - Clicking anywhere outside the input fields releases focus and commits.
      - Hotkeys (G, T, SPACE, R, +/-) are suppressed while a field is focused
        so typed digits don't accidentally trigger other actions.

    Mouse click regions are defined by BUTTONS and INPUTS from gui.py.
    Returns (updated_state, keep_running).
    """
    for event in events:
        if event.type == pygame.QUIT:
            return state, False

        # ── Mouse ──────────────────────────────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Input field focus — check inputs before buttons so clicking
            # an input doesn't also fire a button behind it.
            clicked_input = False

            if INPUTS["seed"].collidepoint(pos):
                state["input_focus"] = "seed"
                state["seed_draft"]  = str(state["seed"])
                clicked_input = True

            if INPUTS["gens"].collidepoint(pos):
                if state.get("converged"):
                    state["input_focus"] = "gens"
                    state["gens_draft"]  = str(state["run_gens"])
                clicked_input = True   # still consumed even if locked

            # Clicking anywhere outside an input commits and releases focus
            if not clicked_input and state["input_focus"]:
                _commit_input(state)

            # Buttons — only process if no input was just focused
            if not clicked_input:
                if BUTTONS["generate"].collidepoint(pos):
                    if not state["populated"]:
                        state = generate_population(state)
                    elif not state["running"] and not state["converged"]:
                        state["running"] = True

                if BUTTONS["randomize"].collidepoint(pos):
                    if not state["running"]:
                        state = make_initial_state(seed=state["seed"])

                if BUTTONS["run"].collidepoint(pos):
                    if (state["populated"] and not state["running"]
                            and not state["converged"]):
                        state["running"] = True

                if BUTTONS["export_sched"].collidepoint(pos):
                    if state["converged"]:
                        stub_export_schedule(state)

                if BUTTONS["export_csv"].collidepoint(pos):
                    if state["converged"]:
                        stub_export_csv(state)

        # ── Keyboard ──────────────────────────────────────────────────────────
        if event.type == pygame.KEYDOWN:

            # ── Input field is focused: route all keys to it ──────────────────
            if state["input_focus"]:
                if event.key == pygame.K_RETURN:
                    _commit_input(state)

                elif event.key == pygame.K_ESCAPE:
                    # Cancel edit — revert draft to last committed value
                    if state["input_focus"] == "seed":
                        state["seed_draft"] = str(state["seed"])
                    elif state["input_focus"] == "gens":
                        state["gens_draft"] = str(state["run_gens"])
                    state["input_focus"] = None

                elif event.key == pygame.K_BACKSPACE:
                    draft_key = state["input_focus"] + "_draft"
                    state[draft_key] = state[draft_key][:-1]

                elif event.unicode.isdigit():
                    draft_key = state["input_focus"] + "_draft"
                    state[draft_key] += event.unicode

                # All other keys are consumed — hotkeys suppressed while editing

            # ── No input focused: normal hotkeys ──────────────────────────────
            else:
                if event.key == pygame.K_ESCAPE:
                    return state, False

                if event.key == pygame.K_SPACE:
                    if state["populated"]:
                        state["paused"] = not state["paused"]

                if event.key == pygame.K_r:
                    state = make_initial_state(seed=state["seed"])

                if event.key == pygame.K_g:
                    if not state["populated"]:
                        state = generate_population(state)
                    elif not state["running"] and not state["converged"]:
                        state["running"] = True

                if event.key == pygame.K_t:
                    if state["populated"]:
                        state["show_all_activities"] = not state["show_all_activities"]

                if event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    state["lam"] = min(0.5, state["lam"] * 2)

                if event.key == pygame.K_MINUS:
                    state["lam"] = max(0.0001, state["lam"] / 2)

    return state, True


# ── Main loop ──────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    state = make_initial_state()

    print(f"Launching {TITLE}")
    print("  [G]       Generate initial population  (or click Generate Population)")
    print("  [SPACE]   Pause / resume")
    print("  [T]       Toggle 6 / all activities in schedule panel")
    print("  [R]       Reset to idle state  (or click Randomize)")
    print("  [+/-]     Adjust mutation rate λ")
    print("  [ESC]     Quit  (or cancel active input field)")

    running = True
    while running:
        events = pygame.event.get()
        state, running = handle_events(events, state)

        if (state["running"] and not state["paused"]
                and not state["converged"] and state["populated"]):
            state = advance_generation(state)

        render(screen, state, pygame.mouse.get_pos())
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()