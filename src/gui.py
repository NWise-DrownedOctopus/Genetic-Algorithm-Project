"""
gui.py — CS 461 Program 2: Genetic Algorithm Scheduler
Member C ownership.

Handles all pygame-ce rendering: window, chart, schedule panel,
metrics panel, and control bar. In the final implementation, this
module receives live data from ga.py via main.py each generation.

Wireframe version: all panels present, buttons visual-only, no live data.
"""

import pygame
import math

# ── Window & Layout Constants ─────────────────────────────────────────────────
WIN_W, WIN_H = 1100, 860
FPS = 60
TITLE = "CS 461 — Genetic Algorithm Scheduler"

# Panel rects (x, y, w, h)
CTRL_BAR_H = 52          # top control bar
BOTTOM_BAR_H = 36        # status bar at bottom
CHART_H = 260            # fitness chart height
PADDING = 10

CTRL_RECT       = pygame.Rect(0,            0,             WIN_W, CTRL_BAR_H)
CHART_RECT      = pygame.Rect(PADDING,      CTRL_BAR_H + PADDING,
                               WIN_W - PADDING*2, CHART_H)
LOWER_Y         = CTRL_BAR_H + PADDING + CHART_H + PADDING
LOWER_H         = WIN_H - LOWER_Y - BOTTOM_BAR_H - PADDING
SCHED_W         = 620
METRICS_W       = WIN_W - SCHED_W - PADDING*3
SCHED_RECT      = pygame.Rect(PADDING,      LOWER_Y, SCHED_W,    LOWER_H)
METRICS_RECT    = pygame.Rect(SCHED_RECT.right + PADDING, LOWER_Y, METRICS_W, LOWER_H)
STATUS_RECT     = pygame.Rect(0, WIN_H - BOTTOM_BAR_H, WIN_W, BOTTOM_BAR_H)

# ── Colour Palette ────────────────────────────────────────────────────────────
C = {
    "bg":           (18,  22,  32),
    "panel":        (26,  31,  45),
    "panel_border": (45,  52,  72),
    "header":       (32,  38,  56),
    "text":         (220, 225, 235),
    "text_dim":     (110, 118, 140),
    "text_muted":   (60,  68,  88),
    "accent":       (82,  140, 255),
    "green":        (72,  210, 140),
    "red":          (255, 90,  90),
    "yellow":       (255, 200, 60),
    "orange":       (255, 145, 60),
    "chart_best":   (72,  210, 140),
    "chart_avg":    (82,  140, 255),
    "chart_worst":  (255, 90,  90),
    "btn":          (42,  50,  72),
    "btn_hover":    (58,  70,  102),
    "btn_accent":   (52,  100, 200),
    "btn_disabled": (30,  35,  50),
    "btn_text":     (200, 208, 228),
    "divider":      (38,  44,  62),
    "status_bar":   (20,  24,  36),
    "converged":    (60,  180, 110),
    "converging":   (255, 175, 50),
    "neutral":      (70,  80,  108),
    "violation":    (255, 110, 80),
}

# ── Fake wireframe data ───────────────────────────────────────────────────────
FAKE_SCHEDULE = [
    {"activity": "SLA101A",  "room": "Roman 201",  "time": "10 AM", "facilitator": "Glen",     "score":  0.8},
    {"activity": "SLA101B",  "room": "Loft 206",   "time": "2 PM",  "facilitator": "Lock",     "score":  0.5},
    {"activity": "SLA191A",  "room": "Frank 119",  "time": "11 AM", "facilitator": "Banks",    "score":  0.6},
    {"activity": "SLA191B",  "room": "Beach 301",  "time": "3 PM",  "facilitator": "Numen",    "score": -0.1},
    {"activity": "SLA201",   "room": "James 325",  "time": "12 PM", "facilitator": "Zeldin",   "score":  0.9},
    {"activity": "SLA291",   "room": "Loft 310",   "time": "1 PM",  "facilitator": "Singer",   "score":  0.3},
    {"activity": "SLA303",   "room": "Beach 201",  "time": "10 AM", "facilitator": "Glen",     "score": -0.2},
    {"activity": "SLA304",   "room": "Slater 003", "time": "11 AM", "facilitator": "Uther",    "score":  0.4},
    {"activity": "SLA394",   "room": "Roman 216",  "time": "2 PM",  "facilitator": "Tyler",    "score":  0.7},
    {"activity": "SLA449",   "room": "Beach 301",  "time": "1 PM",  "facilitator": "Zeldin",   "score":  0.2},
    {"activity": "SLA451",   "room": "Frank 119",  "time": "3 PM",  "facilitator": "Lock",     "score":  1.1},
]

FAKE_METRICS = {
    "generation":   42,
    "best":         6.84,
    "avg":          4.21,
    "worst":        1.03,
    "improvement":  2.47,
    "lam":          0.01,
    "population":   250,
    "room_conflicts":      2,
    "facilitator_overload": 1,
    "size_violations":     3,
    "converged":    False,
}

# Generate a fake fitness history curve
def _fake_history(n=42):
    history = []
    best, avg, worst = -4.0, -6.0, -9.0
    for i in range(n):
        t = i / max(n - 1, 1)
        ease = 1 - math.exp(-4 * t)
        history.append((
            -4.0 + ease * 10.8 + math.sin(i * 0.9) * 0.15,
            -6.0 + ease * 10.2 + math.sin(i * 1.1) * 0.2,
            -9.0 + ease * 10.0 + math.sin(i * 1.3) * 0.25,
        ))
    return history

FAKE_HISTORY = _fake_history()


# ── Helper drawing utilities ──────────────────────────────────────────────────

def draw_panel(surf, rect, title=None, title_icon=None):
    """Draw a rounded panel with optional header label."""
    pygame.draw.rect(surf, C["panel"], rect, border_radius=6)
    pygame.draw.rect(surf, C["panel_border"], rect, width=1, border_radius=6)
    if title:
        hdr = pygame.Rect(rect.x, rect.y, rect.w, 28)
        pygame.draw.rect(surf, C["header"], hdr, border_radius=6)
        # flat bottom edge on header
        pygame.draw.rect(surf, C["header"],
                         pygame.Rect(rect.x, rect.y + 14, rect.w, 14))
        pygame.draw.line(surf, C["panel_border"],
                         (rect.x, rect.y + 28), (rect.right, rect.y + 28))
        label = title_icon + "  " + title if title_icon else title
        _draw_text(surf, label, rect.x + 10, rect.y + 6, "sm", C["text_dim"])


def draw_button(surf, rect, label, style="normal", icon=None):
    """Draw a styled button. style: normal | accent | disabled | danger"""
    color_map = {
        "normal":   C["btn"],
        "accent":   C["btn_accent"],
        "disabled": C["btn_disabled"],
        "danger":   (120, 40, 40),
    }
    text_color = C["text_dim"] if style == "disabled" else C["btn_text"]
    bg = color_map.get(style, C["btn"])
    pygame.draw.rect(surf, bg, rect, border_radius=5)
    pygame.draw.rect(surf, C["panel_border"], rect, width=1, border_radius=5)
    txt = (icon + "  " + label) if icon else label
    _draw_text(surf, txt, rect.centerx, rect.centery, "sm",
               text_color, center=True, center_y=True)


def draw_seed_input(surf, rect, seed_val):
    """Draw seed input field."""
    pygame.draw.rect(surf, C["btn"], rect, border_radius=4)
    pygame.draw.rect(surf, C["accent"], rect, width=1, border_radius=4)
    _draw_text(surf, str(seed_val), rect.x + 8, rect.centery, "sm",
               C["text"], center_y=True)


def _font(size="md"):
    sizes = {"xs": 11, "sm": 13, "md": 15, "lg": 18, "xl": 22, "xxl": 28}
    return pygame.font.SysFont("Segoe UI", sizes.get(size, 14))


def _draw_text(surf, text, x, y, size="md", color=None, center=False,
               center_y=False, bold=False):
    color = color or C["text"]
    font = pygame.font.SysFont("Segoe UI", {"xs":11,"sm":13,"md":15,"lg":18,"xl":22,"xxl":28}.get(size,14), bold=bold)
    surf_t = font.render(str(text), True, color)
    rx = x - surf_t.get_width() // 2 if center else x
    ry = y - surf_t.get_height() // 2 if center_y else y
    surf.blit(surf_t, (rx, ry))
    return surf_t.get_width()


# ── Panel renderers ───────────────────────────────────────────────────────────

def render_control_bar(surf, state):
    """Top control bar: seed input + all action buttons."""
    pygame.draw.rect(surf, C["header"], CTRL_RECT)
    pygame.draw.line(surf, C["panel_border"],
                     (0, CTRL_BAR_H - 1), (WIN_W, CTRL_BAR_H - 1))

    x = 12
    cy = CTRL_BAR_H // 2

    # App title
    _draw_text(surf, "GA Scheduler", x, cy, "md", C["accent"],
               center_y=True, bold=True)
    x += 110

    # Divider
    pygame.draw.line(surf, C["divider"], (x, 8), (x, CTRL_BAR_H - 8))
    x += 12

    # Seed label + input
    _draw_text(surf, "Seed:", x, cy, "sm", C["text_dim"], center_y=True)
    x += 42
    seed_rect = pygame.Rect(x, cy - 12, 72, 24)
    draw_seed_input(surf, seed_rect, state.get("seed", 42))
    x += 80

    # Randomize button
    rand_rect = pygame.Rect(x, cy - 13, 88, 26)
    draw_button(surf, rand_rect, "Randomize", style="normal", icon="⟳")
    x += 96

    # Divider
    pygame.draw.line(surf, C["divider"], (x, 8), (x, CTRL_BAR_H - 8))
    x += 12

    # Generate button — always available
    gen_rect = pygame.Rect(x, cy - 13, 160, 26)
    draw_button(surf, gen_rect, "Generate Population", style="accent", icon="▶")
    x += 168

    # Divider
    pygame.draw.line(surf, C["divider"], (x, 8), (x, CTRL_BAR_H - 8))
    x += 12

    # Generations input label
    run_style = "normal" if state.get("populated") else "disabled"
    _draw_text(surf, "Gens:", x, cy, "sm", C["text_dim"], center_y=True)
    x += 40
    gens_rect = pygame.Rect(x, cy - 12, 48, 24)
    pygame.draw.rect(surf, C["btn"] if state.get("populated") else C["btn_disabled"],
                     gens_rect, border_radius=4)
    pygame.draw.rect(surf, C["panel_border"], gens_rect, width=1, border_radius=4)
    _draw_text(surf, str(state.get("run_gens", 100)), gens_rect.x + 8,
               gens_rect.centery, "sm",
               C["text"] if state.get("populated") else C["text_muted"],
               center_y=True)
    x += 56

    # Run button
    run_rect = pygame.Rect(x, cy - 13, 110, 26)
    draw_button(surf, run_rect, "Run Generations", style=run_style, icon="▶▶")
    x += 118

    # Divider
    pygame.draw.line(surf, C["divider"], (x, 8), (x, CTRL_BAR_H - 8))
    x += 12

    # Export buttons
    exp_style = "normal" if state.get("converged") else "disabled"
    exp_rect = pygame.Rect(x, cy - 13, 118, 26)
    draw_button(surf, exp_rect, "Export Schedule", style=exp_style, icon="↓")
    x += 126
    csv_rect = pygame.Rect(x, cy - 13, 104, 26)
    draw_button(surf, csv_rect, "Export CSV", style=exp_style, icon="↓")


def render_chart(surf, state):
    """Fitness line chart: best (green), avg (blue), worst (red)."""
    draw_panel(surf, CHART_RECT, title="Fitness Over Generations", title_icon="📈")

    # ── Legend in the panel header bar, right-aligned ─────────────────────────
    # Each legend item occupies a fixed 68px slot: [8 gap][18 line][6 gap][text][8 gap]
    legend_items = [("Best", C["chart_best"]),
                    ("Avg",  C["chart_avg"]),
                    ("Worst",C["chart_worst"])]
    LEGEND_SLOT = 72          # fixed px per legend item
    header_cy = CHART_RECT.y + 14
    for i, (label, color) in enumerate(reversed(legend_items)):
        slot_right = CHART_RECT.right - 10 - i * LEGEND_SLOT
        line_x2 = slot_right - 30
        line_x1 = line_x2 - 18
        pygame.draw.line(surf, color, (line_x1, header_cy), (line_x2, header_cy), 2)
        _draw_text(surf, label, line_x2 + 5, header_cy, "xs", color, center_y=True)

    # ── Chart inner area ──────────────────────────────────────────────────────
    # top margin 38px clears header bar; bottom margin 20px fits x-axis labels
    inner = pygame.Rect(
        CHART_RECT.x + 52,
        CHART_RECT.y + 38,
        CHART_RECT.w - 64,
        CHART_RECT.h - 58,
    )

    history = state.get("history", [])
    if not history:
        _draw_text(surf, "Generate a population to begin",
                   inner.centerx, inner.centery, "sm", C["text_muted"], center=True)
        return

    all_vals = [v for pt in history for v in pt]
    mn, mx = min(all_vals) - 0.5, max(all_vals) + 0.5
    span_y = mx - mn or 1
    n = len(history)

    def px(i, val):
        gx = inner.x + int(i / max(n - 1, 1) * inner.w)
        gy = inner.bottom - int((val - mn) / span_y * inner.h)
        return gx, gy

    # Grid lines + y-axis labels
    for tick in range(5):
        val = mn + tick / 4 * span_y
        gy = inner.bottom - int(tick / 4 * inner.h)
        pygame.draw.line(surf, C["divider"], (inner.x, gy), (inner.right, gy))
        _draw_text(surf, f"{val:+.1f}", inner.x - 46, gy, "xs",
                   C["text_muted"], center_y=True)

    # X-axis labels — 4px below inner bottom, fully within panel
    _draw_text(surf, "0", inner.x, inner.bottom + 4, "xs", C["text_muted"])
    _draw_text(surf, f"Gen {n}", inner.right - 30, inner.bottom + 4,
               "xs", C["text_muted"])

    # Draw series lines
    for series_idx, (_, color) in enumerate([
        (0, C["chart_best"]), (1, C["chart_avg"]), (2, C["chart_worst"])
    ]):
        points = [px(i, pt[series_idx]) for i, pt in enumerate(history)]
        if len(points) > 1:
            pygame.draw.lines(surf, color, False, points, 2)
        pygame.draw.circle(surf, color, points[-1], 4)


def render_schedule(surf, state):
    """Schedule panel: table of all 11 activities."""
    draw_panel(surf, SCHED_RECT, title="Best Schedule", title_icon="📋")

    schedule = state.get("schedule", [])
    if not schedule:
        _draw_text(surf, "No schedule generated yet.",
                   SCHED_RECT.centerx, SCHED_RECT.centery,
                   "sm", C["text_muted"], center=True)
        return

    # Column layout inside panel
    inner_x = SCHED_RECT.x + 10
    inner_y = SCHED_RECT.y + 36
    inner_w = SCHED_RECT.w - 20
    row_h = 28

    cols = [
        ("Activity",    120),
        ("Room",        120),
        ("Time",         68),
        ("Facilitator",  100),
        ("Score",        60),
    ]

    # Header row
    cx = inner_x
    for label, w in cols:
        _draw_text(surf, label, cx + 6, inner_y, "sm", C["text_dim"], bold=True)
        cx += w
    inner_y += 22
    pygame.draw.line(surf, C["panel_border"],
                     (inner_x, inner_y), (inner_x + inner_w, inner_y))
    inner_y += 6

    display = schedule if state.get("show_all_activities") else schedule[:6]
    for i, row in enumerate(display):
        if inner_y + row_h > SCHED_RECT.bottom - 6:
            break
        bg_col = C["panel"] if i % 2 == 0 else (30, 36, 52)
        pygame.draw.rect(surf, bg_col,
                         pygame.Rect(inner_x, inner_y, inner_w, row_h - 2),
                         border_radius=3)

        score = row["score"]
        score_color = (C["green"] if score >= 0.5
                       else C["yellow"] if score >= 0
                       else C["red"])

        cx = inner_x
        vals = [row["activity"], row["room"], row["time"],
                row["facilitator"], f"{score:+.2f}"]
        for j, ((_, w), val) in enumerate(zip(cols, vals)):
            col = score_color if j == 4 else C["text"]
            _draw_text(surf, val, cx + 6, inner_y + 6, "sm", col)
            cx += w
        inner_y += row_h


def render_metrics(surf, state):
    """Metrics panel: GA stats, fitness values, violations."""
    draw_panel(surf, METRICS_RECT, title="Metrics", title_icon="📊")

    mx = METRICS_RECT.x + 14
    my = METRICS_RECT.y + 38

    def row(label, value, val_color=None):
        nonlocal my
        _draw_text(surf, label, mx, my, "sm", C["text_dim"], center_y=True)
        # measure and right-align value — erase rect must stop 2px inside border
        font = pygame.font.SysFont("Segoe UI", 13)
        val_w = font.size(str(value))[0]
        erase_right = METRICS_RECT.right - 2   # stay inside the 1px border
        surf.fill(C["panel"], (erase_right - val_w - 16, my - 8,
                               val_w + 14, 16))
        _draw_text(surf, str(value), erase_right - val_w - 2, my,
                   "sm", val_color or C["text"], center_y=True)
        my += 24

    def divider():
        nonlocal my
        pygame.draw.line(surf, C["divider"],
                         (mx, my + 2), (METRICS_RECT.right - 14, my + 2))
        my += 12

    def section(label):
        nonlocal my
        my += 6
        _draw_text(surf, label, mx, my, "sm", C["accent"], bold=True)
        my += 28   # increased from 20 → 28 to give title more breathing room

    if not state.get("populated"):
        _draw_text(surf, "No data yet.",
                   METRICS_RECT.centerx, METRICS_RECT.centery,
                   "sm", C["text_muted"], center=True)
        return

    m = state.get("metrics", {})

    section("GA STATUS")
    row("Generation",   m.get("generation", 0))
    row("Population",   m.get("population", 250))
    row("Mutation λ",   f"{m.get('lam', 0.01):.4f}")
    divider()

    section("FITNESS")
    row("Best",         f"{m.get('best', 0):.4f}",  C["green"])
    row("Average",      f"{m.get('avg', 0):.4f}",   C["chart_avg"])
    row("Worst",        f"{m.get('worst', 0):.4f}", C["red"])
    row("Improvement",  f"{m.get('improvement', 0):.2f}%",
        C["green"] if m.get("improvement", 0) < 1.0 else C["yellow"])
    divider()

    section("VIOLATIONS")
    row("Room Conflicts",      m.get("room_conflicts", 0),
        C["violation"] if m.get("room_conflicts", 0) > 0 else C["green"])
    row("Facilitator Overload", m.get("facilitator_overload", 0),
        C["violation"] if m.get("facilitator_overload", 0) > 0 else C["green"])
    row("Size Violations",     m.get("size_violations", 0),
        C["violation"] if m.get("size_violations", 0) > 0 else C["green"])
    divider()

    section("OVERALL SCORE")
    total = sum(r["score"] for r in state.get("schedule", []))
    row("Total Fitness", f"{total:.4f}", C["green"] if total > 0 else C["red"])


def render_status_bar(surf, state):
    """Bottom status bar: convergence state + keyboard hints."""
    pygame.draw.rect(surf, C["status_bar"], STATUS_RECT)
    pygame.draw.line(surf, C["panel_border"],
                     (0, STATUS_RECT.y), (WIN_W, STATUS_RECT.y))

    # Status indicator
    if not state.get("populated"):
        status_text = "●  Idle — generate a population to begin"
        status_color = C["neutral"]
    elif state.get("converged"):
        status_text = "●  Converged ✓ — stopping condition met"
        status_color = C["converged"]
    else:
        status_text = "●  Converging..."
        status_color = C["converging"]

    _draw_text(surf, status_text, 12, STATUS_RECT.centery,
               "xs", status_color, center_y=True)

    # Keyboard hints right-aligned
    hints = "[SPACE] Pause   [R] Reset   [+/-] Adjust λ   [T] Toggle rows"
    hw = sum(pygame.font.SysFont("Segoe UI", 11).size(hints)[0] for _ in [1])
    _draw_text(surf, hints, WIN_W - 12 - pygame.font.SysFont("Segoe UI", 11).size(hints)[0],
               STATUS_RECT.centery, "xs", C["text_muted"], center_y=True)


# ── Main render entry point ───────────────────────────────────────────────────

def render(surf, state):
    """
    Render all panels. Called once per frame from main.py.

    state dict keys (all optional in wireframe):
        populated   : bool   — has initial population been generated?
        converged   : bool   — has stopping condition been met?
        seed        : int    — current RNG seed
        run_gens    : int    — number of generations for next Run press
        schedule    : list   — list of activity dicts (see FAKE_SCHEDULE)
        metrics     : dict   — GA metrics (see FAKE_METRICS)
        history     : list   — list of (best, avg, worst) tuples per generation
    """
    surf.fill(C["bg"])
    render_control_bar(surf, state)
    render_chart(surf, state)
    render_schedule(surf, state)
    render_metrics(surf, state)
    render_status_bar(surf, state)


# ── Standalone test (run gui.py directly to preview) ─────────────────────────

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Cycle through states with SPACE to demo neutral → populated → converged
    STATES = [
        # State 0: neutral / idle
        {"populated": False, "converged": False, "seed": 42, "run_gens": 100,
         "schedule": [], "metrics": {}, "history": []},
        # State 1: populated, running
        {"populated": True,  "converged": False, "seed": 42, "run_gens": 100,
         "schedule": FAKE_SCHEDULE, "metrics": FAKE_METRICS,
         "history": FAKE_HISTORY},
        # State 2: converged
        {**{"populated": True, "converged": True, "seed": 42, "run_gens": 100,
            "schedule": FAKE_SCHEDULE,
            "metrics": {**FAKE_METRICS, "generation": 187, "improvement": 0.43,
                        "best": 7.92, "avg": 5.88, "worst": 2.14,
                        "room_conflicts": 0, "facilitator_overload": 0,
                        "size_violations": 1}},
         "history": _fake_history(187)},
    ]
    state_idx = 0

    print("GA Scheduler Wireframe")
    print("  SPACE → cycle through UI states (Idle → Running → Converged)")
    print("  ESC / close window → quit")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    state_idx = (state_idx + 1) % len(STATES)

        render(screen, STATES[state_idx])
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()