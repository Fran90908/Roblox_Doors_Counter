# DoorsCounter

A counter for **Roblox Doors** with a floating pill in the style of Apple's
**Dynamic Island**. Works on **macOS** and **Windows**.

![Dynamic Island style — black pill at top center](docs/screenshot.png)

## Why I made this

I built this to keep track of door numbers while running the **Dupe** modifier
on **max difficulty**. At that combo, counting in your head is impossible —
and thanks to this counter, I finally beat **Hotel Hell**.

## Features

- Always-on-top black pill, click-through (clicks pass through to the game).
- Supports Floor 1 (Hotel 1–100) and Floor 2 (Mines 100–200).
- Global hotkeys — work even with Roblox in fullscreen.
- `F5` menu to close, reset, minimize, move, or change opacity without killing the process.

## Hotkeys

| Action               | Mac                | Windows                |
|----------------------|--------------------|------------------------|
| +1 door              | Mouse 4 / `⌘⌥=`    | Mouse 4 / `Ctrl+Alt+=` |
| −1 door              | Mouse 5 / `⌘⌥9`    | Mouse 5 / `Ctrl+Alt+9` |
| Switch Floor 1 ↔ 2   | Wheel click / `⌘⌥F`| Wheel click / `Ctrl+Alt+F` |
| Reset counter        | `⌘⌥0`              | `Ctrl+Alt+0`           |
| Open menu            | `F5`               | `F5`                   |

## Install

### macOS — from source

```bash
git clone https://github.com/Fran90908/Roblox_Doors_Counter.git
cd Roblox_Doors_Counter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-mac.txt
python DoorsCounter.py
```

> **Important:** the first time, macOS will ask for Accessibility permission.
> Go to *System Settings → Privacy & Security → Accessibility* and enable
> the Python interpreter (or PyCharm/Terminal, depending on where you launch it from).

### macOS — build the .app yourself

```bash
./build_mac.command
```

When it finishes, the app is in `dist/DoorsCounter.app`.

### Windows — use the .exe

Download `DoorsCounter.exe` from the **Releases** tab of the repo and
double-click it. No Python needed.

### Windows — from source

```cmd
git clone https://github.com/Fran90908/Roblox_Doors_Counter.git
cd Roblox_Doors_Counter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-windows.txt
python DoorsCounter_windows.py
```

### Windows — build the .exe yourself

```cmd
build_windows.bat
```

When it finishes, the executable is in `dist\DoorsCounter.exe`.

## Releases

Push a tag like `v0.1.0` and GitHub Actions builds the `.exe` (Windows) and
`.app` (macOS) automatically and attaches both to a new GitHub Release.

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Project files

| File                          | What it's for                                   |
|-------------------------------|-------------------------------------------------|
| `DoorsCounter.py`             | Mac version (PyObjC, native click-through)      |
| `DoorsCounter_windows.py`     | Windows version (tkinter + pynput)              |
| `requirements-mac.txt`        | Mac dependencies (`pyobjc`)                     |
| `requirements-windows.txt`    | Windows dependencies (`pynput`)                 |
| `build_mac.command`           | Builds the `.app` with PyInstaller              |
| `build_windows.bat`           | Builds the `.exe` with PyInstaller              |
| `.github/workflows/release.yml` | CI workflow that builds both on every `v*` tag |
