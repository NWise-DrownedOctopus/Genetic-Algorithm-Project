"""
main.py — CS 461 Program 2: Genetic Algorithm Scheduler
Member C ownership.

Entry point.

Application architecture:
    main.py     — owns the game loop and application state dict.
    gui.py      — owns all rendering; receives state and mouse_pos, draws it.
    fitness.py  — owns all scoring calculation.
    schedule.py — owns creating of random schedules to initialise the project.
    ga.py       — owns the GA algorithm; called by advance_generation each frame.
    output.py   — owns file export; called on user request after convergence.

State flow:
    make_initial_state() → state dict
    generate_population(state) → state (populated=True)
    advance_generation(state)  → state (called every frame while running)
    render(screen, state, mouse_pos) → draws current state each frame

Keybindings:
    [G]      Generate initial population (or start running after population exists)
    [SPACE]  Pause / resume the GA loop
    [T]      Toggle schedule panel between 6 and all 11 activities
    [R]      Reset to idle state (preserves current seed)
    [+/-]    Double / halve the mutation rate λ
    [ESC]    Quit (or cancel an active input field edit)

Mouse:
    Click Seed field     — edit the RNG seed (takes effect on next Randomize/Generate)
    Click Gens field     — edit the generation count (unlocked after convergence only)
    Click any button     — same action as the corresponding keybind
    Click outside fields — commits the active draft and releases input focus
"""

import pygame
import output
from gui import (
    WIN_W, WIN_H, FPS, TITLE,
    render, BUTTONS, INPUTS,
)
from schedule import initialize_population
from fitness import score_schedule, count_violations, score_per_assignment
from ga import run_generation, halve_mutation_rate


# ── Application State ──────────────────────────────────────────────────────────

def make_initial_state(seed=42):
    """
    Build and return the default application state dict.

    This is the single source of truth for the entire application.
    Every subsystem (GUI, GA engine, event handler) reads from and writes
    to this dict. It is passed to gui.render() each frame unchanged except
    for whatever the current frame's event handling or GA step modified.

    Args:
        seed: integer RNG seed to initialise the state with. Defaults to 42.
              Pass state["seed"] when resetting so the user's chosen seed
              is preserved across Randomize / [R] resets.

    Returns:
        dict: fully initialised application state.
    """
    return {
        # UI phase flags
        "populated":           False,    # has initial population been generated?
        "running":             False,    # is the GA currently advancing generations?
        "converged":           False,    # has the stopping condition been met?
        "paused":              False,    # is the GA paused mid-run?

        # Input field state
        "input_focus":         None,     # "seed" | "gens" | None — active text field
        "seed_draft":          str(seed),# string currently displayed in the seed field
        "gens_draft":          "100",    # string currently displayed in the gens field

        # Config
        "seed":                seed,     # committed RNG seed (display only for now —
                                         # schedule.py must be updated to consume it)
        "run_gens":            100,      # committed number of generations per run batch
        "show_all_activities": False,    # [T] toggles between 6 and all 11 rows

        # GA state
        "population":          [],       # list[Schedule] — current generation
        "scores":              [],       # list[float]    — parallel fitness scores
        "generation":          0,        # how many generations have been evaluated
        "lam":                 0.01,     # mutation rate λ — single source of truth

        # Display data (updated each generation by advance_generation)
        "schedule":            [],       # best schedule as list of activity dicts
        "metrics":             {},       # GA metrics dict for the metrics panel
        "history":             [],       # list of (best, avg, worst) per generation
    }


# ── Input commit ───────────────────────────────────────────────────────────────

def _commit_input(state):
    """
    Parse the currently focused draft field and write its value back to state.

    Called when the user presses Enter, clicks outside the field, or the
    field loses focus for any other reason. If the draft is empty or
    non-numeric the field reverts to the last successfully committed value
    so state is never left with an invalid entry. Focus is always cleared
    after this call regardless of whether the value was valid.

    Validation rules:
        seed — any non-empty digit string is accepted (no upper bound).
        gens — must be a digit string representing an integer >= 1.

    Args:
        state: application state dict; modified in place.
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

    state["input_focus"] = None


# ── Generate initial population ────────────────────────────────────────────────

def generate_population(state):
    """
    Generate 250 random schedules, score each one, and populate state.

    Calls initialize_population() from schedule.py to create the initial
    generation, then scores every schedule using score_schedule() from
    fitness.py. Extracts the best schedule for display and computes summary
    metrics for the metrics panel.

    Note: initialize_population() currently uses its own internal PCG RNG
    and does not consume state["seed"]. For reproducible runs, schedule.py
    would need to accept a seed argument. This is flagged as a Member A task.

    Args:
        state: application state dict; modified in place and returned.

    Returns:
        dict: updated state with populated=True and all GA fields initialised.
    """
    population    = initialize_population()
    scores        = [score_schedule(s) for s in population]
    best_idx      = scores.index(max(scores))
    best_schedule = population[best_idx]
    average_score = sum(scores) / len(scores)

    violations = count_violations(best_schedule)

    per_scores = score_per_assignment(best_schedule)

    schedule_display = [
        {
            "activity":    a.activity["name"],
            "room":        a.room,
            "time":        a.time,
            "facilitator": a.facilitator,
            "score":       scores[i],
        }
        for i, a in enumerate(best_schedule.assignments)
    ]

    metrics = {
        "generation":           0,
        "population":           len(population),
        "lam":                  state["lam"],
        "best":                 max(scores),
        "avg":                  average_score,
        "worst":                min(scores),
        "improvement":          0.0,
        "room_conflicts":       violations["room_conflicts"],
        "facilitator_overload": violations["facilitator_overload"],
        "size_violations":      violations["size_violations"],
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
    Run one generation of the GA and update state with the results.

    Calls Member B's run_generation() with the correct positional signature,
    unpacks the returned (next_gen, metrics) tuple, re-scores the new
    population, checks the stopping condition, and writes everything back
    into the shared state dict.

    Member B's signature:
        run_generation(
            population : list[Schedule],
            scores     : list[float],
            lam        : float = 0.01,
            generation : int   = 0,
            prev_avg   : float = None,
        ) -> tuple[list[Schedule], dict]

    The returned metrics dict is expected to contain:
        best, avg, worst, improvement, lam, generation

    Stopping condition (spec requirement):
        generation >= 100 AND abs(improvement) < 1.0%

    Mutation rate:
        λ is halved exactly once via halve_mutation_rate() on the first frame
        the stopping condition is met, allowing fine-tuning after convergence.
        state["lam"] is the single source of truth; metrics["lam"] is synced
        from it rather than the other way around.

    Args:
        state: application state dict; modified in place and returned.

    Returns:
        dict: updated state with new population, scores, metrics, and history.
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

    violations = count_violations(best_schedule)

    per_scores = score_per_assignment(best_schedule)

    schedule_display = [
        {
            "activity":    a.activity["name"],
            "room":        a.room,
            "time":        a.time,
            "facilitator": a.facilitator,
            "score":       per_scores[i],
        }
        for i, a in enumerate(best_schedule.assignments)
    ]

    gen         = state["generation"] + 1
    improvement = metrics.get("improvement", 0.0)
    converged   = gen >= 100 and abs(improvement) < 1.0

    if converged and not state["converged"]:
        state["lam"] = halve_mutation_rate(state["lam"])

    metrics.update({
        "population":           len(next_gen),
        "lam":                  state["lam"],
        "room_conflicts":       violations["room_conflicts"],
        "facilitator_overload": violations["facilitator_overload"],
        "size_violations":      violations["size_violations"],
    })

    state["population"]  = next_gen
    state["scores"]      = new_scores
    state["generation"]  = gen
    state["converged"]   = converged
    state["schedule"]    = schedule_display
    state["metrics"]     = metrics
    state["history"].append((metrics["best"], metrics["avg"], metrics["worst"]))

    # Write a log entry every generation so the full run history is preserved.
    output.write_log(
        generation=gen,
        best_fitness=metrics["best"],
        schedule=schedule_display if converged else None,
    )

    return state


# ── Export functions ───────────────────────────────────────────────────────────

def export_schedule(state):
    """
    Write the best schedule from the current converged run to a text file.

    Delegates to output.save_schedule(), passing the schedule list, the
    current generation number, and the best fitness score from metrics.
    Also appends a final timestamped entry to the run log via write_log().

    Only callable after convergence (enforced by the button guard in
    handle_events). Prints the saved file path to the terminal for
    confirmation.

    Args:
        state: application state dict; read-only inside this function.
    """
    path = output.save_schedule(
        schedule=state["schedule"],
        generation=state["generation"],
        fitness=state["metrics"]["best"],
        order="time",
    )
    output.write_log(
        generation=state["generation"],
        best_fitness=state["metrics"]["best"],
        schedule=state["schedule"],
    )
    print(f"[Export] Schedule saved → {path}")


def export_csv(state):
    """
    Write the full per-generation fitness history to a CSV file.

    Delegates to output.export_csv(), passing state["history"] which is a
    list of (best, avg, worst) tuples accumulated across all generations.

    Only callable after convergence (enforced by the button guard in
    handle_events). Prints the saved file path to the terminal for
    confirmation.

    Args:
        state: application state dict; read-only inside this function.
    """
    path = output.export_csv(history=state["history"])
    print(f"[Export] Fitness history saved → {path}")


# ── Event handling ─────────────────────────────────────────────────────────────

def handle_events(events, state):
    """
    Process all pygame events for one frame and update state accordingly.

    Input field focus model:
        Clicking a field loads its current committed value into the draft
        string and sets input_focus. While a field is focused:
          - digit keys append to the draft string
          - Backspace trims the last character
          - Enter commits the draft via _commit_input()
          - Escape cancels (reverts draft) and releases focus
          - all hotkeys (G, T, SPACE, R, +/-) are suppressed so typed
            digits cannot accidentally trigger other actions
        Clicking outside any input field commits the active draft and
        releases focus. The Gens field ignores clicks before convergence.

    Button guards mirror the visual disable states in gui.py:
        Randomize        — blocked while running
        Generate         — blocked after population exists
        Run              — blocked until populated; blocked while running or converged
        Export buttons   — blocked until converged

    Args:
        events: list of pygame.Event objects from pygame.event.get().
        state : application state dict; modified in place.

    Returns:
        tuple[dict, bool]: (updated state, keep_running).
                           keep_running is False when the app should exit.
    """
    for event in events:
        if event.type == pygame.QUIT:
            return state, False

        # ── Mouse ──────────────────────────────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            clicked_input = False

            if INPUTS["seed"].collidepoint(pos):
                state["input_focus"] = "seed"
                state["seed_draft"]  = str(state["seed"])
                clicked_input = True

            if INPUTS["gens"].collidepoint(pos):
                if state.get("converged"):
                    state["input_focus"] = "gens"
                    state["gens_draft"]  = str(state["run_gens"])
                clicked_input = True   # consume click even when locked

            # Clicking outside any input commits the active draft
            if not clicked_input and state["input_focus"]:
                _commit_input(state)

            # Buttons — only fire if no input field was just focused
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
                        export_schedule(state)

                if BUTTONS["export_csv"].collidepoint(pos):
                    if state["converged"]:
                        export_csv(state)

        # ── Keyboard ──────────────────────────────────────────────────────────
        if event.type == pygame.KEYDOWN:

            if state["input_focus"]:
                # Route all keys to the active input field
                if event.key == pygame.K_RETURN:
                    _commit_input(state)

                elif event.key == pygame.K_ESCAPE:
                    # Cancel — revert draft to last committed value
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

                # All other keys consumed — hotkeys suppressed during editing

            else:
                # Normal hotkeys when no field is focused
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
    """
    Initialise pygame and run the application event loop.

    Each frame:
        1. Collect all pending pygame events.
        2. Pass them to handle_events() to update state.
        3. If the GA is running and not paused, advance one generation.
        4. Render the current state to the screen.
        5. Cap the frame rate at FPS (60).
    """
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