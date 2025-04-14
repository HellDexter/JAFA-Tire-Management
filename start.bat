@echo off
echo JAFA Tire Management - Spouštění aplikace
echo =======================================

IF NOT EXIST venv (
    echo Vytvářím virtuální prostředí...
    python -m venv venv
)

echo Aktivuji virtuální prostředí...
call venv\Scripts\activate

echo Kontroluji závislosti...
pip install -r requirements.txt

echo Spouštím aplikaci...
python app.py

pause
