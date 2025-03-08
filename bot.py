from pyrogram import Client, filters
from pyrogram.errors import ListenerTimeout
from pyrogram.raw import functions, types
import asyncio
import os
from flask import Flask
from threading import Thread

# Flask app to keep bot alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Bot credentials
api_id = 29657994
api_hash = "85f461c4f637911d79c65da1fc2bdd77"
bot_token = "7758775669:AAGG26lYm0sYIfK8OTSaLjJST9FRWTXRSxs"  # Replace with your bot token

bot = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Function to handle user input with timeout
async def ask_with_cancel(client, message, question, timeout=30):
    try:
        response = await client.ask(message.chat.id, question, timeout=timeout)
        if response and response.text.lower() == "/cancel":
            await message.reply("❌ Process canceled.")
            return None
        return response.text if response else None
    except ListenerTimeout:
        await message.reply("⏳ Timeout! Process canceled.")
        return None
    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)}")
        return None

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(
        "👋 **Welcome to the Fake Video Generator Bot!**\n\n"
        "🎭 This bot lets you create fake videos with custom settings.\n"
        "📌 **Commands:**\n"
        "🔹 **/generate** - Create a fake video\n"
        "🔹 **/help** - Instructions\n"
        "🔹 **/cancel** - Stop any process\n\n"
        "🚀 Type **/generate** to start!"
    )

@bot.on_message(filters.command("help"))
async def help_command(client, message):
    await message.reply(
        "🆘 **Help Menu** 🆘\n\n"
        "📌 **Commands:**\n"
        "🔹 **/start** - Welcome message\n"
        "🔹 **/help** - Show this help menu\n"
        "🔹 **/generate** - Start fake video creation\n"
        "🔹 **/cancel** - Stop any process\n\n"
        "⚠️ Need help? Restart the bot and try again!"
    )

@bot.on_message(filters.command("generate"))
async def generate(client, message):
    try:
        custom = await ask_with_cancel(client, message, "🛠️ Enter 'yes' for custom settings or 'no' for default:")
        if not custom:
            return

        # Set default values
        custom_htm = "default.htm"
        custom_thumb = "default.jpg"
        custom_duration = 0
        custom_size = (1024, 564)
        custom_caption = "Here is your generated fake video! 🎥"

        if custom.lower() == "yes":
            htm_response = await client.ask(message.chat.id, "📄 Send .htm file or type 'default':", timeout=30)
            if htm_response and htm_response.document:
                custom_htm = await htm_response.download()
            elif htm_response.text.lower() != "default":
                custom_htm = htm_response.text

            thumb_response = await client.ask(message.chat.id, "🖼️ Send thumbnail or type 'default':", timeout=30)
            if thumb_response and (thumb_response.document or thumb_response.photo):
                custom_thumb = await thumb_response.download()
            elif thumb_response.text.lower() != "default":
                custom_thumb = thumb_response.text

            duration_response = await ask_with_cancel(client, message, "⏱️ Enter video duration (or 'default'):")
            if duration_response and duration_response.isdigit():
                custom_duration = int(duration_response)

            size_response = await ask_with_cancel(client, message, "📏 Enter resolution (width,height) or 'default':")
            if size_response and size_response.lower() != "default":
                try:
                    w, h = map(int, size_response.split(","))
                    custom_size = (w, h)
                except ValueError:
                    await message.reply("⚠️ Invalid format. Using default 1024x564.")

            caption_response = await ask_with_cancel(client, message, "✍️ Enter caption (or 'default'):")
            if caption_response and caption_response.lower() != "default":
                custom_caption = caption_response

        # Verify files exist
        if not os.path.exists(custom_htm):
            await message.reply("⚠️ Missing HTML file! Aborting.")
            return
        if not os.path.exists(custom_thumb):
            await message.reply("⚠️ Missing thumbnail! Aborting.")
            return

        # Upload files
        input_file = await client.upload_file(custom_htm)
        input_thumb = await client.upload_file(custom_thumb)

        # Create fake video metadata
        media = types.InputMediaUploadedDocument(
            file=input_file,
            mime_type="video/mp4",
            attributes=[
                types.DocumentAttributeVideo(
                    duration=custom_duration,
                    w=custom_size[0],
                    h=custom_size[1],
                    supports_streaming=True
                ),
                types.DocumentAttributeFilename(file_name="fake_video.htm")
            ],
            thumb=input_thumb,
            force_file=False
        )

        # Send the fake video
        await client.invoke(
            functions.messages.SendMedia(
                peer=await client.resolve_peer(message.chat.id),
                media=media,
                message=custom_caption,
                random_id=client.rnd_id()
            )
        )

        await message.reply("✅ Fake video sent successfully!")

        # Clean up downloaded files
        if custom_htm != "default.htm":
            os.remove(custom_htm)
        if custom_thumb != "default.jpg":
            os.remove(custom_thumb)

    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)}")

# Start Flask in a separate thread
Thread(target=run_flask, daemon=True).start()

# Run bot
async def main():
    await bot.start()
    print("Bot is running...")
    await asyncio.Event().wait()  # Keep the bot running

asyncio.run(main())
