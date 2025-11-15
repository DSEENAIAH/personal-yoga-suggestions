# Mental Health Yoga App

A Flask-based web application that provides personalized yoga flows based on emotional state and intensity levels.

## Features

- **Emotion-based yoga sequences**: 10 different emotions with customized flows
- **Intensity levels**: 1-5 scale for personalized difficulty
- **Interactive guided sessions**: Step-by-step instructions with timers
- **Progress tracking**: Real-time progress bars and session completion
- **Responsive design**: Works on desktop, tablet, and mobile devices
- **Accessibility**: WCAG compliant with screen reader support

## Project Structure

```
mental_health_yoga_app/
├── app.py                    # Main Flask application
├── models.py                 # SQLAlchemy database models
├── seed_data.py             # Database seeding script
├── requirements.txt         # Python dependencies
├── test_app.py             # API endpoint tests
├── test_models.py          # Model validation tests
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── emotion_selection.html
│   └── guided_flow.html
├── static/                 # Static files
│   ├── css/
│   │   └── style.css       # Main stylesheet
│   └── images/             # Yoga pose images
│       └── asanas/         # Individual pose images
└── *.json                  # Asana data files
```

## Setup Instructions

### Prerequisites

- Python 3.7+
 # Personal Yoga Suggestions

A small Flask app that recommends short yoga sequences based on the user's emotional state and intensity. Intended for personal or educational use.

How to use
 - Windows (one-click): run `run_app.bat` from the project root. It creates a `.venv`, installs dependencies, seeds the database if missing, and starts the dev server.
 - Manual (cross-platform): create and activate a virtualenv, run `pip install -r requirements.txt`, then `python seed_data.py` (once) and `python app.py` to start the server.

Open http://127.0.0.1:5000 in your browser.
---

## Quick overview

- Backend: Flask (see `app.py`) using SQLAlchemy models in `models.py`.
- Seed data: JSON files at project root (e.g. `cobra_pose.json`, `mountain_pose.json`) used by `seed_data.py`.
- Static assets: `static/images/asanas/` (pose overview + step images) and `static/css/style.css`.
- Templates: Jinja templates in `templates/` (guided session, chat, emotion selection).
- Automation: `run_app.bat` (Windows one-click runner) and `setup_nltk.py` (downloads required NLTK corpora).

---

## What changed (important notes)

- Images are expected to be served locally from `static/images/asanas/`. JSON files reference these local paths.
- A Windows automation script `run_app.bat` was added to create a virtual env, install requirements, download NLTK data, seed the database (first run), and start the Flask dev server.
- The codebase was updated to remove deprecated SQLAlchemy patterns and to prefer `overview_image` in the UI.

---

## Quick start (Windows - one click)

1. Open PowerShell, change directory to the project root:

```powershell
cd "c:\Users\Seenaiah\OneDrive\Documents\coading\IBM"
```

2. Run the one-click runner:

```powershell
.\run_app.bat
```

What the script does:
- Creates a `.venv` Virtualenv (if missing)
- Installs packages from `requirements.txt`
- Runs `setup_nltk.py` to download NLTK corpora (quiet)
- Seeds the SQLite DB using `seed_data.py` **only if** the DB is missing (so re-running won't overwrite data)
- Starts the Flask development server (listening on http://127.0.0.1:5000)

If you prefer manual setup, see the Manual section below.

---

## Manual setup (cross-platform)

1. Create and activate a virtual environment (example for Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. (One-time) download NLTK data used by TextBlob:

```powershell
python setup_nltk.py
```

4. Create the database and seed it:

```powershell
python seed_data.py
```

5. Run the app:

```powershell
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

---

## Project layout (short)

- `app.py` — Flask routes and analysis logic (emotion detection + endpoints)
- `models.py` — SQLAlchemy models for Asana, Sequence, Session, User
- `seed_data.py` — reads asana JSON files and populates SQLite DB (`yoga_app.db`)
- `run_app.bat` — Windows runner (creates `.venv`, installs deps, seeds DB if missing, launches app)
- `setup_nltk.py` — helper to download NLTK `punkt` used by TextBlob
- `static/images/asanas/` — pose images used by templates (overview + step images)
- `templates/` — HTML templates (guided flow, emotion selection, chat, voice)

---

## Testing

Run unit tests (if present) with unittest discover:

```powershell
python -m unittest discover -s . -p "test_*.py"
```

Note: Some tests were refactored to avoid network access at import time. If a test hits the network, ensure you have network access or skip it.

---

## Packaging / distribution

We include `run_app.bat` for Windows users. To create a zip for sharing, use PowerShell's `Compress-Archive`, excluding `.venv`:

```powershell
# from project root
Compress-Archive -Path * -DestinationPath ..\yoga-app-final.zip -CompressionLevel Optimal
```

When sharing, do NOT include `.venv` (virtual environment) or large raw image backups.

---



## Contributing

1. Fork the repo and create a feature branch
2. Add tests for any new behavior
3. Open a Pull Request and describe changes

---

## Troubleshooting

- If the app reports missing images, verify file paths in the JSON files (they should point to `/static/images/asanas/<name>.webp` or `.jpg`).
- If `seed_data.py` fails, check Python versions and dependency installation. On Windows, use PowerShell and run `.\run_app.bat` for a simpler flow.

---

## License

This project is for personal/educational use. Ensure you have rights to any images you add.

---

If you'd like, I can now attempt to add/commit this updated `README.md` and push it to `https://github.com/DSEENAIAH/personal-yoga-suggestions.git` (I'll run `git init` if needed). Let me know if you want me to proceed with the push now.