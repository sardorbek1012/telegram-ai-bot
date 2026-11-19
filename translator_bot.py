import asyncio
import difflib
import os

from deep_translator import GoogleTranslator
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

LANGS = {
    "uz": ("uz", "O'zbekcha"),
    "ru": ("ru", "Ruscha"),
    "en": ("en", "Inglizcha"),
    "tr": ("tr", "Turkcha"),
    "ar": ("ar", "Arabcha"),
    "ko": ("ko", "Koreyscha"),
}
MAX_LEN = 4500


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("target", None)
    await update.message.reply_text(
        "Salom! Men tarjimon botman.\n\n"
        "Avtomatik ishlashi:\n"
        "- O'zbekcha yozsangiz, inglizchaga tarjima qilaman.\n"
        "- Boshqa tilda yozsangiz, o'zbekchaga tarjima qilaman.\n\n"
        "Tilni o'zingiz tanlash: /ru /en /tr /ar /ko /uz\n"
        "Avtomatik rejimga qaytish: /auto"
    )


async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.split()[0].lstrip("/").split("@")[0].lower()
    if cmd in LANGS:
        context.user_data["target"] = LANGS[cmd][0]
        await update.message.reply_text(
            f"Endi hamma matnni {LANGS[cmd][1]} tiliga tarjima qilaman. "
            "Avtomatik rejimga qaytish: /auto"
        )


async def set_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("target", None)
    await update.message.reply_text(
        "Avtomatik rejim yoqildi: o'zbekcha -> inglizcha, boshqa til -> o'zbekcha"
    )


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def translate(text: str, target):
    if target:
        return GoogleTranslator(source="auto", target=target).translate(text)

    to_uz = GoogleTranslator(source="auto", target="uz").translate(text) or ""
    similarity = difflib.SequenceMatcher(None, _norm(text), _norm(to_uz)).ratio()
    if similarity > 0.85:
        return GoogleTranslator(source="uz", target="en").translate(text)
    return to_uz


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    if len(text) > MAX_LEN:
        await update.message.reply_text("Matn juda uzun, qisqaroq qilib yuboring.")
        return

    target = context.user_data.get("target")
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    try:
        result = await asyncio.to_thread(translate, text, target)
    except Exception as e:
        print("Tarjima xatosi:", e)
        await update.message.reply_text("Tarjima qilib bo'lmadi, keyinroq urinib ko'ring.")
        return

    await update.message.reply_text(result or "Tarjima chiqmadi, boshqa matn yuboring.")


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("auto", set_auto))
    app.add_handler(CommandHandler(list(LANGS.keys()), set_lang))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()


if __name__ == "__main__":
    main() 