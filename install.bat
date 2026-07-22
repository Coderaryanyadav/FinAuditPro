@echo off
title FinAuditPro Setup & Auto-Installer
echo ===================================================
echo  FinAuditPro Automated Environment & Setup Launcher
echo ===================================================
python scripts\bootstrap_env.py %*
pause
