# Roblox Doors Counter

A counter for **Roblox Doors** with a floating pill in the style of Apple's
**Dynamic Island**. Works on **macOS** and **Windows**.

![Dynamic Island style — black pill at top center](docs/screenshot.png)

## Why I made this

I built this to keep track of door numbers while running the **Dupe** modifier
on **max difficulty**. At that combo, counting in your head is impossible —
and thanks to this counter, I finally beat **Hotel Hell**.

## Download

Get the latest version from the **[Releases page](https://github.com/Fran90908/Roblox_Doors_Counter/releases/latest)**.
No Python, no setup — just download and open.

| OS      | File                       | What to do                          |
|---------|----------------------------|-------------------------------------|
| Windows | `DoorsCounter.exe`         | Double-click.                       |
| macOS   | `DoorsCounter-macos.zip`   | Unzip, open `DoorsCounter.app`.     |

### First-launch warnings (one time only)

- **macOS:** right-click the app → **Open** → **Open** in the dialog. Then
  macOS will ask for Accessibility permission so the hotkeys work — grant it
  in *System Settings → Privacy & Security → Accessibility*.
- **Windows:** SmartScreen says "Windows protected your PC" → **More info** →
  **Run anyway**. (The app isn't code-signed because signing certificates cost
  money — but the source is right here, you can build it yourself if you want.)

## Features

- Always-on-top black pill, click-through (clicks pass through to the game).
- Supports Floor 1 (Hotel 1–100) and Floor 2 (Mines 100–200).
- Global hotkeys — work even with Roblox in fullscreen.
- `F5` opens a settings panel with one-click selectors for floor, position,
  size, and opacity. Stays open while you change things.

## Hotkeys

| Action               | Mac                 | Windows                    |
|----------------------|---------------------|----------------------------|
| +1 door              | Mouse 4 / `⌘⌥=`     | Mouse 4 / `Ctrl+Alt+=`     |
| −1 door              | Mouse 5 / `⌘⌥9`     | Mouse 5 / `Ctrl+Alt+9`     |
| Switch Floor 1 ↔ 2   | Wheel click / `⌘⌥F` | Wheel click / `Ctrl+Alt+F` |
| Reset counter        | `⌘⌥0`               | `Ctrl+Alt+0`               |
| Open settings panel  | `F5`                | `F5`                       |

## Build from source

<details>
<summary><b>macOS</b></summary>

Run from source:

```bash
git clone https://github.com/Fran90908/Roblox_Doors_Counter.git
cd Roblox_Doors_Counter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-mac.txt
python DoorsCounter.py
```

Or build a standalone `.app` (output in `dist/DoorsCounter.app`):

```bash
./build_mac.command
```

</details>

<details>
<summary><b>Windows</b></summary>

Run from source:

```cmd
git clone https://github.com/Fran90908/Roblox_Doors_Counter.git
cd Roblox_Doors_Counter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-windows.txt
python DoorsCounter_windows.py
```

Or build a standalone `.exe` (output in `dist\DoorsCounter.exe`):

```cmd
build_windows.bat
```

</details>

---

Released under the [MIT License](LICENSE).
