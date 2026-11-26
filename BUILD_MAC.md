# Building the Mac App

These steps turn the simulator into a normal Mac app (`HillMuscleSim.app`) that you can double-click. You only need to install Python for the build. Once the app is built, it runs without Python.

It takes about 10–15 minutes the first time. You'll type commands into **Terminal**: press `Cmd + Space`, type **Terminal**, and press Enter. Paste each command and press Enter.

The app is built for the type of Mac you build it on. A build made on an Apple Silicon Mac (M1 or newer) runs on Apple Silicon Macs, and a build made on an Intel Mac runs on Intel Macs.

---

## 1. Install Python

Check whether you already have Python 3.11 or newer:

```bash
python3 --version
```

If it prints `Python 3.11` or higher (3.13 is recommended), go to step 2.

Otherwise, download the macOS installer from [python.org/downloads](https://www.python.org/downloads/), run it, then close and reopen Terminal and run `python3 --version` again.

> If you use Homebrew, `brew install python@3.13` also works.

---

## 2. Get the code

**Option A: download a ZIP (no Git needed).** On the GitHub page, click **Code → Download ZIP** and double-click the downloaded file to unzip it. Then in Terminal:

```bash
cd ~/Downloads/BMG5112-Sim-main
```

**Option B: with Git.**

```bash
cd ~/Documents
git clone https://github.com/RaiyanAfiz/BMG5112-Sim.git
cd BMG5112-Sim
```

> If your Mac asks to install "command line developer tools", click **Install**, wait for it to finish, then run the `git clone` command again.

Run all of the following commands from inside this folder.

---

## 3. Create a separate Python environment

This keeps the project's libraries separate from anything else on your Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your Terminal prompt should now start with `(.venv)`. If you close Terminal and come back later, `cd` into the folder and run `source .venv/bin/activate` again.

---

## 4. Install the libraries

```bash
pip install --upgrade pip
pip install -r requirements.txt pyinstaller
```

This downloads PyQt6, matplotlib, numpy and PyInstaller, which can take a few minutes.

---

## 5. Test the simulator (optional but recommended)

```bash
python app.py
```

The simulator window should open. Move a few sliders to check it works, then close the window.

---

## 6. Build the app

```bash
pyinstaller --noconfirm --windowed --name HillMuscleSim app.py
```

This takes 1–3 minutes and prints a lot of text. When it finishes, the app is at:

```
dist/HillMuscleSim.app
```

To open that folder in Finder:

```bash
open dist
```

Drag **HillMuscleSim** into your **Applications** folder if you like.

---

## 7. Open it the first time

The app isn't signed by Apple, so macOS blocks it the first time you open it. To allow it:

1. Double-click **HillMuscleSim**. macOS says it can't be opened. Click **Done** or **Cancel**.
2. Open **System Settings → Privacy & Security**, scroll down, and click **Open Anyway** next to the HillMuscleSim message.
3. Confirm with your password or Touch ID.

On older macOS versions you can instead **right-click** (or Control-click) the app, choose **Open**, then click **Open** again.

You only need to do this once.

---

## Sharing the app with another Mac

Zip it like this so the app isn't damaged in the process:

```bash
ditto -c -k --keepParent dist/HillMuscleSim.app HillMuscleSim-mac.zip
```

Send `HillMuscleSim-mac.zip`. The other person unzips it and follows step 7. Their Mac must be the same type as yours (Apple Silicon or Intel).

If macOS says the app **"is damaged and can't be opened"**, run this once in Terminal (adjust the path if the app isn't in Applications):

```bash
xattr -dr com.apple.quarantine /Applications/HillMuscleSim.app
```

---

## Rebuilding after the code changes

```bash
cd path/to/BMG5112-Sim
git pull                         # or download the ZIP again
source .venv/bin/activate
pip install -r requirements.txt  # in case the libraries changed
pyinstaller --noconfirm --windowed --name HillMuscleSim app.py
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `command not found: python` | Use `python3` for step 3. Inside the environment, `python` works. |
| `command not found: pyinstaller` | The environment isn't active. Run `source .venv/bin/activate` and try again. |
| `pip install` fails with "No matching distribution found for …" | That pinned version isn't available for your Mac or Python version. Open `requirements.txt`, change that line from `==` to `>=` (e.g. `PyQt6>=6.7`), and run step 4 again. |
| The app bounces in the Dock and closes | Run it from Terminal to see the error message: `./dist/HillMuscleSim.app/Contents/MacOS/HillMuscleSim` |
| Text or buttons look wrong | Make sure you have the latest code (`git pull`) and rebuild. |
