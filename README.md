# Telegram Circular Frame Bot

This project is a complete Telegram bot for **@Frameioet_bot**.

## What it does

1. A user sends a portrait photo to the bot.
2. The bot downloads the photo.
3. OpenCV tries to find the largest face.
4. The photo is automatically scaled and positioned so the face sits in the same general position as the supplied second reference.
5. The photo is clipped with a circular mask.
6. The clipped photo is inserted into the circular photo area of the supplied first template.
7. The original template graphics outside that circle stay unchanged.
8. The bot sends the finished PNG back to the user.

The project already contains your template as:

`templates/template.png`

and your second image as:

`templates/reference.png`

## Important: Telegram bot username vs token

The bot username **@Frameioet_bot** is not enough to run a program.

You need the bot's **HTTP API token** from Telegram's **@BotFather**.

Do not put the token directly into `bot.py`, and do not publish `.env`.

---

# Windows + VS Code setup

## 1. Install Python

Use Python 3.11 or 3.12 on Windows.

Check:

```powershell
python --version
```

If `python` is not recognized, install Python and enable **Add Python to PATH**.

## 2. Open the project in VS Code

Extract the ZIP and open the folder:

`telegram_frame_bot`

in VS Code.

## 3. Create a virtual environment

Open the VS Code terminal:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

then:

```powershell
.venv\Scripts\Activate.ps1
```

## 4. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Add your Telegram token

Copy:

`.env.example`

to:

`.env`

Then edit `.env`:

```env
BOT_TOKEN=123456789:YOUR_REAL_BOT_TOKEN
```

Get the token from Telegram's @BotFather.

## 6. Test the image processor

Run:

```powershell
python test_process.py
```

It should create:

`test-output.png`

The supplied `reference.png` is only used as a smoke-test input. For the actual bot, users send normal portrait photos.

## 7. Start the bot

```powershell
python bot.py
```

You should see:

```text
Bot is running. Press Ctrl+C to stop.
```

Now open Telegram, find **@Frameioet_bot**, press Start, and send a portrait photo.

---

# How the cropping works

The circular frame is configured in `config.json`:

```json
"circle": {
  "center_x": 196,
  "center_y": 514,
  "radius": 399
}
```

The target face position is:

```json
"face_target": {
  "center_x": 235,
  "center_y": 315,
  "width": 210
}
```

If you send a normal portrait photo, the program attempts to:

- detect the largest face
- scale the photo based on face width
- move the face to the target position
- keep the rest of the person/body flowing downward
- clip everything to the circular frame

This is why different portrait photos can still be positioned consistently.

## If the face is not detected

The program uses a fallback crop. It will still fill the circle, but positioning can be less precise.

For best results, send:

- one person
- face looking roughly toward the camera
- clear face
- good lighting
- enough torso/body below the face
- portrait-oriented photo when possible

---

# Adjusting the template

If you later replace the template with another 1080x1080 design, edit:

`templates/template.png`

Then adjust the circle values in:

`config.json`

For example:

```json
"circle": {
  "center_x": 196,
  "center_y": 514,
  "radius": 399
}
```

The coordinate system starts at the top-left:

- X increases to the right.
- Y increases downward.
- All measurements are in pixels.

## Adjusting the person's position

Change:

```json
"face_target": {
  "center_x": 235,
  "center_y": 315,
  "width": 210
}
```

- Increase `center_x` → move the person right.
- Decrease `center_x` → move the person left.
- Increase `center_y` → move the person down.
- Decrease `center_y` → move the person up.
- Increase `width` → make the face/person larger.
- Decrease `width` → make the face/person smaller.

---

# Security

Never share your `.env` file or bot token.

If your token is accidentally exposed, revoke it through @BotFather and create a new token.

---

# Project structure

```text
telegram_frame_bot/
│
├── bot.py
├── processor.py
├── config.json
├── requirements.txt
├── .env.example
├── .gitignore
├── test_process.py
├── README.md
│
└── templates/
    ├── template.png
    └── reference.png
```

## Run commands

After the initial installation, the normal workflow is simply:

```powershell
.venv\Scripts\Activate.ps1
python bot.py
```

Keep that terminal open while the bot is running.

For 24/7 hosting, deploy the same project to a Python-capable server and run `python bot.py`.


## Corrected version
This version fixes the oversized photo compositing issue and includes `test_portrait.py` for local testing.


## Important: PIL-only version

This version intentionally does **not** use OpenCV/cv2 or NumPy.
If you previously installed OpenCV, it is no longer required.

From the project folder run:

```powershell
..\.venv\Scripts\python.exe -m pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python numpy
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then test:

```powershell
..\.venv\Scripts\python.exe test_process.py
```

Then start:

```powershell
..\.venv\Scripts\python.exe bot.py
```
