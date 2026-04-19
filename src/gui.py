"""
gui.py — CS 461 Program 2: Genetic Algorithm Scheduler
Member C ownership.

Handles all pygame-ce rendering: window, chart, schedule panel,
metrics panel, and control bar. Receives live data from ga.py
via main.py each generation.
"""

import pygame
import math

# ── Window & Layout Constants ─────────────────────────────────────────────────
WIN_W, WIN_H = 1100, 860
FPS = 60
TITLE = "CS 461 — Genetic Algorithm Scheduler"

CTRL_BAR_H   = 52
BOTTOM_BAR_H = 36
CHART_H      = 260
PADDING      = 10

CTRL_RECT    = pygame.Rect(0,       0,                     WIN_W, CTRL_BAR_H)
CHART_RECT   = pygame.Rect(PADDING, CTRL_BAR_H + PADDING, WIN_W - PADDING*2, CHART_H)
LOWER_Y      = CTRL_BAR_H + PADDING + CHART_H + PADDING
LOWER_H      = WIN_H - LOWER_Y - BOTTOM_BAR_H - PADDING
SCHED_W      = 620
METRICS_W    = WIN_W - SCHED_W - PADDING*3
SCHED_RECT   = pygame.Rect(PADDING, LOWER_Y, SCHED_W, LOWER_H)
METRICS_RECT = pygame.Rect(SCHED_RECT.right + PADDING, LOWER_Y, METRICS_W, LOWER_H)
STATUS_RECT  = pygame.Rect(0, WIN_H - BOTTOM_BAR_H, WIN_W, BOTTOM_BAR_H)

# ── Button & Input rects — shared with main.py for hit-testing ───────────────
# cy = CTRL_BAR_H // 2 = 26
# Buttons: 26px tall, y = cy - 13 = 13
# Inputs:  24px tall, y = cy - 12 = 14
_CY = CTRL_BAR_H // 2

BUTTONS = {
    "randomize":    pygame.Rect(256, _CY - 13, 88,  26),
    "generate":     pygame.Rect(364, _CY - 13, 160, 26),
    "run":          pygame.Rect(640, _CY - 13, 110, 26),
    "export_sched": pygame.Rect(770, _CY - 13, 118, 26),
    "export_csv":   pygame.Rect(896, _CY - 13, 104, 26),
}

INPUTS = {
    "seed": pygame.Rect(176, _CY - 12, 72, 24),
    "gens": pygame.Rect(584, _CY - 12, 48, 24),
}

# ── Colour Palette ────────────────────────────────────────────────────────────
C = {
    "bg":               (18,  22,  32),
    "panel":            (26,  31,  45),
    "panel_border":     (45,  52,  72),
    "header":           (32,  38,  56),
    "text":             (220, 225, 235),
    "text_dim":         (110, 118, 140),
    "text_muted":       (60,  68,  88),
    "accent":           (82,  140, 255),
    "green":            (72,  210, 140),
    "red":              (255, 90,  90),
    "yellow":           (255, 200, 60),
    "orange":           (255, 145, 60),
    "chart_best":       (72,  210, 140),
    "chart_avg":        (82,  140, 255),
    "chart_worst":      (255, 90,  90),
    "btn":              (42,  50,  72),
    "btn_hover":        (58,  70,  102),
    "btn_accent":       (52,  100, 200),
    "btn_accent_hover": (68,  118, 220),
    "btn_disabled":     (30,  35,  50),
    "btn_text":         (200, 208, 228),
    "divider":          (38,  44,  62),
    "status_bar":       (20,  24,  36),
    "converged":        (60,  180, 110),
    "converging":       (255, 175, 50),
    "neutral":          (70,  80,  108),
    "violation":        (255, 110, 80),
}


# ── Helper drawing utilities ──────────────────────────────────────────────────

def draw_panel(surf, rect, title=None, title_icon=None):
    """Draw a rounded panel with optional header label."""
    pygame.draw.rect(surf, C["panel"], rect, border_radius=6)
    pygame.draw.rect(surf, C["panel_border"], rect, width=1, border_radius=6)
    if title:
        hdr = pygame.Rect(rect.x, rect.y, rect.w, 28)
        pygame.draw.rect(surf, C["header"], hdr, border_radius=6)
        pygame.draw.rect(surf, C["header"],
                         pygame.Rect(rect.x, rect.y + 14, rect.w, 14))
        pygame.draw.line(surf, C["panel_border"],
                         (rect.x, rect.y + 28), (rect.right, rect.y + 28))
        label = title_icon + "  " + title if title_icon else title
        _draw_text(surf, label, rect.x + 10, rect.y + 6, "sm", C["text_dim"])


def draw_button(surf, rect, label, style="normal", icon=None, hovered=False):
    """
    Draw a styled button.
    style  : normal | accent | disabled | danger
    hovered: lightens background on mouse-over; ignored for disabled buttons.
    """
    color_map = {
        "normal":   C["btn_hover"]        if hovered else C["btn"],
        "accent":   C["btn_accent_hover"] if hovered else C["btn_accent"],
        "disabled": C["btn_disabled"],
        "danger":   (150, 50, 50)         if hovered else (120, 40, 40),
    }
    text_color = C["text_dim"] if style == "disabled" else C["btn_text"]
    bg = color_map.get(style, C["btn"])
    pygame.draw.rect(surf, bg, rect, border_radius=5)
    pygame.draw.rect(surf, C["panel_border"], rect, width=1, border_radius=5)
    txt = (icon + "  " + label) if icon else label
    _draw_text(surf, txt, rect.centerx, rect.centery, "sm",
               text_color, center=True, center_y=True)


def draw_text_input(surf, rect, value, focused=False, locked=False):
    """
    Draw an editable text input field.
    focused: highlights border in accent colour and appends a cursor character.
    locked : dims the field and border to signal it is not editable.
    """
    if locked:
        border_color = C["text_muted"]
        bg           = C["btn_disabled"]
        text_color   = C["text_muted"]
    elif focused:
        border_color = C["accent"]
        bg           = C["btn"]
        text_color   = C["text"]
    else:
        border_color = C["panel_border"]
        bg           = C["btn"]
        text_color   = C["text"]

    pygame.draw.rect(surf, bg, rect, border_radius=4)
    pygame.draw.rect(surf, border_color, rect, width=1, border_radius=4)

    display = value + "|" if focused else value
    _draw_text(surf, display, rect.x + 8, rect.centery, "sm",
               text_color, center_y=True)


def _draw_text(surf, text, x, y, size="md", color=None, center=False,
               center_y=False, bold=False):
    color = color or C["text"]
    sizes = {"xs": 11, "sm": 13, "md": 15, "lg": 18, "xl": 22, "xxl": 28}
    font = pygame.font.SysFont("Segoe UI", sizes.get(size, 14), bold=bold)
    surf_t = font.render(str(text), True, color)
    rx = x - surf_t.get_width() // 2 if center else x
    ry = y - surf_t.get_height() // 2 if center_y else y
    surf.blit(surf_t, (rx, ry))
    return surf_t.get_width()


# ── Panel renderers ───────────────────────────────────────────────────────────

def render_control_bar(surf, state, mouse_pos):
    """
    Top control bar: seed input, gens input, and all action buttons.
    mouse_pos is passed in each frame to compute per-button hover state.
    Disabled buttons never show hover regardless of mouse position.
    """
    pygame.draw.rect(surf, C["header"], CTRL_RECT)
    pygame.draw.line(surf, C["panel_border"],
                     (0, CTRL_BAR_H - 1), (WIN_W, CTRL_BAR_H - 1))

    x  = 12
    cy = CTRL_BAR_H // 2

    # App title
    _draw_text(surf, "GA Scheduler", x, cy, "md", C["accent"],
               center_y=True, bold=True)
    x += 110

    pygame.draw.line(surf, C["divider"], (x, 8), (x, CTRL_BAR_H - 8))
    x += 12

    # Seed label + editable input
    _draw_text(surf, "Seed:", x, cy, "sm", C["text_dim"], center_y=True)
    x += 42
    draw_text_input(surf, INPUTS["seed"],
                    value=state.get("seed_draft", str(state.get("seed", 42))),
                    focused=state.get("input_focus") == "seed",
                    locked=False)
    x += 80

    # Randomize — disabled while GA is running
    rand_style   = "disabled" if state.get("running") else "normal"
    rand_hovered = rand_style != "disabled" and BUTTONS["randomize"].collidepoint(mouse_pos)
    draw_button(surf, BUTTONS["randomize"], "Randomize",
                style=rand_style, icon="⟳", hovered=rand_hovered)
    x += 96

    pygame.draw.line(surf, C["divider"], (x, 8), (x, CTRL_BAR_H - 8))
    x += 12

    # Generate Population — accent until populated, disabled after
    gen_style   = "disabled" if state.get("populated") else "accent"
    gen_hovered = gen_style != "disabled" and BUTTONS["generate"].collidepoint(mouse_pos)
    draw_button(surf, BUTTONS["generate"], "Generate Population",
                style=gen_style, icon="▶", hovered=gen_hovered)
    x += 168

    pygame.draw.line(surf, C["divider"], (x, 8), (x, CTRL_BAR_H - 8))
    x += 12

    # Gens label + editable input (locked until converged)
    _draw_text(surf, "Gens:", x, cy, "sm", C["text_dim"], center_y=True)
    x += 40
    gens_locked = not state.get("converged", False)
    draw_text_input(surf, INPUTS["gens"],
                    value=state.get("gens_draft", str(state.get("run_gens", 100))),
                    focused=state.get("input_focus") == "gens",
                    locked=gens_locked)
    x += 56

    # Run Generations — disabled until populated and not already running
    can_run     = (state.get("populated") and not state.get("running")
                   and not state.get("converged"))
    run_style   = "normal" if can_run else "disabled"
    run_hovered = run_style != "disabled" and BUTTONS["run"].collidepoint(mouse_pos)
    draw_button(surf, BUTTONS["run"], "Run Generations",
                style=run_style, icon="▶▶", hovered=run_hovered)
    x += 118

    pygame.draw.line(surf, C["divider"], (x, 8), (x, CTRL_BAR_H - 8))
    x += 12

    # Export buttons — only active after convergence
    exp_style     = "normal" if state.get("converged") else "disabled"
    sched_hovered = exp_style != "disabled" and BUTTONS["export_sched"].collidepoint(mouse_pos)
    csv_hovered   = exp_style != "disabled" and BUTTONS["export_csv"].collidepoint(mouse_pos)
    draw_button(surf, BUTTONS["export_sched"], "Export Schedule",
                style=exp_style, icon="↓", hovered=sched_hovered)
    draw_button(surf, BUTTONS["export_csv"], "Export CSV",
                style=exp_style, icon="↓", hovered=csv_hovered)


def render_chart(surf, state):
    """Fitness line chart: best (green), avg (blue), worst (red)."""
    draw_panel(surf, CHART_RECT, title="Fitness Over Generations", title_icon="📈")

    legend_items = [("Best", C["chart_best"]),
                    ("Avg",  C["chart_avg"]),
                    ("Worst",C["chart_worst"])]
    LEGEND_SLOT = 72
    header_cy   = CHART_RECT.y + 14
    for i, (label, color) in enumerate(reversed(legend_items)):
        slot_right = CHART_RECT.right - 10 - i * LEGEND_SLOT
        line_x2    = slot_right - 30
        line_x1    = line_x2 - 18
        pygame.draw.line(surf, color, (line_x1, header_cy), (line_x2, header_cy), 2)
        _draw_text(surf, label, line_x2 + 5, header_cy, "xs", color, center_y=True)

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
    mn, mx   = min(all_vals) - 0.5, max(all_vals) + 0.5
    span_y   = mx - mn or 1
    n        = len(history)

    def px(i, val):
        gx = inner.x + int(i / max(n - 1, 1) * inner.w)
        gy = inner.bottom - int((val - mn) / span_y * inner.h)
        return gx, gy

    for tick in range(5):
        val = mn + tick / 4 * span_y
        gy  = inner.bottom - int(tick / 4 * inner.h)
        pygame.draw.line(surf, C["divider"], (inner.x, gy), (inner.right, gy))
        _draw_text(surf, f"{val:+.1f}", inner.x - 46, gy, "xs",
                   C["text_muted"], center_y=True)

    _draw_text(surf, "0", inner.x, inner.bottom + 4, "xs", C["text_muted"])
    _draw_text(surf, f"Gen {n}", inner.right - 30, inner.bottom + 4,
               "xs", C["text_muted"])

    for series_idx, (_, color) in enumerate([
        (0, C["chart_best"]), (1, C["chart_avg"]), (2, C["chart_worst"])
    ]):
        points = [px(i, pt[series_idx]) for i, pt in enumerate(history)]
        if len(points) > 1:
            pygame.draw.lines(surf, color, False, points, 2)
        pygame.draw.circle(surf, color, points[-1], 4)


def render_schedule(surf, state):
    """Schedule panel: table of activities, toggled between 6 and all 11."""
    draw_panel(surf, SCHED_RECT, title="Best Schedule", title_icon="📋")

    schedule = state.get("schedule", [])
    if not schedule:
        _draw_text(surf, "No schedule generated yet.",
                   SCHED_RECT.centerx, SCHED_RECT.centery,
                   "sm", C["text_muted"], center=True)
        return

    display = schedule if state.get("show_all_activities") else schedule[:6]

    inner_x = SCHED_RECT.x + 10
    inner_y = SCHED_RECT.y + 36
    inner_w = SCHED_RECT.w - 20
    row_h   = 28

    cols = [
        ("Activity",   120),
        ("Room",       120),
        ("Time",        68),
        ("Facilitator", 100),
        ("Score",        60),
    ]

    cx = inner_x
    for label, w in cols:
        _draw_text(surf, label, cx + 6, inner_y, "sm", C["text_dim"], bold=True)
        cx += w

    hint = "showing all 11  [T]" if state.get("show_all_activities") else "showing 6 of 11  [T]"
    _draw_text(surf, hint, SCHED_RECT.right - 140, inner_y, "xs", C["text_muted"])

    inner_y += 22
    pygame.draw.line(surf, C["panel_border"],
                     (inner_x, inner_y), (inner_x + inner_w, inner_y))
    inner_y += 6

    for i, row in enumerate(display):
        if inner_y + row_h > SCHED_RECT.bottom - 6:
            break
        bg_col = C["panel"] if i % 2 == 0 else (30, 36, 52)
        pygame.draw.rect(surf, bg_col,
                         pygame.Rect(inner_x, inner_y, inner_w, row_h - 2),
                         border_radius=3)

        score       = row["score"]
        score_color = (C["green"]  if score >= 0.5
                  else C["yellow"] if score >= 0
                  else C["red"])

        cx   = inner_x
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
        font  = pygame.font.SysFont("Segoe UI", 13)
        val_w = font.size(str(value))[0]
        erase_right = METRICS_RECT.right - 2
        surf.fill(C["panel"], (erase_right - val_w - 16, my - 8, val_w + 14, 16))
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
        my += 28

    if not state.get("populated"):
        _draw_text(surf, "No data yet.",
                   METRICS_RECT.centerx, METRICS_RECT.centery,
                   "sm", C["text_muted"], center=True)
        return

    m = state.get("metrics", {})

    section("GA STATUS")
    row("Generation",  m.get("generation", 0))
    row("Population",  m.get("population", 250))
    row("Mutation λ",  f"{m.get('lam', 0.01):.4f}")
    divider()

    section("FITNESS")
    row("Best",        f"{m.get('best', 0):.4f}",  C["green"])
    row("Average",     f"{m.get('avg', 0):.4f}",   C["chart_avg"])
    row("Worst",       f"{m.get('worst', 0):.4f}", C["red"])
    row("Improvement", f"{m.get('improvement', 0):.2f}%",
        C["green"] if m.get("improvement", 0) < 1.0 else C["yellow"])
    divider()

    section("VIOLATIONS")
    row("Room Conflicts",       m.get("room_conflicts", 0),
        C["violation"] if m.get("room_conflicts", 0) > 0 else C["green"])
    row("Facilitator Overload", m.get("facilitator_overload", 0),
        C["violation"] if m.get("facilitator_overload", 0) > 0 else C["green"])
    row("Size Violations",      m.get("size_violations", 0),
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

    if not state.get("populated"):
        status_text  = "●  Idle — press [G] or click Generate Population to begin"
        status_color = C["neutral"]
    elif state.get("converged"):
        status_text  = "●  Converged ✓ — stopping condition met"
        status_color = C["converged"]
    else:
        status_text  = "●  Converging..."
        status_color = C["converging"]

    _draw_text(surf, status_text, 12, STATUS_RECT.centery,
               "xs", status_color, center_y=True)

    hints = "[G] Generate   [SPACE] Pause   [T] Toggle rows   [R] Reset   [+/-] Adjust λ"
    _draw_text(surf, hints,
               WIN_W - 12 - pygame.font.SysFont("Segoe UI", 11).size(hints)[0],
               STATUS_RECT.centery, "xs", C["text_muted"], center_y=True)


# ── Main render entry point ───────────────────────────────────────────────────

def render(surf, state, mouse_pos):
    """
    Render all panels. Called once per frame from main.py.
    mouse_pos: current (x, y) from pygame.mouse.get_pos(), used for hover state.
    """
    surf.fill(C["bg"])
    render_control_bar(surf, state, mouse_pos)
    render_chart(surf, state)
    render_schedule(surf, state)
    render_metrics(surf, state)
    render_status_bar(surf, state)