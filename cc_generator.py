#!/usr/bin/env python3
"""
CC Generator — Luhn-valid card numbers from BIN prefixes.
BIN lookup: binlist.net primary, free alternatives fallback.
"""

import argparse
import json
import random
import urllib.request
import urllib.error

BIN_APIS = [
    "https://lookup.binlist.net/{}",
    "https://binlist.net/lookup/{}",
    "https://api.freebinchecker.com/bin/{}",
]

def get_card_network(bin_str: str) -> dict:
    b = bin_str
    if len(b) < 2:
        return {"scheme": "UNKNOWN", "length": 16, "cvv_len": 3}
    p2 = int(b[:2]) if len(b) >= 2 else 0
    p3 = int(b[:3]) if len(b) >= 3 else 0
    p4 = int(b[:4]) if len(b) >= 4 else 0
    if b[:2] in ("34", "37"):
        return {"scheme": "AMEX", "length": 15, "cvv_len": 4}
    if b[:3] in ("300","301","302","303","304","305") or b[:2] in ("36","38"):
        return {"scheme": "DINERS", "length": 14, "cvv_len": 3}
    if 3528 <= p4 <= 3589:
        return {"scheme": "JCB", "length": 16, "cvv_len": 3}
    if 51 <= p2 <= 55 or 2221 <= p4 <= 2720:
        return {"scheme": "MASTERCARD", "length": 16, "cvv_len": 3}
    if b[:4] == "6011" or b[:2] == "65" or (644 <= p3 <= 649):
        return {"scheme": "DISCOVER", "length": 16, "cvv_len": 3}
    if p4 in (6304, 6759, 6761, 6762, 6763):
        return {"scheme": "MAESTRO", "length": 16, "cvv_len": 3}
    if b[:2] == "62":
        return {"scheme": "UNIONPAY", "length": 16, "cvv_len": 3}
    if b[:4] in ("5061","6500","6501","6555"):
        return {"scheme": "VERVE", "length": 16, "cvv_len": 3}
    if b[:3] in ("508","810","811","812") or b[:2] in ("81","82"):
        return {"scheme": "RUPAY", "length": 16, "cvv_len": 3}
    if b[:1] == "4":
        return {"scheme": "VISA", "length": 16, "cvv_len": 3}
    return {"scheme": "UNKNOWN", "length": 16, "cvv_len": 3}

def expand_wildcards(pattern: str) -> str:
    return "".join(str(random.randint(0, 9)) if c in ("x", "X") else c for c in pattern)

def calc_luhn_check(partial: str) -> str:
    total = 0
    for i, c in enumerate(reversed(partial)):
        d = int(c)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - (total % 10)) % 10)

def generate_number(bin_pattern: str, length: int = 16) -> str:
    expanded = expand_wildcards(bin_pattern)
    if len(expanded) >= length:
        partial = expanded[:length - 1]
    else:
        remaining = length - len(expanded) - 1
        partial = expanded + "".join(str(random.randint(0, 9)) for _ in range(max(0, remaining)))
    return partial + calc_luhn_check(partial)

def lookup_bin(bin_code: str) -> dict | None:
    clean = "".join(c for c in bin_code if c.isdigit())[:8]
    if len(clean) < 6:
        return None
    for tmpl in BIN_APIS:
        url = tmpl.format(clean)
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "cc-gen/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    return {
                        "scheme": (data.get("scheme") or "").upper(),
                        "type": (data.get("type") or "").upper(),
                        "brand": data.get("brand") or "",
                        "bank": (data.get("bank") or {}).get("name") or "",
                        "country": (data.get("country") or {}).get("name") or "",
                        "alpha2": (data.get("country") or {}).get("alpha2") or "",
                    }
        except Exception:
            continue
    return None

def generate_cards(bin_pattern: str | None = None, count: int = 10, mes: str = "N", ano: str = "N", cvv: str = "N") -> list[dict]:
    if not bin_pattern:
        bin_pattern = random.choice(["411111", "457173", "510510", "601100", "374245"])
    net = get_card_network(bin_pattern)
    length = net["length"]
    default_cvv = net["cvv_len"]
    meta = lookup_bin(bin_pattern)
    cards = []
    for _ in range(count):
        number = generate_number(bin_pattern, length)
        month = mes if mes and mes.upper() != "N" else f"{random.randint(1,12):02d}"
        year = ano if ano and ano.upper() != "N" else str(random.randint(2026, 2035))
        if len(year) == 2:
            year = "20" + year
        cvv_final = cvv
        if not cvv_final or cvv_final.upper() == "N":
            cvv_final = "".join(str(random.randint(0,9)) for _ in range(default_cvv))
        elif all(c in ("x","X") for c in cvv_final):
            cvv_final = "".join(str(random.randint(0,9)) for _ in range(len(cvv_final)))
        cards.append({
            "number": number,
            "month": month,
            "year": year,
            "cvv": cvv_final,
            "bin": bin_pattern,
            "network": net["scheme"],
            "meta": meta,
        })
    return cards

def main():
    parser = argparse.ArgumentParser(description="Generate Luhn-valid CC numbers")
    parser.add_argument("--bin", type=str, help="BIN prefix (6-8 digits or with x wildcards)")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--month", type=str, default="N")
    parser.add_argument("--year", type=str, default="N")
    parser.add_argument("--cvv", type=str, default="N")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cards = generate_cards(args.bin, args.count, args.month, args.year, args.cvv)
    if args.json:
        print(json.dumps(cards, indent=2))
    else:
        for c in cards:
            print(f"{c['number']}|{c['month']}|{c['year']}|{c['cvv']}")
            if c["meta"]:
                print(f"  {c['meta'].get('scheme','')} / {c['meta'].get('bank','')} / {c['meta'].get('country','')}")

if __name__ == "__main__":
    main()
