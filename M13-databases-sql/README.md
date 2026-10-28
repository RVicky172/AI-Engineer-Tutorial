# M13 · Databases, SQL and Enterprise Data Sources

**Priority:** Must have · **Roadmap week:** 2

Agents often need structured data. You should query it safely and understand how enterprise data is organised.

## How to work through this module
1. **Study** — read [docs/guide.md](docs/guide.md) and write key points in your own words in [docs/notes.md](docs/notes.md).
2. **Set up** — follow [labs/SETUP.md](labs/SETUP.md).
3. **Practise** — do the labs in order (at least the first two before moving on).
4. **Check** — answer the self-check questions out loud without notes, then update [PROGRESS.md](../PROGRESS.md).

## Labs
- [ ] [Lab 01: Safe text-to-SQL tool](labs/lab-01-text-to-sql-safe/README.md)
- [ ] [Lab 02: Result cache for the SQL tool](labs/lab-02-result-cache/README.md)

## Self-check (answer aloud, no notes)
- [ ] How do you let an agent query a production database safely?
- [ ] What breaks when many Lambda invocations open database connections at once?

## Folder layout
```
M13-databases-sql/
├── README.md          ← you are here
├── docs/
│   ├── guide.md       ← study guide
│   └── notes.md       ← your notes
└── labs/
    ├── SETUP.md       ← environment setup
    ├── lab-01-text-to-sql-safe/
    └── lab-02-result-cache/
```
