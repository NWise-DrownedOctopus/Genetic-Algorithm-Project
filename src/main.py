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
)
from schedule import (
    initialize_population,
)
from fitness import (
    score_schedule
)
from ga import (
    run_generation, halve_mutation_rate
)

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
        "show_all_activities": False,   # T toggles 6 vs all 11 in schedule panel

        # Config
        "seed":         42,      # RNG seed
        "run_gens":     100,     # how many generations to run per [Run] press

        # GA state (populated by ga.py in final version)
        "population":   [],      # list of Schedule objects
        "scores":       [],      # fitness scores, parallel to population
        "generation":   0,       # current generation count
        "lam":          0.01,    # current mutation rate

        # Display data (updated each generation)
        "schedule":     [],      # best schedule — list of activity dicts
        "metrics":      {},      # dict of GA metrics for metrics panel
        "history":      [],      # list of (best, avg, worst) per generation
    }


# ── Generate initial population ────────────────────────────────────────
def generate_population(state):
    # Generate initial population and calculate starting scores 
    population = initialize_population()
    scores = []
    for schedule in population:
        scores.append(score_schedule(schedule))
        
    # Store best, average, and worst schedule
    best_idx = scores.index(max(scores))
    best_schedule = population[best_idx]      
    average_score = sum(scores)/len(scores)
    
    # Grab data from best schedule
    schedule_display = [
        {
            "activity":    a.activity["name"],
            "room":        a.room,
            "time":        a.time,
            "facilitator": a.facilitator,
            "score":       0.0,   # per-assignment scores not tracked yet, placeholder
        }
        for a in best_schedule.assignments
    ]
    
    # Build initial metrics
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
    
    # Update state to reflect data generated
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
    Calls run_generation() with the correct signature and
    unpacks its return value back into the shared state dict.

    """
    prev_avg = state["metrics"].get("avg") if state["metrics"] else None
 
    next_gen, metrics = run_generation(
        population=state["population"],
        scores=state["scores"],
        lam=state["lam"],
        generation=state["generation"] + 1,
        prev_avg=prev_avg,
    )
 
    # Re-score the new generation so state["scores"] stays in sync
    new_scores = [score_schedule(s) for s in next_gen]
 
    best_idx = new_scores.index(max(new_scores))
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
    gen = state["generation"] + 1
    improvement = metrics.get("improvement", 0.0)
    converged = gen >= 100 and abs(improvement) < 1.0
 
    # Halve mutation rate once converged to allow fine-tuning
    if converged and not state["converged"]:
        state["lam"] = halve_mutation_rate(state["lam"])
 
    # Carry violation counts forward until Member A supplies live values
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


# ── Stub: Export ──────────────────────────────────────────────────────────────
def stub_export_schedule(state):
    """In final version, calls output.save_schedule(state['schedule'])"""
    print("[STUB] Would export schedule to output/best_schedule.txt")


def stub_export_csv(state):
    """In final version, calls output.export_csv(state['history'])"""
    print("[STUB] Would export fitness history to output/fitness_history.csv")


# ── Event handling ─────────────────────────────────────────────────────────────
def handle_events(events, state):
    """
    Process keyboard and window events.
    Returns updated state and a running bool.
    """
    for event in events:
        if event.type == pygame.QUIT:
            return state, False
 
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return state, False
 
            if event.key == pygame.K_SPACE:
                if state["populated"]:
                    state["paused"] = not state["paused"]
 
            if event.key == pygame.K_r:
                state = make_initial_state()
                
            if event.key == pygame.K_t:
                if state["populated"]:
                    state["show_all_activities"] = not state["show_all_activities"]
 
            if event.key == pygame.K_g:
                if not state["populated"]:
                    state = generate_population(state)
                elif not state["running"] and not state["converged"]:
                    state["running"] = True
 
            if event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                state["lam"] = min(0.5, state["lam"] * 2)

            if event.key == pygame.K_MINUS:
                state["lam"] = max(0.0001, state["lam"] / 2)
 
    return state, True


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    
    state = make_initial_state()
    
    print(f"Launching {TITLE}")
    print("  [G]       Generate initial population")
    print("  [T]       Toggle 6 / all activities in schedule panel")
    print("  [SPACE]   Pause / resume")
    print("  [R]       Reset to idle state")
    print("  [+/-]     Adjust mutation rate λ")
    print("  [ESC]     Quit")

    running = True
    while running:
        events = pygame.event.get()
        state, running = handle_events(events, state)
        
        if state["running"] and not state["paused"] and not state["converged"] and state["populated"]:
            state = advance_generation(state)

        render(screen, state)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()