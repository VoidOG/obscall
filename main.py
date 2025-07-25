import logging
import pymongo
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, EditedMessageHandler

# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")  # Use Atlas URI if on cloud
db = client['telegram_mirror']
collection = db['mirrored_messages']

PUBLIC_CHANNEL_ID = '@YourPublicChannelUsername'
PRIVATE_CHANNEL_ID = -1001234567890

async def mirror_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    sent_msg = None
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
    # ... Handle other media types similarly

    if sent_msg:
        collection.insert_one({
            "public_msg_id": msg.message_id,
            "private_msg_id": sent_msg.message_id
        })

async def mirror_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.edited_channel_post
    mapping = collection.find_one({"public_msg_id": msg.message_id})
    if mapping:
        private_msg_id = mapping['private_msg_id']
        await context.bot.edit_message_text(
            chat_id=PRIVATE_CHANNEL_ID,
            message_id=private_msg_id,
            text=msg.text or msg.caption,
            entities=msg.entities or msg.caption_entities
        )

# Deletion polling & advanced sync routines would check the collection for mappings.

if __name__ == '__main__':
    application = ApplicationBuilder().token("YOUR-BOT-TOKEN").build()
    application.add_handler(MessageHandler(filters.Chat(PUBLIC_CHANNEL_ID) & filters.ALL, mirror_new_message))
    application.add_handler(EditedMessageHandler(mirror_edit))
    application.run_polling()
  
