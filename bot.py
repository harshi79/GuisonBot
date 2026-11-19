#!/usr/bin/env python3
"""GuisonBot — made by @Yorichii | owner 7728424218
Premium VCC generator + BIN lookup (binlist.net + alts)"""

import os
import random
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
OWNER_ID = 7728424218

BIN_ENDPOINTS = [
    "https://lookup.binlist.net/{bin}",
    "https://binlist.io/lookup/{bin}/",
]

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

def get_bin_meta(bin_digits: str) -> dict | None:
    headers = {"Accept-Version": "3", "Accept": "application/json"}
    for url_tmpl in BIN_ENDPOINTS:
        try:
            url = url_tmpl.format(bin=bin_digits[:8])
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200:
                data = r.json()
                if data.get("scheme") or data.get("success"):
                    return data
        except Exception:
            continue
    return None

def get_network(bin_str: str) -> dict:
    b = bin_str
    if len(b) < 2:
        return {"scheme": "UNKNOWN", "length": 16, "cvv_len": 3}
    p2 = int(b[:2]) if len(b) >= 2 else 0
    p4 = int(b[:4]) if len(b) >= 4 else 0
    if b[:2] in ("34", "37"):
        return {"scheme": "AMEX", "length": 15, "cvv_len": 4}
    if 51 <= p2 <= 55 or 2221 <= p4 <= 2720:
        return {"scheme": "MASTERCARD", "length": 16, "cvv_len": 3}
    if b[:1] == "4":
        return {"scheme": "VISA", "length": 16, "cvv_len": 3}
    if b[:4] == "6011" or b[:2] == "65":
        return {"scheme": "DISCOVER", "length": 16, "cvv_len": 3}
    return {"scheme": "UNKNOWN", "length": 16, "cvv_len": 3}

def expand_wild(pattern: str) -> str:
    return "".join(str(random.randint(0, 9)) if c.lower() == "x" else c for c in pattern)

def luhn_check_digit(partial: str) -> str:
    total = 0
    for i, c in enumerate(reversed(partial)):
        d = int(c)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - (total % 10)) % 10)

def gen_card(bin_pat: str, month: str = "N", year: str = "N", cvv: str = "N") -> dict:
    net = get_network(bin_pat)
    tgt = net["length"]
    expanded = expand_wild(bin_pat)[:tgt - 1]
    remain = max(0, tgt - 1 - len(expanded))
    partial = expanded + "".join(str(random.randint(0, 9)) for _ in range(remain))
    cc = partial + luhn_check_digit(partial)
    m = f"{random.randint(1, 12):02d}" if month.upper() == "N" else month.zfill(2)
    y = str(random.randint(2026, 2035)) if year.upper() == "N" else ("20" + year if len(year) == 2 else year)
    cv = "".join(str(random.randint(0, 9)) for _ in range(net["cvv_len"])) if cvv.upper() == "N" else cvv
    return {"cc": cc, "month": m, "year": y, "cvv": cv}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    premium = "💎 PREMIUM" if is_owner(user.id) else "👤 USER"
    text = (
        f"<b>💎 ʏᴏʀɪ ɴᴇᴛᴡᴏʀᴋ 💎</b>\n"
        f"made by @Yorichii · owner <code>{OWNER_ID}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{premium}</b>\n\n"
        "<b>💳 CARD TOOLS</b>\n"
        "├ <code>/gen</code> Luhn VCC + BIN\n"
        "├ <code>/mgen</code> mass (owner)\n"
        "└ <code>/luhn</code> validate\n\n"
        "<b>🛡️ PREMIUM TABLE</b>\n"
        "├ unlimited gens ✔\n"
        "├ BIN meta tables ✔\n"
        "├ owner cmds ✔\n"
        "└ priority lookup ✔\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 @Yorichii · ⚜️ @YoriFederation"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("❓ HELP", callback_data="help"),
        InlineKeyboardButton("❌ CLOSE", callback_data="close")
    ]])
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    max_amt = 100 if is_owner(user.id) else 20
    args = context.args
    if not args:
        await update.message.reply_text(
            "<b>💳 /gen</b>\n"
            "<code>/gen 457173</code> or <code>/gen 457173 10</code>\n"
            "wild: <code>/gen 4571xx</code>",
            parse_mode="HTML"
        )
        return
    bin_pat = args[0]
    amount = int(args[1]) if len(args) > 1 and args[1].isdigit() else 10
    amount = max(1, min(amount, max_amt))
    bin_digits = "".join(c for c in bin_pat if c.isdigit())
    meta = get_bin_meta(bin_digits) if len(bin_digits) >= 6 else None
    cards = [gen_card(bin_pat) for _ in range(amount)]
    scheme = (meta or {}).get("scheme", "UNKNOWN").upper()
    bank = ((meta or {}).get("bank") or {}).get("name", "Unknown")
    country = ((meta or {}).get("country") or {}).get("name", "Unknown")
    emoji = ((meta or {}).get("country") or {}).get("emoji", "")
    out = (
        "<b>💳 CC GENERATED</b>\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        f"<b>BIN:</b> <code>{bin_digits[:6]}</code>\n"
        f"<b>SCHEME:</b> {scheme}\n"
        f"<b>BANK:</b> {bank}\n"
        f"<b>COUNTRY:</b> {country} {emoji}\n"
        f"<b>AMOUNT:</b> {amount}\n\n"
        "━━━━━━━━━━━━━━━━━\n"
    )
    for c in cards:
        out += f"<code>{c['cc']}|{c['month']}|{c['year']}|{c['cvv']}</code>\n"
    out += "\n━━━━━━━━━━━━━━━━━\n👨‍💻 @Yorichii"
    await update.message.reply_text(out, parse_mode="HTML")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("🔒 owner only")
        return
    await update.message.reply_text(
        f"<b>📊 STATS</b>\n"
        f"owner: <code>{OWNER_ID}</code>\n"
        f"time: {datetime.utcnow().isoformat()}\n"
        "bot live ✅",
        parse_mode="HTML"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>❓ HELP</b>\n"
        "<code>/start</code> welcome\n"
        "<code>/gen BIN [amt]</code> generate\n"
        "<code>/stats</code> owner only\n"
        "made by @Yorichii",
        parse_mode="HTML"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "close":
        await q.message.delete()
    elif q.data == "help":
        await q.message.reply_text("use /help")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
