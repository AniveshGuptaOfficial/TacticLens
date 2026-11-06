# Windows helper. Usage:  .\run.ps1 setup | test | inspect | prepare | datacard | checkset | kappa | m0 | overlap | all
param([string]$task = "help")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Run($cmd) { Write-Host ">> $cmd" -ForegroundColor Cyan; Invoke-Expression $cmd }

switch ($task) {
  "setup"    { Run "python -m venv .venv"; Run ".\.venv\Scripts\python -m pip install -r requirements.txt"; Run ".\.venv\Scripts\python -m pip install -e ." }
  "test"     { Run ".\.venv\Scripts\python -m pytest -q" }
  "inspect"  { Run ".\.venv\Scripts\python -m tacticlens.cli inspect" }
  "prepare"  { Run ".\.venv\Scripts\python -m tacticlens.cli prepare" }
  "datacard" { Run ".\.venv\Scripts\python -m tacticlens.cli datacard" }
  "checkset" { Run ".\.venv\Scripts\python -m tacticlens.cli checkset" }
  "kappa"    { Run ".\.venv\Scripts\python -m tacticlens.cli kappa" }
  "m0"       { Run ".\.venv\Scripts\python -m tacticlens.cli train-m0" }
  "overlap"  { Run ".\.venv\Scripts\python -m tacticlens.cli llm-overlap" }
  "all"      { foreach ($t in "prepare","datacard","checkset","m0") { & $PSCommandPath $t } }
  default    { Write-Host "Tasks: setup, test, inspect, prepare, datacard, checkset, kappa, m0, overlap, all" }
}
