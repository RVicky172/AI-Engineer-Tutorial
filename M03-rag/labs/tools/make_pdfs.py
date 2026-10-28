"""Writes the three PDF documents in corpus/ and their metadata sidecars.

Real corpora contain PDFs, and PDFs lose structure: a table becomes lines of text with spaces.
That is the point of including them. Re-run with `python tools/make_pdfs.py` after editing.

The PDF writer is deliberately tiny (Helvetica, one text object per page, standard xref) so the
corpus needs no extra dependency; pypdf extracts the text back.
"""

import textwrap
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[1] / "corpus"
LINES_PER_PAGE = 50

DOCS = {
    "vendor-sla-summary": {
        "meta": {
            "title": "IT vendor SLA summary",
            "type": "contract",
            "service": "process",
            "updated": "2026-06-01",
            "allowed_groups": ["it-ops"],
        },
        "text": """\
IT vendor SLA summary
Owner: IT service management. Review: every June.

This summary lists the support commitments in our main IT vendor contracts. The contract text
always wins; use this page to know what to ask for when you open a vendor case.

Vendor              Contract   Severity 1 response   Severity 1 restore   Support hours
ERP vendor          ERP-2290   30 minutes            8 hours              24x7
VPN gateway vendor  NW-7781    1 hour                next business day    24x7 for Sev 1
AWS Support         Business   1 hour                not committed        24x7
Smart host (mail)   MAIL-1180  2 hours               not committed        business hours
Printer service     PRN-0450   4 business hours      2 business days      business hours
IR retainer         SEC-0042   2 hours on site call  not applicable       24x7

How to open a case
1. Use the vendor portal and quote the contract number. Phone lines are for Severity 1 only.
2. Severity 1 means production down. Opening a Severity 1 for anything else costs us goodwill
   and, for the ERP vendor, an extra fee per case.
3. Record the vendor case number in the incident ticket.

Service credits
The ERP vendor pays a service credit of 5 percent of the monthly fee for each missed Severity 1
restore target, capped at 25 percent. Claim it within 30 days through the vendor manager.
No other contract has service credits.
""",
    },
    "travel-expense-policy": {
        "meta": {
            "title": "Travel and expense policy",
            "type": "policy",
            "service": "finance",
            "updated": "2026-04-01",
            "allowed_groups": ["all-staff"],
        },
        "text": """\
Travel and expense policy
Applies to all employees from 1 April 2026.

Booking
Book all flights, trains and hotels through the travel desk portal. Bookings made elsewhere
are reimbursed only if they were cheaper than the portal price on the same day.

Limits per night for hotels
Mumbai, Delhi, Bengaluru: up to INR 9,000
Other Indian cities: up to INR 6,000
International: the city limit listed in the travel desk portal

Flights
Economy class for all flights under 6 hours. Premium economy for longer flights. Business
class needs approval from a director.

Meals
Up to INR 1,500 per day in India without receipts. Above that, receipts are required.
Alcohol is not reimbursed.

Equipment and IT purchases
IT equipment (laptops, monitors, headsets, software) is never bought on expenses. Order it
through the service portal so IT can register, secure and support it. Expensed IT purchases
are rejected.

Claims
Submit claims in the expense tool within 30 days of the trip. The expense tool uses single
sign-on; if it shows an SSO error, see the IT status page. Claims are paid with the next
salary run after approval by your manager.
""",
    },
    "datacenter-maintenance-2026": {
        "meta": {
            "title": "Data centre maintenance windows H2 2026",
            "type": "schedule",
            "service": "infrastructure",
            "updated": "2026-06-20",
            "allowed_groups": ["it-ops"],
        },
        "text": """\
Data centre maintenance windows, second half of 2026
Pune DC (primary) and Mumbai DC (secondary)

Standing windows
Pune DC: second Saturday of every month, 22:00 to 02:00 IST.
Mumbai DC: fourth Saturday of every month, 22:00 to 02:00 IST.
No maintenance in both data centres on the same weekend.

Planned major work
Date         Site    Work                                   Expected impact
2026-07-11   Pune    UPS battery replacement                none, on generator
2026-08-22   Mumbai  core switch firmware upgrade           VPN standby unavailable 30 min
2026-09-12   Pune    VPN gateway firmware 9.1.5 to 9.2.0    VPN fails over to Mumbai
2026-10-24   Mumbai  storage array controller replacement   reporting replica read-only 2 h
2026-11-14   Pune    cooling unit service                   none
2026-12-12   Pune    year-end readiness checks              none

Rules
Work that affects a P1 service needs a normal change approved by CAB.
During month-end close and the year-end freeze (15 December to 5 January) only
emergency changes are allowed, so no major work is planned in those periods.
When the Pune VPN gateway is under maintenance, users connect to Mumbai with a limit of
1,500 VPN seats; send a notice to all staff one week before.
""",
    },
}


def _escape(line: str) -> str:
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def pdf_bytes(text: str) -> bytes:
    lines = [w for raw in text.splitlines() for w in (textwrap.wrap(raw, 95) or [""])]
    pages = [lines[i : i + LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)]
    objects: list[bytes] = []  # object n is objects[n-1]
    page_ids = [3 + 2 * i for i in range(len(pages))]
    font_id = 3 + 2 * len(pages)
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{p} 0 R" for p in page_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode())
    for page_id, page in zip(page_ids, pages, strict=True):
        body = "BT /F1 10 Tf 13 TL 50 800 Td " + " ".join(
            f"({_escape(line)}) Tj T*" for line in page
        ) + " ET"
        stream = body.encode("latin-1")
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {page_id + 1} 0 R >>".encode()
        )
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def sidecar(meta: dict[str, object]) -> str:
    lines = [f"{k}: {v}" if not isinstance(v, list) else f"{k}: [{', '.join(v)}]" for k, v in meta.items()]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    for name, doc in DOCS.items():
        (CORPUS / f"{name}.pdf").write_bytes(pdf_bytes(str(doc["text"])))
        meta = doc["meta"]
        assert isinstance(meta, dict)
        (CORPUS / f"{name}.pdf.meta.yaml").write_text(sidecar(meta), encoding="utf-8")
    print(f"wrote {len(DOCS)} PDFs to {CORPUS}")
