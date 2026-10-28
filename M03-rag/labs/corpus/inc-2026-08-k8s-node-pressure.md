---
title: "INC0011398: Kubernetes nodes NotReady from disk pressure"
type: incident
service: kubernetes
updated: 2026-08-23
allowed_groups: [it-ops]
---
# INC0011398: Kubernetes nodes NotReady from disk pressure

**Priority:** P2 · **Duration:** 3 h · **Impact:** report generation slow; two batch jobs failed

## Summary
On 20 August 2026, four nodes of the `general` node group in `prod-eks-1` went `NotReady` with `DiskPressure=True`. Pods were evicted and rescheduled onto the remaining nodes, which then filled up too.

## Root cause
A new version of the reporting service wrote debug logs to the container's writable layer (not stdout) at about 2 GB per hour. Together with cached container images, the 50 GB root volumes filled up.

## Resolution
The reporting service was rolled back (`kubectl rollout undo`), and the affected nodes were cordoned, drained and replaced.

## Actions
1. Root volumes in the `general` node group increased to 100 GB.
2. Containers must log to stdout; an admission policy rejects pods without `ephemeral-storage` limits.
3. Node disk usage above 80% alerts the platform on-call.
