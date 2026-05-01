# DoorsCounter — Mac (PyObjC) · estilo Dynamic Island
# ====================================================
# Requisitos: pip install pyobjc
# Permisos:   System Settings → Privacy & Security → Accessibility →
#             activa PyCharm (o Terminal) para que funcionen los hotkeys.
#
# CONTROLES
#   Mouse 4   /  Cmd+Alt+=   → +1 puerta
#   Mouse 5   /  Cmd+Alt+9   → -1 puerta
#   Click rueda / Cmd+Alt+F  → cambiar Floor 1 ↔ 2
#   Cmd+Alt+0                → reset
#   Cmd+Alt+P                → cambiar posición (centro / derecha / izquierda)
#   Cmd+Alt+T                → cambiar transparencia
#   F5                       → menú (cerrar / resetear / minimizar / mover / transparencia / cancelar)

import sys
import objc
from Foundation import NSObject, NSMakePoint
from AppKit import (
    NSApplication, NSApplicationActivationPolicyAccessory,
    NSWindow, NSWindowStyleMaskBorderless, NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable, NSBackingStoreBuffered,
    NSFloatingWindowLevel, NSColor, NSTextField, NSFont,
    NSMakeRect, NSScreen, NSEvent, NSEventMaskKeyDown,
    NSRunningApplication, NSApplicationActivateIgnoringOtherApps,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSTextAlignmentCenter, NSButton, NSBezelStyleRounded,
    NSSegmentedControl, NSSegmentStyleRounded,
    NSSegmentSwitchTrackingSelectOne, NSBox, NSBoxSeparator,
)
from Quartz import (
    CGEventTapCreate, kCGHIDEventTap, kCGHeadInsertEventTap,
    kCGEventTapOptionDefault, kCGEventOtherMouseDown,
    CGEventMaskBit, CGEventTapEnable, CGEventGetIntegerValueField,
    kCGMouseEventButtonNumber, CFMachPortCreateRunLoopSource,
    CFRunLoopAddSource, CFRunLoopGetCurrent, kCFRunLoopCommonModes,
)


# ============== Look (Dynamic Island) ==============
PILL_W = 220        # ancho en modo pastilla
PILL_H = 64         # alto en ambos modos
CIRCLE_D = 64       # diámetro del círculo cuando está minimizado
TOP_MARGIN = 8      # separación desde el borde superior
SIDE_MARGIN = 20    # separación de los bordes laterales (modo izquierda/derecha)
BG_ALPHA = 0.95     # casi opaco
FONT_SIZE_MAIN = 32
FONT_SIZE_FLOOR = 11
CONSUME_CLICKS = True
# ===================================================

POSITIONS = ("center", "right", "left")
POSITION_LABELS_ES = {
    "center": "centro",
    "right":  "derecha",
    "left":   "izquierda",
}

OPACITY_LEVELS = (0.95, 0.6, 0.35)
OPACITY_NAMES = ("opaco", "translúcido", "fantasma")
opacity_idx = 0

count = 0
floor = 1                # 1 = Hotel, 2 = Mines/Floor 2
is_minimized = False     # False = pastilla, True = círculo
position = "center"      # "center" | "right" | "left"
label_main = None
label_floor = None
window = None

# Panel del menú (se construye perezosamente la primera vez que se abre)
menu_window = None
menu_target = None
menu_status_label = None
menu_segments = {}       # key ("floor"/"position"/"size"/"opacity") -> NSSegmentedControl


def update_labels():
    if label_main:
        label_main.setStringValue_(str(count))
    if label_floor:
        label_floor.setStringValue_(f"FLOOR {floor}")


def set_floor(new_floor):
    """Cambia entre Floor 1 y Floor 2 manteniendo la lógica original."""
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


# ============== Layout ==============

def _compute_x(screen_w, w):
    """Devuelve la X para colocar la ventana según `position`."""
    if position == "left":
        return SIDE_MARGIN
    if position == "right":
        return screen_w - w - SIDE_MARGIN
    return (screen_w - w) / 2.0   # center


def relayout():
    """Coloca la ventana y los labels según is_minimized y position.

    En modo pastilla:  número arriba (centrado vertical) + FLOOR debajo.
    En modo círculo:   solo número, centrado en un disco.
    """
    if window is None:
        return

    screen = NSScreen.mainScreen().frame()
    if is_minimized:
        w = h = CIRCLE_D
    else:
        w, h = PILL_W, PILL_H

    x = _compute_x(screen.size.width, w)
    y = screen.size.height - h - TOP_MARGIN          # pegada arriba
    window.setFrame_display_(NSMakeRect(x, y, w, h), True)

    # Radio de esquina = altura / 2 → pastilla o círculo perfecto
    window.contentView().layer().setCornerRadius_(h / 2.0)

    # Actualizar color de fondo con transparencia actual
    window.contentView().layer().setBackgroundColor_(
        NSColor.colorWithCalibratedWhite_alpha_(0.0, OPACITY_LEVELS[opacity_idx]).CGColor()
    )

    if is_minimized:
        # Solo número, vertical-centrado dentro del círculo.
        label_main.setFrame_(NSMakeRect(0, h * 0.22, w, h * 0.56))
        label_floor.setHidden_(True)
    else:
        # Número subido un poco (top padding ~ bottom padding).
        # Floor debajo, atenuado (estilo subtítulo del Dynamic Island).
        label_main.setFrame_(NSMakeRect(0, h * 0.36, w, h * 0.55))
        label_floor.setFrame_(NSMakeRect(0, h * 0.10, w, h * 0.20))
        label_floor.setHidden_(False)


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
    """Cicla entre 3 niveles de transparencia."""
    global opacity_idx
    opacity_idx = (opacity_idx + 1) % len(OPACITY_LEVELS)
    relayout()
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
        relayout()
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

def make_window():
    global window
    win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(0, 0, PILL_W, PILL_H),
        NSWindowStyleMaskBorderless,
        NSBackingStoreBuffered,
        False,
    )
    win.setLevel_(NSFloatingWindowLevel)
    win.setOpaque_(False)
    win.setBackgroundColor_(NSColor.clearColor())
    win.setIgnoresMouseEvents_(True)         # click-through hacia Roblox
    win.setCollectionBehavior_(
        NSWindowCollectionBehaviorCanJoinAllSpaces
        | NSWindowCollectionBehaviorFullScreenAuxiliary
    )

    cv = win.contentView()
    cv.setWantsLayer_(True)
    cv.layer().setBackgroundColor_(
        NSColor.colorWithCalibratedWhite_alpha_(0.0, OPACITY_LEVELS[opacity_idx]).CGColor()
    )
    # Sin esto los subviews pueden dibujar fuera del pill cuando hay textos largos
    cv.layer().setMasksToBounds_(True)

    # Labels (la posición real se aplica en relayout())
    global label_main, label_floor

    label_main = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, PILL_W, PILL_H))
    label_main.setEditable_(False)
    label_main.setSelectable_(False)
    label_main.setBezeled_(False)
    label_main.setBordered_(False)
    label_main.setDrawsBackground_(False)
    label_main.setTextColor_(NSColor.whiteColor())
    # Asegurar centrado tanto en el field como en su cell — algunos builds de
    # PyObjC sólo respetan uno de los dos.
    label_main.setAlignment_(NSTextAlignmentCenter)
    label_main.cell().setAlignment_(NSTextAlignmentCenter)
    try:
        font_main = NSFont.monospacedDigitSystemFontOfSize_weight_(
            float(FONT_SIZE_MAIN), 0.6
        )
    except Exception:
        font_main = NSFont.systemFontOfSize_(float(FONT_SIZE_MAIN))
    label_main.setFont_(font_main)

    label_floor = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, PILL_W, 20))
    label_floor.setEditable_(False)
    label_floor.setSelectable_(False)
    label_floor.setBezeled_(False)
    label_floor.setBordered_(False)
    label_floor.setDrawsBackground_(False)
    label_floor.setTextColor_(
        NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.55)
    )
    label_floor.setAlignment_(NSTextAlignmentCenter)
    label_floor.cell().setAlignment_(NSTextAlignmentCenter)
    label_floor.setFont_(NSFont.systemFontOfSize_(float(FONT_SIZE_FLOOR)))

    cv.addSubview_(label_main)
    cv.addSubview_(label_floor)

    window = win
    relayout()
    win.makeKeyAndOrderFront_(None)
    return win


# ============== Menú F5 — panel persistente con segmented controls ==============

# Cada fila del menú es un selector segmentado (un click = una opción directa,
# no cíclica). Estructura: (key, título_sección, opciones, getter_idx, setter_idx)
def _segment_specs():
    """Devuelto como función para que las lambdas lean los globals al vuelo."""
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


class MenuTarget(NSObject):
    """Receptor de los clicks de segmented controls + botones del panel.
    PyObjC infiere los selectores ObjC a partir del nombre Python:
    `closeProgram_` (Python) → `closeProgram:` (selector ObjC, un arg sender)."""

    def segmentChanged_(self, sender):
        # Identifica de qué fila viene el evento por referencia al sender.
        for key, _label, _opts, _getter, setter in _segment_specs():
            if menu_segments.get(key) is sender:
                setter(sender.selectedSegment())
                break

    def resetCounter_(self, sender):
        global count
        count = 0
        update_labels()
        update_menu_state()

    def closeProgram_(self, sender):
        NSApplication.sharedApplication().terminate_(None)


def _make_section_label(text, frame):
    label = NSTextField.alloc().initWithFrame_(frame)
    label.setStringValue_(text)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setBezeled_(False)
    label.setBordered_(False)
    label.setDrawsBackground_(False)
    label.setFont_(NSFont.boldSystemFontOfSize_(11.0))
    label.setTextColor_(NSColor.secondaryLabelColor())
    return label


def build_menu():
    """Construye la ventana del panel una sola vez (lazy)."""
    global menu_window, menu_target, menu_status_label, menu_segments

    menu_target = MenuTarget.alloc().init()

    PANEL_W = 320
    PADDING = 16
    SECTION_LABEL_H = 16
    SEG_H = 24
    SECTION_GAP = 14
    HEADER_H = 30

    specs = _segment_specs()
    sections_h = (
        len(specs) * (SECTION_LABEL_H + 4 + SEG_H) + (len(specs) - 1) * SECTION_GAP
    )
    SEPARATOR_H = 1
    SEP_GAP = 14
    BTN_H = 32
    BTN_GAP = 8
    n_action_btns = 2  # Reset + Cerrar programa
    actions_h = n_action_btns * BTN_H + (n_action_btns - 1) * BTN_GAP

    PANEL_H = (
        PADDING + HEADER_H + 8 +
        sections_h + SEP_GAP + SEPARATOR_H + SEP_GAP +
        actions_h + PADDING
    )

    win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(0, 0, PANEL_W, PANEL_H),
        NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
        NSBackingStoreBuffered, False,
    )
    win.setTitle_("Doors Counter")
    win.setLevel_(NSFloatingWindowLevel)
    win.setReleasedWhenClosed_(False)        # NO destruir al pulsar la X
    win.setHidesOnDeactivate_(False)

    screen = NSScreen.mainScreen().frame()
    win.setFrameOrigin_(NSMakePoint(
        (screen.size.width - PANEL_W) / 2,
        (screen.size.height - PANEL_H) / 2,
    ))

    cv = win.contentView()

    # --- Header (status text) ---
    y = PANEL_H - PADDING - HEADER_H
    menu_status_label = NSTextField.alloc().initWithFrame_(
        NSMakeRect(PADDING, y, PANEL_W - 2 * PADDING, HEADER_H)
    )
    menu_status_label.setEditable_(False)
    menu_status_label.setSelectable_(False)
    menu_status_label.setBezeled_(False)
    menu_status_label.setBordered_(False)
    menu_status_label.setDrawsBackground_(False)
    menu_status_label.setFont_(NSFont.systemFontOfSize_(11.0))
    menu_status_label.setTextColor_(NSColor.secondaryLabelColor())
    cv.addSubview_(menu_status_label)
    y -= 8

    # --- Segmented sections ---
    menu_segments = {}
    for i, (key, title, opts, getter, _setter) in enumerate(specs):
        # Section label
        y -= SECTION_LABEL_H
        cv.addSubview_(_make_section_label(
            title, NSMakeRect(PADDING, y, PANEL_W - 2 * PADDING, SECTION_LABEL_H)
        ))
        y -= 4

        # Segmented control
        y -= SEG_H
        seg = NSSegmentedControl.alloc().initWithFrame_(
            NSMakeRect(PADDING, y, PANEL_W - 2 * PADDING, SEG_H)
        )
        seg.setSegmentCount_(len(opts))
        seg_w = (PANEL_W - 2 * PADDING) / len(opts)
        for j, opt in enumerate(opts):
            seg.setLabel_forSegment_(opt, j)
            seg.setWidth_forSegment_(seg_w, j)
        seg.setSegmentStyle_(NSSegmentStyleRounded)
        seg.setTrackingMode_(NSSegmentSwitchTrackingSelectOne)
        seg.setSelectedSegment_(getter())
        seg.setTarget_(menu_target)
        seg.setAction_("segmentChanged:")
        cv.addSubview_(seg)
        menu_segments[key] = seg

        if i < len(specs) - 1:
            y -= SECTION_GAP

    # --- Separator ---
    y -= SEP_GAP + SEPARATOR_H
    sep = NSBox.alloc().initWithFrame_(
        NSMakeRect(PADDING, y, PANEL_W - 2 * PADDING, SEPARATOR_H)
    )
    sep.setBoxType_(NSBoxSeparator)
    cv.addSubview_(sep)
    y -= SEP_GAP

    # --- Action buttons ---
    y -= BTN_H
    reset_btn = NSButton.alloc().initWithFrame_(
        NSMakeRect(PADDING, y, PANEL_W - 2 * PADDING, BTN_H)
    )
    reset_btn.setBezelStyle_(NSBezelStyleRounded)
    reset_btn.setTitle_("Resetear contador")
    reset_btn.setTarget_(menu_target)
    reset_btn.setAction_("resetCounter:")
    cv.addSubview_(reset_btn)

    y -= (BTN_GAP + BTN_H)
    close_btn = NSButton.alloc().initWithFrame_(
        NSMakeRect(PADDING, y, PANEL_W - 2 * PADDING, BTN_H)
    )
    close_btn.setBezelStyle_(NSBezelStyleRounded)
    close_btn.setTitle_("Cerrar programa")
    close_btn.setTarget_(menu_target)
    close_btn.setAction_("closeProgram:")
    # Tinte rojo nativo (macOS 11+)
    try:
        close_btn.setBezelColor_(NSColor.systemRedColor())
    except Exception:
        pass
    cv.addSubview_(close_btn)

    menu_window = win
    update_menu_state()


def update_menu_state():
    """Refresca el header y la selección de cada segmented control."""
    if menu_status_label is None:
        return
    menu_status_label.setStringValue_(
        f"Floor {floor}   ·   {POSITION_LABELS_ES[position]}   ·   "
        f"{'círculo' if is_minimized else 'pastilla'}   ·   "
        f"{OPACITY_NAMES[opacity_idx]}"
    )
    for key, _title, _opts, getter, _setter in _segment_specs():
        seg = menu_segments.get(key)
        if seg is not None:
            current = getter()
            if seg.selectedSegment() != current:
                seg.setSelectedSegment_(current)


def toggle_menu():
    """F5: si el panel está oculto lo muestra; si está visible lo oculta."""
    if menu_window is None:
        build_menu()
    if menu_window.isVisible():
        menu_window.orderOut_(None)
    else:
        update_menu_state()
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        menu_window.makeKeyAndOrderFront_(None)


# ============== Ratón (Mouse4 / Mouse5 / rueda) ==============

def mouse_callback(proxy, type_, event, refcon):
    """Mouse 4 (+1), Mouse 5 (-1), Click rueda → alterna Floor."""
    global count, floor
    if type_ == kCGEventOtherMouseDown:
        btn = CGEventGetIntegerValueField(event, kCGMouseEventButtonNumber)
        if btn == 4:
            count += 1
            update_labels()
            return None if CONSUME_CLICKS else event
        elif btn == 3:                       # Mouse 5 en macOS suele ser btn 3
            count = max(0, count - 1)
            update_labels()
            return None if CONSUME_CLICKS else event
        elif btn == 2:                       # rueda
            set_floor(2 if floor == 1 else 1)
            return None if CONSUME_CLICKS else event
    return event


def start_mouse_tap():
    mask = CGEventMaskBit(kCGEventOtherMouseDown)
    tap = CGEventTapCreate(
        kCGHIDEventTap, kCGHeadInsertEventTap, kCGEventTapOptionDefault,
        mask, mouse_callback, None,
    )
    if not tap:
        print(
            "No se pudo crear el EventTap.\n"
            "Activa permisos en: System Settings → Privacy & Security → Accessibility",
            file=sys.stderr,
        )
        sys.exit(1)
    CGEventTapEnable(tap, True)
    src = CFMachPortCreateRunLoopSource(None, tap, 0)
    CFRunLoopAddSource(CFRunLoopGetCurrent(), src, kCFRunLoopCommonModes)
    return tap


# ============== Hotkeys globales ==============

def handle_hotkeys(event):
    """F5 abre menú; Cmd+Alt+0/9/=/F/P/T controlan el contador, la posición y transparencia."""
    global count, floor

    # F5 (keyCode 96) sin modificadores → abre/cierra el panel
    try:
        if event.keyCode() == 96:
            toggle_menu()
            return None
    except Exception:
        pass

    mods = event.modifierFlags() & 0x18      # cmd(0x10) + alt(0x08)
    if mods == 0x18:
        k = event.charactersIgnoringModifiers() or ""
        if k == "0":
            count = 0
            update_labels(); return None
        elif k == "9":
            count = max(0, count - 1)
            update_labels(); return None
        elif k == "=":
            count += 1
            update_labels(); return None
        elif k.lower() == "f":
            set_floor(2 if floor == 1 else 1)
            return None
        elif k.lower() == "p":
            cycle_position()
            return None
        elif k.lower() == "t":
            cycle_opacity()
            return None
    return event


# ============== Main ==============

def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    make_window()
    set_floor(1)
    start_mouse_tap()
    NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
        NSEventMaskKeyDown, handle_hotkeys
    )

    NSRunningApplication.currentApplication().activateWithOptions_(
        NSApplicationActivateIgnoringOtherApps
    )
    app.run()


if __name__ == "__main__":
    main()
