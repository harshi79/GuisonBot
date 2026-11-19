#!/usr/bin/env python3
"""VCC Generator - generates Luhn-valid card numbers from BIN prefixes, optionally enriched with Guison API metadata."""

import argparse
import json
import random
import urllib.request
import urllib.error

def calculate_luhn_check_digit(partial: str) -> str:
    """Compute the Luhn check digit for a partial card number (without check digit)."""
    total = 0
    reverse = partial[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    check = (10 - (total % 10)) % 10
    return str(check)

def generate_card_number(bin_prefix: str, length: int = 16) -> str:
    """Generate a full card number starting with bin_prefix that passes Luhn."""
    prefix = str(bin_prefix)
    if len(prefix) >= length:
        raise ValueError("BIN prefix longer than card length")
    while len(prefix) < length - 1:
        prefix += str(random.randint(0, 9))
    check = calculate_luhn_check_digit(prefix)
    return prefix + check

def lookup_bin(bin_code: str) -> dict | None:
    """Fetch metadata from Guison API."""
    url = f"https://guison-api.onrender.com/{bin_code}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        pass
    return None

def random_expiry() -> str:
    month = random.randint(1, 12)
    year = random.randint(26, 30)  # 2026-2030
    return f"{month:02d}/{year:02d}"

def random_cvv() -> str:
    return f"{random.randint(0, 999):03d}"

def generate_vccs(bin_prefix: str | None = None, count: int = 5, length: int = 16) -> list[dict]:
    if not bin_prefix:
        # common test BINs
        bin_prefix = random.choice(["411111", "457173", "510510", "601100", "374245"])
    results = []
    meta = lookup_bin(bin_prefix[:8] if len(bin_prefix) > 6 else bin_prefix)
    for _ in range(count):
        number = generate_card_number(bin_prefix, length)
        results.append({
            "number": number,
            "expiry": random_expiry(),
            "cvv": random_cvv(),
            "bin": bin_prefix,
            "meta": meta,
        })
    return results

def main():
    parser = argparse.ArgumentParser(description="Generate Luhn-valid VCC numbers")
    parser.add_argument("--bin", type=str, help="BIN prefix (6-8 digits)")
    parser.add_argument("--count", type=int, default=5, help="Number of cards to generate")
    parser.add_argument("--length", type=int, default=16, help="Card number length")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    cards = generate_vccs(args.bin, args.count, args.length)
    if args.json:
        print(json.dumps(cards, indent=2))
    else:
        for c in cards:
            print(f"{c['number']}|{c['expiry']}|{c['cvv']}")
            if c["meta"]:
                bank = c["meta"].get("bank", {}).get("name", "")
                scheme = c["meta"].get("scheme", "")
                print(f"  {scheme} / {bank}")

if __name__ == "__main__":
    main()
