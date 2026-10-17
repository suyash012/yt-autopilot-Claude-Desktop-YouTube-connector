@echo off
title YouTube Autopilot for Claude - Installer
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (
  echo.
  echo Something went wrong. Take a photo of this window and send it to the person who shared this package.
  pause
)
