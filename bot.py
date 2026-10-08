from contextlib import asynccontextmanager
from http import HTTPStatus
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
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
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").strip()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# --- HANDLERS (Unchanged) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
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


# --- APPLICATION SETUP ---
if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing. Add your Telegram bot token to environment variables."
    )

ptb_app = Application.builder().token(BOT_TOKEN).build()
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))
ptb_app.add_handler(MessageHandler(~(filters.PHOTO | filters.Document.IMAGE), handle_other))


# --- FASTAPI WEBHOOK WRAPPER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set the webhook URL with Telegram automatically when Render starts
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/webhook"
        logger.info(f"Setting webhook to {webhook_url}")
        await ptb_app.bot.set_webhook(url=webhook_url)
    else:
        logger.warning("RENDER_EXTERNAL_URL not set. Skipping automated webhook setup.")

    async with ptb_app:
        await ptb_app.start()
        yield
        await ptb_app.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health_check():
    return {"status": "ok", "bot": "running"}


@app.post("/webhook")
async def process_update(request: Request):
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=HTTPStatus.OK)