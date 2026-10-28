---
title: "INC0011802: Printers stuck with E-512 after firmware update"
type: incident
service: printing
updated: 2026-09-30
allowed_groups: [it-ops]
---
# INC0011802: Printers stuck with E-512 after firmware update

**Priority:** P3 · **Duration:** 2 days · **Impact:** 14 of 22 office printers unusable

## Summary
On 22 September 2026 the printer management tool pushed firmware 4.2 to all printers at once. Printers that were printing at the time aborted the update and showed `E-512 firmware update failed`.

## Resolution
The vendor provided a recovery image that IT installed remotely over two days, floor by floor. Users printed on the remaining printers in the meantime.

## Actions
1. Firmware updates go to one pilot printer first, then the rest a week later, outside office hours.
2. The printer error code KB now explains E-512.
3. Printers that cannot be updated remotely are flagged in the asset list.
