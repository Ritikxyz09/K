import os
import time
import logging
from telegram.constants import ParseMode
import asyncio
import random
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from telegram.ext import ChatMemberHandler
from telegram.helpers import escape_markdown
import paramiko
from scp import SCPClient
import sys
import subprocess
import threading
from pathlib import Path
import re

def escape_markdown(text: str, version: int = 1) -> str:
    if version == 2:
        escape_chars = r'\_*[]()~`>#+-=|{}.!'
    else:
        escape_chars = r'\_*[]()'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

# Suppress HTTP request logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Bot management system
BOT_INSTANCES = {}  # Stores running bot processes
BOT_CONFIG_FILE = "bot_configs.json"
BOT_DATA_DIR = "bot_data"  # Directory to store each bot's data

# Bot Configuration
TELEGRAM_BOT_TOKEN = '8369168928:AAEvMS6P4hhK7PrMNyqC1ub1j9ZDHbqCJ2U'
OWNER_ID = 6437994839 # 👈 Put your real Telegram user ID here
CO_OWNERS = []  # List of user IDs for co-owners
OWNER_CONTACT = "Contact to buy keys"
ALLOWED_GROUP_IDS = [-1002539413749]
MAX_THREADS = 1000
max_duration = 120
bot_open = False
OWNER_USERNAME = "Ritikxyz099"
SPECIAL_MAX_DURATION = 600
SPECIAL_MAX_THREADS = 2000
BOT_START_TIME = time.time()

ACTIVE_VPS_COUNT = 10000  # डिफॉल्ट रूप से 6 VPS इस्तेमाल होंगे
# Display Name Configuration
GROUP_DISPLAY_NAMES = {}  # Key: group_id, Value: display_name
DISPLAY_NAME_FILE = "display_names.json"

# Link Management
LINK_FILE = "links.json"
LINKS = {}

# VPS Configuration
VPS_FILE = "vps.txt"
BINARY_NAME = "bgmi"
BINARY_PATH = f"/home/master/{BINARY_NAME}"
VPS_LIST = []

# Key Prices
KEY_PRICES = {
    "1H": 5,
    "2H": 10,  # Price for 1-hour key
    "3H": 15,  # Price for 1-hour key
    "4H": 20,  # Price for 1-hour key
    "5H": 25,  # Price for 1-hour key
    "6H": 30,  # Price for 1-hour key
    "7H": 35,  # Price for 1-hour key
    "8H": 40,  # Price for 1-hour key
    "9H": 45,  # Price for 1-hour key
    "10H": 50, # Price for 1-hour key
    "1D": 60,  # Price for 1-day key
    "2D": 100,  # Price for 1-day key
    "3D": 160, # Price for 1-day key
    "5D": 250, # Price for 2-day key
    "7D": 320, # Price for 2-day key
    "15D": 700, # Price for 2-day key
    "30D": 1250, # Price for 2-day key
    "60D": 2000, # Price for 2-day key,
}

# Special Key Prices
SPECIAL_KEY_PRICES = {
    "1D": 70,  
    "2D": 130,  # 30 days special key price
    "3D": 250,  # 30 days special key price
    "4D": 300,  # 30 days special key price
    "5D": 400,  # 30 days special key price
    "6D": 500,  # 30 days special key price
    "7D": 550,  # 30 days special key price
    "8D": 600,  # 30 days special key price
    "9D": 750,  # 30 days special key price
    "10D": 800,  # 30 days special key price
    "11D": 850,  # 30 days special key price
    "12D": 900,  # 30 days special key price
    "13D": 950,  # 30 days special key price
    "14D": 1000,  # 30 days special key price
    "15D": 1050,  # 30 days special key price
    "30D": 1500,  # 30 days special key price
}

# Image configuration - REMOVED ALL PHOTO URLs
START_IMAGES = [
    {
        'caption': (
            '🔥 *Welcome to the Ultimate DDoS Bot !*' + '\n\n'
            '💻 *Example:* `20.235.43.9 14533 120 100`' + '\n\n'
            '💀 *Bsdk threads ha 100 dalo time 120 dalne ke baad*' + '\n\n'
            '⚠️ *🥰🥰🥰🥰🥰🥰🥰🥰🥰🥰🤬*⚠️' + '\n\n'
            '⚠️ *JOIN CHANNEL  @https://t.me/+DmfLq9fiVrJhNmY1 *' + '\n\n'
        )
    },
]

# File to store key data
KEY_FILE = "keys.txt"

# Key System
keys = {}
special_keys = {}
redeemed_users = {}
redeemed_keys_info = {}
feedback_waiting = {}

# Reseller System
resellers = set()
reseller_balances = {}

# Global Cooldown
global_cooldown = 0
last_attack_time = 0

# Track running attacks
running_attacks = {}
attack_messages = {}  # Store attack messages for editing

# Empty keyboard (all buttons removed)
empty_keyboard = [[]]
empty_markup = ReplyKeyboardMarkup(empty_keyboard, resize_keyboard=True)

# Conversation States
GET_DURATION = 1
GET_KEY = 2
GET_ATTACK_ARGS = 3
GET_SET_DURATION = 4
GET_SET_THREADS = 5
GET_DELETE_KEY = 6
GET_RESELLER_ID = 7
GET_REMOVE_RESELLER_ID = 8
GET_ADD_COIN_USER_ID = 9
GET_ADD_COIN_AMOUNT = 10
GET_SET_COOLDOWN = 11
GET_SPECIAL_KEY_DURATION = 12
GET_SPECIAL_KEY_FORMAT = 13
ADD_GROUP_ID = 14
REMOVE_GROUP_ID = 15
MENU_SELECTION = 16
GET_RESELLER_INFO = 17
GET_VPS_INFO = 18
GET_VPS_TO_REMOVE = 19
CONFIRM_BINARY_UPLOAD = 20
GET_ADD_CO_OWNER_ID = 21
GET_REMOVE_CO_OWNER_ID = 22
GET_DISPLAY_NAME = 23
GET_GROUP_FOR_DISPLAY_NAME = 24
GET_BOT_TOKEN = 25
GET_OWNER_USERNAME = 26
SELECT_BOT_TO_START = 27
SELECT_BOT_TO_STOP = 28
CONFIRM_BINARY_DELETE = 29
GET_LINK_NUMBER = 30
GET_LINK_URL = 31
GET_BROADCAST_MESSAGE = 32
GET_VPS_COUNT = 33

def get_uptime():
    uptime_seconds = int(time.time() - BOT_START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def get_display_name(group_id=None):
    """Returns the current display name for the owner in specific group or default"""
    if group_id is None:
        return GROUP_DISPLAY_NAMES.get('default', f"@{OWNER_USERNAME}")
    return GROUP_DISPLAY_NAMES.get(group_id, GROUP_DISPLAY_NAMES.get('default', f"@{OWNER_USERNAME}"))

async def owner_settings(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner can access these settings!*", parse_mode='Markdown')
        return
    
    current_display_name = get_display_name_from_update(update)
    
    escaped_display_name = escape_markdown(current_display_name)
    
    await update.message.reply_text(
        f"⚙️ *Owner Settings Menu*\n\n"
        f"Select an option below:\n\n"
        f"👑 *Bot Owner:* {escaped_display_name}",
        parse_mode='Markdown',
        reply_markup=empty_markup
    )

async def set_display_name(update: Update, new_name: str, group_id=None):
    """Updates the display name for specific group or default"""
    if group_id is not None:
        GROUP_DISPLAY_NAMES[group_id] = new_name
    else:
        GROUP_DISPLAY_NAMES['default'] = new_name
    
    with open(DISPLAY_NAME_FILE, 'w') as f:
        json.dump(GROUP_DISPLAY_NAMES, f)
    
    if update:
        await update.message.reply_text(
            f"✅ Display name updated to: {new_name}" + 
            (f" for group {group_id}" if group_id else " as default name"),
            parse_mode='Markdown'
        )

def load_vps():
    global VPS_LIST
    VPS_LIST = []
    if os.path.exists(VPS_FILE):
        with open(VPS_FILE, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line and len(line.split(',')) == 3:  # IP,username,password फॉर्मेट चेक करें
                    VPS_LIST.append(line.split(','))

async def set_vps_count(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can set VPS count!", parse_mode='Markdown')
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"⚠️ Enter number of VPS to use (current: {ACTIVE_VPS_COUNT}, available: {len(VPS_LIST)}):",
        parse_mode='Markdown'
    )
    return GET_VPS_COUNT

async def set_vps_count_input(update: Update, context: CallbackContext):
    global ACTIVE_VPS_COUNT
    try:
        count = int(update.message.text)
        if 1 <= count <= len(VPS_LIST):
            ACTIVE_VPS_COUNT = count
            await update.message.reply_text(
                f"✅ Active VPS set to {ACTIVE_VPS_COUNT}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ Please enter between 1 and {len(VPS_LIST)}",
                parse_mode='Markdown'
            )
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number!", parse_mode='Markdown')
    return ConversationHandler.END

async def promote(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only owner can promote!*", parse_mode='Markdown')
        return
    
    # Create the promotion message using the stored links
    promotion_message = (
        "🔰 *Join our groups for more information, free keys, and hosting details!*\n\n"
        "Click the buttons below to join:"
    )
    
    # Create buttons dynamically based on available links
    keyboard = []
    if 'link_1' in LINKS and LINKS['link_1']:
        keyboard.append([InlineKeyboardButton("Join Group 1", url=LINKS['link_1'])])
    if 'link_2' in LINKS and LINKS['link_2']:
        keyboard.append([InlineKeyboardButton("Join Group 2", url=LINKS['link_2'])])
    if 'link_3' in LINKS and LINKS['link_3']:
        keyboard.append([InlineKeyboardButton("Join Group 3", url=LINKS['link_3'])])
    if 'link_4' in LINKS and LINKS['link_4']:
        keyboard.append([InlineKeyboardButton("Join Group 4", url=LINKS['link_4'])])
    
    # If no links are set, show a message
    if not keyboard:
        await update.message.reply_text("ℹ️ No links have been set up yet. Use the 'Manage Links' option to add links.")
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send to current chat first
    await update.message.reply_text(
        promotion_message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    # Track success/failure
    success_count = 0
    fail_count = 0
    group_success = 0
    private_success = 0
    
    # Get all chats the bot is in
    all_chats = set()
    
    # Add allowed groups
    for group_id in ALLOWED_GROUP_IDS:
        all_chats.add(group_id)
    
    # Add tracked private chats (users who have interacted with bot)
    if 'users_interacted' in context.bot_data:
        for user_id in context.bot_data['users_interacted']:
            all_chats.add(user_id)
    
    # Send promotion to all chats
    for chat_id in all_chats:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=promotion_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            success_count += 1
            
            # Track group vs private
            try:
                chat = await context.bot.get_chat(chat_id)
                if chat.type in ['group', 'supergroup']:
                    group_success += 1
                else:
                    private_success += 1
            except:
                pass
                
            await asyncio.sleep(0.5)  # Rate limiting
        except Exception as e:
            logging.error(f"Failed to send promotion to {chat_id}: {str(e)}")
            fail_count += 1
    
    # Send report
    await update.message.reply_text(
        f"📊 *Promotion Results*\n\n"
        f"✅ Successfully sent to: {success_count} chats\n"
        f"❌ Failed to send to: {fail_count} chats\n\n"
        f"• Groups: {group_success}\n"
        f"• Private chats: {private_success}",
        parse_mode='Markdown'
    )

def load_links():
    """Load links from file"""
    global LINKS
    if os.path.exists(LINK_FILE):
        try:
            with open(LINK_FILE, 'r') as f:
                LINKS = json.load(f)
        except (json.JSONDecodeError, ValueError):
            LINKS = {}

def save_links():
    """Save links to file"""
    with open(LINK_FILE, 'w') as f:
        json.dump(LINKS, f)

async def manage_links(update: Update, context: CallbackContext):
    """Show link management menu"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can manage links!", parse_mode='Markdown')
        return
    
    current_links_text = (
        "🔗 *Link Management*\n\n"
        "Current Links:\n"
        "1. Link 1\n"
        "2. Link 2\n"
        "3. Link 3\n"
        "4. Link 4\n\n"
        "Enter the number (1, 2, 3, or 4) of the link you want to replace:"
    )
    
    escaped_text = escape_markdown(current_links_text, version=2)
    
    await update.message.reply_text(
        escaped_text,
        parse_mode='MarkdownV2'
    )
    return GET_LINK_NUMBER

async def get_link_number(update: Update, context: CallbackContext):
    """Get which link number to update"""
    try:
        link_num = int(update.message.text)
        if link_num not in [1, 2, 3, 4]:
            raise ValueError
        
        context.user_data['editing_link'] = f"link_{link_num}"
        await update.message.reply_text(
            f"⚠️ Enter new URL for link {link_num}:",
            parse_mode='Markdown'
        )
        return GET_LINK_URL
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input! Please enter 1, 2, 3, or 4.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def get_link_url(update: Update, context: CallbackContext):
    if 'editing_link' not in context.user_data:
        return ConversationHandler.END
    
    link_key = context.user_data['editing_link']
    new_url = update.message.text.strip()
    
    if not (new_url.startswith('http://') or new_url.startswith('https://')):
        await update.message.reply_text("❌ Invalid URL! Must start with http:// or https://")
        return ConversationHandler.END
    
    LINKS[link_key] = new_url
    save_links()
    
    link_num = link_key.split('_')[1]
    text = f"✅ Link {link_num} updated successfully!\nNew URL: `{new_url}`"
    
    escaped_text = escape_markdown(text, version=2)
    
    await update.message.reply_text(
        escaped_text,
        parse_mode='MarkdownV2'
    )
    
    # Clear the editing state
    context.user_data.pop('editing_link', None)
    return ConversationHandler.END

async def broadcast_start(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner can broadcast messages!*", parse_mode='Markdown')
        return ConversationHandler.END
    
    await update.message.reply_text(
        "⚠️ *Enter the message you want to broadcast to all channels, groups and private chats:*",
        parse_mode='Markdown'
    )
    return GET_BROADCAST_MESSAGE

async def broadcast_message(update: Update, context: CallbackContext):
    message = update.message.text
    
    # Track success/failure
    success_count = 0
    fail_count = 0
    group_success = 0
    private_success = 0
    
    # Get all chats the bot is in
    all_chats = set()
    
    # Add allowed groups
    for group_id in ALLOWED_GROUP_IDS:
        all_chats.add(group_id)
    
    # Add tracked private chats (users who have interacted with bot)
    if 'users_interacted' in context.bot_data:
        for user_id in context.bot_data['users_interacted']:
            all_chats.add(user_id)
    
    # Send broadcast to all chats
    for chat_id in all_chats:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            success_count += 1
            
            # Track group vs private
            try:
                chat = await context.bot.get_chat(chat_id)
                if chat.type in ['group', 'supergroup']:
                    group_success += 1
                else:
                    private_success += 1
            except:
                pass
                
            await asyncio.sleep(0.5)  # Rate limiting
        except Exception as e:
            logging.error(f"Failed to send broadcast to {chat_id}: {str(e)}")
            fail_count += 1
    
    # Send report
    await update.message.reply_text(
        f"📊 *Broadcast Results*\n\n"
        f"✅ Successfully sent to: {success_count} chats\n"
        f"❌ Failed to send to: {fail_count} chats\n\n"
        f"• Groups: {group_success}\n"
        f"• Private chats: {private_success}",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

def load_display_name():
    """Loads the display names from file"""
    global GROUP_DISPLAY_NAMES
    if os.path.exists(DISPLAY_NAME_FILE):
        try:
            with open(DISPLAY_NAME_FILE, 'r') as f:
                GROUP_DISPLAY_NAMES = json.load(f)
            new_dict = {}
            for k, v in GROUP_DISPLAY_NAMES.items():
                try:
                    if k != 'default':
                        new_dict[int(k)] = v
                    else:
                        new_dict[k] = v
                except ValueError:
                    new_dict[k] = v
            GROUP_DISPLAY_NAMES = new_dict
        except (json.JSONDecodeError, ValueError):
            GROUP_DISPLAY_NAMES = {'default': f"@{OWNER_USERNAME}"}
    else:
        GROUP_DISPLAY_NAMES = {'default': f"@{OWNER_USERNAME}"}

def load_keys():
    if not os.path.exists(KEY_FILE):
        return

    with open(KEY_FILE, "r") as file:
        for line in file:
            key_type, key_data = line.strip().split(":", 1)
            if key_type == "ACTIVE_KEY":
                parts = key_data.split(",")
                if len(parts) == 2:
                    key, expiration_time = parts
                    keys[key] = {
                        'expiration_time': float(expiration_time),
                        'generated_by': None
                    }
                elif len(parts) == 3:
                    key, expiration_time, generated_by = parts
                    keys[key] = {
                        'expiration_time': float(expiration_time),
                        'generated_by': int(generated_by)
                    }
            elif key_type == "REDEEMED_KEY":
                key, generated_by, redeemed_by, expiration_time = key_data.split(",")
                redeemed_users[int(redeemed_by)] = float(expiration_time)
                redeemed_keys_info[key] = {
                    'generated_by': int(generated_by),
                    'redeemed_by': int(redeemed_by)
                }
            elif key_type == "SPECIAL_KEY":
                key, expiration_time, generated_by = key_data.split(",")
                special_keys[key] = {
                    'expiration_time': float(expiration_time),
                    'generated_by': int(generated_by)
                }
            elif key_type == "REDEEMED_SPECIAL_KEY":
                key, generated_by, redeemed_by, expiration_time = key_data.split(",")
                redeemed_users[int(redeemed_by)] = {
                    'expiration_time': float(expiration_time),
                    'is_special': True
                }
                redeemed_keys_info[key] = {
                    'generated_by': int(generated_by),
                    'redeemed_by': int(redeemed_by),
                    'is_special': True
                }

def save_keys():
    with open(KEY_FILE, "w") as file:
        for key, key_info in keys.items():
            if key_info['expiration_time'] > time.time():
                file.write(f"ACTIVE_KEY:{key},{key_info['expiration_time']},{key_info['generated_by']}\n")

        for key, key_info in special_keys.items():
            if key_info['expiration_time'] > time.time():
                file.write(f"SPECIAL_KEY:{key},{key_info['expiration_time']},{key_info['generated_by']}\n")

        for key, key_info in redeemed_keys_info.items():
            user_id = key_info['redeemed_by']
            if user_id in redeemed_users:
                expiration_info = redeemed_users[user_id]
                if 'is_special' in key_info and key_info['is_special']:
                    # redeemed_users[user_id] can be dict or float; handle both
                    if isinstance(expiration_info, dict):
                        expiration_time = expiration_info.get('expiration_time', 0)
                    else:
                        expiration_time = expiration_info
                    file.write(f"REDEEMED_SPECIAL_KEY:{key},{key_info['generated_by']},{user_id},{expiration_time}\n")
                else:
                    # normal keys store expiration as float
                    if isinstance(expiration_info, dict):
                        expiration_time = expiration_info.get('expiration_time', 0)
                    else:
                        expiration_time = expiration_info
                    file.write(f"REDEEMED_KEY:{key},{key_info['generated_by']},{user_id},{expiration_time}\n")

def load_bot_configs():
    """Load bot configurations from file"""
    if not os.path.exists(BOT_CONFIG_FILE):
        return []
    
    try:
        with open(BOT_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []

def save_bot_configs(configs):
    """Save bot configurations to file"""
    with open(BOT_CONFIG_FILE, 'w') as f:
        json.dump(configs, f)

def load_vps():
    global VPS_LIST
    if os.path.exists(VPS_FILE):
        with open(VPS_FILE, 'r') as f:
            VPS_LIST = [line.strip().split(',') for line in f.readlines()]

def save_vps():
    with open(VPS_FILE, 'w') as f:
        for vps in VPS_LIST:
            f.write(','.join(vps) + '\n')

def is_allowed_group(update: Update):
    chat = update.effective_chat
    return chat.type in ['group', 'supergroup'] and chat.id in ALLOWED_GROUP_IDS

def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID

def is_co_owner(update: Update):
    return update.effective_user.id in CO_OWNERS

def is_reseller(update: Update):
    return update.effective_user.id in resellers

def is_authorized_user(update: Update):
    return is_owner(update) or is_co_owner(update) or is_reseller(update)

def get_random_start_image():
    return random.choice(START_IMAGES)

async def reset_vps(update: Update, context: CallbackContext):
    """Reset all busy VPS to make them available again"""
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ *Only owner or co-owners can reset VPS!*", parse_mode='Markdown')
        return
    
    global running_attacks
    
    # Count how many VPS are busy
    busy_count = len(running_attacks)
    
    if busy_count == 0:
        await update.message.reply_text("ℹ️ *No VPS are currently busy.*", parse_mode='Markdown')
        return
    
    # Clear all running attacks
    running_attacks.clear()
    
    current_display_name = get_display_name_from_update(update)
    
    await update.message.reply_text(
        f"✅ *Reset {busy_count} busy VPS - they are now available for new attacks!*\n\n"
        f"👑 *Bot Owner:* {current_display_name}",
        parse_mode='Markdown'
    )

async def add_bot_instance(update: Update, context: CallbackContext):
    """Add a new bot instance"""
    if not is_owner(update):
        await update.message.reply_text("❌ Only owner can add bot instances!", parse_mode='Markdown')
        return ConversationHandler.END
    
    await update.message.reply_text(
        "⚠️ Enter the new bot token:",
        parse_mode='Markdown'
    )
    return GET_BOT_TOKEN

async def show_users(update: Update, context: CallbackContext):
    if not is_owner(update):
        await update.message.reply_text("❌ *Only the owner can check users!*", parse_mode='Markdown')
        return
    
    try:
        # Get owner info
        try:
            owner_chat = await context.bot.get_chat(OWNER_USERNAME)
            owner_info = f"👑 Owner: {owner_chat.full_name} (@{owner_chat.username if owner_chat.username else 'N/A'})"
        except Exception as e:
            owner_info = f"👑 Owner: @{OWNER_USERNAME} (Could not fetch details)"
        
        # Get co-owners info
        co_owners_info = []
        for co_owner_id in CO_OWNERS:
            try:
                co_owner_chat = await context.bot.get_chat(co_owner_id)
                co_owners_info.append(
                    f"🔹 Co-Owner: {co_owner_chat.full_name} (@{co_owner_chat.username if co_owner_chat.username else 'N/A'})"
                )
            except Exception as e:
                co_owners_info.append(f"🔹 Co-Owner: ID {co_owner_id} (Could not fetch details)")
        
        # Get resellers info
        resellers_info = []
        for reseller_id in resellers:
            try:
                reseller_chat = await context.bot.get_chat(reseller_id)
                balance = reseller_balances.get(reseller_id, 0)
                resellers_info.append(
                    f"🔸 Reseller: {reseller_chat.full_name} (@{reseller_chat.username if reseller_chat.username else 'N/A'}) - Balance: {balance} coins"
                )
            except Exception as e:
                resellers_info.append(f"🔸 Reseller: ID {reseller_id} (Could not fetch details)")
        
        # Compile the message
        message_parts = [
            "📊 *User Information*",
            "",
            owner_info,
            "",
            "*Co-Owners:*",
            *co_owners_info,
            "",
            "*Resellers:*",
            *resellers_info
        ]
        
        message = "\n".join(message_parts)
        
        # Split message if too long
        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        logging.error(f"Error in show_users: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ *An error occurred while fetching user information.*",
            parse_mode='Markdown'
        )   

async def add_bot_token(update: Update, context: CallbackContext):
    """Get bot token for new instance"""
    token = update.message.text.strip()
    context.user_data['new_bot_token'] = token
    
    await update.message.reply_text(
        "⚠️ Enter the owner username for this bot:",
        parse_mode='Markdown'
    )
    return GET_OWNER_USERNAME
    
async def delete_binary_start(update: Update, context: CallbackContext):
    if not (is_owner(update) or is_co_owner(update)):
        await update.message.reply_text("❌ Only owner or co-owners can delete binaries!", parse_mode='Markdown')
        return ConversationHandler.END
    
    current_display_name = get_display_name_from_update(update)
    
    await update.message.reply_text(
        f"⚠️ Are you sure you want to delete {BINARY_NAME} from all VPS?\n\n"
        f"Type 'YES' to confirm or anything else to cancel.\n\n"
        f"👑 *Bot Owner:* {current_display_name}",
        parse_mode='Markdown'
    )
    return CONFIRM_BINARY_DELETE

async def delete_binary_confirm(update: Update, context: CallbackContext):
    confirmation = update.message.text.strip().upper()
    
    if confirmation != 'YES':
        await update.message.reply_text("❌ Binary deletion canceled.", parse_mode='Markdown')
        return ConversationHandler.END
    
    if not VPS_LIST:
        await update.message.reply_text("❌ No VPS configured!", parse_mode='Markdown')
        return ConversationHandler.END
    
    message = await update.message.reply_text(
        f"⏳ Starting {BINARY_NAME} binary deletion from all VPS...\n\n",
        parse_mode='Markdown'
    )
    
    success_count = 0
    fail_count = 0
    results = []
    
    for i, vps in enumerate(VPS_LIST):
        ip, username, password = vps
        try:
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=username, password=password, timeout=10)
            
            # Define the binary path
            binary_path = f"/home/master/{BINARY_NAME}"
            
            try:
                # Check if binary exists
                stdin, stdout, stderr = ssh.exec_command(f'ls {binary_path} 2>/dev/null || echo "Not found"')
                output = stdout.read().decode().strip()
                
                if output == "Not found":
                    results.append(f"ℹ️ {i+1}. {ip} - Binary not found")
                    continue
                
                # Delete the binary
                ssh.exec_command(f'rm -f {binary_path}')
                
                # Verify deletion
                stdin, stdout, stderr = ssh.exec_command(f'ls {binary_path} 2>/dev/null || echo "Deleted"')
                if "Deleted" not in stdout.read().decode():
                    raise Exception("Deletion verification failed")
                
                results.append(f"✅ {i+1}. {ip} - Successfully deleted")
                success_count += 1
                
            except Exception as e:
                results.append(f"❌ {i+1}. {ip} - Failed: {str(e)}")
                fail_count += 1
            
            ssh.close()
            
        except Exception as e:
            results.append(f"❌ {i+1}. {ip} - Connection Failed: {str(e)}")
            fail_count += 1
    
    # Send results
    result_text = "\n".join(results)
    current_display_name = get_display_name_from_update(update)
    
    await message.edit_text(
        f"🗑️ {BINARY_NAME} Binary Deletion Results:\n\n"
        f"✅ Success: {success_count}\n"
        f"❌ Failed: {fail_count}\n\n"
        f"{result_text}\n\n"
        f"👑 *Bot Owner:* {current_display_name}",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def add_owner_username(update: Update, context: CallbackContext):
    """Get owner username and start new bot instance"""
    owner_username = update.message.text.strip()
    token = context.user_data['new_bot_token']
    
    # Load existing configs
    configs = load_bot_configs()
    
    # Check if token already exists
    if any(c['token'] == token for c in configs):
        await update.message.reply_text(
            "❌ This bot token is already configured!",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Add new config
    new_config = {
        'token': token,
        'owner_username': owner_username,
        'active': False
    }
    configs.append(new_config)
    save_bot_configs(configs)
    
    # Start the
