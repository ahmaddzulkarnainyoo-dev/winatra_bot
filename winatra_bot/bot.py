#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import asyncio
from typing import Dict

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Konfigurasi
TOKEN = os.getenv("BOT_TOKEN", "8853931882:AAFnP69yTmc9STCFrjArqEsm9szke70DoI")
ADMIN_PHONES = [
    os.getenv("ADMIN_PHONE_1", "+6285366374530"),
    os.getenv("ADMIN_PHONE_2", "+6289531801226"),
]

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

user_context: Dict[int, Dict] = {}

ANSWERS = {
    "cara_pakai": "📱 *Cara Pakai Winatra AI:*\n\n1️⃣ Mode Notifikasi...\n2️⃣ Mode Keyboard...",
    "donasi": "💖 *Dukung Pengembangan Winatra AI*\n\n1. Buka aplikasi...",
    "premium_info": "✨ *Fitur Premium*...",
}

def get_admin_contact_text() -> str:
    return f"📞 Hubungi admin: {ADMIN_PHONES[0]} atau {ADMIN_PHONES[1]} (via Telegram)"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Saya asisten Winatra AI. Ketik /help")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start, /help, /carapakai, /donasi, /error, /premium, /admin")

async def cara_pakai_command(update, context):
    await update.message.reply_text(ANSWERS["cara_pakai"], parse_mode="Markdown")

async def donasi_command(update, context):
    await update.message.reply_text(ANSWERS["donasi"], parse_mode="Markdown")

async def error_command(update, context):
    await update.message.reply_text("Solusi error: izin clipboard, notifikasi, dll. Ketik 'bantuan admin' jika perlu.")

async def premium_command(update, context):
    await update.message.reply_text(f"{ANSWERS['premium_info']}\n\n{get_admin_contact_text()}", parse_mode="Markdown")

async def admin_command(update, context):
    await update.message.reply_text(get_admin_contact_text(), parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "premium" in text or "upgrade" in text:
        await premium_command(update, context)
    elif "bantuan admin" in text:
        await admin_command(update, context)
    elif "error" in text or "gagal" in text:
        await error_command(update, context)
    else:
        await update.message.reply_text("Ketik /help untuk bantuan.")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("carapakai", cara_pakai_command))
    app.add_handler(CommandHandler("donasi", donasi_command))
    app.add_handler(CommandHandler("error", error_command))
    app.add_handler(CommandHandler("premium", premium_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot berjalan...")
    await app.run_polling()

if __name__ == "__main__":
    if " " in TOKEN:
        TOKEN = TOKEN.replace(" ", "")
    asyncio.run(main())
