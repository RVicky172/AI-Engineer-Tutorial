---
title: "ERP invoice posting fails with ERP-4012"
type: kb
service: erp
updated: 2026-06-27
allowed_groups: [all-staff]
---
# ERP invoice posting fails with ERP-4012

When you post a supplier invoice, the ERP shows `ERP-4012 Posting timed out. The document was not posted.`

## What it means
Another process held a lock on the same supplier or period for longer than 60 seconds. Usually this is a batch job that overran into business hours, or a colleague with the same supplier open in edit mode.

## What to do
1. Wait 5 minutes and post again. Your invoice was **not** posted, so there is no risk of a duplicate.
2. Ask colleagues in your team whether anyone has the same supplier open, and close it.
3. If the error continues for more than 30 minutes, or many people in your team get it, raise a ticket with category ERP and the document number. Mention the time of the first error.

Do not post the same invoice from a second session while the first is still running; that can create a duplicate posting.

During month-end close, postings are slower; the ERP support team publishes the close timetable on the finance intranet page.
