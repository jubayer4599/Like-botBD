import telebot
import requests
import time
import json
import os
import threading
import random
import string
import logging
import re
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from concurrent.futures import ThreadPoolExecutor

# ===================== CONFIGURATION =====================
class Config:
    # Bot Credentials
    BOT_TOKEN = "8309490353:AAEJMzYoMCfjfUZXdIf9IW3IS9REZJDTBUk" # Placeholder - replace with your actual token if running
    OWNER_ID = 1926956969 # Replace with your actual owner ID

    # Channels & Groups
    CHANNELS = ["@capcutpro_bd", "@OB52LIKE", "@GHOST_X_BACKUP"]
    GROUP_LINK = "https://t.me/fflikebd"
    CHANNEL_JOIN_LINK = "https://t.me/bdmodspro" # Auto-join list if available

    # API Endpoints
    LIKE_API_URL = "https://api-v2-ecru.vercel.app/like"
    VISIT_API_URL = "https://ajay-visit-api-10-k.vercel.app"
    PROFILE_API_URL = "http://danger-info-alpha.vercel.app/accinfo" # Updated for UID only
    BANNER_API_URL = "https://after-banner-636.vercel.app/banner-image"
    OUTFIT_API_URL = "https://outfit-info-by-agajay.vercel.app/outfit-image"
    SPAM_API_URL = "https://mg24-gamer-spam-api.vercel.app/spam"
    BANCHECK_API_URL = "https://ff.garena.com/api/antihack/check_banned"

    # Video Files (Ensure these files exist in your bot's directory)
    SUCCESS_VIDEO = "success.mp4"
    ALREADY_LIKED_VIDEO = "mt.mp4"
    ERROR_VIDEO = "error.mp4"
    VERIFICATION_VIDEO = "verification_video.mp4" # Video for verification

    # Other Settings
    SHORTENER_API = "52a5a7d6635e1e4e210db5438dca09f8a5fe885d"
    SHORTENER_URL = "https://just2earn.com/api?api"
    VISIT_COOLDOWN = 120 # seconds
    SPAM_COOLDOWN = 60 # seconds
    VERIFICATION_COOLDOWN = 1200 # seconds (20 minutes) for user to re-verify after a successful one
    FREE_USER_DAILY_LIMIT = 1
    VIP_USER_DAILY_LIMIT = 5
    RESET_TIME = 4 # Hour (0-23) at which daily limits reset (e.g., 7 for 7 AM)
    VERIFICATION_VIDEO_ENABLED = False # Set to False by default

    # Footer buttons settings
    FOOTER_BUTTONS_ENABLED = True
    BUTTON1_TEXT = "𓆩𝐒𝐇𝐀𝐑𝐄𓆪"
    BUTTON1_URL = "https://t.me/Qyroxbot?startgroup=true"
    BUTTON2_TEXT = "𓆩𝐎𝐖𝐍𝐄𝐑𓆪"
    BUTTON2_URL = "https://t.me/Chikwho"

    # Valid regions mapping
    VALID_REGIONS = {
        'bd': 'BGD', 'ind': 'IND', 'pk': 'PAK', 'id': 'IDA',
        'th': 'THA', 'my': 'MYS', 'vn': 'VNM', 'ru': 'RUS',
        'mx': 'MEX', 'tw': 'TWN', 'me': 'MDE', 'eu': 'EUR',
        'sg': 'SGP', 'ssa': 'SSA', 'us': 'USA', 'br': 'BRL', 'sac': 'SAC', 'na': 'NA'
    }

# Initialize bot with threaded execution
bot = telebot.TeleBot(Config.BOT_TOKEN, parse_mode='HTML', threaded=True)
executor = ThreadPoolExecutor(max_workers=20)

# Optimized logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class DataStorage:
    def __init__(self):
        self.vip_users = set()
        self.verification_credits = {}
        self.used_tokens = set()
        self.user_last_verification = {}
        self.pending_requests = {} # {user_id: {'region': 'bd', 'uid': '123', 'type': 'like', 'chat_id': 1234, 'message_id': 5678, 'pending_message_id': 999}}
        self.token_to_user = {}
        self.vip_expiry = {}
        self.visit_cooldowns = {}
        self.spam_cooldowns = {}
        self.user_coins = {}
        self.all_users = set()
        self.bot_active = True
        self.user_daily_likes = {}
        self.custom_limits = {}
        self.verification_enabled = True
        self.command_status = {} # Stores status of commands: {'command_name': {'enabled': True/False, 'message': 'custom_message'}}
        self.config_values = {} # To store dynamic config values
        self.load_data()

    def save_data(self):
        try:
            data = {
                'vip_users': list(self.vip_users),
                'verification_credits': self.verification_credits,
                'used_tokens': list(self.used_tokens),
                'user_last_verification': self.user_last_verification,
                'pending_requests': self.pending_requests, 
                'token_to_user': self.token_to_user,
                'vip_expiry': self.vip_expiry,
                'visit_cooldowns': self.visit_cooldowns,
                'spam_cooldowns': self.spam_cooldowns,
                'user_coins': self.user_coins,
                'all_users': list(self.all_users),
                'bot_active': self.bot_active,
                'user_daily_likes': self.user_daily_likes,
                'custom_limits': self.custom_limits,
                'verification_enabled': self.verification_enabled,
                'command_status': self.command_status,
                'config_values': self.config_values
            }
            with open('bot_data.json', 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Save data error: {e}")

    def load_data(self):
        try:
            if os.path.exists('bot_data.json'):
                with open('bot_data.json', 'r') as f:
                    data = json.load(f)
                    self.vip_users = set(data.get('vip_users', []))
                    self.verification_credits = {int(k): v for k, v in data.get('verification_credits', {}).items()}
                    self.used_tokens = set(data.get('used_tokens', []))
                    self.user_last_verification = {int(k): v for k, v in data.get('user_last_verification', {}).items()}
                    # Convert keys to int for pending_requests as well
                    self.pending_requests = {int(k): v for k, v in data.get('pending_requests', {}).items()}
                    self.token_to_user = data.get('token_to_user', {})
                    self.vip_expiry = {int(k): v for k, v in data.get('vip_expiry', {}).items()}
                    self.visit_cooldowns = {int(k): v for k, v in data.get('visit_cooldowns', {}).items()}
                    self.spam_cooldowns = {int(k): v for k, v in data.get('spam_cooldowns', {}).items()}
                    self.user_coins = {int(k): v for k, v in data.get('user_coins', {}).items()}
                    self.all_users = set(data.get('all_users', []))
                    self.bot_active = data.get('bot_active', True)
                    self.user_daily_likes = {int(k): v for k, v in data.get('user_daily_likes', {}).items()}
                    self.custom_limits = {int(k): v for k, v in data.get('custom_limits', {}).items()}
                    self.verification_enabled = data.get('verification_enabled', True)
                    self.command_status = data.get('command_status', {})
                    self.config_values = data.get('config_values', {})

            # Apply dynamic config values to Config class
            for key, value in self.config_values.items():
                if hasattr(Config, key):
                    setattr(Config, key, value)
        except Exception as e:
            logger.error(f"Load data error: {e}")

    def reset_daily_counts(self):
        try:
            now = datetime.now()
            today_str = now.strftime('%Y-%m-%d')

            reset_date_check = now.replace(hour=Config.RESET_TIME, minute=0, second=0, microsecond=0)
            if now < reset_date_check:
                reset_date_check -= timedelta(days=1)

            for user_id_str in list(self.user_daily_likes.keys()):
                user_id = int(user_id_str)
                user_data = self.user_daily_likes[user_id]
                if datetime.strptime(user_data['date'], '%Y-%m-%d').date() < reset_date_check.date():
                    self.user_daily_likes[user_id] = {'count': 0, 'date': today_str}

            self.save_data()
        except Exception as e:
            logger.error(f"Reset counts error: {e}")

    def can_send_like(self, user_id):
        try:
            user_id = int(user_id) # Ensure user_id is integer
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')

            daily_limit = Config.FREE_USER_DAILY_LIMIT
            if user_id in self.custom_limits:
                daily_limit = self.custom_limits[user_id]
            elif is_vip(user_id):
                daily_limit = Config.VIP_USER_DAILY_LIMIT

            if user_id not in self.user_daily_likes or self.user_daily_likes[user_id]['date'] != today:
                self.user_daily_likes[user_id] = {'count': 0, 'date': today}
                self.save_data()

            if self.user_daily_likes[user_id]['count'] < daily_limit:
                return True, daily_limit - self.user_daily_likes[user_id]['count']

            return False, 0
        except Exception as e:
            logger.error(f"Can send like error: {e}")
            return False, 0

    def increment_like_count(self, user_id):
        try:
            user_id = int(user_id) # Ensure user_id is integer
            today = datetime.now().strftime('%Y-%m-%d')
            if user_id not in self.user_daily_likes or self.user_daily_likes[user_id]['date'] != today:
                self.user_daily_likes[user_id] = {'count': 1, 'date': today}
            else:
                self.user_daily_likes[user_id]['count'] += 1
            self.save_data()
        except Exception as e:
            logger.error(f"Increment like error: {e}")

db = DataStorage()

# ===================== OPTIMIZED UTILITY FUNCTIONS =====================
def get_next_reset_time():
    now = datetime.now()
    reset_time = now.replace(hour=Config.RESET_TIME, minute=0, second=0, microsecond=0)
    if now.hour >= Config.RESET_TIME:
        next_reset = reset_time + timedelta(days=1)
    else:
        next_reset = reset_time
    return next_reset.strftime('%I:%M %p (%d %B)')

def shorten_url(url):
    try:
        params = {
            'api': Config.SHORTENER_API,
            'url': url,
            'format': 'text'
        }
        response = requests.get(Config.SHORTENER_URL, params=params, timeout=15)
        return response.text.strip() if response.status_code == 200 and response.text.startswith(('http://', 'https://')) else url
    except Exception as e:
        logger.error(f"Error shortening URL {url}: {e}")
        return url

def is_subscribed(user_id):
    try:
        unjoined = []
        for channel in Config.CHANNELS:
            try:
                member_status = bot.get_chat_member(channel, user_id).status
                if member_status not in ['member', 'creator', 'administrator']:
                    unjoined.append(channel)
            except telebot.apihelper.ApiTelegramException as e:
                if "user not found" in str(e).lower() or "user is not a member of the chat" in str(e).lower():
                    unjoined.append(channel)
                else:
                    logger.error(f"Telegram API error checking subscription for {user_id} in {channel}: {e}")
            except Exception as e:
                logger.error(f"General error checking subscription for {user_id} in {channel}: {e}")
        return unjoined
    except Exception as e:
        logger.error(f"Overall is_subscribed error: {e}")
        return Config.CHANNELS

def validate_region(region):
    """Check if the region code is valid"""
    return region.lower() in Config.VALID_REGIONS

def validate_uid(uid):
    """Check if UID is in correct format (8-12 digits)"""
    return uid.isdigit() and 8 <= len(uid) <= 12

def call_like_api(region, uid):
    try:
        response = requests.get(f"{Config.LIKE_API_URL}?server_name={region}&uid={uid}", timeout=30)
        return response.json() if response.status_code == 200 else {"status": 0, "error": f"API_ERROR: HTTP {response.status_code}"}
    except requests.exceptions.Timeout:
        logger.error(f"Like API timeout for UID {uid}, region {region}")
        return {"status": 0, "error": "API Request Timed Out"}
    except requests.exceptions.ConnectionError:
        logger.error(f"Like API connection error for UID {uid}, region {region}")
        return {"status": 0, "error": "API Connection Error"}
    except json.JSONDecodeError:
        logger.error(f"Like API JSON decode error for UID {uid}, region {region}. Response: {response.text}")
        return {"status": 0, "error": "Invalid API Response"}
    except Exception as e:
        logger.error(f"Like API unexpected error for UID {uid}, region {region}: {e}")
        return {"status": 0, "error": "Unknown API Error"}

def call_visit_api(region, uid):
    try:
        response = requests.get(f"{Config.VISIT_API_URL}/{region}/{uid}", timeout=60)
        return response.json() if response.status_code == 200 else {"error": f"API_ERROR: HTTP {response.status_code}"}
    except requests.exceptions.Timeout:
        logger.error(f"Visit API timeout for UID {uid}, region {region}")
        return {"error": "API Request Timed Out"}
    except requests.exceptions.ConnectionError:
        logger.error(f"Visit API connection error for UID {uid}, region {region}")
        return {"error": "API Connection Error"}
    except json.JSONDecodeError:
        logger.error(f"Visit API JSON decode error for UID {uid}, region {region}. Response: {response.text}")
        return {"error": "Invalid API Response"}
    except Exception as e:
        logger.error(f"Visit API unexpected error for UID {uid}, region {region}: {e}")
        return {"error": "Unknown API Error"}

def call_spam_api(region, uid):
    try:
        response = requests.get(f"{Config.SPAM_API_URL}?uid={uid}", timeout=60)
        return {"status": 1} if response.status_code == 200 else {"status": 0, "error": f"API_ERROR: HTTP {response.status_code}"}
    except requests.exceptions.Timeout:
        logger.error(f"Spam API timeout for UID {uid}, region {region}")
        return {"status": 0, "error": "API Request Timed Out"}
    except requests.exceptions.ConnectionError:
        logger.error(f"Spam API connection error for UID {uid}, region {region}")
        return {"status": 0, "error": "API Connection Error"}
    except Exception as e:
        logger.error(f"Spam API unexpected error for UID {uid}, region {region}: {e}")
        return {"status": 0, "error": "Unknown API Error"}

def call_bancheck_api(uid):
    url = f'https://team-ujjaiwal.vercel.app/api/player/check-ban?uid={uid}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        data = resp.json()

        ban_status = data.get("ban_status", "Unknown")
        banned_since = data.get("banned_since", "N/A")
        nickname = data.get("nickname", "N/A")
        region = data.get("region", "N/A")
        level = data.get("level", "N/A")
        likes = data.get("likes", 0)

        status_icon = "✅" if ban_status == "Not Banned" else "🚫"

        return f"""<b>{status_icon} UID:</b> <code>{uid}</code>
<b>Status:</b> {ban_status}
<b>Name:</b> {nickname}
<b>Region:</b> {region}
<b>Level:</b> {level}
<b>Likes:</b> {likes:,}
<b>Since:</b> <i>{banned_since}</i>""" if ban_status != "Not Banned" else f"""<b>{status_icon} UID:</b> <code>{uid}</code>
<b>Status:</b> Not Banned 😎"""

    except requests.exceptions.Timeout:
        logger.error(f"Bancheck API timeout for UID {uid}")
        return "⚠️ Bancheck API request timed out. Please try again later."
    except requests.exceptions.ConnectionError:
        logger.error(f"Bancheck API connection error for UID {uid}")
        return "❌ Failed to connect to Bancheck API. Please check your internet connection or try again later."
    except requests.exceptions.RequestException as e:
        logger.error(f"Bancheck API request error for UID {uid}: {e}")
        return f"❌ An error occurred while checking ban status: {e}. Please try again later."
    except Exception as e:
        logger.error(f"Unexpected error in call_bancheck_api for UID {uid}: {e}")
        return "⚠️ An unexpected error occurred. Please try again later."

def generate_verification_token(user_id):
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    db.token_to_user[token] = user_id
    db.save_data()
    return token

def is_vip(user_id):
    try:
        user_id = int(user_id) # Ensure user_id is integer for lookups
        if user_id == Config.OWNER_ID:
            return True # Owner is always VIP
        
        if user_id in db.vip_users:
            if user_id in db.vip_expiry:
                if time.time() < db.vip_expiry[user_id]:
                    return True
                else:
                    # VIP expired
                    db.vip_users.remove(user_id)
                    del db.vip_expiry[user_id]
                    db.save_data()
                    logger.info(f"VIP for user {user_id} expired and was removed.")
                    return False
            return True # Permanent VIP
        return False
    except Exception as e:
        logger.error(f"Error checking VIP status for {user_id}: {e}")
        return False

def get_profile_info(uid): # Removed 'region' parameter
    try:
        # Construct URL without region as per new API structure
        response = requests.get(f"{Config.PROFILE_API_URL}?uid={uid}&key=DANGERxINFO", timeout=10)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.Timeout:
        logger.error(f"Profile API timeout for UID {uid}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Profile API connection error for UID {uid}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Profile API JSON decode error for UID {uid}. Response: {response.text}")
        return None
    except Exception as e:
        logger.error(f"Profile API unexpected error for UID {uid}: {e}")
        return None

def format_timestamp(ts):
    try:
        if isinstance(ts, (int, float)) and ts > 1000000000000: # Check if timestamp is in milliseconds
            ts = ts / 1000 # Convert to seconds
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts).strftime('%d %B %Y %H:%M:%S')
        elif isinstance(ts, str) and ts.isdigit():
            # Handle string timestamps, checking for milliseconds
            if len(ts) == 13: # Assume milliseconds if 13 digits
                return datetime.fromtimestamp(int(ts) / 1000).strftime('%d %B %Y %H:%M:%S')
            return datetime.fromtimestamp(int(ts)).strftime('%d %B %Y %H:%M:%S')
        return "N/A"
    except (ValueError, TypeError, OSError) as e:
        logger.error(f"Error formatting timestamp {ts}: {e}")
        return "N/A"

def get_user_info(user_id):
    try:
        user = bot.get_chat(user_id)
        username_str = f"@{user.username}" if user.username else f"ID: {user_id}"
        full_name_str = f"{user.first_name or ''} {user.last_name or ''}".strip()
        display_name = full_name_str if full_name_str else username_str
        return (username_str, display_name)
    except Exception as e:
        logger.error(f"Error fetching user info for {user_id}: {e}")
        return (f"ID: {user_id}", f"User {user_id}")

def is_admin(user_id):
    return user_id == Config.OWNER_ID

def check_bot_active(message):
    if not db.bot_active:
        bot.reply_to(message, "🔴 <b>BOT IS CURRENTLY OFFLINE</b>\n\n"
                               "Please wait until the bot is back online to use commands.", parse_mode='HTML')
        return False
    return True

def check_command_status(message):
    command_text = message.text.split()[0]
    command_name = command_text.split('@')[0][1:].lower()
    
    status = db.command_status.get(command_name, {'enabled': True, 'message': None})
    if not status['enabled']:
        bot.reply_to(message, status['message'] if status['message'] else f"❌ <b>'{command_name.upper()}' COMMAND IS CURRENTLY DISABLED.</b>\n"
                                                                         "Please try again later.", parse_mode='HTML')
        return False
    return True

def create_verification_message(user_id, region, uid, command_type, chat_id, message_id, pending_message_id):
    token = generate_verification_token(user_id)
    verify_url = f"https://t.me/{bot.get_me().username}?start=verify_{token}"
    short_url = shorten_url(verify_url)

    db.pending_requests[user_id] = {
        'region': region,
        'uid': uid,
        'type': command_type,
        'chat_id': chat_id,
        'message_id': message_id,
        'pending_message_id': pending_message_id # Store the message ID of the verification message
    }
    db.save_data()

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ 𝗖𝗟𝗜𝗖𝗞 𝗧𝗢 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡", url=short_url))
    kb.add(InlineKeyboardButton("❓𝗛𝗢𝗪 𝗧𝗢 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡", url="https://t.me/GHOST_X_BACKUP/30"))
    kb.add(InlineKeyboardButton("💎 𝗕𝗨𝗬 𝗣𝗥𝗘𝗠𝗜𝗨𝗠", url="https://t.me/Chikwho"))

    if Config.VERIFICATION_VIDEO_ENABLED:
        return {
            'video': open(Config.VERIFICATION_VIDEO, 'rb'),
            'caption': (
                "🔐 <b>VERIFICATION REQUIRED</b>\n"
                "--- \n\n"
                f"🆔 <b>UID:</b> <code>{uid}</code>\n"
                f"🌍 <b>Region:</b> {Config.VALID_REGIONS.get(region.lower(), region).upper()}\n"
                f"💎 <b>Service:</b> {command_type.upper()}\n\n"
                "📌 <b>VERIFICATION STEPS:</b>\n"
                "1️⃣ Click the '✅ 𝗖𝗟𝗜𝗖𝗞 𝗧𝗢 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡 ✅' button below.\n"
                "2️⃣ Complete the simple verification task.\n"
                "3️⃣ Return to the group/chat to receive your requested service automatically!\n\n"
                "⚠️ <i>Each verification link can only be used once.</i>\n"
                "⏳ <i>Verification expires in 20 minutes.</i>\n\n"
                "💡 <b>PRO TIP:</b> Get VIP to skip verification and cooldowns!\nUse /coins to check your credits."
            ),
            'reply_markup': kb
        }
    else:
        return {
            'text': (
                "🔒 <b>VERIFICATION REQUIRED</b>\n"
                "--- \n\n"
                f"🆔 <b>UID:</b> <code>{uid}</code>\n"
                f"🌍 <b>Region:</b> {Config.VALID_REGIONS.get(region.lower(), region).upper()}\n"
                f"💎 <b>Service:</b> {command_type.upper()}\n\n"
                "📌 <b>VERIFICATION STEPS:</b>\n"
                "1️⃣ Click the '✅ 𝗖𝗟𝗜𝗖𝗞 𝗧𝗢 𝗩𝗘𝗥𝗜𝗙𝗜𝗖𝗔𝗧𝗜𝗢𝗡 ✅' button below.\n"
                "2️⃣ Complete the simple verification task.\n"
                "3️⃣ Return to the group/chat to receive your requested service automatically!\n\n"
                "🔗 <b>Verification Link:</b>\n"
                f"<code>{short_url}</code>\n\n"
                "⚠️ <i>Each verification link can only be used once.</i>\n"
                "⏳ <i>Verification expires in 20 minutes.</i>\n\n"
                "💡 <b>PRO TIP:</b> Get VIP to skip verification and cooldowns!\nUse /coins to check your credits."
            ),
            'reply_markup': kb
        }

def create_footer_buttons():
    if not Config.FOOTER_BUTTONS_ENABLED:
        return None
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(f"1. {Config.BUTTON1_TEXT}", url=Config.BUTTON1_URL),
        InlineKeyboardButton(f"2. {Config.BUTTON2_TEXT}", url=Config.BUTTON2_URL)
    )
    return kb

def send_video_reply(chat_id, message_id, video_file, caption):
    try:
        if not os.path.exists(video_file):
            logger.error(f"Video file not found: {video_file}")
            sent_msg = bot.send_message(chat_id, caption, parse_mode='HTML', reply_to_message_id=message_id)
            # Add footer buttons if enabled
            footer_buttons = create_footer_buttons()
            if footer_buttons:
                bot.edit_message_reply_markup(chat_id, sent_msg.message_id, reply_markup=footer_buttons)
            return sent_msg

        with open(video_file, 'rb') as video:
            sent_msg = bot.send_video(
                chat_id=chat_id,
                video=video,
                caption=caption,
                reply_to_message_id=message_id,
                parse_mode='HTML'
            )
            
            # Add footer buttons if enabled
            footer_buttons = create_footer_buttons()
            if footer_buttons:
                bot.edit_message_reply_markup(chat_id, sent_msg.message_id, reply_markup=footer_buttons)
            
            return sent_msg
    except Exception as e:
        logger.error(f"Error sending video to chat {chat_id}, msg {message_id}: {e}")
        sent_msg = bot.send_message(chat_id, caption, parse_mode='HTML', reply_to_message_id=message_id)
        
        # Add footer buttons if enabled
        footer_buttons = create_footer_buttons()
        if footer_buttons:
            bot.edit_message_reply_markup(chat_id, sent_msg.message_id, reply_markup=footer_buttons)
            
        return sent_msg

def send_sticker_reply(chat_id, message_id, image_data):
    try:
        if image_data:
            temp_file_path = 'temp_sticker.webp'
            with open(temp_file_path, 'wb') as f:
                f.write(image_data)
            with open(temp_file_path, 'rb') as sticker:
                sent_msg = bot.send_sticker(
                    chat_id=chat_id,
                    sticker=sticker,
                    reply_to_message_id=message_id
                )
                
                # Add footer buttons if enabled
                footer_buttons = create_footer_buttons()
                if footer_buttons:
                    bot.edit_message_reply_markup(chat_id, sent_msg.message_id, reply_markup=footer_buttons)
                    
            os.remove(temp_file_path)
    except Exception as e:
        logger.error(f"Error sending sticker to chat {chat_id}, msg {message_id}: {e}")

def send_photo_reply(chat_id, message_id, image_data, caption=None):
    try:
        if image_data:
            temp_file_path = 'temp_photo.jpg'
            with open(temp_file_path, 'wb') as f:
                f.write(image_data)
            with open(temp_file_path, 'rb') as photo:
                sent_msg = bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    reply_to_message_id=message_id,
                    parse_mode='HTML'
                )
                
                # Add footer buttons if enabled
                footer_buttons = create_footer_buttons()
                if footer_buttons:
                    bot.edit_message_reply_markup(chat_id, sent_msg.message_id, reply_markup=footer_buttons)
                    
            os.remove(temp_file_path)
    except Exception as e:
        logger.error(f"Error sending photo to chat {chat_id}, msg {message_id}: {e}")

# ===================== ADMIN COMMANDS =====================
@bot.message_handler(commands=['verification-on', 'verification-off', 'verification_video_on', 'verification_video_off', 'ghost-off', 'ghost-on'])
def toggle_settings(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⚠️ You are not authorized to use this command!", parse_mode='HTML')
        return

    cmd = message.text.split()[0][1:]
    response = "Unknown command."

    if cmd == 'verification-on':
        db.verification_enabled = True
        response = "✅ <b>Verification system has been enabled.</b>\n" \
                   "Free users will now need to verify before using certain commands."
    elif cmd == 'verification-off':
        db.verification_enabled = False
        response = "❌ <b>Verification system has been disabled.</b>\n" \
                   "Free users can now use commands without verification."
    elif cmd == 'verification_video_on':
        Config.VERIFICATION_VIDEO_ENABLED = True
        db.config_values['VERIFICATION_VIDEO_ENABLED'] = True # Store in dynamic config
        response = "✅ <b>Verification video has been enabled.</b>\n" \
                   "Users will now receive a video guide for verification."
    elif cmd == 'verification_video_off':
        Config.VERIFICATION_VIDEO_ENABLED = False
        db.config_values['VERIFICATION_VIDEO_ENABLED'] = False # Store in dynamic config
        response = "❌ <b>Verification video has been disabled.</b>\n" \
                   "Users will now receive a text-based verification guide."
    elif cmd == 'ghost-off':
        db.bot_active = False
        response = "🔴 <b>BOT HAS BEEN TURNED OFF.</b>\n" \
                   "All user commands are now disabled."
    elif cmd == 'ghost-on':
        db.bot_active = True
        response = "🟢 <b>BOT HAS BEEN TURNED ON.</b>\n" \
                   "User commands are now active."

    db.save_data()
    bot.reply_to(message, response, parse_mode='HTML')

@bot.message_handler(commands=['addvip'])
def add_vip(message):
    if not check_bot_active(message) or not is_admin(message.from_user.id):
        return

    args = message.text.split()

    if len(args) < 3:
        bot.reply_to(message,
            "✨ <b>VIP ADDITION COMMAND</b> ✨\n\n"
            "<code>/addvip &lt;duration&gt; &lt;user_id/@username/reply&gt;</code>\n\n"
            "⏳ <b>Duration Examples:</b>\n"
            "<code>30min</code>, <code>2hours</code>, <code>15days</code>, <code>perm</code>\n\n"
            "💎 <b>Examples:</b>\n"
            "<code>/addvip 30min @username</code>\n"
            "<code>/addvip 2hours 123456789</code>\n"
            "<code>/addvip perm @user</code>",
            parse_mode='HTML'
        )
        return

    duration_input = args[1].lower()
    target_input = args[2]

    try:
        target = int(target_input) if not target_input.startswith('@') else bot.get_chat(target_input).id
    except Exception as e:
        bot.reply_to(message, f"❌ Invalid user specified: {e}", parse_mode='HTML')
        return

    if target in db.vip_users:
        if target not in db.vip_expiry and duration_input == 'perm':
            bot.reply_to(message, "⚠️ User is already a permanent VIP. No changes needed.", parse_mode='HTML')
            return
        elif target in db.vip_expiry and duration_input != 'perm' and time.time() < db.vip_expiry[target]:
            bot.reply_to(message, "⚠️ User is already VIP with an active membership. Update will override.", parse_mode='HTML')


    expiry_str = 'Permanent'
    if duration_input == 'perm':
        db.vip_users.add(target)
        if target in db.vip_expiry:
            del db.vip_expiry[target] # Remove expiry if setting to permanent
    else:
        match = re.match(r'^(\d+)(min|mins|minute|minutes|hour|hours|day|days)$', duration_input)
        if not match:
            bot.reply_to(message, "❌ Invalid duration format. Examples: <code>30min</code>, <code>2hours</code>, <code>15days</code>", parse_mode='HTML')
            return

        amount = int(match.group(1))
        unit = match.group(2).lower()

        expiry_time = time.time()
        if unit.startswith('min'):
            expiry_time += (amount * 60)
            expiry_str = f"{amount} minute(s)"
        elif unit.startswith('hour'):
            expiry_time += (amount * 3600)
            expiry_str = f"{amount} hour(s)"
        elif unit.startswith('day'):
            expiry_time += (amount * 86400)
            expiry_str = f"{amount} day(s)"

        db.vip_users.add(target)
        db.vip_expiry[target] = expiry_time

    db.all_users.add(target) # Ensure VIP users are also in all_users
    db.save_data()

    username, name = get_user_info(target)

    bot.reply_to(message,
        f"🎉 <b>VIP STATUS GRANTED!</b> 🎉\n\n"
        f"👤 <b>User:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{target}</code>\n"
        f"⏳ <b>Duration:</b> {expiry_str}\n"
        f"🔑 <b>Added by:</b> @{message.from_user.username or message.from_user.id}",
        parse_mode='HTML'
    )

    try:
        bot.send_message(
            target,
            f"✨ <b>🌟 VIP MEMBERSHIP ACTIVATED! 🌟</b> ✨\n\n"
            f"⏳ <b>Duration:</b> {expiry_str}\n"
            f"📅 <b>Activated at:</b> {datetime.now().strftime('%d %B %Y %H:%M:%S')}\n\n"
            f"Thank you for being part of our VIP community! Enjoy exclusive perks like no cooldowns and increased daily limits.",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Failed to send VIP activation message to user {target}: {e}")

@bot.message_handler(commands=['dvip'])
def remove_vip(message):
    if not check_bot_active(message) or not is_admin(message.from_user.id):
        return

    args = message.text.split()
    target = None

    if message.reply_to_message:
        target = message.reply_to_message.from_user.id
    elif len(args) > 1:
        target_input = args[1]
        try:
            target = int(target_input) if not target_input.startswith('@') else bot.get_chat(target_input).id
        except Exception as e:
            bot.reply_to(message, f"❌ Invalid user specified: {e}", parse_mode='HTML')
            return
    else:
        bot.reply_to(message, "⚠️ <b>Usage:</b> Reply to a user's message or provide their ID/username.\n"
                               "Example: <code>/dvip 123456789</code> or <code>/dvip @username</code>", parse_mode='HTML')
        return

    if target is None:
        bot.reply_to(message, "❌ Could not determine target user.", parse_mode='HTML')
        return

    if target in db.vip_users:
        db.vip_users.discard(target)
        if target in db.vip_expiry:
            del db.vip_expiry[target]
        db.save_data()

        username, name = get_user_info(target)
        bot.reply_to(message,
            f"🚫 <b>VIP STATUS REVOKED</b> 🚫\n\n"
            f"👤 <b>User:</b> {username}\n"
            f"🆔 <b>ID:</b> <code>{target}</code>\n"
            f"🔑 <b>Removed by:</b> @{message.from_user.username or message.from_user.id}",
            parse_mode='HTML'
        )
        try:
            bot.send_message(target, "💔 Your VIP membership has been revoked.", parse_mode='HTML')
        except Exception as e:
            logger.error(f"Failed to notify user {target} of VIP removal: {e}")
    else:
        bot.reply_to(message, f"⚠️ User <code>{target}</code> is not currently in the VIP list.", parse_mode='HTML')

@bot.message_handler(commands=['vips'])
def list_vips(message):
    if not check_bot_active(message) or not is_admin(message.from_user.id):
        return

    if not db.vip_users:
        bot.reply_to(message, "😔 No VIP users registered yet.", parse_mode='HTML')
        return

    text = "👑 <b>CURRENT VIP USERS:</b>\n\n"
    sorted_vips = sorted(list(db.vip_users))

    for user_id in sorted_vips:
        expiry = db.vip_expiry.get(user_id)
        expiry_str = "Permanent"
        if expiry:
            if time.time() < expiry:
                remaining_seconds = expiry - time.time()
                days, remainder = divmod(remaining_seconds, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, _ = divmod(remainder, 60)
                expiry_str = f"Expires in: {int(days)}d {int(hours)}h {int(minutes)}m"
            else:
                expiry_str = "Expired (needs removal/update)"
        username, _ = get_user_info(user_id)
        text += f"• {username} (<code>{user_id}</code>) - {expiry_str}\n"

    bot.reply_to(message, text, parse_mode='HTML')

@bot.message_handler(commands=['addc', 'dcn'])
def manage_coins(message):
    if not check_bot_active(message) or not is_admin(message.from_user.id):
        return

    args = message.text.split()
    cmd = args[0][1:] # 'addc' or 'dcn'

    target_user_id = None
    amount_str = None

    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        if len(args) > 1:
            amount_str = args[1]
    elif len(args) > 2: # /cmd <amount/all> <user_id/@username>
        amount_str = args[1]
        target_input = args[2]
        try:
            target_user_id = int(target_input) if not target_input.startswith('@') else bot.get_chat(target_input).id
        except Exception as e:
            bot.reply_to(message, f"❌ Invalid user specified: {e}", parse_mode='HTML')
            return
    else:
        help_text = {
            'addc': "💎 <b>Add Coins Command Usage</b> 💎\n\n<code>/addc &lt;amount&gt; &lt;user_id/@username/reply&gt;</code>",
            'dcn': "💎 <b>Deduct Coins Command Usage</b> 💎\n\n<code>/dcn &lt;amount/all&gt; &lt;user_id/@username/reply&gt;</code>"
        }
        bot.reply_to(message, help_text[cmd], parse_mode='HTML')
        return

    if target_user_id is None:
        bot.reply_to(message, "❌ Could not determine target user.", parse_mode='HTML')
        return

    try:
        amount = 0
        if cmd == 'dcn' and amount_str and amount_str.lower() == 'all':
            amount = db.user_coins.get(target_user_id, 0)
        else:
            amount = int(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be positive.")
    except (ValueError, TypeError):
        bot.reply_to(message, f"❌ Invalid amount specified. Must be a positive number or 'all' for deduction.", parse_mode='HTML')
        return

    current_coins = db.user_coins.get(target_user_id, 0)
    if cmd == 'addc':
        db.user_coins[target_user_id] = current_coins + amount
        action = "ADDED"
    else: # dcn
        if current_coins < amount:
            bot.reply_to(message, f"❌ User <code>{target_user_id}</code> only has {current_coins} coins.", parse_mode='HTML')
            return
        db.user_coins[target_user_id] = current_coins - amount
        action = "DEDUCTED"

    db.all_users.add(target_user_id)
    db.save_data()

    username, name = get_user_info(target_user_id)
    bot.reply_to(message,
        f"💰 <b>COINS {action} SUCCESSFULLY!</b>\n\n"
        f"👤 <b>User:</b> {username}\n"
        f"📛 <b>Name:</b> {name}\n"
        f"🆔 <b>ID:</b> <code>{target_user_id}</code>\n"
        f"🪙 <b>Amount {action}:</b> {amount} coins\n"
        f"💎 <b>New Balance:</b> {db.user_coins.get(target_user_id, 0)} coins",
        parse_mode='HTML'
    )

@bot.message_handler(commands=['coins'])
def check_coins(message):
    if not check_bot_active(message) or not check_command_status(message):
        return

    args = message.text.split()
    target_user_id = message.from_user.id

    if len(args) > 1 and is_admin(message.from_user.id):
        try:
            target_input = args[1]
            target_user_id = int(target_input) if not target_input.startswith('@') else bot.get_chat(target_input).id
        except Exception as e:
            bot.reply_to(message, f"❌ Invalid user specified: {e}", parse_mode='HTML')
            return

    coins = db.user_coins.get(target_user_id, 0)
    username, name = get_user_info(target_user_id)
    can_send, remaining_likes = db.can_send_like(target_user_id)
    daily_limit = Config.FREE_USER_DAILY_LIMIT

    if target_user_id in db.custom_limits:
        limit_type = "Custom"
        daily_limit = db.custom_limits[target_user_id]
    elif is_vip(target_user_id):
        limit_type = "VIP"
        daily_limit = Config.VIP_USER_DAILY_LIMIT
    else:
        limit_type = "Free"

    verification_credits = db.verification_credits.get(target_user_id, 0)
    
    response = (
        f"✨ <b>Ghost x coin & limits</b>\n"
        f"--- \n\n"
        f"👤 <b>User:</b> {username}\n"
        f"📛 <b>Name:</b> {name}\n"
        f"🆔 <b>ID:</b> <code>{target_user_id}</code>\n\n"
        f"💰 <b>Coin Balance:</b>\n"
        f"╰┈➤ <b>{coins} Coins</b>\n\n"
        f"🌟 <b>Verification Credits:</b>\n"
        f"╰┈➤ <b>{verification_credits} Credits</b>\n\n"
        f"🚀 <b>Daily Like Usage:</b>\n"
        f"╰┈➤ <b>Status:</b> {limit_type} User\n"
        f"╰┈➤ <b>Daily Limit:</b> {daily_limit} Likes\n"
        f"╰┈➤ <b>Likes Remaining:</b> {remaining_likes}\n"
        f"<b>Next Reset:</b>\n{get_next_reset_time()}"
    )

    bot.reply_to(message, response, parse_mode='HTML')

BROADCAST_STATE = {}
@bot.message_handler(commands=['broadcast', 'modhu'])
def initiate_broadcast(message):
    if not check_bot_active(message) or not is_admin(message.from_user.id):
        return
    BROADCAST_STATE[message.from_user.id] = {
        'waiting_for_message': True,
        'is_modhu': message.text.startswith('/modhu')
    }
    bot.reply_to(message, "📢 <b>Please send the message (text, photo, video, etc.) you want to broadcast now.</b>\n"
                           "Once sent, you'll receive a confirmation prompt.", parse_mode='HTML')

@bot.message_handler(func=lambda message: message.from_user.id in BROADCAST_STATE and BROADCAST_STATE[message.from_user.id]['waiting_for_message'], content_types=['text', 'photo', 'video', 'sticker', 'document', 'audio', 'voice', 'video_note'])
def receive_broadcast_message(message):
    user_id = message.from_user.id
    if user_id not in BROADCAST_STATE or not BROADCAST_STATE[user_id]['waiting_for_message']:
        return

    is_modhu = BROADCAST_STATE[user_id]['is_modhu']
    del BROADCAST_STATE[user_id]

    confirm_text = (
        "📢 <b>OFFICIAL BROADCAST MESSAGE</b> 📢\n\n"
        "🔰 <b>From: GHOST X ADMIN TEAM</b>\n\n"
        f"This message will be sent to <b>{len(db.all_users)} users</b>.\n\n"
        "Are you sure you want to proceed?"
    ) if is_modhu else (
        "⚠️ <b>BROADCAST CONFIRMATION</b>\n\n"
        f"This message will be sent to <b>{len(db.all_users)} users</b>.\n\n"
        "Are you sure you want to proceed?"
    )

    confirm_kb = InlineKeyboardMarkup()
    confirm_kb.add(
        InlineKeyboardButton("✅ Confirm Broadcast", callback_data=f"broadcast_confirm:{message.message_id}:{message.chat.id}:{int(is_modhu)}"),
        InlineKeyboardButton("❌ Cancel Broadcast", callback_data="broadcast_cancel")
    )
    bot.send_message(message.chat.id, confirm_text, reply_markup=confirm_kb, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('broadcast_'))
def handle_broadcast_confirmation(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⚠️ You are not authorized!", show_alert=True)
        return

    if call.data == "broadcast_cancel":
        bot.edit_message_text("❌ <b>Broadcast cancelled.</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
        bot.answer_callback_query(call.id, "Broadcast cancelled")
        return

    bot.answer_callback_query(call.id, "Starting broadcast... This may take a while.")

    parts = call.data.split(':')
    original_message_id = int(parts[1])
    original_chat_id = int(parts[2])
    is_modhu = bool(int(parts[3]))

    total_users = len(db.all_users)
    sent_count = 0
    failed_count = 0

    status_msg = bot.edit_message_text(
        "📢 <b>BROADCAST IN PROGRESS</b>\n\n"
        f"• Sent: 0/{total_users}\n"
        f"• Failed: 0",
        call.message.chat.id, call.message.message_id, parse_mode='HTML'
    )

    def send_to_user(user_id):
        nonlocal sent_count, failed_count
        try:
            if is_modhu:
                bot.send_message(user_id, "📢 <b>OFFICIAL BROADCAST MESSAGE</b> 📢\n\n🔰 <b>From: GHOST X ADMIN TEAM</b>\n\n", parse_mode='HTML')
            bot.copy_message(user_id, original_chat_id, original_message_id)
            sent_count += 1
            return True
        except telebot.apihelper.ApiTelegramException as e:
            if e.result_json and e.result_json.get('error_code') == 403:
                logger.warning(f"User {user_id} blocked the bot. Removing from all_users list.")
                db.all_users.discard(user_id) # Optionally remove user
            else:
                logger.error(f"Error sending broadcast to user {user_id}: {e}")
            failed_count += 1
            return False

    user_list = list(db.all_users)
    start_time = time.time()
    for i, user_id in enumerate(user_list):
        executor.submit(send_to_user, user_id)
        if i % 25 == 0 or (i + 1) == total_users: # Update status every 25 users or at the end
            time.sleep(1) # Sleep to avoid hitting rate limits and allow counters to update
            try:
                bot.edit_message_text(
                    "📢 <b>BROADCAST IN PROGRESS</b>\n\n"
                    f"• Sent: {sent_count}/{total_users}\n"
                    f"• Failed: {failed_count}",
                    call.message.chat.id, status_msg.message_id, parse_mode='HTML'
                )
            except telebot.apihelper.ApiTelegramException as e:
                if "message is not modified" not in str(e).lower():
                    logger.error(f"Error updating broadcast status: {e}")

    # Wait for all threads to complete for final count
    time.sleep(5) # Give some buffer time for last threads
    db.save_data()
    end_time = time.time()
    duration = end_time - start_time
    
    bot.edit_message_text(
        "✅ <b>BROADCAST COMPLETED!</b>\n\n"
        f"🚀 <b>Summary:</b>\n"
        f"╰┈➤ <b>Total Users:</b> {total_users}\n"
        f"╰┈➤ <b>Successfully Sent:</b> {sent_count}\n"
        f"╰┈➤ <b>Failed:</b> {failed_count}\n"
        f"╰┈➤ <b>Duration:</b> {duration:.2f} seconds\n\n"
        f"📅 <b>Finished At:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        call.message.chat.id, status_msg.message_id, parse_mode='HTML'
    )

@bot.message_handler(commands=['addremind', 'rmremind'])
def manage_limits(message):
    if not check_bot_active(message) or not is_admin(message.from_user.id):
        return

    args = message.text.split()
    cmd = args[0][1:]
    
    target_user_id = None
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    elif len(args) > (2 if cmd == 'addremind' else 1):
        target_input = args[2] if cmd == 'addremind' else args[1]
        try:
            target_user_id = int(target_input) if not target_input.startswith('@') else bot.get_chat(target_input).id
        except Exception as e:
            bot.reply_to(message, f"❌ Invalid user specified: {e}", parse_mode='HTML')
            return
    else:
        if cmd == 'addremind':
            bot.reply_to(message, "💎 <b>Add Custom Daily Limit</b> 💎\n\n<code>/addremind &lt;limit&gt; &lt;user_id/username/reply&gt;</code>", parse_mode='HTML')
        else:
            bot.reply_to(message, "💎 <b>Remove Custom Daily Limit</b> 💎\n\n<code>/rmremind &lt;user_id/username/reply&gt;</code>", parse_mode='HTML')
        return
    
    if target_user_id is None:
        bot.reply_to(message, "❌ Could not determine target user.", parse_mode='HTML')
        return

    if cmd == 'addremind':
        try:
            limit = int(args[1])
            if limit < 1: raise ValueError
        except (ValueError, IndexError):
            bot.reply_to(message, "❌ Invalid limit. Please provide a positive integer.", parse_mode='HTML')
            return
        
        db.custom_limits[target_user_id] = limit
        action_text = "SET"
        details_text = f"💎 <b>Daily Like Limit:</b> {limit}"
        final_message_part = f"This user can now send up to {limit} Account Likes per day."
    else: # rmremind
        if target_user_id in db.custom_limits:
            del db.custom_limits[target_user_id]
            action_text = "REMOVED"
            details_text = ""
            final_message_part = "This user will now revert to their default daily like limit."
        else:
            bot.reply_to(message, "⚠️ This user doesn't have a custom limit set.", parse_mode='HTML')
            return
    
    db.save_data()
    username, name = get_user_info(target_user_id)
    bot.reply_to(message,
        f"✨ <b>CUSTOM DAILY LIMIT {action_text}!</b> ✨\n\n"
        f"👤 <b>User:</b> {username}\n"
        f"📛 <b>Name:</b> {name}\n"
        f"🆔 <b>ID:</b> <code>{target_user_id}</code>\n"
        f"{details_text}\n\n{final_message_part}",
        parse_mode='HTML'
    )

@bot.message_handler(commands=['c-off', 'c-on'])
def toggle_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⚠️ You are not authorized to use this command!", parse_mode='HTML')
        return

    args = message.text.split(maxsplit=2)
    cmd_action = args[0][1:].lower()

    if len(args) < 2:
        bot.reply_to(message, f"<b>❗ USAGE:</b> <code>/{cmd_action} &lt;command_name&gt; [custom_message]</code>", parse_mode='HTML')
        return

    target_command = args[1].lower().replace('/', '')
    allowed_commands_to_toggle = ['like', 'visit', 'spam', 'get', 'coins', 'bancheck', 'help']

    if target_command not in allowed_commands_to_toggle:
        bot.reply_to(message, f"❌ <b>Invalid command.</b> Allowed: <code>{', '.join(allowed_commands_to_toggle)}</code>", parse_mode='HTML')
        return
    
    custom_message = args[2] if len(args) > 2 else None

    if cmd_action == 'c-off':
        db.command_status[target_command] = {'enabled': False, 'message': custom_message}
        response = f"❌ Command <code>/{target_command}</code> has been <b>DISABLED</b>."
        if custom_message:
            response += f"\n\nUsers will see: <i>\"{custom_message}\"</i>"
    else:
        if target_command in db.command_status:
            del db.command_status[target_command]
        response = f"✅ Command <code>/{target_command}</code> has been <b>ENABLED</b>."
    
    db.save_data()
    bot.reply_to(message, response, parse_mode='HTML')

@bot.message_handler(commands=['control'])
def handle_control_panel(message):
    if not is_admin(message.from_user.id):
        return

    text = "⚙️ <b>GHOST X ADMIN CONTROL PANEL</b> ⚙️\n"
    text += "--- \n\n"
    text += "To change a setting, use the format:\n"
    text += "<code>/setx &lt;SETTING_NAME&gt; &lt;new_value&gt;</code>\n\n"
    text += "<b>Current Config Values:</b>\n"
    
    for attr_name in sorted(dir(Config)):
        if not attr_name.startswith('__') and not callable(getattr(Config, attr_name)):
            if attr_name not in ['BOT_TOKEN', 'OWNER_ID', 'SHORTENER_API']:
                attr_value = getattr(Config, attr_name)
                if isinstance(attr_value, dict):
                    text += f"• <b>{attr_name}:</b> (Dictionary)\n"
                    for k, v in attr_value.items():
                        text += f"  - <code>{k}</code>: <code>{v}</code>\n"
                elif isinstance(attr_value, list):
                    text += f"• <b>{attr_name}:</b> (List)\n  - <code>{', '.join(attr_value)}</code>\n"
                else:
                    text += f"• <b>{attr_name}:</b> <code>{attr_value}</code>\n"
    
    text += "\n<b>Examples for <code>/setx</code>:</b>\n"
    text += "<code>/setx LIKE_API_URL https://new-like-api.com</code>\n"
    text += "<code>/setx FREE_USER_DAILY_LIMIT 2</code>\n"
    text += "<code>/setx SPAM_COOLDOWN 90</code>\n"
    text += "<code>/setx CHANNELS @c1,@c2</code> (comma separated, NO spaces)\n\n"
    text += "<b>⚠️ WARNING: Incorrect values can break the bot!</b>\n"
    
    bot.reply_to(message, text, parse_mode='HTML', disable_web_page_preview=True)

@bot.message_handler(commands=['setx'])
def handle_set_config(message):
    if not check_bot_active(message) or not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        bot.reply_to(message, "<b>❗ USAGE:</b> <code>/setx &lt;SETTING_NAME&gt; &lt;new_value&gt;</code>", parse_mode='HTML')
        return

    setting_name = args[1].upper() # Match Config attributes which are uppercase
    new_value_str = args[2]

    if not hasattr(Config, setting_name):
        bot.reply_to(message, f"❌ Setting <code>{setting_name}</code> not found in Config.", parse_mode='HTML')
        return
    
    if setting_name in ['BOT_TOKEN', 'OWNER_ID', 'SHORTENER_API']:
        bot.reply_to(message, f"❌ Changing <code>{setting_name}</code> is not allowed for security reasons.", parse_mode='HTML')
        return

    old_value = getattr(Config, setting_name)
    value_type = type(old_value)

    try:
        new_value = None
        if value_type is int: new_value = int(new_value_str)
        elif value_type is float: new_value = float(new_value_str)
        elif value_type is bool: new_value = new_value_str.lower() in ['true', '1', 'yes']
        elif value_type is list: new_value = [item.strip() for item in new_value_str.split(',') if item.strip()]
        elif value_type is dict:
            new_value = {}
            for item in new_value_str.split(','):
                if ':' in item:
                    k, v = item.split(':', 1)
                    new_value[k.strip()] = v.strip()
                else: raise ValueError(f"Invalid dict format: '{item}'")
        else: new_value = new_value_str
        
        setattr(Config, setting_name, new_value)
        db.config_values[setting_name] = new_value
        db.save_data()
        
        bot.reply_to(message,
                     f"✅ <b>Setting Updated Successfully!</b>\n\n"
                     f"• <b>{setting_name}:</b>\n"
                     f"  - Old Value: <code>{old_value}</code>\n"
                     f"  - New Value: <code>{new_value}</code>",
                     parse_mode='HTML')
    except ValueError as e:
        bot.reply_to(message, f"❌ Invalid value format for <code>{setting_name}</code>. Expected <code>{value_type.__name__}</code>.\nError: <i>{e}</i>", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error setting config {setting_name}: {e}")
        bot.reply_to(message, f"❌ An unexpected error occurred: {e}", parse_mode='HTML')

@bot.message_handler(commands=['admin'])
def admin_commands(message):
    if not is_admin(message.from_user.id): return
    
    admin_help = """
🔐 <b>GHOST X ADMIN PANEL</b> 🔐

---
💰 <b>Coin & Limit Management:</b>
<code>/addc &lt;amt&gt; &lt;id/user/reply&gt;</code> - Add coins.
<code>/dcn &lt;amt/all&gt; &lt;id/user/reply&gt;</code> - Deduct coins.
<code>/coins &lt;id/user&gt;</code> - Check user balance.
<code>/addremind &lt;limit&gt; &lt;id/user/reply&gt;</code> - Set custom daily like limit.
<code>/rmremind &lt;id/user/reply&gt;</code> - Remove custom limit.

---
👑 <b>VIP Membership:</b>
<code>/addvip &lt;duration&gt; &lt;id/user/reply&gt;</code> - Grant VIP (e.g., 30min, 2h, 15d, perm).
<code>/dvip &lt;id/user/reply&gt;</code> - Revoke VIP.
<code>/vips</code> - List all VIP users.

---
📢 <b>Global Messaging:</b>
<code>/broadcast</code> - Send a message to all users.
<code>/modhu</code> - Send an official broadcast.

---
⚙️ <b>Bot & Command Control:</b>
<code>/ghost-on</code> / <code>/ghost-off</code> - Toggle bot status.
<code>/verification-on</code> / <code>/verification-off</code> - Toggle user verification.
<code>/verification_video_on</code> / <code>/verification_video_off</code> - Toggle verification video.
<code>/c-on &lt;cmd&gt;</code> / <code>/c-off &lt;cmd&gt; [msg]</code> - Toggle a command.

---
📊 <b>Advanced Configuration:</b>
<code>/control</code> - View bot settings.
<code>/setx &lt;SETTING&gt; &lt;value&gt;</code> - Modify a bot setting. <b>(Use with caution!)</b>
"""
    bot.reply_to(message, admin_help, parse_mode='HTML', disable_web_page_preview=True)

# ===================== OPTIMIZED USER COMMANDS =====================
@bot.message_handler(commands=['start'])
def handle_start(message):
    if not check_bot_active(message): return
    
    db.all_users.add(message.from_user.id)
    db.save_data()

    args = message.text.split()
    if len(args) > 1 and args[1].startswith('verify_'):
        handle_verification(message)
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🌟 JOIN VIP GROUP", url=Config.GROUP_LINK))
    kb.add(InlineKeyboardButton("🔗 CHANNELS", url=Config.CHANNEL_JOIN_LINK))
    bot.reply_to(message,
        "🤖<b> Welcome to ghost x vip bot</b>\n"
        "--- \n\n"
        "💎 <b>Premium Free Fire ID Services:</b>\n"
        "⚡ Instant Like/Visit Delivery\n"
        "🔒 Secure VIP Network\n"
        "🌐 Advanced Player Information Tools\n\n"
        "<b>🔗 Before Using: Please Join Our Channels!</b>\n"
        "⚠️ You must join ALL specified channels to unlock bot features.",
        reply_markup=kb, disable_web_page_preview=True)

@bot.message_handler(commands=['help'])
def handle_help(message):
    if not check_bot_active(message) or not check_command_status(message): return
    
    is_vip_user = is_vip(message.from_user.id)
    vip_text = (f"\n\n👑 <b>Vip member perks:</b>\n"
                f"╰┈➤ {Config.VIP_USER_DAILY_LIMIT} Accounts per day.\n"
                f"╰┈➤ No cooldowns & Skips verification.") if is_vip_user else (
                f"\n🆓 <b>Free user limits:</b>\n"
                f"╰┈➤ {Config.FREE_USER_DAILY_LIMIT} Account per day.\n"
                f"╰┈➤ Cooldowns and verification required.")
    
    help_message = f"""
🤖 <b>Ghost x vip bot help center</b>

🎮 <b>Essential commands:</b>
<code>/start</code> - Start the bot.
<code>/help</code> - Show this help message.
<code>/coins</code> - Check your coins..

💎 <b>Premium ff services:</b>
<code>/like &lt;region&gt; &lt;uid&gt;</code> - Likes.
<code>/visit &lt;region&gt; &lt;uid&gt;</code> - Visits.
<code>/spam &lt;region&gt; &lt;uid&gt;</code> - Spam.
<code>/gt &lt;uid&gt;</code> - Get detailed account info (no region needed).
<code>/bancheck &lt;uid&gt;</code> - bancheck.

🌍 <b>Supported regions:</b>
Use 2-letter codes: <code>bd</code>, <code>ind</code>, <code>pk</code>, <code>id</code>, <code>th</code>, <code>my</code>, <code>vn</code>, <code>ru</code>, <code>mx</code>, <code>tw</code>, <code>me</code>, <code>eu</code>, <code>sg</code>, <code>ssa</code>
"""
    help_message += vip_text
    bot.reply_to(message, help_message, parse_mode='HTML', disable_web_page_preview=True)

@bot.message_handler(commands=['like', 'visit', 'spam'])
def handle_like_visit_spam(message):
    if not check_bot_active(message) or not check_command_status(message):
        return
    
    user_id = message.from_user.id
    db.all_users.add(user_id) # Ensure user is in global list
    db.save_data() # Save user to all_users

    # Check if command is used in private chat, if it's meant for groups
    if message.chat.type == "private":
        bot.reply_to(message, f"⚠️ This command is restricted to our official group for security and functionality:\n{Config.GROUP_LINK}\n\nPlease use it there.", disable_web_page_preview=True)
        return

    command_type = message.text.split()[0][1:] # 'like', 'visit', or 'spam'
    
    # 1. Check Daily Like Limit (only for 'like' command)
    if command_type == 'like':
        can_send, remaining = db.can_send_like(user_id)
        if not can_send:
            reset_time = get_next_reset_time()
            if is_vip(user_id) or user_id in db.custom_limits:
                limit_info = "VIP User" if is_vip(user_id) else "Custom Limit User"
                bot.reply_to(message,
                    f"⚠️ <b>DAILY LIKE LIMIT REACHED!</b>\n\n"
                    f"You have reached your daily limit for sending likes.\n"
                    f"Your limit will reset at <b>{reset_time}</b>.\n\n"
                    f"💎 <b>Current Status:</b> {limit_info}",
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            else:
                bot.reply_to(message,
                    f"⚠️ <b>DAILY FREE LIKE LIMIT REACHED!</b>\n\n"
                    f"You have used your <b>{Config.FREE_USER_DAILY_LIMIT} free like</b> for today.\n"
                    f"Your limit will reset at <b>{reset_time}</b>.\n\n"
                    f"🚀 <b>Upgrade to VIP</b> to send up to {Config.VIP_USER_DAILY_LIMIT} Account daily and bypass cooldowns!\n"
                    f"Contact: @BABA_TILLU_XY",
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            return
    
    # 2. Parse Command Arguments
    args = message.text.split()
    if len(args) < 3:
        usage_text = (
            f"<b>💎 VIP {command_type.upper()} COMMAND USAGE</b>\n\n"
            f"<code>/{command_type} &lt;region&gt; &lt;uid&gt;</code>\n\n"
            f"<b>Examples:</b>\n"
            f"<code>/{command_type} bd 123456789</code>\n"
            f"<code>/{command_type} id 987654321</code>"
        )
        if command_type == 'spam':
            usage_text += "\n\n⚠️ <b>NOTE:</b> `/spam` command is currently only available for Bangladesh (<code>bd</code>) region."
        
        bot.reply_to(message, usage_text, parse_mode='HTML', disable_web_page_preview=True)
        return
    
    region, uid = args[1].lower(), args[2] # Ensure region is lowercased for validation
    
    # 3. Validate Region and UID
    if not validate_region(region):
        bot.reply_to(message,
            "❌ <b>INVALID REGION CODE!</b>\n\n"
            "Please use a valid 2-letter region code from the list in /help.",
            parse_mode='HTML'
        )
        return
    
    if not validate_uid(uid):
        bot.reply_to(message,
            "❌ <b>INVALID UID FORMAT!</b>\n\n"
            "UID must be 8-12 digits and contain only numbers.\n"
            "Example: <code>12345678</code> or <code>123456789012</code>",
            parse_mode='HTML'
        )
        return
    
    # 4. Specific region validation for /spam command
    if command_type == 'spam' and region != 'bd': # Use lowercased region
        bot.reply_to(message,
            "❌ <b>SPAM COMMAND LIMITATION!</b>\n\n"
            "The <code>/spam</code> command is currently only available for the <b>Bangladesh (<code>bd</code>)</b> server. "
            "Please select a valid region for other services or use `bd` for spam.",
            parse_mode='HTML'
        )
        return
    
    # Store command details before channel check, in case user needs to join channels
    db.pending_requests[user_id] = {
        'type': command_type,
        'region': region,
        'uid': uid,
        'chat_id': message.chat.id,
        'message_id': message.message_id,
        'pending_message_id': None # This will be set if a verification message is sent
    }
    db.save_data()

    # 5. Check Channel Subscription (for all users, regardless of VIP)
    not_joined_channels = is_subscribed(user_id)
    if not_joined_channels:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔗 REQUIRED CHANNELS", url=Config.CHANNEL_JOIN_LINK)) # Primary button
        for channel in not_joined_channels:
            kb.add(InlineKeyboardButton(f"📢 Join {channel}", url=f"https://t.me/{channel.replace('@', '')}"))
        # Using a new callback_data prefix to differentiate from /start verify_
        kb.add(InlineKeyboardButton("🔓 VERIFY JOINING", callback_data=f"check_join:{user_id}")) # Simplified callback

        bot.reply_to(message,
            "<b>🔒 CHANNEL JOIN REQUIRED!</b>\n\n"
            "⚠️ To use this bot's features, you *must* join all our official channels.\n"
            "Click the button(s) below to join, then click 'VERIFY JOINING'.",
            reply_markup=kb,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        return # Stop here, user needs to join channels and re-trigger check_join

    # 6. Check Cooldowns (for non-VIP users)
    if not is_vip(user_id):
        current_time = time.time()
        if command_type == 'visit':
            last_visit = db.visit_cooldowns.get(user_id, 0)
            elapsed = current_time - last_visit
            if elapsed < Config.VISIT_COOLDOWN:
                remaining_time = int(Config.VISIT_COOLDOWN - elapsed)
                bot.reply_to(message,
                    f"⏳ <b>COOLDOWN ACTIVE!</b> ⏳\n\n"
                    f"Please wait <b>{remaining_time} seconds</b> before sending another visit request.\n"
                    f"✨ <b>Become a VIP Member</b> to bypass all cooldowns! Contact: @BABA_TILLU_XY",
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                return
        elif command_type == 'spam':
            last_spam = db.spam_cooldowns.get(user_id, 0)
            elapsed = current_time - last_spam
            if elapsed < Config.SPAM_COOLDOWN:
                remaining_time = int(Config.SPAM_COOLDOWN - elapsed)
                bot.reply_to(message,
                    f"⏳ <b>COOLDOWN ACTIVE!</b> ⏳\n\n"
                    f"Please wait <b>{remaining_time} seconds</b> before sending another spam request.\n"
                    f"✨ <b>Become a VIP Member</b> to bypass all cooldowns! Contact: @BABA_TILLU_XY",
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                return
    
    # 7. Check Verification Requirements (for non-VIP users)
    if db.verification_enabled and not is_vip(user_id) and db.verification_credits.get(user_id, 0) <= 0:
        # Send initial processing message that will be replaced by the verification message
        initial_msg = bot.send_message(message.chat.id, "⏳ Generating verification link...", reply_to_message_id=message.message_id, parse_mode='HTML')
        
        # Store initial message ID for later deletion
        if user_id in db.pending_requests:
            db.pending_requests[user_id]['pending_message_id'] = initial_msg.message_id
            db.save_data()

        verification_msg_data = create_verification_message(user_id, region, uid, command_type, message.chat.id, message.message_id, initial_msg.message_id)
        
        try:
            if Config.VERIFICATION_VIDEO_ENABLED:
                bot.delete_message(message.chat.id, initial_msg.message_id) # Delete "generating" message
                sent_msg = send_video_reply(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    video_file=Config.VERIFICATION_VIDEO,
                    caption=verification_msg_data['caption']
                )
            else:
                bot.edit_message_text( # Edit "generating" message into verification message
                    verification_msg_data['text'],
                    chat_id=message.chat.id,
                    message_id=initial_msg.message_id,
                    reply_markup=verification_msg_data['reply_markup'],
                    disable_web_page_preview=True,
                    parse_mode='HTML'
                )
            return
        except Exception as e:
            logger.error(f"Error sending/editing verification message: {e}")
            bot.delete_message(message.chat.id, initial_msg.message_id) # Clean up
            bot.reply_to(message, "❌ An error occurred while preparing verification. Please try again.", parse_mode='HTML')
            return
    
    # 8. Process the command (after all checks passed)
    if command_type == 'like':
        process_like(message.chat.id, message.message_id, user_id, region, uid, original_credits=db.verification_credits.get(user_id, 0))
    elif command_type == 'visit':
        process_visit(message.chat.id, message.message_id, user_id, region, uid, original_credits=db.verification_credits.get(user_id, 0))
    elif command_type == 'spam':
        process_spam(message.chat.id, message.message_id, user_id, region, uid, original_credits=db.verification_credits.get(user_id, 0))

@bot.callback_query_handler(func=lambda call: call.data.startswith('check_join:'))
def handle_channel_join_verification(call):
    user_id = int(call.data.split(':')[1])
    
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "⚠️ This button is not for you!", show_alert=True)
        return

    bot.answer_callback_query(call.id, "Checking your channel subscriptions...")

    not_joined_channels = is_subscribed(user_id)
    
    if not not_joined_channels:
        # User is now subscribed, retrieve and process the pending request
        req_data = db.pending_requests.get(user_id)
        if req_data:
            command_type = req_data['type']
            region = req_data['region']
            uid = req_data['uid']
            original_chat_id = req_data['chat_id']
            original_message_id = req_data['message_id']
            
            # Delete the "CHANNEL JOIN REQUIRED" message
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception as e:
                logger.error(f"Error deleting channel join message: {e}")

            # Now, proceed with the main command logic (cooldowns, shortener verification)
            # Send a confirmation in the group
            bot.send_message(original_chat_id,
                             f"✅ <b>Channel verification successful!</b>\n"
                             f"Proceeding with your <code>/{command_type}</code> request...",
                             reply_to_message_id=original_message_id,
                             parse_mode='HTML')

            # Re-call the original handler, but now they are subscribed
            # This will re-evaluate cooldowns and then proceed to shortener if needed
            # We recreate a dummy message object for the handler, copying relevant info
            dummy_message = type('obj', (object,), {
                'from_user': call.from_user,
                'chat': type('obj', (object,), {'id': original_chat_id, 'type': 'group'}), # Or 'supergroup'
                'message_id': original_message_id,
                'text': f"/{command_type} {region} {uid}" # Reconstruct the original command
            })()
            
            handle_like_visit_spam(dummy_message)

            # Clear the pending request only after successful processing
            # It will be cleared by the /like /visit /spam handler itself if all checks pass.
            # If a new shortener is sent, pending_requests will be updated.
            # If no shortener, it means they are VIP or have credits, so it processes.

        else:
            bot.edit_message_text(
                "✅ <b>You are now subscribed to all channels!</b>\n"
                "Please send your command again (e.g., <code>/like &lt;region&gt; &lt;uid&gt;</code>).",
                call.message.chat.id, call.message.message_id, parse_mode='HTML'
            )
    else:
        # User still hasn't joined all channels
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔗 REQUIRED CHANNELS", url=Config.CHANNEL_JOIN_LINK))
        for channel in not_joined_channels:
            kb.add(InlineKeyboardButton(f"📢 Join {channel}", url=f"https://t.me/{channel.replace('@', '')}"))
        kb.add(InlineKeyboardButton("🔓 VERIFY JOINING", callback_data=f"check_join:{user_id}")) # Keep callback for re-check

        bot.edit_message_text(
            "❌ <b>CHANNEL JOIN FAILED!</b>\n\n"
            "You have not joined all required channels. Please ensure you join *all* listed channels, then click 'VERIFY JOINING' again.",
            call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode='HTML', disable_web_page_preview=True
        )


def process_like(chat_id, message_id, user_id, region, uid, original_credits=None, pending_message_id=None):
    # Send initial "processing" message as a reply to the user's original command
    try:
        if pending_message_id: # If there was a pending verification message, edit that
            msg_to_edit = bot.edit_message_text("⚡ <b>Processing vip like request...</b>", chat_id, pending_message_id, parse_mode='HTML')
        else: # Otherwise, send a new one
            msg_to_edit = bot.send_message(chat_id, "⚡ <b>Processing vip like request...</b>", parse_mode='HTML', reply_to_message_id=message_id)
    except Exception as e:
        logger.error(f"Failed to send/edit initial processing message for like: {e}")
        return # Cannot proceed if we can't send messages

    steps = [
        "🔐 Verifying account access...",
        "🌐 Connecting to Free Fire server...",
        "💎 Injecting likes securely...",
        "✅ Finalizing transaction and updating statistics..."
    ]
    
    for step in steps:
        try:
            bot.edit_message_text(step, chat_id, msg_to_edit.message_id, parse_mode='HTML')
            time.sleep(0.8) # Simulate processing time
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" in str(e).lower():
                pass # Ignore if message content is identical
            else:
                logger.error(f"Error editing message during like process for user {user_id} in chat {chat_id}: {e}")
        except Exception as e:
            logger.error(f"General error editing message during like process: {e}")

    api_result = call_like_api(region, uid)
    status = api_result.get('status', 0)

    # Handle credits and daily limits based on VIP status and verification
    if not is_vip(user_id) and db.verification_enabled:
        if status == 1: # Success
            db.verification_credits[user_id] = db.verification_credits.get(user_id, 0) - 1
            db.increment_like_count(user_id) # Increment daily like count
        elif status == 0 and original_credits is not None and original_credits == db.verification_credits.get(user_id, 0):
            # Only restore credit if it wasn't already consumed (e.g., if a prior verification failed to record)
            # This logic needs careful consideration. If API failed for reasons other than "already liked", credit should be restored.
            # However, the current API returns status=2 for "already liked", and status=0 for other errors.
            # If a credit was consumed and the API returned status=0, it implies a true failure, and credit should be restored.
            # Simplified: if it wasn't a success (status=1) AND credit was used, restore it.
            if original_credits > db.verification_credits.get(user_id, 0): # Check if credit was actually decremented by previous step
                db.verification_credits[user_id] = db.verification_credits.get(user_id, 0) + 1 # Restore the credit
                logger.info(f"Restored credit for user {user_id} due to like API error (status=0).")

    elif is_vip(user_id): # For VIP users, only increment if successful
        if status == 1:
            db.increment_like_count(user_id)

    db.save_data() # Save data after credit/limit adjustments

    try:
        if status == 1:
            likes_given = int(api_result.get('LikesGivenByAPI', 0))
            likes_before = int(api_result.get('LikesbeforeCommand', 0))
            likes_after = int(api_result.get('LikesafterCommand', 0))
            
            send_video_reply(
                chat_id=chat_id,
                message_id=message_id,
                video_file=Config.SUCCESS_VIDEO,
                caption=(
                    "✅ <b>Likes sent successfully!</b>\n"
                    "--- \n\n"
                    f"👑 <b>Player:</b> {api_result.get('PlayerNickname', 'N/A')}\n"
                    f"🆔 <b>UID:</b> <code>{api_result.get('UID', uid)}</code>\n"
                    f"🌍 <b>Region:</b> {Config.VALID_REGIONS.get(region, region).upper()}\n\n"
                    f"❤️ <b>Likes Sent:</b> {likes_given}\n"
                    f"🤍 <b>Likes Before:</b> {likes_before:,} \n🩷 <b>Likes After:</b> {likes_after:,}\n\n"
                    f"📊 <b>Total Likes Now:</b> {likes_after:,}\n\n"
                    f"🌟 <b>Status:</b> {'VIP MEMBER' if is_vip(user_id) else f'CREDITS LEFT: {db.verification_credits.get(user_id, 0)}'}\n\n"
                )
            )
            
        elif status == 2:
            # For status 2 (already liked), if free user, restore credit since no service was provided.
            if not is_vip(user_id) and db.verification_enabled and original_credits is not None and original_credits > db.verification_credits.get(user_id, 0):
                 db.verification_credits[user_id] = db.verification_credits.get(user_id, 0) + 1
                 logger.info(f"Restored credit for user {user_id} because account was already liked.")
                 db.save_data()

            send_video_reply(
                chat_id=chat_id,
                message_id=message_id,
                video_file=Config.ALREADY_LIKED_VIDEO,
                caption=(
                    "⚠️ <b>ACCOUNT ALREADY LIKED!</b> ⚠️\n"
                    "--- \n\n"
                    f"👑 <b>Player:</b> {api_result.get('PlayerNickname', 'N/A')}\n"
                    f"🆔 <b>UID:</b> <code>{api_result.get('UID', uid)}</code>\n"
                    f"🌍 <b>Region:</b> {Config.VALID_REGIONS.get(region, region).upper()}\n\n"
                    f"💖 <b>Current Likes:</b> {api_result.get('LikesafterCommand', 'N/A'):,}\n\n"
                    "It seems this account has already received a like recently.\n"
                    "Your VIP Credit has been *restored* for free users, and VIP users can try again later.\n\n"
                    f"For support, join: @GHOST_OFCL"
                )
            )
            
        else:
            error_message = api_result.get('error', 'Unknown API Error. Please check UID/Region.')
            send_video_reply(
                chat_id=chat_id,
                message_id=message_id,
                video_file=Config.ERROR_VIDEO,
                caption=(
                    "❌ <b>LIKE REQUEST FAILED!</b>\n"
                    "--- \n\n"
                    f"🆔 <b>UID:</b> <code>{uid}</code>\n"
                    f"🌍 <b>Region:</b> {Config.VALID_REGIONS.get(region, region).upper()}\n"
                    f"Error: <i>{error_message}</i>\n\n"
                    "Please double-check the UID and region, then try again.\n"
                    "If the issue persists, contact support.\n"
                )
            )
        
        # Delete the initial "processing" or "verification" message after sending the final result
        try:
            bot.delete_message(chat_id, msg_to_edit.message_id)
        except Exception as e:
            logger.error(f"Error deleting processing/verification message {msg_to_edit.message_id}: {e}")

    except Exception as e:
        logger.error(f"Error sending final like result to chat {chat_id}, msg {message_id}: {e}")
        # Fallback to plain text message if video/sticker sending fails
        bot.edit_message_text(
            f"<b>💎 VIP LIKE PROCESSED</b>\n"
            f"🆔 <b>UID:</b> <code>{uid}</code>\n"
            f"🌍 <b>Region:</b> {Config.VALID_REGIONS.get(region, region).upper()}\n"
            f"💖 <b>Status:</b> {'SUCCESS' if status == 1 else 'ALREADY LIKED' if status == 2 else 'FAILED'}.\n"
            f"Error details: {api_result.get('error', 'N/A')}",
            chat_id,
            msg_to_edit.message_id,
            parse_mode='HTML'
        )
        try:
            bot.delete_message(chat_id, msg_to_edit.message_id) # Try deleting even if error
        except Exception: pass


def process_visit(chat_id, message_id, user_id, region, uid, original_credits=None, pending_message_id=None):
    # Send initial "processing" message
    try:
        if pending_message_id:
            msg_to_edit = bot.edit_message_text("⚡ <b>PROCESSING VIP VISIT REQUEST...</b>", chat_id, pending_message_id, parse_mode='HTML')
        else:
            msg_to_edit = bot.send_message(chat_id, "⚡ <b>PROCESSING VIP VISIT REQUEST...</b>", parse_mode='HTML', reply_to_message_id=message_id)
    except Exception as e:
        logger.error(f"Failed to send/edit initial processing message for visit: {e}")
        return

    steps = [
        "🔐 Authenticating request...",
        "🌐 Establishing connection to game server...",
        "👀 Sending profile visits...",
        "✅ Completing visit delivery..."
    ]
    
    for step in steps:
        try:
            bot.edit_message_text(step, chat_id, msg_to_edit.message_id, parse_mode='HTML')
            time.sleep(0.8)
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" in str(e).lower():
                pass
            else:
                logger.error(f"Error editing message during visit process for user {user_id} in chat {chat_id}: {e}")
        except Exception as e:
            logger.error(f"General error editing message during visit process: {e}")

    api_result = call_visit_api(region, uid)
    
    # Handle credits and cooldowns
    if not is_vip(user_id) and db.verification_enabled:
        if "nickname" in api_result: # Visit successful
            db.verification_credits[user_id] = db.verification_credits.get(user_id, 0) - 1
            db.visit_cooldowns[user_id] = time.time() # Set cooldown for free users
        elif original_credits is not None and original_credits == db.verification_credits.get(user_id, 0): # Check if credit was consumed
            db.verification_credits[user_id] = db.verification_credits.get(user_id, 0) + 1 # Restore credit on API error
            logger.info(f"Restored credit for user {user_id} due to visit API error.")
    elif is_vip(user_id): # For VIP, always set cooldown for tracking, though it's bypassed
        db.visit_cooldowns[user_id] = time.time()
    
    db.save_data()
    
    try:
        if "nickname" in api_result:
            send_video_reply(
                chat_id=chat_id,
                message_id=message_id,
                video_file=Config.SUCCESS_VIDEO,
                caption=(
                    "👑 <b>VIP VISIT SUCCESSFULLY DELIVERED!</b> 👑\n"
                    "--- \n\n"
                    f"🔰 <b>FF Name:</b> {api_result.get('nickname', 'N/A')}\n"
                    f"🆔 <b>UID:</b> <code>{api_result.get('uid', uid)}</code>\n"
                    f"📊 <b>Level:</b> {api_result.get('level', 'N/A')}\n"
                    f"🌍 <b>Region:</b> {Config.VALID_REGIONS.get(region, region).upper()}\n"
                    f"✅ <b>Success Count:</b> {api_result.get('success', 0)}\n"
                    f"❌ <b>Failed Count:</b> {api_result.get('fail', 0)}\n\n"
                    f"🌟 <b>Status:</b> {'VIP MEMBER' if is_vip(user_id) else f'CREDITS LEFT: {db.verification_credits.get(user_id, 0)}'}\n\n"
                )
            )
        else:
            error_message = api_result.get('error', 'Unknown API Error. Please check UID/Region.')
            send_video_reply(
                chat_id=chat_id,
                message_id=message_id,
                video_file=Config.ERROR_VIDEO,
                caption=(
                    "❌ <b>VISIT REQUEST FAILED!</b> ❌\n"
                    "--- \n\n"
                    f"🆔 <b>UID:</b> <code>{uid}</code>\n"
                    f"🌍 <b>Region:</b> {Config.VALID_REGIONS.get(region, region).upper()}\n"
                    f"Error: <i>{error_message}</i>\n\n"
                    "Please verify the UID and region, then try again.\n"
                    "If problems persist, contact our support team.\n\n"
                )
            )
        try:
            bot.delete_message(chat_id, msg_to_edit.message_id) # Delete message
        except Exception as e:
            logger.error(f"Error deleting processing/verification message {msg_to_edit.message_id}: {e}")
    except Exception as e:
        logger.error(f"Error sending final visit result to chat {chat_id}, msg {message_id}: {e}")
        bot.edit_message_text(
            f"<b>👑 VIP VISIT PROCESSED</b>\n"
            f"🆔 <b>UID:</b> <code>{uid}</code>\n"
            f"🌍 <b>Region:</b> {Config.VALID_REGIONS.get(region, region).upper()}\n"
            f"👀 <b>Status:</b> {'SUCCESS' if 'nickname' in api_result else 'FAILED'}.\n"
            f"Error details: {api_result.get('error', 'N/A')}",
            chat_id,
            msg_to_edit.message_id,
            parse_mode='HTML'
        )
        try:
            bot.delete_message(chat_id, msg_to_edit.message_id) # Try deleting even if error
        except Exception: pass


def process_spam(chat_id, message_id, user_id, region, uid, original_credits=None, pending_message_id=None):
    try:
        if pending_message_id:
            msg_to_edit = bot.edit_message_text("⚡ <b>INITIALIZING VIP SPAM REQUEST...</b>", chat_id, pending_message_id, parse_mode='HTML')
        else:
            msg_to_edit = bot.send_message(chat_id, "⚡ <b>INITIALIZING VIP SPAM REQUEST...</b>", parse_mode='HTML', reply_to_message_id=message_id)
    except Exception as e:
        logger.error(f"Failed to send/edit initial processing message for spam: {e}")
        return

    def send_spam_and_report():
        # This function runs in a separate thread
        api_result = call_spam_api(region, uid)
        
        # Handle credits and cooldowns
        if not is_vip(user_id) and db.verification_enabled:
            # Credit is consumed regardless of API success, as the "sending" process started.
            db.verification_credits[user_id] = db.verification_credits.get(user_id, 0) - 1
            db.spam_cooldowns[user_id] = time.time()
        elif is_vip(user_id):
            db.spam_cooldowns[user_id] = time.time() # Set cooldown for VIPs as well for tracking
            
        db.save_data()
        
        try:
            # Delete the "processing..." message.
            bot.delete_message(chat_id, msg_to_edit.message_id)

            # Send the final result as a reply to the original user message
            send_video_reply(
                chat_id=chat_id,
                message_id=message_id,
                video_file=Config.SUCCESS_VIDEO if api_result.get('status') == 1 else Config.ERROR_VIDEO,
                caption=(
                    f"<b>✨ Spam request sent!</b>\n"
                    f"--- \n\n"
                    f"🆔 <b>Target UID:</b> <code>{uid}</code>\n"
                    f"🌍 <b>Region:</b> {Config.VALID_REGIONS.get(region, region).upper()}\n\n"
                    f"{'✅ Your spam request has been successfully processed.' if api_result.get('status') == 1 else '❌ Failed to send spam. Error: ' + api_result.get('error', 'Unknown Error.')}\n\n"
                    "Results may vary and are not instantly visible. Please check the target account after some time.\n\n"
                    f"🌟 <b>Status:</b> {'VIP MEMBER' if is_vip(user_id) else f'CREDITS LEFT: {db.verification_credits.get(user_id, 0)}'}\n\n"
                )
            )

        except Exception as e:
            logger.error(f"Error editing message after spam processing for chat {chat_id}, msg {msg_to_edit.message_id}: {e}")
            # Fallback message
            bot.send_message(chat_id,
                             f"<b>💥 Spam request for UID <code>{uid}</code> has been processed!</b>\n"
                             f"Please check the target after some time. Status: {'SUCCESS' if api_result.get('status') == 1 else 'FAILED'}.\n"
                             f"Error details: {api_result.get('error', 'N/A')}",
                             reply_to_message_id=message_id,
                             parse_mode='HTML')
            try:
                bot.delete_message(chat_id, msg_to_edit.message_id) # Try deleting even if error
            except Exception: pass

    # Immediately send "Sending..." message and indicate it's in progress.
    executor.submit(send_spam_and_report) # Run the actual spam logic in a separate thread
    
    try:
        bot.edit_message_text(
            f"<b>💥 Sending Spam to UID <code>{uid}</code>...</b>\n"
            f"This process runs in the background and may take a moment. "
            f"You will receive a confirmation update on this message once completed.",
            chat_id,
            msg_to_edit.message_id,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error updating initial spam message to 'sending...': {e}")


@bot.message_handler(commands=['gt'])
def handle_freefire_info(message):
    if not check_bot_active(message) or not check_command_status(message):
        return

    db.all_users.add(message.from_user.id)
    db.save_data()

    args = message.text.split()
    if len(args) != 2: # Only expect /gt <uid>
        bot.reply_to(message, "⚠️ <b>Usage:</b> <code>/gt &lt;uid&gt;</code>\n\nExample: <code>/gt 123456789</code>", parse_mode='HTML')
        return

    uid = args[1]
    if not validate_uid(uid): # UID validation remains
        bot.reply_to(message, "❌ <b>INVALID UID FORMAT!</b>\n\nUID must be 8-12 digits and contain only numbers.", parse_mode='HTML')
        return

    msg = bot.reply_to(message, f"🔍 <b>Fetching player info\n🆔 <code>{uid}</code>...</b>", parse_mode='HTML')

    profile_data = get_profile_info(uid) # Call API without region
    if not profile_data:
        bot.edit_message_text(f"❌ <b>PLAYER NOT FOUND OR API ERROR!</b>\nCould not retrieve info for UID <code>{uid}</code>. Please double-check the UID.", message.chat.id, msg.message_id, parse_mode='HTML')
        return

    def safe_str(s):
        # Handles potential emoji or special characters that cause encoding issues
        if isinstance(s, (int, float)):
            return str(s)
        return str(s).replace('<', '&lt;').replace('>', '&gt;').encode('utf-16', 'surrogatepass').decode('utf-16')

    basic = profile_data.get("basicInfo", {})
    social = profile_data.get("socialInfo", {})
    pet = profile_data.get("petInfo", {})
    credit = profile_data.get("creditScoreInfo", {})
    profile_details = profile_data.get("profileInfo", {})
    clan = profile_data.get("clanBasicInfo", {})
    captain = profile_data.get("captainBasicInfo", {})
    diamond_cost = profile_data.get("diamondCostRes", {})

    nickname = safe_str(basic.get('nickname', 'N/A'))
    signature = safe_str(social.get('signature', 'N/A'))
    captain_nick = safe_str(captain.get('nickname', 'N/A'))

    msg_text = f"""✨ <b>GHOST X PLAYER PROFILE</b> ✨
---
┌🧑‍💻 <b>BASIC INFO</b>
├─ <b>Name:</b> {nickname}
├─ <b>UID:</b> <code>{basic.get('accountId', uid)}</code>
├─ <b>Level:</b> {basic.get('level', 'N/A')} (EXP: {basic.get('exp', 0):,})
├─ <b>Region:</b> {basic.get('region', 'N/A')}
├─ <b>Likes:</b> {basic.get('liked', 0):,}
├─ <b>Honor Score:</b> {credit.get('creditScore', 'N/A')}
└─ <b>Title ID:</b> <code>{basic.get('title', 'N/A')}</code>

---
┌🛡️ <b>RANK & STATS</b>
├─ <b>BR Rank Score:</b> {basic.get('rankingPoints', 'N/A')}
├─ <b>CS Rank Score:</b> {basic.get('csRankingPoints', 'N/A')}
├─ <b>Booyah Pass:</b> {'✅ Yes' if basic.get('badgeCnt', 0) > 0 else '❌ No'} (Badges: {basic.get('badgeCnt', 'N/A')})
└─ <b>Total Diamonds Spent:</b> {diamond_cost.get('diamondCost', 0):,} 💎

---
┌✍️ <b>SOCIAL INFO</b>
├─ <b>Signature:</b> <i>{signature}</i>
├─ <b>Gender:</b> {social.get('gender', 'N/A').replace('Gender_', '').title()}
└─ <b>Language:</b> {social.get('language', 'N/A').replace('Language_', '').title()}

---
┌👕 <b>APPEARANCE & SKILLS</b>
├─ <b>Avatar ID:</b> <code>{profile_details.get('avatarId', 'N/A')}</code>
├─ <b>Outfits (IDs):</b> <code>{", ".join(map(str, profile_details.get('clothes', []))) or "N/A"}</code>
└─ <b>Skills (IDs):</b> <code>{", ".join(map(str, profile_details.get('equipedSkills', []))) or "N/A"}</code>

---
┌🐾 <b>PET DETAILS</b>
├─ <b>Equipped:</b> {'✅ Yes' if pet.get('isSelected') else '❌ No'}
├─ <b>Pet ID:</b> <code>{pet.get('id', 'N/A')}</code>
└─ <b>Level:</b> {pet.get('level', 'N/A')}

---
┌🤝 <b>GUILD DETAILS</b>
├─ <b>Name:</b> {clan.get('clanName', 'N/A')}
├─ <b>ID:</b> <code>{clan.get('clanId', 'N/A')}</code>
├─ <b>Level:</b> {clan.get('clanLevel', 'N/A')} ({clan.get('memberNum', 'N/A')}/{clan.get('capacity', 'N/A')})
└─ <b>Captain UID:</b> <code>{clan.get('captainId', 'N/A')}</code>

---
┌🧑‍✈️ <b>CAPTAIN INFO</b>
├─ <b>Name:</b> {captain_nick}
├─ <b>UID:</b> <code>{captain.get('accountId', 'N/A')}</code>
├─ <b>Level:</b> {captain.get('level', 'N/A')} (EXP: {captain.get('exp', 0):,})
├─ <b>Region:</b> {captain.get('region', 'N/A')}
├─ <b>Likes:</b> {captain.get('liked', 0):,}
├─ <b>Badge Count:</b> {captain.get('badgeCnt', 0)}
├─ <b>BR Rank:</b> {captain.get('rankingPoints', 'N/A')}
├─ <b>CS Rank:</b> {captain.get('csRankingPoints', 'N/A')}
├─ <b>Version:</b> {captain.get('releaseVersion', 'N/A')}
└─ <b>Created:</b> {format_timestamp(captain.get('createAt'))}

---
┌🕒 <b>ACCOUNT TIMELINE</b>
├─ <b>Created:</b> {format_timestamp(basic.get('createAt'))}
├─ <b>Last Login:</b> {format_timestamp(basic.get('lastLoginAt'))}
└─ <b>OB Version:</b> {basic.get('releaseVersion', 'N/A')}
---
"""

    bot.edit_message_text(msg_text, message.chat.id, msg.message_id, parse_mode='HTML', disable_web_page_preview=True)
    # The 'region' parameter for banner and outfit APIs needs to be derived or omitted if not supported
    # Assuming the FF profile API might return the region, or using a default if necessary.
    # For now, I'll pass basic.get('region', 'N/A') as a fallback.
    executor.submit(send_banner_and_outfit, message.chat.id, message.message_id, uid, basic.get('region', 'N/A').lower())


def send_banner_and_outfit(chat_id, msg_id, uid, region):
    try:
        # 1. Send information message (initial processing)
        info_msg = bot.send_message(
            chat_id,
            f"⚡ <b>PROCESSING PLAYER DATA FOR UID:</b> <code>{uid}</code>",
            reply_to_message_id=msg_id,
            parse_mode='HTML'
        )

        # 2. Send Banner Image (as sticker) - FAST
        banner_url = f"https://after-banner-636.vercel.app/banner-image?uid={uid}"
        banner_response = requests.get(banner_url, timeout=5)
        if banner_response.status_code == 200:
            bot.send_sticker(
                chat_id, 
                banner_response.content, 
                reply_to_message_id=msg_id
            )
        else:
            logger.error(f"Banner API error for UID {uid}")

        # 3. Send Outfit Image (as photo with buttons) - FAST
        outfit_url = f"https://outfit-image-v2-ghost-x.vercel.app/outfit-image?uid={uid}"
        outfit_response = requests.get(outfit_url, timeout=5)
        
        if outfit_response.status_code == 200:
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton(Config.BUTTON1_TEXT, url=Config.BUTTON1_URL),
                InlineKeyboardButton(Config.BUTTON2_TEXT, url=Config.BUTTON2_URL)
            )
            
            bot.send_photo(
                chat_id,
                photo=outfit_response.content,
                caption=f"🎮 <b>OUTFIT FOR UID:</b> <code>{uid}</code>",
                parse_mode='HTML',
                reply_to_message_id=msg_id,
                reply_markup=kb
            )
        else:
            logger.error(f"Outfit API error for UID {uid}")

        # 4. Delete the initial processing message
        try:
            bot.delete_message(chat_id, info_msg.message_id)
        except Exception as e:
            logger.error(f"Error deleting info message: {e}")

    except Exception as e:
        logger.error(f"Error in send_banner_and_outfit: {e}")
        bot.send_message(
            chat_id,
            f"❌ <b>ERROR PROCESSING IMAGES FOR UID:</b> <code>{uid}</code>",
            reply_to_message_id=msg_id,
            parse_mode='HTML'
        )


@bot.message_handler(commands=['bancheck'])
def handle_bancheck(message):
    if not check_bot_active(message) or not check_command_status(message): return
    db.all_users.add(message.from_user.id); db.save_data()

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "<b>❗ USAGE:</b> <code>/bancheck &lt;uid&gt;</code>", parse_mode='HTML')
        return
    
    uid = args[1]
    if not (uid.isdigit() and 8 <= len(uid) <= 11):
        bot.reply_to(message, "<b>❌ INVALID UID!</b> Must be 8-11 digits.", parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, f"🔍 <b>CHECKING BAN STATUS for <code>{uid}</code>...</b>", parse_mode='HTML')
    ban_status_result = call_bancheck_api(uid)
    
    # Add footer buttons if enabled
    footer_buttons = create_footer_buttons()
    if footer_buttons:
        bot.edit_message_text(ban_status_result, message.chat.id, msg.message_id, parse_mode='HTML', reply_markup=footer_buttons)
    else:
        bot.edit_message_text(ban_status_result, message.chat.id, msg.message_id, parse_mode='HTML')

def handle_verification(message):
    try:
        token = message.text.split()[1][7:] # Extract token from /start verify_<token>
        user_id = message.from_user.id
        
        # 1. Validate Token and Ownership
        if token not in db.token_to_user or db.token_to_user[token] != user_id:
            bot.reply_to(message,
                "<b>⚠️ INVALID OR EXPIRED VERIFICATION LINK!</b>\n\n"
                "This link is either invalid, has expired, or doesn't belong to you. "
                "Please go back to the group and try again by initiating a command like /like, /visit, or /spam to get a fresh link.",
                parse_mode='HTML'
            )
            return

        # 2. Check if Token Already Used
        if token in db.used_tokens:
            bot.reply_to(message,
                "<b>⚠️ LINK ALREADY USED!</b>\n\n"
                "This verification link has already been used. Your previous request should have been processed in the group.\n"
                "If you need to use another service, please request a new verification link.",
                parse_mode='HTML'
            )
            return
        
        # 3. Check Verification Cooldown
        last_verification_time = db.user_last_verification.get(user_id, 0)
        if time.time() - last_verification_time < Config.VERIFICATION_COOLDOWN:
            remaining_time = int(Config.VERIFICATION_COOLDOWN - (time.time() - last_verification_time))
            bot.reply_to(message,
                f"⏳ <b>VERIFICATION COOLDOWN ACTIVE!</b> ⏳\n\n"
                f"You can complete verification again in <b>{remaining_time} seconds</b>. Please wait before attempting another verification.",
                parse_mode='HTML'
            )
            return

        # 4. Mark Token Used, Grant Credit/Coin, Update Cooldown
        db.used_tokens.add(token)
        db.verification_credits[user_id] = db.verification_credits.get(user_id, 0) + 1
        db.user_coins[user_id] = db.user_coins.get(user_id, 0) + 1 # Grant a coin for verification
        db.user_last_verification[user_id] = time.time()
        db.all_users.add(user_id) # Ensure user is in all_users
        db.save_data()
        
        # 5. Process Pending Request (AUTOMATED EXECUTION)
        if user_id in db.pending_requests:
            req_data = db.pending_requests[user_id]
            command_type = req_data['type']
            region = req_data['region']
            uid = req_data['uid']
            original_chat_id = req_data['chat_id']
            original_message_id = req_data['message_id']
            pending_message_id = req_data.get('pending_message_id') # Get the ID of the verification message sent previously

            # Delete the verification message from the group
            if pending_message_id:
                try:
                    bot.delete_message(original_chat_id, pending_message_id)
                except Exception as e:
                    logger.error(f"Error deleting pending verification message {pending_message_id}: {e}")

            # Send a confirmation message in private chat first
            bot.reply_to(message,
                "✨ <b>✅ VERIFICATION SUCCESSFUL!</b> ✨\n\n"
                f"💎 <b>Credit Received:</b> 1 VIP credit\n"
                f"🪙 <b>Coin Bonus:</b> 1 Ghost Coin\n\n"
                f"📊 <b>Current Balance:</b>\n"
                f"╰┈➤ <b>VIP Credits:</b> {db.verification_credits.get(user_id, 0)}\n"
                f"╰┈➤ <b>Ghost Coins:</b> {db.user_coins.get(user_id, 0)}\n\n"
                f"🚀 Your requested service (`/{command_type}`) for UID <code>{uid}</code> in region {Config.VALID_REGIONS.get(region, region).upper()} is now being processed automatically in the group.\n\n"
                f"Go back to the group \n👉 ({Config.GROUP_LINK})\nto see the result!",
                parse_mode='HTML',
                disable_web_page_preview=True
            )

            # Now, trigger the actual command processing in the original group/chat
            if command_type == 'like':
                process_like(original_chat_id, original_message_id, user_id, region, uid, original_credits=db.verification_credits.get(user_id, 0), pending_message_id=None) # Pass None because it's already deleted
            elif command_type == 'visit':
                process_visit(original_chat_id, original_message_id, user_id, region, uid, original_credits=db.verification_credits.get(user_id, 0), pending_message_id=None)
            elif command_type == 'spam':
                process_spam(original_chat_id, original_message_id, user_id, region, uid, original_credits=db.verification_credits.get(user_id, 0), pending_message_id=None)
            
            # Clean up pending request
            if user_id in db.pending_requests: # Check again, just in case it was modified by the processing functions
                del db.pending_requests[user_id]
                db.save_data() # Save after deleting pending request
            return
        
        # If no pending request (user just used /start verify_ for fun)
        bot.reply_to(message,
            "✨ <b>✅ VERIFICATION SUCCESSFUL!</b> ✨\n\n"
            f"💎 <b>Credit Received:</b> 1 VIP credit\n"
            f"🪙 <b>Coin Bonus:</b> 1 Ghost Coin\n\n"
            f"📊 <b>Current Balance:</b>\n"
            f"╰┈➤ <b>VIP Credits:</b> {db.verification_credits.get(user_id, 0)}\n"
            f"╰┈➤ <b>Ghost Coins:</b> {db.user_coins.get(user_id, 0)}\n\n"
            f"Use commands like <code>/like &lt;region&gt; &lt;uid&gt;</code> in our group ({Config.GROUP_LINK}) to utilize your credits!\n\n"
            f"🌟 Check your balance anytime with <code>/coins</code>.",
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Verification process error for user {message.from_user.id}: {e}")
        bot.reply_to(message,
            "⚠️ <b>VERIFICATION ERROR!</b>\n\n"
            "An unexpected error occurred during verification. Please try again or contact support."
            "If you tried to verify multiple times too quickly, please wait a moment.",
            parse_mode='HTML'
        )
        
def schedule_daily_reset():
    while True:
        try:
            db.reset_daily_counts()
            now = datetime.now()
            next_reset = (now + timedelta(days=1)).replace(hour=Config.RESET_TIME, minute=0, second=0, microsecond=0)
            time_to_sleep = (next_reset - now).total_seconds()
            logger.info(f"Daily counts reset. Next reset in {time_to_sleep / 3600:.2f} hours.")
            time.sleep(time_to_sleep)
        except Exception as e:
            logger.error(f"Reset scheduler error: {e}")
            time.sleep(600)

if __name__ == "__main__":
    print("╭━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╮\n│🤖 FAYSAL Likes Bot is running...│\n╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n")
    # Start reset scheduler in a background thread
    threading.Thread(target=schedule_daily_reset, daemon=True).start()
    
    # Ensure video files exist
    for video in [Config.SUCCESS_VIDEO, Config.ALREADY_LIKED_VIDEO, Config.ERROR_VIDEO, Config.VERIFICATION_VIDEO]:
        if not os.path.exists(video):
            logger.warning(f"Missing video file: {video}. Video replies will fail.")
            
    bot.infinity_polling(timeout=20, long_polling_timeout=30)
