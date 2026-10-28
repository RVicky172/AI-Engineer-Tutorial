---
title: Drain a stuck outbound mail queue on the mail relay
type: runbook
service: email
updated: 2026-05-30
allowed_groups: [it-ops]
---
# Drain a stuck outbound mail queue on the mail relay

The mail relay (`mail-relay-01`, Postfix) sends outbound mail for applications: ERP invoices, ticket notifications and password reset emails. User mailboxes are in Exchange Online and do not pass through it.

## Symptoms
- Alert `postfix_queue_size > 1000`.
- Users report that password reset emails or ERP invoices never arrive.

## Diagnose
1. `mailq | tail -1` shows the queue size.
2. `postqueue -p | grep -c "Connection timed out"` counts messages waiting on a remote server.
3. The most common cause: the upstream smart host `smtp.provider.example` throttles us after a burst, for example a mass ERP invoice run. Check its status page.

## Fix
1. If upstream is throttling: wait; Postfix retries with backoff. Do not flush repeatedly, since flushing makes throttling worse.
2. If the relay disk is above 90%: free space in `/var/log` first, then run `postqueue -f`.
3. If one sender is flooding (a looping application): hold its messages with `postsuper -h` per queue ID and contact the app owner.
4. Restart Postfix (`systemctl restart postfix`) only if the process is hung. A restart does not lose queued mail.
