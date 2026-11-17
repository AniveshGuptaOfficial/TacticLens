@echo off
:: Adds DailyDialog (everyday chat, no tactics) to training and measures false alarms before and after.
:: Run from the TacticLens folder:   scripts\retrain_dailydialog.cmd
:: Takes about 1 hour, mostly waiting. Safe to re-run: finished steps are skipped.
setlocal
cd /d "%~dp0.."
call .venv\Scripts\activate.bat || (echo Could not activate .venv & exit /b 1)

echo.
echo === 1/8 Tests
python -m pytest -q || (echo Tests failed: stop here and send the output. & exit /b 1)

echo.
echo === 2/8 Download DailyDialog (Hugging Face parquet export)
if exist data\raw\dailydialog\default\train\0000.parquet (
  echo Already downloaded.
) else (
  pip install -q pyarrow huggingface_hub || exit /b 1
  python -c "from huggingface_hub import snapshot_download; snapshot_download('li2017dailydialog/daily_dialog', repo_type='dataset', revision='refs/convert/parquet', local_dir='data/raw/dailydialog')" || (echo Download failed. Put ijcnlp_dailydialog.zip in data\raw\dailydialog by hand, then re-run. & exit /b 1)
)

echo.
echo === 3/8 False alarms on everyday chat, current model
if not exist reports\everyday_before.md (
  python -m tacticlens.cli everyday --tag before || exit /b 1
) else (echo Already measured.)

echo.
echo === 4/8 Back up the current model, data and app bundle (backup_v1\)
if not exist backup_v1\m3_no-context_ev (
  xcopy /E /I /Q /Y models\m3_no-context_ev backup_v1\m3_no-context_ev >nul || exit /b 1
  xcopy /E /I /Q /Y models\onnx backup_v1\onnx >nul || exit /b 1
  xcopy /E /I /Q /Y data\processed backup_v1\processed >nul || exit /b 1
  copy /Y reports\m3_no-context_ev_results.md backup_v1\ >nul
) else (echo Backup already exists.)

echo.
echo === 5/8 Prepare data with DailyDialog
python -m tacticlens.cli prepare || exit /b 1

echo.
echo === 6/8 Embed new turns (10-20 min)
python -m tacticlens.cli embed || exit /b 1

echo.
echo === 7/8 Retrain the final model
python -m tacticlens.cli train m3 --variant no-context --evidence-aug || exit /b 1

echo.
echo === 8/8 Export the app model and measure false alarms again
python -m tacticlens.cli export-onnx || exit /b 1
python -m tacticlens.cli everyday --tag after || exit /b 1

echo.
echo Done. Send these three files:
echo   reports\everyday_before.md
echo   reports\everyday_after.md
echo   reports\m3_no-context_ev_results.md   (old version: backup_v1\m3_no-context_ev_results.md)
echo To undo: copy backup_v1 back into models\ and data\processed\.
endlocal
