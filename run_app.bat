@echo off
echo === Mental Health Yoga App ===

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Setting up NLTK...
python setup_nltk.py

if not exist "yoga_app.db" (
    echo Seeding database...
    python seed_data.py
)

echo Starting Flask server...
echo Open http://127.0.0.1:5000 in your browser
python app.py
pause