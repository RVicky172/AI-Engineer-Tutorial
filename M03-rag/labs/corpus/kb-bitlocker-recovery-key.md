---
title: BitLocker recovery key
type: kb
service: device
updated: 2026-06-17
allowed_groups: [all-staff]
---
# BitLocker recovery key

All company laptops are encrypted with BitLocker. After a firmware update, a hardware change or several wrong PINs, the laptop asks for a 48-digit **recovery key** before Windows starts.

## Get your key yourself
1. On your phone or another computer, go to `https://myaccount.acme.example/device-keys`.
2. Sign in with your SSO account.
3. Find the laptop by the **Key ID** shown on the recovery screen (the first 8 characters are enough).
4. Type the 48 digits into the laptop.

## Cannot sign in?
Call the service desk on extension 4357. They read the key to you after verifying your identity. Recovery keys are never sent by email or chat.

If the recovery screen appears again after every restart, bring the laptop to the IT desk: the TPM chip may need to be reset.
