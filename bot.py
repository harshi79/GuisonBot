#!/usr/bin/env python3
"""GuisonBot — made by @Yorichii | owner 7728424218
Button admin + force sub + broadcast + premium emojis"""

import os
import random
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
OWNER_ID = 7728424218

# Example premium animated emoji IDs (replace with your own from @FIND_MY_ID_BOT)
PREMIUM_EMOJI = {
    "fire": "5368324170671202286",
    "diamond": "5368324170671202286",  # placeholder
    "check": "5368324170671202286",
}

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

def get_users(context) -> set:
    return context.bot_data.get("users", set())

def add_user(context, uid: int):
    users = get_users(context)
    users.add(uid)
    context.bot_data["users"] = users

def get_fsubs(context) -> list:
    return context.bot_data.get("fsubs", [])

def set_fsubs(context, channels: list):
    context.bot_data["fsubs"] = channels

def premium_emoji(key: str, fallback: str = "🔥") -> str:
    eid = PREMIUM_EMOJI.get(key, "5368324170671202286")
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'

async def check_fsub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if is_owner(update.effective_user.id):
        return True
    channels = get_fsubs(context)
    if not channels:
        return True
    uid = update.effective_user.id
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch, uid)
            if member.status in ("left", "kicked"):
                return False
        except:
            continue
    return True

async def send_fsub_wall(update: Update, context):
    channels = get_fsubs(context)
    if not channels:
        return
    buttons = []
    for ch in channels:
        try:
            chat = await context.bot.get_chat(ch)
            title = chat.title or str(ch)
            uname = chat.username
            url = f"https://t.me/{uname}" if uname else f"https://t.me/c/{str(ch).replace('-100','')}"
            buttons.append([InlineKeyboardButton(f"🔔 {title}", url=url)])
        except:
            buttons.append([InlineKeyboardButton(f"🔔 {ch}", url=f"https://t.me/{ch}")])
    buttons.append([InlineKeyboardButton("✅ i joined", callback_data="check_sub")])
    kb = InlineKeyboardMarkup(buttons)
    await update.effective_message.reply_text(
        f"<b>{premium_emoji('fire')} join required</b>\nthen tap ✅",
        parse_mode="HTML", reply_markup=kb
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
    add_user(context, update.effective_user.id)
    if not await check_fsub(update, context):
        await send_fsub_wall(update, context)
        return
    u = update.effective_user
    tag = f"{premium_emoji('diamond')} OWNER" if is_owner(u.id) else "👤 USER"
    text = (
        f"<b>{premium_emoji('diamond')} ʏᴏʀɪ ɴᴇᴛᴡᴏʀᴋ</b>\n"
        f"made by @Yorichii · <code>{OWNER_ID}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{tag}\n\n"
        "<b>💳 TOOLS</b>\n"
        "├ /gen ├ /bins ├ /luhn\n"
        "└ /panel (owner)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 @Yorichii"
    )
    buttons = [
        [InlineKeyboardButton("💳 GEN", callback_data="quick_gen"),
         InlineKeyboardButton("🏦 BINS", callback_data="show_bins")],
        [InlineKeyboardButton("❓ HELP", callback_data="help"),
         InlineKeyboardButton("❌ CLOSE", callback_data="close")]
    ]
    if is_owner(u.id):
        buttons.insert(0, [InlineKeyboardButton("⚙️ ADMIN PANEL", callback_data="admin_panel")])
    kb = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("🔒 owner only")
        return
    await show_admin_panel(update, context)

async def show_admin_panel(update, context, edit=False):
    fsubs = get_fsubs(context)
    users = len(get_users(context))
    text = (
        f"<b>{premium_emoji('diamond')} ADMIN PANEL</b>\n"
        f"users: {users}\n"
        f"fsubs: {len(fsubs)}\n"
        f"utc: {datetime.utcnow().strftime('%H:%M')}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 LIST FSUB", callback_data="list_fsub"),
         InlineKeyboardButton("➕ ADD FSUB", callback_data="add_fsub")],
        [InlineKeyboardButton("➖ REMOVE FSUB", callback_data="rem_fsub"),
         InlineKeyboardButton("📢 BROADCAST", callback_data="broadcast")],
        [InlineKeyboardButton("📊 STATS", callback_data="owner_stats"),
         InlineKeyboardButton("❌ CLOSE", callback_data="close")]
    ])
    msg = update.effective_message or (update.callback_query.message if update.callback_query else None)
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await msg.reply_text(text, parse_mode="HTML", reply_markup=kb)

async def broadcast_to_all(context, text: str):
    users = get_users(context)
    sent = 0
    for uid in list(users):
        try:
            await context.bot.send_message(uid, text, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)  # smooth rate limit
        except Exception:
            users.discard(uid)
    context.bot_data["users"] = users
    return sent

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(context, update.effective_user.id)
    if not await check_fsub(update, context):
        await send_fsub_wall(update, context)
        return
    u = update.effective_user
    max_a = 200 if is_owner(u.id) else 30
    args = context.args or []
    if not args:
        await update.message.reply_text(f"<b>{premium_emoji('fire')} /gen</b>\n<code>/gen 457173 15</code>", parse_mode="HTML")
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
        f"<b>{premium_emoji('fire')} GENERATED</b>\n"
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
    out += f"\n━━━━━━━━━━━━━━━━━\n👨‍💻 @Yorichii"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 REGEN", callback_data=f"regen:{bin_pat}:{amt}")]])
    await update.message.reply_text(out, parse_mode="HTML", reply_markup=kb)

async def bins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(context, update.effective_user.id)
    if not await check_fsub(update, context):
        await send_fsub_wall(update, context)
        return
    text = f"<b>{premium_emoji('diamond')} POPULAR BINS</b>\n━━━━━━━━━━━━━━━━━\n\n"
    for name, bin_, typ in POPULAR_BINS:
        text += f"<b>{name}</b>\n<code>{bin_}</code> · {typ}\n\n"
    text += "━━━━━━━━━━━━━━━━━"
    await update.effective_message.reply_text(text, parse_mode="HTML")

async def luhn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(context, update.effective_user.id)
    if not await check_fsub(update, context):
        await send_fsub_wall(update, context)
        return
    if not context.args:
        await update.message.reply_text("<code>/luhn CC</code>", parse_mode="HTML")
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

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    mode = context.user_data.get("mode")
    text = update.message.text.strip()
    if mode == "add_fsub":
        ch = text.lstrip("@")
        if str(ch).startswith("-100"):
            ch = int(ch)
        else:
            ch = "@" + ch if not str(ch).startswith("@") else ch
        fsubs = get_fsubs(context)
        if ch not in fsubs:
            fsubs.append(ch)
            set_fsubs(context, fsubs)
        context.user_data.pop("mode", None)
        await update.message.reply_text(f"✅ added {ch}")
        await show_admin_panel(update, context)
    elif mode == "rem_fsub":
        fsubs = get_fsubs(context)
        if text in fsubs:
            fsubs.remove(text)
            set_fsubs(context, fsubs)
            await update.message.reply_text(f"❌ removed {text}")
        else:
            await update.message.reply_text("not found")
        context.user_data.pop("mode", None)
        await show_admin_panel(update, context)
    elif mode == "broadcast":
        context.user_data.pop("mode", None)
        sent = await broadcast_to_all(context, text)
        await update.message.reply_text(f"📢 broadcasted to {sent} users")
        await show_admin_panel(update, context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "close":
        await q.message.delete()
    elif data == "admin_panel":
        await show_admin_panel(update, context, edit=True)
    elif data == "list_fsub":
        fsubs = get_fsubs(context)
        text = "<b>📋 FSUB LIST</b>\n" + ("\n".join(f"<code>{c}</code>" for c in fsubs) or "empty")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]])
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
    elif data == "add_fsub":
        context.user_data["mode"] = "add_fsub"
        await q.edit_message_text("send channel @username or -100id now")
    elif data == "rem_fsub":
        context.user_data["mode"] = "rem_fsub"
        fsubs = get_fsubs(context)
        await q.edit_message_text("send the exact channel to remove:\n" + "\n".join(str(c) for c in fsubs))
    elif data == "broadcast":
        context.user_data["mode"] = "broadcast"
        await q.edit_message_text("send the broadcast message now (HTML ok)")
    elif data == "owner_stats":
        await q.edit_message_text(f"<b>📊</b> users {len(get_users(context))}\nfsubs {len(get_fsubs(context))}\nutc {datetime.utcnow().strftime('%H:%M')}")
    elif data == "check_sub":
        if await check_fsub(update, context):
            await q.message.reply_text("✅ good, /start")
            await q.message.delete()
        else:
            await q.answer("not yet", show_alert=True)
    elif data == "show_bins":
        await bins(update, context)
    elif data.startswith("regen:"):
        parts = data.split(":")
        await q.message.reply_text(f"use /gen {parts[1]} {parts[2]}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(CommandHandler("bins", bins))
    app.add_handler(CommandHandler("luhn", luhn))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("bot up — broadcast + premium emoji ready")
    app.run_polling()

if __name__ == "__main__":
    main()
