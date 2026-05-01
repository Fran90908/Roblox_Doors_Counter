# DoorsCounter — Windows · estilo Dynamic Island
# ===============================================
# Requisitos: pip install pynput
# (No necesita pywin32 — usamos ctypes que viene con Python.)
#
# CONTROLES (mismos que la versión de Mac)
#   Mouse 4   /  Ctrl+Alt+=   → +1 puerta
#   Mouse 5   /  Ctrl+Alt+9   → -1 puerta
#   Click rueda / Ctrl+Alt+F  → cambiar Floor 1 ↔ 2
#   Ctrl+Alt+0                → reset
#   Ctrl+Alt+P                → cambiar posición (centro / derecha / izquierda)
#   Ctrl+Alt+T                → cambiar transparencia
#   F5                        → menú (cerrar / resetear / minimizar / mover / transparencia / cancelar)
#
# Para crear el .exe:  ejecuta build_windows.bat (usa PyInstaller)

import ctypes
import sys
import tkinter as tk
import tkinter.font as tkfont

try:
    from pynput import keyboard, mouse
except ImportError:
    print("Falta pynput. Instálalo con:  pip install pynput", file=sys.stderr)
    sys.exit(1)


# ============== Look (Dynamic Island) ==============
PILL_W = 220
PILL_H = 64
CIRCLE_D = 64
TOP_MARGIN = 8
SIDE_MARGIN = 20
BG_COLOR = "#000000"
CHROMA = "#FF00FE"          # color "transparente" (no debe aparecer en la pastilla)
TEXT_COLOR = "#FFFFFF"
SUBTEXT_COLOR = "#A8A8A8"
FONT_SIZE_MAIN = 30
FONT_SIZE_FLOOR = 11
ALPHA = 0.95
# ===================================================

OPACITY_LEVELS = (0.95, 0.6, 0.35)
OPACITY_NAMES = ("opaco", "translúcido", "fantasma")

POSITIONS = ("center", "right", "left")
POSITION_LABELS_ES = {
    "center": "centro",
    "right":  "derecha",
    "left":   "izquierda",
}

count = 0
floor = 1
is_minimized = False
position = "center"
opacity_idx = 0

# Refs Tk (creadas en build_window)
root = None
canvas = None
text_main = None
text_floor = None

# Menú (panel persistente, lazy)
menu = None
menu_status_label = None
menu_segments = {}        # key -> list[tk.Button]  (botones de cada segmented row)


# ============== Lógica del contador ==============

def update_labels():
    if root is None:
        return
    root.after(0, _do_update_labels)


def _do_update_labels():
    if canvas is None:
        return
    if text_main is not None:
        canvas.itemconfigure(text_main, text=str(count))
    if text_floor is not None and not is_minimized:
        canvas.itemconfigure(text_floor, text=f"FLOOR {floor}")


def increment():
    global count
    count += 1
    update_labels()


def decrement():
    global count
    count = max(0, count - 1)
    update_labels()


def reset_counter():
    global count
    count = 0
    update_labels()
    update_menu_state()


def set_floor(new_floor):
    global floor, count
    floor = new_floor
    if floor == 2:
        if count < 100:
            count = 100
    else:
        if count >= 100:
            count = 0
    update_labels()
    update_menu_state()


def cycle_floor():
    set_floor(2 if floor == 1 else 1)


# ============== Layout ==============

def _compute_x(screen_w, w):
    if position == "left":
        return SIDE_MARGIN
    if position == "right":
        return screen_w - w - SIDE_MARGIN
    return (screen_w - w) // 2


def relayout():
    """Reposiciona y redibuja la pastilla según is_minimized y position."""
    if root is None or canvas is None:
        return

    if is_minimized:
        w = h = CIRCLE_D
    else:
        w, h = PILL_W, PILL_H

    sw = root.winfo_screenwidth()
    x = _compute_x(sw, w)
    root.geometry(f"{w}x{h}+{x}+{TOP_MARGIN}")
    canvas.config(width=w, height=h)

    # Limpiar y redibujar la forma + textos
    canvas.delete("all")
    if is_minimized:
        # Disco perfecto
        canvas.create_oval(0, 0, w, h, fill=BG_COLOR, outline=BG_COLOR)
    else:
        _draw_pill(canvas, 0, 0, w, h, BG_COLOR)

    f_main = tkfont.Font(family="Segoe UI", size=-FONT_SIZE_MAIN, weight="bold")
    f_sub = tkfont.Font(family="Segoe UI", size=-FONT_SIZE_FLOOR)

    global text_main, text_floor
    if is_minimized:
        # Solo número, centrado en el círculo
        text_main = canvas.create_text(
            w / 2, h / 2,
            text=str(count),
            fill=TEXT_COLOR, font=f_main, anchor="center",
        )
        text_floor = None
    else:
        # Número arriba (un pelín bajado para centrarlo con el FLOOR)
        text_main = canvas.create_text(
            w / 2, h * 0.40,
            text=str(count),
            fill=TEXT_COLOR, font=f_main, anchor="center",
        )
        text_floor = canvas.create_text(
            w / 2, h * 0.78,
            text=f"FLOOR {floor}",
            fill=SUBTEXT_COLOR, font=f_sub, anchor="center",
        )


def _draw_pill(c, x1, y1, x2, y2, color):
    """Rectángulo con esquinas perfectamente redondeadas (pill)."""
    h = y2 - y1
    r = h / 2
    c.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline=color)
    c.create_oval(x1, y1, x1 + h, y2, fill=color, outline=color)
    c.create_oval(x2 - h, y1, x2, y2, fill=color, outline=color)


def toggle_minimize():
    global is_minimized
    is_minimized = not is_minimized
    relayout()
    update_menu_state()


def cycle_position():
    """center → right → left → center …"""
    global position
    i = POSITIONS.index(position) if position in POSITIONS else 0
    position = POSITIONS[(i + 1) % len(POSITIONS)]
    relayout()
    update_menu_state()


def cycle_opacity():
    """Cycle through opacity levels and update the window."""
    global opacity_idx
    opacity_idx = (opacity_idx + 1) % len(OPACITY_LEVELS)
    if root is not None:
        root.attributes("-alpha", OPACITY_LEVELS[opacity_idx])
    update_menu_state()


# Setters directos — para selección de un click desde el panel.
def set_position(new_pos):
    global position
    if position != new_pos:
        position = new_pos
        relayout()
    update_menu_state()


def set_opacity(idx):
    global opacity_idx
    if opacity_idx != idx:
        opacity_idx = idx
        if root is not None:
            root.attributes("-alpha", OPACITY_LEVELS[idx])
    update_menu_state()


def set_minimize(value):
    global is_minimized
    if is_minimized != bool(value):
        is_minimized = bool(value)
        relayout()
    update_menu_state()


def _next_position_label():
    i = POSITIONS.index(position) if position in POSITIONS else 0
    nxt = POSITIONS[(i + 1) % len(POSITIONS)]
    es = POSITION_LABELS_ES[nxt]
    if nxt == "center":
        return "Mover al centro"
    return f"Mover a la {es}"


# ============== Ventana ==============

def build_window():
    global root, canvas

    root = tk.Tk()
    root.title("DoorsCounter")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", OPACITY_LEVELS[opacity_idx])
    root.configure(bg=CHROMA)
    root.attributes("-transparentcolor", CHROMA)

    canvas = tk.Canvas(
        root, width=PILL_W, height=PILL_H, bg=CHROMA,
        highlightthickness=0, bd=0,
    )
    canvas.pack()

    relayout()
    _make_click_through(root)


def _make_click_through(window):
    """En Windows, marca la ventana como WS_EX_TRANSPARENT (los clicks
    pasan a la ventana de debajo, p.ej. Roblox)."""
    if sys.platform != "win32":
        return
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
    user32 = ctypes.windll.user32
    hwnd = user32.GetParent(window.winfo_id())
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(
        hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT
    )


# ============== Menú F5 — panel persistente con segmented controls ==============

# Colores estilo macOS dark
_BG       = "#1c1c1e"
_BG_BTN   = "#2c2c2e"
_BG_HOVER = "#3a3a3c"
_BG_SEL   = "#0a84ff"     # azul Apple system
_FG       = "white"
_FG_DIM   = "#9b9b9e"
_FG_RED   = "#ff453a"


def _segment_specs():
    """(key, título_sección, opciones, getter_idx, setter_idx)
    Función para que las lambdas lean los globals al vuelo."""
    return [
        ("floor",    "Floor",         ["Floor 1", "Floor 2"],
         lambda: floor - 1,
         lambda i: set_floor(i + 1)),
        ("position", "Posición",      ["Izquierda", "Centro", "Derecha"],
         lambda: ["left", "center", "right"].index(position),
         lambda i: set_position(["left", "center", "right"][i])),
        ("size",     "Tamaño",        ["Pastilla", "Círculo"],
         lambda: 1 if is_minimized else 0,
         lambda i: set_minimize(i == 1)),
        ("opacity",  "Transparencia", ["Opaco", "Translúcido", "Fantasma"],
         lambda: opacity_idx,
         lambda i: set_opacity(i)),
    ]


def _menu_status_text():
    return (
        f"Floor {floor}  ·  {POSITION_LABELS_ES[position]}  ·  "
        f"{'círculo' if is_minimized else 'pastilla'}  ·  "
        f"{OPACITY_NAMES[opacity_idx]}"
    )


def _on_close_program():
    """Cerrar el programa entero desde el botón rojo del panel."""
    global menu
    if menu is not None:
        menu.destroy()
        menu = None
    if root is not None:
        root.destroy()
    sys.exit(0)


def _on_dismiss_menu():
    """Ocultar (no destruir) el panel."""
    if menu is not None:
        menu.withdraw()


def _make_segmented_row(parent, options, current_idx, on_change):
    """Crea una fila de botones que actúan como segmented control.
    Devuelve (frame, lista_de_botones)."""
    row = tk.Frame(parent, bg=_BG)
    btns = []
    for i, label in enumerate(options):
        sel = (i == current_idx)
        btn = tk.Button(
            row, text=label,
            command=lambda i=i: on_change(i),
            bg=_BG_SEL if sel else _BG_BTN,
            fg=_FG,
            activebackground=_BG_SEL if sel else _BG_HOVER,
            activeforeground=_FG,
            bd=0, relief="flat", font=("Segoe UI", 10),
            padx=6, pady=6,
        )
        btn.pack(side="left", expand=True, fill="x", padx=1)
        btns.append(btn)
    return row, btns


def build_menu():
    """Construye el panel UNA vez. Después se muestra/oculta con withdraw/deiconify."""
    global menu, menu_status_label, menu_segments
    if root is None:
        return

    menu = tk.Toplevel(root)
    menu.title("Doors Counter")
    menu.attributes("-topmost", True)
    menu.resizable(False, False)
    menu.configure(bg=_BG)
    menu.protocol("WM_DELETE_WINDOW", _on_dismiss_menu)
    menu.bind("<Escape>", lambda e: _on_dismiss_menu())

    # --- Header ---
    header = tk.Frame(menu, bg=_BG)
    header.pack(fill="x", padx=16, pady=(14, 8))

    tk.Label(
        header, text="Doors Counter",
        bg=_BG, fg=_FG, font=("Segoe UI", 14, "bold"),
    ).pack(anchor="w")

    menu_status_label = tk.Label(
        header, text=_menu_status_text(),
        bg=_BG, fg=_FG_DIM, font=("Segoe UI", 9),
    )
    menu_status_label.pack(anchor="w", pady=(2, 0))

    # --- Segmented sections ---
    menu_segments = {}
    sections_frame = tk.Frame(menu, bg=_BG)
    sections_frame.pack(fill="x", padx=16, pady=(4, 4))

    for key, title, options, getter, setter in _segment_specs():
        section = tk.Frame(sections_frame, bg=_BG)
        section.pack(fill="x", pady=(8, 0))
        tk.Label(
            section, text=title,
            bg=_BG, fg=_FG_DIM, font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        row, btns = _make_segmented_row(section, options, getter(), setter)
        row.pack(fill="x")
        menu_segments[key] = btns

    # --- Separador ---
    tk.Frame(menu, bg="#2c2c2e", height=1).pack(fill="x", padx=16, pady=(14, 8))

    # --- Botones de acción ---
    actions = tk.Frame(menu, bg=_BG)
    actions.pack(fill="x", padx=16, pady=(0, 14))

    def _make_action_btn(text, cmd, danger=False):
        fg = _FG_RED if danger else _FG
        btn = tk.Button(
            actions, text=text, command=cmd,
            bg=_BG_BTN, fg=fg,
            activebackground=_BG_HOVER, activeforeground=fg,
            bd=0, relief="flat", font=("Segoe UI", 10),
            padx=0, pady=8,
        )
        btn.pack(fill="x", pady=2)
        btn.bind("<Enter>", lambda e: btn.config(bg=_BG_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=_BG_BTN))
        return btn

    _make_action_btn("Resetear contador", reset_counter)
    _make_action_btn("Cerrar programa",   _on_close_program, danger=True)

    # Centrar en pantalla la primera vez
    menu.update_idletasks()
    w, h = menu.winfo_width(), menu.winfo_height()
    sw, sh = menu.winfo_screenwidth(), menu.winfo_screenheight()
    menu.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    # Empezar oculto — toggle_menu lo muestra
    menu.withdraw()


def update_menu_state():
    """Refresca el header y los segmented controls (resaltado del seleccionado)."""
    if menu is None or menu_status_label is None:
        return
    try:
        menu_status_label.config(text=_menu_status_text())
        for key, _title, _opts, getter, _setter in _segment_specs():
            btns = menu_segments.get(key)
            if not btns:
                continue
            current = getter()
            for i, btn in enumerate(btns):
                sel = (i == current)
                btn.config(
                    bg=_BG_SEL if sel else _BG_BTN,
                    activebackground=_BG_SEL if sel else _BG_HOVER,
                )
    except tk.TclError:
        # El menú fue destruido (e.g. al cerrar el programa). Ignorar.
        pass


def toggle_menu():
    """F5: si el panel está oculto lo muestra; si está visible lo oculta."""
    if menu is None:
        build_menu()
    if menu is None:                     # build falló (root no existía)
        return
    if menu.state() == "withdrawn":
        update_menu_state()
        menu.deiconify()
        menu.lift()
        menu.focus_force()
    else:
        menu.withdraw()


# ============== Hooks globales (pynput) ==============

def _on_click(x, y, button, pressed):
    if not pressed:
        return
    name = getattr(button, "name", str(button))
    # En Windows pynput nombra los botones laterales como x1 / x2.
    if name in ("x2", "button8"):
        increment()
    elif name in ("x1", "button9"):
        decrement()
    elif name == "middle":
        cycle_floor()


def _start_mouse_listener():
    listener = mouse.Listener(on_click=_on_click)
    listener.daemon = True
    listener.start()
    return listener


def _start_hotkeys():
    def _safe(fn):
        return lambda: root.after(0, fn) if root else None

    hotkeys = {
        "<ctrl>+<alt>+0": _safe(reset_counter),
        "<ctrl>+<alt>+9": _safe(decrement),
        "<ctrl>+<alt>+=": _safe(increment),
        "<ctrl>+<alt>+f": _safe(cycle_floor),
        "<ctrl>+<alt>+p": _safe(cycle_position),
        "<ctrl>+<alt>+t": _safe(cycle_opacity),
        "<f5>":           _safe(toggle_menu),
    }
    listener = keyboard.GlobalHotKeys(hotkeys)
    listener.daemon = True
    listener.start()
    return listener


# ============== Main ==============

def main():
    build_window()
    update_labels()
    _start_mouse_listener()
    _start_hotkeys()
    root.mainloop()


if __name__ == "__main__":
    main()
