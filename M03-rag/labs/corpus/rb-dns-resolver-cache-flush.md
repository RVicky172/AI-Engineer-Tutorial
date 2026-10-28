---
title: Flush the internal DNS resolver cache
type: runbook
service: network
updated: 2026-07-25
allowed_groups: [it-ops]
---
# Flush the internal DNS resolver cache

Internal clients use the resolvers `dns-01` and `dns-02` (BIND 9). They forward `acme.example` lookups to the authoritative servers and everything else to the internet.

## When
- A DNS record was changed (for example during a VPN or database failover) but clients still get the old address after the TTL has passed.
- A wrong record was published and has been corrected.

## Steps
1. Confirm the authoritative answer is correct: `dig @ns1.acme.example host.acme.example +short`.
2. Flush one name on both resolvers: `rndc flushname host.acme.example`.
3. Flush everything only if many names are wrong: `rndc flush`. This causes a short spike in upstream queries.
4. Client caches: Windows clients run `ipconfig /flushdns`; most browsers keep their own cache for up to 60 seconds.

The July 2026 DNS incident (INC0011207) was a wrong CNAME with a 24-hour TTL: fixing the record was not enough until the resolvers were flushed.
