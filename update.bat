@echo off
REM ═══════════════════════════════════════════════════════════════════════
REM   Mise a jour du dashboard P&L Tri CS
REM   ───────────────────────────────────
REM   1. Modifiez les valeurs dans BDD_dashboard.xlsx (et enregistrez)
REM   2. Double-cliquez sur ce fichier (update.bat)
REM   3. Le dashboard.html est regenere automatiquement
REM ═══════════════════════════════════════════════════════════════════════
cd /d "%~dp0"
python refresh_and_generate.py
echo.
echo ═══════════════════════════════════════════════════════════════════════
pause
