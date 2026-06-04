#!/usr/bin/env python3
"""
Winatra AI Customer Support Bot for Telegram
Bot ini berfungsi sebagai first line support untuk aplikasi Winatra AI
Dengan fitur admin anonim: user bisa menghubungi admin via @admin tanpa melihat identitas admin

Mode: Webhook (siap deploy ke Railway)
"""

import logging
import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ========== KONFIGURASI ENVIRONMENT (LANGSUNG DARI RAILWAY) ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_GROUP_ID = int(os.environ.get("ADMIN_GROUP_ID", "-1004250133633"))

# Konfigurasi webhook dari Railway
PORT = int(os.environ.get("PORT", 8080))
RAILWAY_PUBLIC_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
WEBHOOK_URL = f"https://{RAILWAY_PUBLIC_DOMAIN}/webhook" if RAILWAY_PUBLIC_DOMAIN else ""

# ========== LOGGING ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ========== STATE & MAPPING ==========
user_context = {}           # Menyimpan state percakapan user
forwarded_map = {}          # {message_id_di_grup_admin: user_id}

# ========== PENGETAHUAN BOT ==========
ANSWERS = {
    "cara_pakai": """📱 *Cara Pakai Winatra AI:*

*Mode Notifikasi:*
1️⃣ Copy teks soal dari app lain
2️⃣ Notifikasi Winatra AI akan muncul
3️⃣ Tekan tombol "Jawab"
4️⃣ Untuk Essay: AI auto-copy jawaban
5️⃣ Untuk PG: Pop-up pilihan + tombol "Kenapa?"
6️⃣ Auto-solve: Jika soal diakhiri tanda `?`, AI auto-solve

*Mode Keyboard:*
1️⃣ Aktifkan di Pengaturan
2️⃣ Tiga tab tersedia: Ketik, Tanya AI, Baca
3️⃣ Lebih praktis jika clipboard bermasalah

Butuh bantuan lebih? Ketik: /error""",

    "donasi": """💖 *Dukung Pengembangan Winatra AI*

*Langkah-langkah donasi:*
1️⃣ Buka aplikasi Winatra AI
2️⃣ Pergi ke halaman 'Dukung Kami'
3️⃣ Pilih metode QRIS (semua bank/e-wallet diterima)
4️⃣ Lakukan transfer minimal Rp10.000
5️⃣ Kirim bukti transfer ke Instagram: *@winatraa__24*
6️⃣ Sertakan email akun Anda dalam pesan

✅ Admin akan upgrade akun Anda ke *Premium dalam 1x24 jam*

*Pertanyaan lain tentang premium?* Ketik: /premium""",

    "approval": """⏳ *Status Approval Akun Winatra AI*

Setelah Anda mendaftar:
- Status awal: *PENDING*
- Admin akan verify akun Anda secara manual via dashboard
- ⏱️ Waktu tunggu: *Maksimal 1x24 jam*

*Jika akun belum approve setelah 24 jam:*
Ketik: @admin beri tahu akun saya belum di-approve

Terima kasih atas kesabaran Anda! 🙏""",

    "error_clipboard": """⚠️ *Solusi: Clipboard Tidak Terbaca*

*Langkah penyelesaian:*
1️⃣ Buka Pengaturan HP → Aplikasi
2️⃣ Cari "Winatra AI"
3️⃣ Berikan izin akses clipboard
4️⃣ Restart aplikasi Winatra AI
5️⃣ Coba copy-paste soal lagi

*Alternatif:*
Gunakan Mode Keyboard (aktifkan di Pengaturan aplikasi)

*Jika masih tidak berhasil:*
Ketik: @admin saya masih error clipboard""",

    "error_notifikasi": """🔕 *Solusi: Notifikasi Tidak Muncul*

*Langkah penyelesaian:*
1️⃣ Buka Pengaturan HP → Notifikasi
2️⃣ Pastikan Winatra AI *notifikasi aktif*
3️⃣ Buka Pengaturan → Baterai
4️⃣ Matikan "Optimasi Baterai" untuk Winatra AI
5️⃣ Pastikan aplikasi berjalan di background

*Alternatif:*
Gunakan Mode Keyboard (tidak perlu notifikasi)

*Jika masih tidak berhasil:*
Ketik: @admin saya masih tidak terima notifikasi""",

    "force_update": """🔄 *Penjelasan Force Update*

Jika muncul notifikasi "Force Update":
- Ini berarti ada versi terbaru yang wajib diinstall
- Download APK terbaru dari link yang dikirim dalam notifikasi
- Install APK tanpa menghapus aplikasi lama
- Update akan selesai dan Anda bisa langsung pakai fitur terbaru

💡 *Tips:*
- Pastikan punya storage minimal 100MB
- Gunakan WiFi untuk download lebih cepat
- Jangan uninstall aplikasi sebelum update selesai""",

    "premium_info": """✨ *Fitur Premium Winatra AI*

*Keuntungan Premium:*
✅ Unlimited pertanyaan (tidak ada batasan)
✅ Mode Offline (AI bekerja tanpa internet)
✅ Prioritas support (respon lebih cepat)
✅ Tanpa iklan (pengalaman bersih)
✅ Fitur-fitur eksklusif terbaru

*Harga:*
💰 Rp25.000/bulan atau sesuai promo terkini

*Cara upgrade:*
1️⃣ Metode 1: Donasi via QRIS → kirim bukti ke IG @winatraa__24
2️⃣ Metode 2: Ketik @admin untuk menghubungi tim support anonim""",

    "admin_help": """📞 *Hubungi Tim Support Secara Anonim*

Ketik: `@admin` diikuti pertanyaan/masalah Anda

Contoh:
• `@admin saya error clipboard`
• `@admin mau upgrade premium`
• `@admin akun saya belum di-approve`

Tim admin akan membalas pesan Anda melalui bot ini. Identitas admin tetap anonim! 🔒""",
}

# ========== HANDLER PERINTAH ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_context[user_id] = {"state": "idle"}
    welcome_message = """👋 *Selamat Datang di Winatra AI Support Bot!*

Saya di sini untuk membantu Anda dengan:
✅ Pertanyaan tentang cara pakai Winatra AI
✅ Masalah teknis (error, clipboard, notifikasi)
✅ Informasi donasi & upgrade premium
✅ Status approval akun
✅ Kontak admin secara anonim

*Pilih menu di bawah atau ketik salah satu:*

/carapakai - Cara menggunakan Winatra AI
/donasi - Informasi donasi & upgrade premium
/error - Solusi error umum
/premium - Fitur & harga premium
/admin - Hubungi tim support anonim
/help - Tampilkan menu bantuan

Atau ketik pertanyaan Anda langsung! 😊"""
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """📚 *Menu Bantuan Winatra AI Support*

*Perintah yang tersedia:*
/start - Tampilkan pesan sambutan
/help - Tampilkan menu ini
/carapakai - Cara menggunakan Winatra AI
/donasi - Informasi donasi & upgrade premium
/error - Solusi error umum
/premium - Fitur & harga premium
/admin - Hubungi tim support anonim

*Atau langsung ketik pertanyaan Anda:*
• "Gimana cara pakai mode notifikasi?"
• "Clipboard tidak terbaca"
• "Mau beli premium"
• "Bantuan admin"
• Dan lainnya...

*Atau gunakan fitur admin anonim:*
Ketik: @admin <pertanyaan/masalah Anda>

Bot ini adalah first line support. Jika masalah tidak terselesaikan, kami akan mengarahkan Anda ke tim admin profesional kami."""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def carapakai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_context[update.effective_user.id] = {"state": "idle"}
    await update.message.reply_text(ANSWERS["cara_pakai"], parse_mode="Markdown")

async def donasi_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_context[update.effective_user.id] = {"state": "idle"}
    await update.message.reply_text(ANSWERS["donasi"], parse_mode="Markdown")

async def error_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_context[user_id] = {"state": "dealing_with_error"}
    error_menu = """⚠️ *Solusi Error Umum Winatra AI*

Pilih error yang Anda alami:

1️⃣ *Clipboard tidak terbaca*
   → Ketik: clipboard

2️⃣ *Notifikasi tidak muncul*
   → Ketik: notifikasi

3️⃣ *Force Update*
   → Ketik: force update

4️⃣ *Masalah lainnya*
   → Ketik: @admin <jelaskan masalah Anda>

Atau jelaskan masalah Anda secara langsung! 🔧"""
    await update.message.reply_text(error_menu, parse_mode="Markdown")

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_context[user_id] = {"state": "interested_in_premium"}
    await update.message.reply_text(ANSWERS["premium_info"], parse_mode="Markdown")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_context[user_id] = {"state": "contacted_admin"}
    await update.message.reply_text(ANSWERS["admin_help"], parse_mode="Markdown")

# ========== ADMIN ANONIM HANDLER ==========
async def admin_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text
    username = update.effective_user.username or "tanpa username"

    if user_text.lower().startswith("@admin "):
        message_content = user_text[7:].strip()
    elif user_text.lower().startswith("/adminchat "):
        message_content = user_text[11:].strip()
    else:
        message_content = user_text

    if not message_content:
        await update.message.reply_text("⚠️ Silakan ketik pesan Anda setelah @admin\n\nContoh: @admin saya error clipboard", parse_mode="Markdown")
        return

    forward_text = f"""📨 *Pesan dari User*

🆔 User ID: `{user_id}`
👤 Username: @{username}

*Pesan:*
{message_content}"""

    try:
        admin_message = await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=forward_text, parse_mode="Markdown")
        forwarded_map[admin_message.message_id] = user_id
        await update.message.reply_text("✅ Pesan Anda telah dikirim ke tim support.\n\nTim admin akan membalas dalam waktu segera. Tunggu balasan melalui bot ini! 🙏", parse_mode="Markdown")
        logger.info(f"Pesan dari user {user_id} dikirim ke grup admin")
    except Exception as e:
        logger.error(f"Gagal mengirim pesan ke grup admin: {e}")
        await update.message.reply_text("❌ Maaf, terjadi error saat mengirim pesan. Silakan coba lagi.", parse_mode="Markdown")

async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat_id != ADMIN_GROUP_ID:
        return
    if not update.message.reply_to_message:
        return

    replied_to_msg_id = update.message.reply_to_message.message_id
    admin_reply_text = update.message.text

    if replied_to_msg_id not in forwarded_map:
        logger.info("Reply di grup admin bukan untuk pesan forward user. Abaikan.")
        return

    user_id = forwarded_map[replied_to_msg_id]
    reply_message = f"""📩 *Balasan dari Tim Support:*

{admin_reply_text}"""

    try:
        await context.bot.send_message(chat_id=user_id, text=reply_message, parse_mode="Markdown")
        del forwarded_map[replied_to_msg_id]
        logger.info(f"Balasan admin dikirim ke user {user_id}")
    except Exception as e:
        logger.error(f"Gagal mengirim balasan ke user {user_id}: {e}")

# ========== HANDLER PESAN TEKS BIASA ==========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat_id == ADMIN_GROUP_ID:
        return

    user_id = update.effective_user.id
    user_text = update.message.text.lower().strip()

    if user_id not in user_context:
        user_context[user_id] = {"state": "idle"}
    current_state = user_context[user_id].get("state", "idle")

    response = None

    if any(k in user_text for k in ["clipboard", "clipboard tidak terbaca", "copy paste"]):
        response = ANSWERS["error_clipboard"]
        user_context[user_id]["state"] = "dealing_with_error"
    elif any(k in user_text for k in ["notifikasi", "notifikasi tidak muncul", "tidak dapat notifikasi"]):
        response = ANSWERS["error_notifikasi"]
        user_context[user_id]["state"] = "dealing_with_error"
    elif any(k in user_text for k in ["force update", "update", "apk"]):
        response = ANSWERS["force_update"]
        user_context[user_id]["state"] = "idle"
    elif any(k in user_text for k in ["cara pakai", "gimana cara", "bagaimana cara", "notifikasi", "keyboard", "mode", "auto solve"]):
        response = ANSWERS["cara_pakai"]
        user_context[user_id]["state"] = "idle"
    elif any(k in user_text for k in ["donasi", "dukung", "qris", "transfer", "bukti", "biaya"]):
        response = ANSWERS["donasi"]
        user_context[user_id]["state"] = "idle"
    elif any(k in user_text for k in ["approval", "pending", "belum approve", "verifikasi", "status akun"]):
        response = ANSWERS["approval"]
        user_context[user_id]["state"] = "idle"
    elif any(k in user_text for k in ["premium", "beli premium", "upgrade", "langganan"]):
        response = ANSWERS["premium_info"]
        user_context[user_id]["state"] = "interested_in_premium"
    elif any(k in user_text for k in ["admin", "hubungi admin", "kontak admin", "bantuan admin"]):
        response = ANSWERS["admin_help"]
        user_context[user_id]["state"] = "idle"
    elif current_state == "dealing_with_error" and any(k in user_text for k in ["tetap tidak bisa", "masih tidak bisa", "tetap gagal", "masih gagal", "masih error"]):
        response = ANSWERS["admin_help"]
        user_context[user_id]["state"] = "contacted_admin"
    else:
        response = """🤖 *Maaf, saya kurang memahami pertanyaan Anda.*

Silakan coba salah satu dari opsi berikut:

/carapakai - Cara menggunakan Winatra AI
/donasi - Informasi donasi & upgrade premium
/error - Solusi error umum
/premium - Fitur & harga premium
/admin - Hubungi tim support anonim
/help - Tampilkan menu bantuan

Atau langsung ketik pertanyaan Anda dengan detail! 😊"""
        user_context[user_id]["state"] = "idle"

    if response:
        await update.message.reply_text(response, parse_mode="Markdown")

# ========== ERROR HANDLER ==========
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Maaf, terjadi kesalahan. Silakan coba lagi atau ketik /help")

# ========== MAIN WEBHOOK ==========
async def main() -> None:
    if not BOT_TOKEN:
        logger.error("❌ ERROR: BOT_TOKEN tidak ditemukan. Pastikan variabel environment BOT_TOKEN sudah diatur di Railway.")
        return
    if not WEBHOOK_URL:
        logger.error("❌ ERROR: RAILWAY_PUBLIC_DOMAIN tidak ditemukan. Pastikan deploy di Railway.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("carapakai", carapakai_command))
    application.add_handler(CommandHandler("donasi", donasi_command))
    application.add_handler(CommandHandler("error", error_command))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("admin", admin_command))

    # Handler untuk @admin atau /adminchat
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & (filters.Regex(r"^@admin\s+") | filters.Regex(r"^/adminchat\s+")),
            admin_chat_handler
        )
    )

    # Handler untuk balasan admin di grup internal
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Chat(chat_id=ADMIN_GROUP_ID),
            admin_reply_handler
        )
    )

    # Handler teks biasa (keyword)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)

    # Set webhook dan mulai server
    await application.initialize()
    await application.bot.set_webhook(url=WEBHOOK_URL)
    logger.info(f"✅ Webhook berhasil disetel ke {WEBHOOK_URL}")

    logger.info("🚀 Bot Winatra AI berjalan dalam mode webhook...")
    await application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    # Fix untuk Windows (tidak diperlukan di Railway, tapi aman)
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot dihentikan oleh user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")