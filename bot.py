#!/usr/bin/env python3
"""GuisonBot — made by @Yorichii | owner 7728424218
Cooler premium VCC + BIN lookup + force sub admin panel"""

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

POPULAR_BINS = [
    ("Chase", "414720", "VISA"),
    ("Bank of America", "435688", "VISA"),
    ("Citibank", "542418", "MC"),
    ("Wells Fargo", "473702", "VISA"),
    ("Capital One", "517805", "MC"),
    ("Amex", "378281", "AMEX"),
    ("Discover", "601100", "DISC"),
]

def is_owner(uid: int) -> bool:
    return uid == OWNER_ID

def get_fsubs(context: ContextTypes.DEFAULT_TYPE) -> list:
    return context.bot_data.get("fsubs", [])

def set_fsubs(context: ContextTypes.DEFAULT_TYPE, channels: list):
    context.bot_data["fsubs"] = channels

async def check_fsub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if is_owner(update.effective_user.id):
        return True
    channels = get_fsubs(context)
    if not channels:
        return True
    user_id = update.effective_user.id
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status in ("left", "kicked"):
                return False
        except:
            continue
    return True

async def send_fsub_wall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = get_fsubs(context)
    if not channels:
        return
    buttons = []
    for ch in channels:
        try:
            chat = await context.bot.get_chat(ch)
            buttons.append([InlineKeyboardButton(f"🔔 join {chat.title or ch}", url=f"https://t.me/{chat.username or ch}")])
        except:
            buttons.append([InlineKeyboardButton(f"🔔 join {ch}", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton("✅ i joined", callback_data="check_sub")])
    kb = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        "<b>🔒 access denied</b>\njoin the channels first then tap ✅",
        parse_mode="HTML",
        reply_markup=kb
    )

def get_bin_meta(bin_digits: str):
    headers = {"Accept-Version": "3", "Accept": "application/json"}
    for tmpl in BIN_ENDPOINTS:
        try:
            r = requests.get(tmpl.format(bin=bin_digits[:8]), headers=headers, timeout=8)
            if r.status_code == 200:
                d = r.json()
                if d.get("scheme") or d.get("success"):
                    return d
        except:
            continue
    return None

def get_network(b: str):
    if len(b) < 2: return {"scheme": "UNKNOWN", "length": 16, "cvv_len": 3}
    p2 = int(b[:2] or 0)
    p4 = int(b[:4] or 0)
    if b[:2] in ("34", "37"): return {"scheme": "AMEX", "length": 15, "cvv_len": 4}
    if 51 <= p2 <= 55 or 2221 <= p4 <= 2720: return {"scheme": "MASTERCARD", "length": 16, "cvv_len": 3}
    if b[0] == "4": return {"scheme": "VISA", "length": 16, "cvv_len": 3}
    if b[:4] == "6011" or b[:2] == "65": return {"scheme": "DISCOVER", "length": 16, "cvv_len": 3}
    return {"scheme": "UNKNOWN", "length": 16, "cvv_len": 3}

def expand_wild(p: str) -> str:
    return "".join(str(random.randint(0,9)) if c.lower()=="x" else c for c in p)

def luhn_digit(partial: str) -> str:
    total = 0
    for i, c in enumerate(reversed(partial)):
        d = int(c)
        if i % 2 == 0:
            d *= 2
            if d > 9: d -= 9
        total += d
    return str((10 - total % 10) % 10)

def gen_card(bin_pat: str):
    net = get_network(bin_pat)
    tgt = net["length"]
    exp = expand_wild(bin_pat)[:tgt-1]
    rem = max(0, tgt-1-len(exp))
    partial = exp + "".join(str(random.randint(0,9)) for _ in range(rem))
    cc = partial + luhn_digit(partial)
    m = f"{random.randint(1,12):02d}"
    y = str(random.randint(2026, 2035))
    cv = "".join(str(random.randint(0,9)) for _ in range(net["cvv_len"]))
    return f"{cc}|{m}|{y}|{cv}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_fsub(update, context):
        await send_fsub_wall(update, context)
        return
    u = update.effective_user
    tag = "💎 OWNER" if is_owner(u.id) else "👤 USER"
    text = (
        f"<b>💎 ʏᴏʀɪ ɴᴇᴛᴡᴏʀᴋ 💎</b>\n"
        f"made by @Yorichii · <code>{OWNER_ID}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{tag}\n\n"
        "<b>💳 TOOLS</b>\n"
        "├ /gen BIN [n] — generate\n"
        "├ /bins — popular BINs\n"
        "├ /luhn CC — check\n"
        "└ /stats — owner\n\n"
        "<b>⚡ PREMIUM</b>\n"
        "├ higher limits\n"
        "├ live BIN tables\n"
        "├ regen buttons\n"
        "└ owner panel + fsub\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 @Yorichii · ⚜️ @YoriFederation"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 GEN", callback_data="quick_gen"),
         InlineKeyboardButton("🏦 BINS", callback_data="show_bins")],
        [InlineKeyboardButton("❓ HELP", callback_data="help"),
         InlineKeyboardButton("❌ CLOSE", callback_data="close")]
    ])
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_fsub(update, context):
        await send_fsub_wall(update, context)
        return
    u = update.effective_user
    max_a = 200 if is_owner(u.id) else 30
    args = context.args or []
    if not args:
        await update.message.reply_text("<b>💳 /gen</b>\n<code>/gen 457173 15</code>", parse_mode="HTML")
        return
    bin_pat = args[0]
    amt = int(args[1]) if len(args)>1 and args[1].isdigit() else 10
    amt = max(1, min(amt, max_a))
    digits = "".join(c for c in bin_pat if c.isdigit())
    meta = get_bin_meta(digits) if len(digits)>=6 else None
    cards = [gen_card(bin_pat) for _ in range(amt)]
    sch = (meta or {}).get("scheme","UNKNOWN").upper()
    bank = ((meta or {}).get("bank") or {}).get("name","?")
    ctry = ((meta or {}).get("country") or {}).get("name","?")
    flag = ((meta or {}).get("country") or {}).get("emoji","")
    out = (
        "<b>💳 GENERATED</b>\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        f"<b>BIN</b> <code>{digits[:6]}</code>\n"
        f"<b>SCHEME</b> {sch}\n"
        f"<b>BANK</b> {bank}\n"
        f"<b>COUNTRY</b> {ctry} {flag}\n"
        f"<b>COUNT</b> {amt}\n\n"
        "━━━━━━━━━━━━━━━━━\n"
    )
    for c in cards:
        out += f"<code>{c}</code>\n"
    out += "\n━━━━━━━━━━━━━━━━━\n👨‍💻 @Yorichii"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 REGEN", callback_data=f"regen:{bin_pat}:{amt}")]])
    await update.message.reply_text(out, parse_mode="HTML", reply_markup=kb)

async def bins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_fsub(update, context):
        await send_fsub_wall(update, context)
        return
    text = "<b>🏦 POPULAR BINS</b>\n━━━━━━━━━━━━━━━━━\n\n"
    for name, bin_, typ in POPULAR_BINS:
        text += f"<b>{name}</b>\n<code>{bin_}</code> · {typ}\n\n"
    text += "━━━━━━━━━━━━━━━━━\nuse /gen <code>BIN</code>"
    await update.message.reply_text(text, parse_mode="HTML")

async def luhn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_fsub(update, context):
        await send_fsub_wall(update, context)
        return
    if not context.args:
        await update.message.reply_text("<code>/luhn 4571736012345678</code>", parse_mode="HTML")
        return
    cc = "".join(c for c in context.args[0] if c.isdigit())
    if not (13 <= len(cc) <= 19):
        await update.message.reply_text("bad length")
        return
    def valid(n):
        s = 0
        alt = False
        for d in reversed(n):
            x = int(d)
            if alt:
                x *= 2
                if x > 9: x -= 9
            s += x
            alt = not alt
        return s % 10 == 0
    ok = "✅ VALID" if valid(cc) else "❌ INVALID"
    await update.message.reply_text(f"<b>{ok}</b>\n<code>{cc}</code>", parse_mode="HTML")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("🔒 owner only")
        return
    fsubs = get_fsubs(context)
    await update.message.reply_text(
        f"<b>📊 OWNER PANEL</b>\n"
        f"id: <code>{OWNER_ID}</code>\n"
        f"utc: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}\n"
        f"fsubs: {len(fsubs)}\n"
        "status: 🟢 LIVE",
        parse_mode="HTML"
    )

async def addfsub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("usage: /addfsub @channel or -100xxx")
        return
    ch = context.args[0].lstrip("@")
    if ch.startswith("-100"):
        ch = int(ch)
    else:
        ch = "@" + ch if not ch.startswith("@") else ch
    fsubs = get_fsubs(context)
    if ch not in fsubs:
        fsubs.append(ch)
        set_fsubs(context, fsubs)
    await update.message.reply_text(f"✅ added fsub: {ch}\ncurrent: {fsubs}")

async def remfsub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("usage: /remfsub @channel")
        return
    ch = context.args[0]
    fsubs = get_fsubs(context)
    if ch in fsubs:
        fsubs.remove(ch)
        set_fsubs(context, fsubs)
        await update.message.reply_text(f"❌ removed: {ch}")
    else:
        await update.message.reply_text("not found")

async def listfsub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    fsubs = get_fsubs(context)
    text = "<b>🔔 FSUB CHANNELS</b>\n" + "\n".join(f"<code>{c}</code>" for c in fsubs) if fsubs else "none"
    await update.message.reply_text(text, parse_mode="HTML")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "close":
        await q.message.delete()
    elif data == "help":
        await q.message.reply_text("/start /gen /bins /luhn /stats\nowner: /addfsub /remfsub /listfsub")
    elif data == "check_sub":
        if await check_fsub(update, context):
            await q.message.reply_text("✅ joined, use /start")
            await q.message.delete()
        else:
            await q.answer("still not joined", show_alert=True)
    elif data == "show_bins":
        await bins(q, context)
    elif data.startswith("regen:"):
        _, bin_pat, amt = data.split(":")
        await q.message.reply_text(f"regen → /gen {bin_pat} {amt}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    handlers = [
        ("start", start), ("gen", gen), ("bins", bins), ("luhn", luhn),
        ("stats", stats), ("addfsub", addfsub), ("remfsub", remfsub), ("listfsub", listfsub)
    ]
    for cmd, h in handlers:
        app.add_handler(CommandHandler(cmd, h))
    app.add_handler(CallbackQueryHandler(button))
    logger.info("bot up — made by @Yorichii | fsub ready")
    app.run_polling()

if __name__ == "__main__":
    main()
