---
title: Restart the print spooler on the central print server
type: runbook
service: printing
updated: 2026-03-14
allowed_groups: [it-ops]
---
# Restart the print spooler on the central print server

Office printers are shared from the central Windows print server `print-srv-01`. When its spooler hangs, nobody in the building can print.

This runbook is for the **server**. A single user whose laptop queue is stuck should follow the KB article "Clear a stuck print queue on your laptop" instead.

## Steps
1. Confirm the problem is server-wide: at least two floors are affected, or the `print-srv-01 spooler` monitor is red.
2. Connect to print-srv-01 over RDP with your admin account.
3. Run `Restart-Service -Name Spooler -Force` in an elevated PowerShell.
4. If jobs get stuck again within minutes, a corrupt job is the usual cause: stop the spooler, delete the files in `C:\Windows\System32\spool\PRINTERS`, then start the spooler.
5. Print a test page to `FL3-PRN-01`.

Restarting the spooler cancels jobs that were printing; users must send them again.
