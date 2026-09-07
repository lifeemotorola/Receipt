#!/usr/bin/env python3
"""Generate the platform's receipt library: 40 ready receipts of all kinds.

Every receipt is a *filled* recipe the single editor (index.html) can open,
edit and print.  This script writes:

    data/receipts.js     loaded by index.html (works even on file://)
    data/receipts.json   the same data as plain JSON, for other tools

Edit SPECS below and re-run:   python3 tools/make_receipts_data.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# ------------------------------------------------------------------ helpers
ONES = ("Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
        "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen").split()
TENS = ("", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy",
        "Eighty", "Ninety")


def _words(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else "")
    if n < 1000:
        s = ONES[n // 100] + " Hundred"
        if n % 100:
            s += " " + _words(n % 100)
        return s
    out = ""
    for unit, size in (("Thousand", 1000), ("Million", 1000000)):
        if n >= size:
            out += _words(n // size) + " " + unit + " "
            n %= size
    if n:
        out += _words(n)
    return out.strip()


def words(amount, currency="USD"):
    """Legal 'the sum of' line:  Four Hundred Fifty US Dollars and 00/100 Only"""
    dollars = int(amount)
    cents = int(round((round(amount, 2) - dollars) * 100))
    unit = "US Dollars" if currency == "USD" else "Liberian Dollars"
    w = "%s %s and %02d/100 Only" % (_words(dollars) if dollars else "Zero", unit, cents)
    return w


def money(v, currency="USD"):
    return "%s%s" % ("$" if currency == "USD" else "L$", format(v, ",.2f"))


# ------------------------------------------------------------------ issuers
BIZ = {
    "suahco4":   ("Suahco4", "COW FARM, NEW ISRAEL COMMUNITY, BREWERVILLE -LIBERIA", "Phone: 0778662590 | Email:"),
    "grace":     ("Grace Provision Store", "Duport Road Junction, Brewerville City", "Phone: 0886123456"),
    "unity":     ("Unity Pharmacy", "Brewerville Main Street, Shop 3", "Phone: 0775551234"),
    "buildmart": ("BuildMart Hardware", "Stage 6 Road, Brewerville City", "Phone: 0887774512"),
    "autocity":  ("AutoCity Spare Parts", "Bassama Highway, Brewerville", "Phone: 0555123987"),
    "haven":     ("Beauty Haven Cosmetics", "Main Street Shop 14, Brewerville", "Phone: 0886222333"),
    "copyhub":   ("Copy & Print Hub", "Opposite Big Church, Brewerville", "Phone: 0778333999"),
    "newdesign": ("New Design Tailoring", "Fish Market Lane, Brewerville", "Phone: 0888456123"),
    "comfort":   ("Mama Comfort Catering", "Old Airport Road, Brewerville", "Phone: 0777009112"),
    "lofa":      ("Lofa Rice Mill Wholesale", "Ganta lorry Park, Brewerville", "Phone: 0886555222"),
    "stpeters":  ("St. Peter's Lutheran Church", "Lutheran Chapel Road, Brewerville City", "Phone: 0776411222"),
    "watch":     ("Brewerville Neighbourhood Watch", "Block D Community Hall, Brewerville", "Phone: 0555778899"),
    "easyride":  ("Easy Ride Transport Union", "Brewerville Bus Park", "Phone: 0886333777"),
    "props":     ("Brewerville Properties Ltd", "City Hall Road, Brewerville", "Phone: 0779222111"),
    "hope":      ("Hope Micro-finance SACCO", "Market Plaza, Brewerville", "Phone: 0888111000"),
    "aqua":      ("AquaFlow Water Services", "Stage 7 Borehole Site, Brewerville", "Phone: 0555990111"),
    "powershare": ("PowerShare Generator Group", "Block B Junction, Brewerville", "Phone: 0770444555"),
    "familyassn": ("Kporkpor Family Association", "Sandawo Town, Brewerville", "Phone: 0886777000"),
}


def mk(id_, name, kind, template, biz, no, *, pad=4, prefix="", copies=2,
       title=None, foot=None, sig=None, fills=None,
       labels=None, values=None, totals=None, rows=None, date, amount,
       currency="USD"):
    """Compact receipt spec -> full model the editor can apply."""
    bizn, addr, contact = BIZ[biz]
    r = dict(id=id_, name=name, kind=kind, template=template,
             no=no, pad=pad, prefix=prefix, biz=bizn, addr=addr, contact=contact,
             copies=copies, date=date, amount=money(amount, currency),
             fills=fills or {})
    if title:
        r["title"] = title
    if foot:
        r["footNote"] = foot
    if sig:
        r["sigCap"] = sig
    if labels is not None:
        r["labels"] = "\n".join(labels)
    if values is not None:
        r["values"] = "\n".join(" | ".join(c) for c in values)
    if totals is not None:
        r["totals"] = "\n".join(totals)
    if rows is not None:
        r["rows"] = rows
    return r


def line_receipt(id_, name, kind, biz, no, *, date, payer, purpose, amount,
                 balance="Nil", currency="USD", method="Cash", **kw):
    """A 'simple' or 'wide' blank-line receipt, filled in by label."""
    fills = {
        "Date:": date,
        "Received from:": payer,
        "The sum of:": words(amount, currency),
        "Amount Paid$:": money(amount, currency),
        "Balance:": balance,
        "Payment Method:": method,
        "Currency:": currency,
    }
    fills["Being payment for:" if kw.get("template") == "wide" else "For:"] = purpose
    return mk(id_, name, kind, kw.pop("template", "simple"), biz, no,
              fills=fills, date=date, amount=amount, currency=currency, **kw)


def fees_receipt(id_, name, no, *, student, sid, grade, term, lines,
                 date, currency="USD", method="Cash", copies=2, balance_note=None):
    """Suahco4 school-fees slip: lines = [(particular, due, paid), ...]."""
    labels = [l[0] for l in lines]
    values = [[format(d, ",.2f"), format(p, ",.2f"), format(round(d - p, 2), ",.2f")]
              for (_, d, p) in lines]
    td = sum(l[1] for l in lines)
    tp = round(sum(l[2] for l in lines), 2)
    totals = ["TOTAL | %s | %s | %s" % (format(td, ",.2f"), format(tp, ",.2f"),
                                        format(round(td - tp, 2), ",.2f"))]
    fills = {
        "Student Name:": student,
        "Student ID:": sid,
        "Class / Grade:": grade,
        "Academic Year:": "2026 / 2027",
        "Term:": term,
        "Amount in words:": words(tp, currency),
        "Payment Method:": method,
        "Currency:": currency,
        "Balance Carried Forward:": format(round(td - tp, 2), ",.2f"),
        "Next Payment Due:": "15 Nov 2026",
    }
    return mk(id_, name, "School fees", "fees", "suahco4", no,
              prefix="SUAHCO4-", copies=copies,
              fills=fills, labels=labels, values=values, totals=totals, rows=len(labels),
              foot="Keep this slip safe \u2014 it is your proof of payment.",
              date=date, amount=tp, currency=currency)


def itemized_receipt(id_, name, kind, biz, no, *, customer, items, date,
                     title="SALES RECEIPT", currency="USD", method="Cash",
                     prefix="", foot="Thank you for your patronage!"):
    """Item-table receipt: items = [(desc, qty, rate), ...]."""
    values, sub = [], 0.0
    for i, (d, q, r_) in enumerate(items, 1):
        amt = round(q * r_, 2)
        sub = round(sub + amt, 2)
        values.append([str(i), d, str(q), format(r_, ",.2f"), format(amt, ",.2f")])
    totals = ["Sub-Total | %s" % format(sub, ",.2f"),
              "Discount | 0.00",
              "TOTAL | %s" % format(sub, ",.2f")]
    fills = {
        "Date:": date,
        "Received from:": customer,
        "Amount in words:": words(sub, currency),
        "Payment Method:": method,
        "Currency:": currency,
    }
    return mk(id_, name, kind, "itemized", biz, no,
              fills=fills, values=values, totals=totals, rows=len(items),
              title=title, prefix=prefix, foot=foot,
              date=date, amount=sub, currency=currency, copies=1)


SU = "SUAHCO4-"

# =================================================================== 40 receipts
SPECS = [
    # ---------- 1-12 · School fees (Suahco4, fees template, original + carbon) ----------
    fees_receipt("school-0001", "Admission & Registration", 101, date="01 Sep 2026",
                 student="Kollie, Fanta V.", sid="SU-26-0142", grade="Senior 3", term="1st Term",
                 lines=[("Registration (Form 1)", 100.00, 100.00), ("PTA Levy", 25.00, 25.00)]),
    fees_receipt("school-0002", "Tuition — 1st Semester (part paid)", 102, date="05 Sep 2026",
                 student="Kollie, Fanta V.", sid="SU-26-0142", grade="Senior 3", term="1st Term",
                 method="MTN MoMo",
                 lines=[("Tuition Fee", 450.00, 200.00)]),
    fees_receipt("school-0003", "Tuition — 2nd Semester instalment", 103, date="02 Feb 2026",
                 student="Dolo, Emmanuel T.", sid="SU-26-0089", grade="Junior 2", term="2nd Term",
                 lines=[("Tuition Fee", 450.00, 450.00)]),
    fees_receipt("school-0004", "Boys Uniform Set", 104, date="28 Aug 2026",
                 student="Worjinee, Prince K.", sid="SU-26-0201", grade="Senior 1", term="1st Term",
                 lines=[("Boys Uniform (2 sets)", 60.00, 60.00), ("Shoes & Socks", 25.00, 25.00)]),
    fees_receipt("school-0005", "Girls Pinafore & Blouses", 105, date="28 Aug 2026",
                 student="Ngombelu, Comfort D.", sid="SU-26-0155", grade="Junior 3", term="1st Term",
                 lines=[("Girls Pinafore (2)", 45.00, 45.00), ("Blouses (3)", 30.00, 20.00)]),
    fees_receipt("school-0006", "Books & Class Materials", 106, date="03 Sep 2026",
                 student="Kamara, Isata S.", sid="SU-26-0118", grade="Senior 2", term="1st Term",
                 lines=[("Textbooks pack", 55.00, 55.00), ("Exercise books", 20.00, 20.00),
                        ("Writing materials", 10.00, 5.00)]),
    fees_receipt("school-0007", "WAEC Examination Entry", 107, date="15 Jun 2026",
                 student="Tetteh, Gladys M.", sid="SU-26-0044", grade="Senior 4", term="1st Term",
                 lines=[("WAEC form & entry", 120.00, 120.00)]),
    fees_receipt("school-0008", "Science Laboratory Fee", 108, date="04 Sep 2026",
                 student="Sano, Prince E.", sid="SU-26-0077", grade="Senior 2", term="1st Term",
                 lines=[("Lab consumables & reagents", 30.00, 30.00)]),
    fees_receipt("school-0009", "Computer Class Fee", 109, date="04 Sep 2026",
                 student="Fahnballah, Ruthy A.", sid="SU-26-0193", grade="Junior 1", term="1st Term",
                 method="Check",
                 lines=[("Computer lab (term)", 45.00, 30.00)]),
    fees_receipt("school-0010", "Field Trip — Science Day", 110, date="18 Sep 2026",
                 student="Junior 2 class (collective)", sid="SU-26-0089", grade="Junior 2", term="1st Term",
                 lines=[("Bus hire (share)", 15.00, 15.00), ("Botanical garden entry", 8.00, 8.00),
                        ("Lunch", 6.00, 6.00)]),
    fees_receipt("school-0011", "Graduation Fee & Photo Pack", 111, date="20 Jun 2026",
                 student="Dolo, Emmanuel T.", sid="SU-26-0089", grade="Senior 4", term="1st Term",
                 lines=[("Graduation ceremony", 35.00, 35.00), ("Photo pack (4-pc)", 20.00, 20.00)]),
    fees_receipt("school-0012", "Library Card & Overdue Fine", 112, date="07 Sep 2026",
                 student="Karnga, Musu J.", sid="SU-26-0166", grade="Senior 1", term="1st Term",
                 lines=[("New library card", 5.00, 5.00), ("Overdue fine (3 books)", 3.00, 3.00)]),

    # ---------- 13-22 · Sales, market & services (itemized) ----------
    itemized_receipt("sales-1001", "Groceries — weekly shop", "Retail", "grace", 1001, date="06 Sep 2026",
                     customer="Fornah, Mary",
                     items=[("Rice 50kg bag", 1, 45.00), ("Palm oil 1gal", 2, 12.50),
                            ("Sugar 2kg", 3, 3.00), ("Laundry soap", 6, 1.25)]),
    itemized_receipt("sales-1002", "Party catering — Dolo wedding", "Catering", "comfort", 1002, date="19 Jul 2026",
                     customer="Dolo, Solomon", method="MTN MoMo", title="CATERING RECEIPT",
                     items=[("Fried rice plates", 60, 3.50), ("Jollof rice plates", 40, 3.00),
                            ("Soda crate", 8, 9.00), ("Water sachets pack", 12, 2.50)]),
    itemized_receipt("sales-1003", "Pharmacy — malaria treatment", "Health", "unity", 1003, date="02 Sep 2026",
                     customer="Gbessay, Korto", title="PHARMACY RECEIPT",
                     foot="Get well soon! Keep receipts for insurance claims.",
                     items=[("ACTped tabs (24)", 2, 4.00), ("ORS sachets", 6, 0.75),
                            ("Paracetamol 500mg", 1, 2.50), ("Fever thermometer", 1, 5.00)]),
    itemized_receipt("sales-1004", "Hardware — house repair lot", "Construction", "buildmart", 1004, date="24 Aug 2026",
                     customer="Tarpeh, Joseph", title="HARDWARE RECEIPT",
                     items=[("Cement 50kg bag", 20, 9.50), ("Roofing sheet", 15, 7.25),
                            ("Nails 1kg", 3, 4.00), ("Paint 1gal (blue)", 2, 28.00)]),
    itemized_receipt("sales-1005", "Garage — taxi service & parts", "Auto", "autocity", 1005, date="11 Sep 2026",
                     customer="Blessing Taxi Service", title="GARAGE RECEIPT",
                     items=[("Brake pads (front)", 1, 35.00), ("Air filter", 1, 12.00),
                            ("Engine oil 5L", 1, 38.00), ("Labour", 1, 25.00)]),
    itemized_receipt("sales-1006", "Cosmetics order", "Retail", "haven", 1006, date="29 Aug 2026",
                     customer="Sirleaf, Priscilla", method="Orange Money",
                     items=[("Body lotion 500ml", 2, 6.50), ("Lipstick set", 1, 9.00),
                            ("Wig glue", 3, 3.25), ("Shea butter jar", 4, 2.00)]),
    itemized_receipt("sales-1007", "Bulk printing & binding", "Services", "copyhub", 1007, date="08 Sep 2026",
                     customer="Suahco4 School", title="PRINT SHOP RECEIPT",
                     items=[("Photocopies (500 @ 0.05)", 1, 25.00), ("Spiral binding", 12, 2.00),
                            ("Project typing (45 pages)", 1, 22.50)]),
    itemized_receipt("sales-1008", "Tailoring — graduation gowns", "Services", "newdesign", 1008, date="01 Jun 2026",
                     customer="Suahco4 Graduation Unit", title="TAILORING RECEIPT",
                     foot="Gowns ready for fitting two days before the ceremony.",
                     items=[("Graduation gown (adult)", 25, 18.00), ("Hood & tie set", 25, 4.50),
                            ("Alterations", 8, 2.00)]),
    itemized_receipt("sales-1009", "Wholesale rice — market resellers", "Wholesale", "lofa", 1009, date="17 Sep 2026",
                     customer="Brewerville Market Women Coop", method="Bank transfer",
                     title="WHOLESALE RECEIPT",
                     items=[("Rice 50kg (grade A)", 20, 42.00), ("Broken rice 25kg", 10, 18.00)]),
    itemized_receipt("sales-1010", "Farm produce — crates & baskets", "Market", "grace", 1010, date="30 Aug 2026",
                     customer="Kollie, Mama B.", currency="LRD", title="MARKET PRODUCE RECEIPT",
                     items=[("Tomato crate", 4, 900.00), ("Onion crate", 3, 1100.00),
                            ("Pepper basket", 6, 275.00)]),

    # ---------- 23-32 · Church, community, rent & finance (simple) ----------
    line_receipt("offer-2001", "Sunday thank-offering", "Church & community", "stpeters", 2001,
                 date="07 Sep 2026", payer="Congregation (counted team)",
                 purpose="Sunday Harvest Offering — counted by J. Paye, M. Dorley, A. Kollie",
                 amount=312.75, prefix="SP-", copies=1, title="OFFERING RECEIPT",
                 foot="The Lord loves a cheerful giver (2 Cor 9:7)."),
    line_receipt("offer-2002", "Wedding thank-offering", "Church & community", "stpeters", 2002,
                 date="19 Jul 2026", payer="Dolo & Sirleaf Families",
                 purpose="Wedding thank-offering — Dolo\u2013Sirleaf marriage ceremony",
                 amount=500.00, prefix="SP-", copies=1, title="THANKS RECEIPT"),
    line_receipt("offer-2003", "Funeral support contribution", "Church & community", "familyassn", 2003,
                 date="09 Aug 2026", payer="Youth Fellowship", currency="LRD",
                 purpose="Burial fund — Pa Kollie, received by the burial committee treasurer",
                 amount=1500.00, prefix="KFA-", copies=1, title="CONTRIBUTION RECEIPT"),
    line_receipt("offer-2004", "Harvest dedication envelope", "Church & community", "stpeters", 2004,
                 date="25 Oct 2026", payer="Worship Zone 4",
                 purpose="Annual harvest dedication",
                 amount=85.00, prefix="SP-", copies=1, title="OFFERING RECEIPT"),
    line_receipt("comm-2101", "Neighbourhood security dues — Q3", "Community", "watch", 2101,
                 date="01 Jul 2026", payer="Block D Rep — G. Sirleaf",
                 purpose="Night-watch dues, Block D (20 households) — Jul–Sep 2026",
                 amount=200.00, prefix="BNW-", copies=1, title="DUES RECEIPT"),
    line_receipt("rent-2201", "Shop rent — Oct to Dec quarter", "Rent & property", "props", 2201,
                 date="01 Oct 2026", payer="Fornah, Mary",
                 purpose="Quarterly rent, kiosk #7, Market Plaza (Oct–Dec 2026)",
                 amount=300.00, prefix="BPL-26-", copies=2, method="Check",
                 title="RENT RECEIPT", foot="Next quarter due 01 Jan 2027."),
    line_receipt("rent-2202", "Flat security deposit", "Rent & property", "props", 2202,
                 date="15 Aug 2026", payer="Kamara, Isata S.",
                 purpose="Refundable deposit — Flat 2B, Stage 6",
                 amount=450.00, prefix="BPL-26-", copies=1, title="DEPOSIT RECEIPT",
                 foot="Refundable at move-out, less any damages."),
    line_receipt("pay-2301", "Staff salary advance", "Payroll & finance", "suahco4", 2301,
                 date="20 Nov 2026", payer="Nyanor, Sekou (janitor)",
                 purpose="Salary advance, recovered in two deductions (Nov–Dec)",
                 amount=150.00, prefix=SU, copies=1, title="ADVANCE RECEIPT"),
    line_receipt("loan-2401", "Loan repayment — instalment 6", "Payroll & finance", "hope", 2401,
                 date="22 Sep 2026", payer="Market Women Group A",
                 purpose="Group A solidarity loan, instalment 6 of 12 (interest $35.00 incl.)",
                 amount=185.00, prefix="HMF-26-", copies=1, title="LOAN REPAYMENT RECEIPT"),
    line_receipt("school-3201", "School ID card reprint", "School fees", "suahco4", 3201,
                 date="06 Oct 2026", payer="Karnga, Musu J.",
                 purpose="Reprint of lost student ID card",
                 amount=5.00, prefix=SU, copies=1,
                 foot="Card ready at the bursar desk in 3 working days."),

    # ---------- 33-40 · Wide payments & one-offs (wide template) ----------
    line_receipt("rent-2203", "School hall rental — PTA fundraiser", "Rent & property", "suahco4", 2203,
                 template="wide", date="14 Nov 2026", payer="Brewerville Neighbourhood Watch",
                 purpose="Hall hire, Saturday community fundraiser (setup included)",
                 amount=75.00, prefix=SU, copies=2, title="RENTAL RECEIPT",
                 foot="Hall to be returned clean; caretaker inspection signed off."),
    line_receipt("offer-2005", "Church building project pledge", "Church & community", "stpeters", 2005,
                 template="wide", date="12 Apr 2026", payer="Tarpeh, Joseph & family",
                 purpose="Roofing appeal — pledge payment 3 of 4",
                 amount=250.00, balance="$250.00 pledge remaining", prefix="SP-BP-",
                 copies=1, title="BUILDING PLEDGE RECEIPT",
                 foot="Balance due by 31 Dec 2026."),
    line_receipt("offer-2006", "Youth camp registration", "Church & community", "stpeters", 2006,
                 template="wide", date="05 Jul 2026", payer="Fahnballah, Ruthy A.",
                 purpose="Luther Youth Union Camp, Tappita — registration & feeding",
                 amount=40.00, prefix="SP-YC-", copies=1, title="REGISTRATION RECEIPT"),
    line_receipt("trans-3001", "Charter bus — church programme", "Transport", "easyride", 3001,
                 template="wide", date="10 Sep 2026", payer="St. Peter's Lutheran Church",
                 purpose="40-seater charter, Brewerville\u2013Monrovia return",
                 amount=220.00, prefix="ERT-", copies=1, title="TRIP PAYMENT RECEIPT",
                 foot="Fuel on the charterer. Pickup 6:00 AM at the Bus Park."),
    line_receipt("trans-3002", "Taxi union monthly dues", "Transport", "easyride", 3002,
                 template="wide", date="01 Oct 2026", payer="Blessing Taxi Service (G. Wleh)",
                 purpose="October 2026 dispatch dues — taxi plate BVR-114",
                 amount=60.00, prefix="ERT-", copies=1, title="DUES RECEIPT"),
    line_receipt("util-3101", "Water tanker delivery", "Utilities", "aqua", 3101,
                 template="wide", date="21 Sep 2026", payer="Suahco4 School", currency="LRD",
                 purpose="10,000L poly-tank refill, Block C school yard",
                 amount=950.00, prefix="AF-", copies=1, method="MTN MoMo",
                 title="DELIVERY PAYMENT RECEIPT", foot="Charged at L$95 per 1,000L."),
    line_receipt("util-3102", "Generator fuel cost share", "Utilities", "powershare", 3102,
                 template="wide", date="28 Sep 2026", payer="Block B residents (12 homes)",
                 currency="LRD", purpose="Diesel cost share — Sept (60L @ L$360/L \u00f7 12 homes)",
                 amount=1800.00, prefix="PSG-", copies=1, title="FUEL DUES RECEIPT"),
    line_receipt("school-3202", "Bursar counter — tuition cash receipt", "School fees", "suahco4", 3202,
                 template="wide", date="07 Sep 2026", payer="Dolo, Solomon",
                 purpose="Tuition cash paid at the bursar counter (2nd term balance)",
                 amount=250.00, prefix=SU, copies=2, title="CASH RECEIPT",
                 foot="Balance of account posted at the next counter audit."),
]


def main():
    assert len(SPECS) == 40, "expected 40 receipts, got %d" % len(SPECS)
    ids = [r["id"] for r in SPECS]
    assert len(set(ids)) == len(ids), "duplicate receipt ids"
    os.makedirs(DATA, exist_ok=True)
    js = ("/* Suahco4 Receipt Platform \u2014 the receipt library: 40 ready receipts of all kinds.\n"
          "   Generated by tools/make_receipts_data.py \u2014 edit SPECS there and re-run. */\n"
          "window.SUAHCO4_RECEIPTS = ")
    js += json.dumps(SPECS, indent=1, ensure_ascii=False)
    js += ";\n"
    with open(os.path.join(DATA, "receipts.js"), "w", encoding="utf-8") as f:
        f.write(js)
    with open(os.path.join(DATA, "receipts.json"), "w", encoding="utf-8") as f:
        json.dump({"count": len(SPECS), "receipts": SPECS}, f, indent=1, ensure_ascii=False)
        f.write("\n")
    kinds = {}
    for r in SPECS:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    tpl = {}
    for r in SPECS:
        tpl[r["template"]] = tpl.get(r["template"], 0) + 1
    print("wrote %d receipts | templates: %s | kinds: %s"
          % (len(SPECS),
             ", ".join("%s×%d" % kv for kv in sorted(tpl.items())),
             ", ".join("%s×%d" % kv for kv in sorted(kinds.items()))))


if __name__ == "__main__":
    main()
