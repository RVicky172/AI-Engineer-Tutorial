---
title: Outlook on your laptop shows "Disconnected" or old mail
type: kb
service: email
updated: 2026-04-22
allowed_groups: [all-staff]
---
# Outlook on your laptop shows "Disconnected" or old mail

1. Check the status bar at the bottom of Outlook. "Working offline": click **Send/Receive → Work Offline** to turn it off.
2. "Disconnected": check your internet connection, then restart Outlook.
3. "Need password": click it and sign in with SSO.
4. Still showing old mail: close Outlook, open **Control Panel → Mail → Data Files** and rebuild the cache by deleting the `.ost` file. Outlook downloads your mailbox again, which can take an hour.

Outlook on the web (`https://outlook.office.com`) always shows the current mailbox; use it while the desktop app catches up.
