---
title: Outlook on your phone stopped syncing
type: kb
service: email
updated: 2026-04-22
allowed_groups: [all-staff]
---
# Outlook on your phone stopped syncing

Company email on phones is only supported in the Outlook app (iOS and Android). The built-in Mail apps are blocked.

## Fix in this order
1. Check that the phone has internet: open any website.
2. In Outlook, go to **Settings**, tap your account, and choose **Reset account**. This re-downloads mail and fixes most sync problems.
3. If you recently changed your SSO password, Outlook needs the new password: remove the account and add it again.
4. Check that Intune Company Portal is installed and shows the phone as **compliant**. Non-compliant phones (old OS, no screen lock) are blocked from mail after 7 days.
5. Still not working: remove the account, restart the phone, add the account again.

Mail on your laptop is not affected by any of these steps.
