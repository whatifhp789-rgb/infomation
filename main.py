import asyncio
import re
import json
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)
from telegram.constants import ChatMemberStatus

# ==========================
# CONFIG
# ==========================
BOT_TOKEN = "8693148816:AAGtEdT7kI3UXMYcXahqDeATa5AdGEA3br0"
OWNER_USERNAME = "@SANJUklNG"
API_BASE = "https://san-ju.vercel.app/userid/"

# Force Join Channel & Group
FORCE_CHANNEL_ID = -1002091456364
FORCE_CHANNEL_LINK = "https://t.me/+pDQ_FnUdGD00Zjk1"
FORCE_GROUP_LINK = "https://t.me/+opPct8-cKC0zZDZl"

# ==========================
# WELCOME MESSAGE WITH VERIFY BUTTONS
# ==========================
async def send_welcome_with_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message with inline buttons to join channel/group and verify."""
    keyboard = [
        [
            InlineKeyboardButton("📢 Join Channel", url=FORCE_CHANNEL_LINK),
            InlineKeyboardButton("👥 Join Group", url=FORCE_GROUP_LINK),
        ],
        [
            InlineKeyboardButton("✅ Joined - Verify", callback_data="verify_join"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"**Welcome {update.effective_user.first_name}!**\n\n"
        "Please join these first:\n"
        "🔹 Channel\n"
        "🔹 Group\n\n"
        "After joining, click **Verify** button!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==========================
# VERIFY CALLBACK
# ==========================
async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    try:
        member = await context.bot.get_chat_member(chat_id=FORCE_CHANNEL_ID, user_id=user_id)
        
        # Check status
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await query.edit_message_text("✅ Verification successful! You can now use the bot.")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="System Online...\nNumber Info Bot Ready!\nEnter Target Number:\n9876543210\nDeveloper: {SANJU}")
        else:
            await query.answer("❌ Aapne abhi tak channel join nahi kiya hai!", show_alert=True)
            
    except Exception as e:
        print(f"Error: {e}")
        # Pehle error batayein
        await query.answer("❌ Error: Check karein ki bot channel mein Admin hai.", show_alert=True)
        # Phir naya message bhejein jisme button ho
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please join the channel and try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=FORCE_CHANNEL_LINK)],
                [InlineKeyboardButton("Verify Again", callback_data="verify_join")]
            ])
        )

# ==========================
# FORCE JOIN CHECK (UPDATED)
# ==========================
async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if user is a member of the channel.
    If not, send the welcome-with-verify message and return False.
    If yes, return True.
    """
    user_id = update.effective_user.id

    try:
        member = await context.bot.get_chat_member(FORCE_CHANNEL_ID, user_id)
        if member.status in (ChatMemberStatus.MEMBER,
                             ChatMemberStatus.ADMINISTRATOR,
                             ChatMemberStatus.OWNER):
            return True
        else:
            # Not a member – send welcome
            await send_welcome_with_verify(update, context)
            return False
    except Exception:
        # If bot can't check, still send welcome
        await send_welcome_with_verify(update, context)
        return False

# ==========================
# START COMMAND
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_force_join(update, context):
        # Already joined – show main menu
        await update.message.reply_text(
            "⚡ System Online...\n\n"
            "🤖 Number Info Bot Ready!\n\n"
            "📱 Enter Target Number:\n"
            "💡 9876543210\n\n"
            f"👨‍💻 Developer: {SANJUKlNG}"
        )

# ==========================
# /NUM COMMAND
# ==========================
async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_force_join(update, context):
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Usage:\n"
            "/num 9876543210"
        )
        return

    number = context.args[0]
    await process_number(update, number)

# ==========================
# HANDLE NORMAL MESSAGE
# ==========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_force_join(update, context):
        return

    text = update.message.text.strip()

    if re.match(r'^\+?[\d\s\-()]+$', text):
        number = re.sub(r'[\s\-()]', '', text)

        if re.fullmatch(r'\+?\d{7,15}', number):
            await process_number(update, number)
            return

# ==========================
# PROCESS NUMBER
# ==========================
async def process_number(update: Update, number: str):
    url = API_BASE + number

    try:
        msg = await update.message.reply_text(
            "🔍 Fetching Data..."
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                timeout=10.0
            )

        if response.status_code != 200:
            await msg.edit_text(
                f"❌ API Error: HTTP {response.status_code}"
            )
            return

        data = response.json()

        if isinstance(data, dict):
            data.pop("developer", None)
            data.pop("channel", None)

        json_output = json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        )

        await msg.edit_text(
            f"📋 Number Information\n\n"
            f"```json\n{json_output}\n```",
            parse_mode="Markdown"
        )

    except httpx.RequestError as e:
        await update.message.reply_text(
            f"❌ Network Error:\n{str(e)}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Failed:\n{str(e)}"
        )

# ==========================
# MAIN
# ==========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("num", num_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_join$"))

    print("✅ Bot is running... (with verify buttons)")
    app.run_polling()

# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    main()
