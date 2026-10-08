import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from processor import make_framed_image

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Send me a portrait photo and I will crop it, clip/mask it into "
        "the circular frame, and return the finished design."
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return

    # Accept either Telegram's compressed photo or a document/image.
    if message.photo:
        tg_file = await message.photo[-1].get_file()
        extension = ".jpg"
    elif message.document and (message.document.mime_type or "").startswith("image/"):
        tg_file = await message.document.get_file()
        extension = Path(message.document.file_name or "photo.jpg").suffix or ".jpg"
    else:
        await message.reply_text("Please send an image/portrait photo. / ፎቶ ብቻ ይላኩ። ")
        return

    user_dir = OUTPUT_DIR / str(update.effective_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    input_path = user_dir / f"input{extension}"
    output_path = user_dir / "framed.png"

    await message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
    await tg_file.download_to_drive(input_path)

    try:
        make_framed_image(input_path, output_path)
        with output_path.open("rb") as f:
            await message.reply_document(
                document=f,
                filename="framed.png",
                caption="የአዲስ ኪዳን መነጽር የመጽሃፍ ምርቃት ቀን ስለሚገኙ እናመሰግናለን።"
            )
    except Exception:
        logger.exception("Image processing failed")
        await message.reply_text(
            "I could not process that image. Please try again with a clear portrait photo."
        )


async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Please send a portrait photo.")


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Copy .env.example to .env and add your Telegram bot token."
        )

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))
    app.add_handler(MessageHandler(~(filters.PHOTO | filters.Document.IMAGE), handle_other))

    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
