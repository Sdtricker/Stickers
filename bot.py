from pyromod import Client
from pyromod.exceptions.listener_timeout import ListenerTimeout
from pyrogram import filters
from pyrogram.raw import functions, types
import os
from flask import Flask

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

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Function to handle user input with timeout
async def ask_with_cancel(c, m, question, timeout=30):
    try:
        response = await c.ask(m.chat.id, question, timeout=timeout)
        if response and response.text and response.text.lower() == "/cancel":
            await m.reply("❌ Process canceled.")
            return None
        return response.text if response else None
    except ListenerTimeout:
        await m.reply("⏳ Timeout! Process canceled.")
        return None
    except Exception as e:
        await m.reply(f"⚠️ Error: {str(e)}")
        return None

@app.on_message(filters.command("start"))
async def start(c, m):
    await m.reply(
        "👋 **Welcome to the Fake Video Generator Bot!**\n\n"
        "🎭 This bot lets you create fake videos with custom settings.\n"
        "💡 You can use it to experiment, test, or just have fun!\n\n"
        "📌 **Available Commands:**\n"
        "🔹 **/generate** - Start creating a fake video\n"
        "🔹 **/help** - Get detailed instructions\n"
        "🔹 **/cancel** - Stop any ongoing process\n\n"
        "🚀 **Get Started:** Just type **/generate** and follow the prompts!\n\n"
        "⚠️ Need help? Use **/help** for guidance."
    )

@app.on_message(filters.command("help"))
async def help_command(c, m):
    await m.reply(
        "🆘 **Help Menu** 🆘\n\n"
        "This bot allows you to generate fake videos with customizable settings.\n\n"
        "📌 **Available Commands:**\n"
        "🔹 **/start** - Welcome message and basic info.This bot made by @GOAT_NG \n"
        "🔹 **/help** - Show this help menu.\n"
        "🔹 **/generate** - Start the fake video generation process.\n"
        "🔹 **/cancel** - Stop any ongoing process.\n\n"
        "📋 **How to Use:**\n"
        "1️⃣ Use **/generate** to create a fake video.\n"
        "2️⃣ Follow the prompts to customize or use default settings.\n"
        "3️⃣ Receive your generated fake video.\n\n"
        "⚠️ If you face any issues, simply restart the bot and try again.\n\n"
        "🚀 Happy generating!"
    )

@app.on_message(filters.command("generate"))
async def generate(c, m):
    try:
        custom = await ask_with_cancel(c, m, "🛠️ Enter 'yes' for custom settings or 'no' for direct generation:")
        if not custom:
            return

        # Set default values
        custom_htm = "default.htm"
        custom_thumb = "default.jpg"
        custom_duration = 0
        custom_size = (1024, 564)
        custom_caption = "Here is your generated fake video! 🎥"

        if custom.lower() == "yes":
            # Ask for custom .htm file
            htm_response = await c.ask(m.chat.id, "📄 Send your .htm file or type 'default' for default.htm:", timeout=30)
            if htm_response:
                # Check if a document was attached
                if htm_response.document:
                    custom_htm = await htm_response.download()  # Download the .htm file
                elif htm_response.text.lower() != "default" and os.path.exists(htm_response.text):
                    custom_htm = htm_response.text
                else:
                    await m.reply("⚠️ .htm file not found! Using default.htm.")

            # Ask for custom thumbnail
            thumb_response = await c.ask(m.chat.id, "🖼️ Send your thumbnail (image) or type 'default' for default.jpg:", timeout=30)
            if thumb_response:
                if thumb_response.document or thumb_response.photo:
                    custom_thumb = await thumb_response.download()  # Download the thumbnail
                elif thumb_response.text.lower() != "default" and os.path.exists(thumb_response.text):
                    custom_thumb = thumb_response.text
                else:
                    await m.reply("⚠️ Thumbnail file not found! Using default.jpg.")

            # Ask for custom duration
            duration_response = await ask_with_cancel(c, m, "⏱️ Enter custom video duration in seconds (or 'default' for 0s):")
            if duration_response and duration_response.isdigit():
                custom_duration = int(duration_response)

            # Ask for custom resolution
            size_response = await ask_with_cancel(c, m, "📏 Enter resolution as width,height (or 'default' for 1024,564):")
            if size_response and size_response.lower() != "default":
                try:
                    w, h = map(int, size_response.split(","))
                    custom_size = (w, h)
                except ValueError:
                    await m.reply("⚠️ Invalid resolution format. Using default 1024x564.")

            # Ask for custom caption
            caption_response = await ask_with_cancel(c, m, "✍️ Enter a custom caption for your video (or 'default' for standard caption):")
            if caption_response and caption_response.lower() != "default":
                custom_caption = caption_response

        # Verify that the files exist (or were downloaded)
        if not os.path.exists(custom_htm):
            await m.reply("⚠️ Missing HTML file! Aborting process.")
            return
        if not os.path.exists(custom_thumb):
            await m.reply("⚠️ Missing thumbnail file! Aborting process.")
            return

        # Open and read the .htm file
        with open(custom_htm, "rb") as f:
            file_data = f.read()

        file_id = c.rnd_id()
        await c.invoke(
            functions.upload.SaveFilePart(
                file_id=file_id,
                file_part=0,
                bytes=file_data
            )
        )

        input_file = types.InputFile(
            id=file_id,
            parts=1,
            name="fake_video.htm",
            md5_checksum=""
        )

        # Open and read the thumbnail
        with open(custom_thumb, "rb") as f:
            thumb_data = f.read()

        thumb_id = c.rnd_id()
        await c.invoke(
            functions.upload.SaveFilePart(
                file_id=thumb_id,
                file_part=0,
                bytes=thumb_data
            )
        )

        input_thumb = types.InputFile(
            id=thumb_id,
            parts=1,
            name="thumbnail.jpg",
            md5_checksum=""
        )

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

        # Send the fake video with a custom caption
        await c.invoke(
            functions.messages.SendMedia(
                peer=await c.resolve_peer(m.chat.id),
                media=media,
                message=custom_caption,
                random_id=c.rnd_id()
            )
        )

        await m.reply("✅ File sent successfully with fake video metadata!")

        # Clean up downloaded files (if they are not the defaults)
        if custom_htm != "default.htm":
            os.remove(custom_htm)
        if custom_thumb != "default.jpg":
            os.remove(custom_thumb)

    except Exception as e:
        await m.reply(f"⚠️ An unexpected error occurred: {str(e)}")

app.run()
