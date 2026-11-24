# Phase 1 Handoff: Monitoring Agent

## What it does
Monitors files and processes and logs them to events.jsonl

## How to run
cd C:\PurpleShield
.\venv\Scripts\Activate.ps1
python -m agent.main

## Config keys (config.yaml)
watch_paths, log_path, rotate_mb, debounce_seconds, self_ignore

## Known issues
- File-to-process attribution is an estimate (see confidence field)
- Very fast operations may have process = null

## Owner: Nouran & Maram