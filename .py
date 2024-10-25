from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import randomfrom
import logging

# Replace 'YOUR_TOKEN' with your bot's token from BotFather
TOKEN = '7812041653:AAGs1jDYw2brgpUHpHNqCwwPpTa1MMhVF5o'

# Replace this with your Telegram user ID (Admin ID)
ADMIN_ID = 1910885330

# Conversation states
GENDER, AGE, LOCATION, PREFERENCE, INTERESTS = range(5)

# Lists for gender and location selection
GENDER_OPTIONS = ['Male', 'Female', 'Other']
MATCH_OPTIONS = ['Male', 'Female', 'Any']

# Store user data and logs
waiting_users = {}
matched_pairs = {}
user_stats = {}
chat_logs = []

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when /start is issued."""
    update.message.reply_text('Welcome! Type /join to find a chat partner.')

def join(update: Update, context: CallbackContext) -> int:
    """Start collecting user info for matchmaking."""
    reply_keyboard = [GENDER_OPTIONS]
    update.message.reply_text(
        "Please select your gender:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return GENDER

def gender(update: Update, context: CallbackContext) -> int:
    """Store user's gender and ask for age."""
    context.user_data['gender'] = update.message.text
  update.message.reply_text("Please enter your age:")
    return AGE

def age(update: Update, context: CallbackContext) -> int:
    """Store user's age and ask for location."""
    age = update.message.text
    if not age.isdigit() or int(age) < 13:
        update.message.reply_text("Please enter a valid age (13 or older):")
        return AGE
    context.user_data['age'] = age
    update.message.reply_text("Please enter your location:")
    return LOCATION

def location(update: Update, context: CallbackContext) -> int:
    """Store user's location and ask for match preference."""
    context.user_data['location'] = update.message.text
    reply_keyboard = [MATCH_OPTIONS]
    update.message.reply_text(
        "Who would you like to chat with? (Male/Female/Any):",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return PREFERENCE

def preference(update: Update, context: CallbackContext) -> int:
    """Store user preferences and ask for interests."""
    context.user_data['preference'] = update.message.text
    update.message.reply_text("Please enter your interests (e.g., music, sports):")
    return INTERESTS

def interests(update: Update, context: CallbackContext) -> int:
    """Store user interests and try to find a match."""
    context.user_data['interests'] = update.message.text
    user_id = update.message.from_user.id

    # Add user info to waiting_users and user_stats
    user_info = {
        'chat_id': update.message.chat.id,
        'gender': context.user_data['gender'],
        'age': context.user_data['age'],
        'location': context.user_data['location'],
        'preference': context.user_data['preference'],
        'interests': context.user_data['interests']
    }
    waiting_users[user_id] = user_info

    # Store user stats
    user_stats[user_id] = user_info

    update.message.reply_text("You've joined the waiting list. Finding a match...")

    # Try to find a match
    match_found = False
    for other_user_id, other_user_data in waiting_users.items():
        if other_user_id != user_id:
            # Check gender preference match
            if (context.user_data['preference'] == 'Any' or other_user_data['gender'] == context.user_data['preference']):
                # Match found
                matched_pairs[user_id] = other_user_id
                matched_pairs[other_user_id] = user_id

                context.bot.send_message(chat_id=user_id, text="You've been matched! Start chatting.")
                context.bot.send_message(chat_id=other_user_id, text="You've been matched! Start chatting.")

                # Remove users from waiting list
                del waiting_users[user_id]
                del waiting_users[other_user_id]
                match_found = True
                break

    if not match_found:
        update.message.reply_text("Still waiting for a match...")

    return ConversationHandler.END

def update_profile(update: Update, context: CallbackContext) -> None:
    """Update user profile information."""
    user_id = update.message.from_user.id
    if user_id in user_stats:
        update.message.reply_text("What would you like to update? (e.g., interests)")
    else:
        update.message.reply_text("You need to join first using /join.")

def handle_profile_update(update: Update, context: CallbackContext) -> None:
    """Handle user input for profile updates."""
    user_id = update.message.from_user.id
    if user_id in user_stats:
        user_stats[user_id]['interests'] = update.message.text
        update.message.reply_text("Your profile has been updated!")
    else:
        update.message.reply_text("You haven't initiated a profile update yet. Use /update_profile.")

def message_handler(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages and forward them to the matched partner."""
    user_id = update.message.from_user.id
    if user_id in matched_pairs:
        partner_id = matched_pairs[user_id]

        # Log the chat
        chat_logs.append({
            'user_id': user_id,
            'partner_id': partner_id,
            'message': update.message.text
        })

        # Forward the message to the matched partner
        context.bot.send_message(chat_id=partner_id, text=update.message.text)

def leave(update: Update, context: CallbackContext) -> None:
    """Remove user from the waiting list or chat."""
    user_id = update.message.from_user.id
    if user_id in waiting_users:
        del waiting_users[user_id]
        update.message.reply_text("You've been removed from the waiting list.")
    elif user_id in matched_pairs:
        partner_id = matched_pairs[user_id]
        del matched_pairs[user_id]
        del matched_pairs[partner_id]
        context.bot.send_message(chat_id=partner_id, text="Your chat partner has left the conversation.")
        update.message.reply_text("You've left the chat.")

def stats(update: Update, context: CallbackContext) -> None:
    """Admin command to get user
    stats."""
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        user_count = len(user_stats)
        location_count = {info['location']: list(user_stats.values()).count(info['location']) for info in user_stats.values()}
        message = f"Total users: {user_count}\n"
        message += "Users by location:\n" + "\n".join([f"{loc}: {count}" for loc, count in location_count.items()])
        update.message.reply_text(message)
    else:
        update.message.reply_text("You don't have permission to view stats.")

def show_logs(update: Update, context: CallbackContext) -> None:
    """Admin command to show chat logs."""
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        log_messages = [f"User {log['user_id']} -> User {log['partner_id']}: {log['message']}" for log in chat_logs]
        update.message.reply_text("\n".join(log_messages) if log_messages else "No chats logged yet.")
    else:
        update.message.reply_text("You don't have permission to view chat logs.")

def main() -> None:
    """Start the bot."""
    updater = Updater(TOKEN)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('join', join)],
        states={
            GENDER: [MessageHandler(Filters.text & ~Filters.command, gender)],
            AGE: [MessageHandler(Filters.text & ~Filters.command, age)],
            LOCATION: [MessageHandler(Filters.text & ~Filters.command, location)],
            PREFERENCE: [MessageHandler(Filters.text & ~Filters.command, preference)],
            INTERESTS: [MessageHandler(Filters.text & ~Filters.command, interests)],
        },
        fallbacks=[]
    )

    # Register handlers
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("leave", leave))
    updater.dispatcher.add_handler(CommandHandler("update_profile", update_profile))  # New command for updating profile
    updater.dispatcher.add_handler(CommandHandler("stats", stats))  # Admin-only command to check stats
    updater.dispatcher.add_handler(CommandHandler("logs", show_logs))  # Admin-only command to view chat logs
    updater.dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_profile_update))

    # Start polling for updates
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
