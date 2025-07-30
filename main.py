import logging
import pymongo
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# MongoDB setup
client = pymongo.MongoClient("mongodb+srv://botnet:botnet@cluster0.izjogcb.mongodb.net/")
db = client['telegram_mirror']
collection = db['mirrored_messages']

# Channel config
PUBLIC_CHANNEL_ID = '@Obscall'
PRIVATE_CHANNEL_ID = -1002376229093

# Mirrors new messages from public channel
async def mirror_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if not msg:
        return

    sent_msg = None

    try:
        if msg.text or msg.caption:
            sent_msg = await context.bot.send_message(
                chat_id=PRIVATE_CHANNEL_ID,
                text=msg.text or msg.caption,
                entities=msg.entities or msg.caption_entities
            )

        elif msg.photo:
            sent_msg = await context.bot.send_photo(
                chat_id=PRIVATE_CHANNEL_ID,
                photo=msg.photo[-1].file_id,
                caption=msg.caption,
                caption_entities=msg.caption_entities
            )

        elif msg.video:
            sent_msg = await context.bot.send_video(
                chat_id=PRIVATE_CHANNEL_ID,
                video=msg.video.file_id,
                caption=msg.caption,
                caption_entities=msg.caption_entities
            )

        elif msg.document:
            sent_msg = await context.bot.send_document(
                chat_id=PRIVATE_CHANNEL_ID,
                document=msg.document.file_id,
                caption=msg.caption,
                caption_entities=msg.caption_entities
            )

        elif msg.audio:
            sent_msg = await context.bot.send_audio(
                chat_id=PRIVATE_CHANNEL_ID,
                audio=msg.audio.file_id,
                caption=msg.caption,
                caption_entities=msg.caption_entities
            )

        elif msg.voice:
            sent_msg = await context.bot.send_voice(
                chat_id=PRIVATE_CHANNEL_ID,
                voice=msg.voice.file_id,
                caption=msg.caption,
                caption_entities=msg.caption_entities
            )

        elif msg.animation:
            sent_msg = await context.bot.send_animation(
                chat_id=PRIVATE_CHANNEL_ID,
                animation=msg.animation.file_id,
                caption=msg.caption,
                caption_entities=msg.caption_entities
            )

        elif msg.sticker:
            sent_msg = await context.bot.send_sticker(
                chat_id=PRIVATE_CHANNEL_ID,
                sticker=msg.sticker.file_id
            )

        if sent_msg:
            collection.insert_one({
                "public_msg_id": msg.message_id,
                "private_msg_id": sent_msg.message_id,
                "msg_type": type(msg.effective_attachment).__name__ if msg.effective_attachment else "text"
            })

    except Exception as e:
        logging.error(f"Failed to mirror message: {e}")

# Mirrors edits of channel messages (text/caption only: Telegram limits media editing)
async def mirror_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.edited_channel_post
    if not msg:
        return

    mapping = collection.find_one({"public_msg_id": msg.message_id})
    if not mapping:
        return

    try:
        if msg.text or msg.caption:
            await context.bot.edit_message_text(
                chat_id=PRIVATE_CHANNEL_ID,
                message_id=mapping['private_msg_id'],
                text=msg.text or msg.caption,
                entities=msg.entities or msg.caption_entities
            )
        # Media edits not supported by Telegram Bot API for channels
    except Exception as e:
        logging.error(f"Failed to edit message: {e}")

# Bot setup
if __name__ == '__main__':
    app = ApplicationBuilder().token("8286785222:AAF5cg4HI210JbTyiYlMFvxJTwXnXiC0eRs").build()

    # New channel posts
    app.add_handler(MessageHandler(
        filters.Chat(PUBLIC_CHANNEL_ID) & filters.UpdateType.CHANNEL_POST,
        mirror_new_message
    ))

    # Edited channel posts
    app.add_handler(MessageHandler(
        filters.Chat(PUBLIC_CHANNEL_ID) & filters.UpdateType.EDITED_CHANNEL_POST,
        mirror_edit
    ))

    app.run_polling()
    
