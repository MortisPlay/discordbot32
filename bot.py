import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import View, Button, Modal, TextInput, Select
from datetime import datetime, timedelta, timezone
import json
import os
import asyncio
import re
import random
import aiohttp
import io
from collections import defaultdict, deque
import uuid
import traceback
import sys

# ───────────────────────────────────────────────
#   НАСТРОЙКИ (БЕЗ ТОКЕНА!)
# ───────────────────────────────────────────────
# Токен берется из переменной окружения DISCORD_TOKEN
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    print("❌ ОШИБКА: Не найден токен в переменных окружения!")
    print("📌 Установите переменную DISCORD_TOKEN")
    print("💡 Например: export DISCORD_TOKEN='ваш_токен'")
    sys.exit(1)

OWNER_ID = 765476979792150549
FULL_ACCESS_GUILD_ID = 1474623510268739790

MOD_LOG_CHANNEL_ID = 1475291899672657940
WELCOME_CHANNEL_ID = 1475048502370500639
GOODBYE_CHANNEL_ID = 1475048502370500639
TICKET_ARCHIVE_CHANNEL_ID = 1475338423513649347
PREFIX = "!"
WARNINGS_FILE = "warnings.json"
ECONOMY_FILE = "economy.json"
CASES_FILE = "cases.json"

# ───────────────────────────────────────────────
#   НОВЫЕ НАСТРОЙКИ ДЛЯ TWITCH
# ───────────────────────────────────────────────
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')  # ID приложения Twitch
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')  # Секрет приложения Twitch
TWITCH_ACCESS_TOKEN = None  # Будет получен автоматически
TWITCH_TOKEN_EXPIRY = 0  # Время истечения токена

# Канал для уведомлений о стримах
TWITCH_ANNOUNCE_CHANNEL_ID = 1475048502370500639  # Можно изменить на нужный канал

# Файл для хранения подписок на стримеров
TWITCH_SUBS_FILE = "twitch_subs.json"

# Настройки проверки
TWITCH_CHECK_INTERVAL = 60  # Проверка каждые 60 секунд
TWITCH_STREAMER_ROLE_ID = None  # ID роли стримера (можно указать позже)

TICKET_CATEGORY_ID = 1475334525344157807
SUPPORT_ROLE_ID = 1475331888163066029

SPAM_THRESHOLD = 5
SPAM_TIME = 8
ECONOMY_AUTOSAVE_INTERVAL = 300

DAILY_COOLDOWN = 86400
MESSAGE_COOLDOWN = 60
TAX_THRESHOLD = 10000
TAX_RATE = 0.01

# НАСТРОЙКИ ДЛЯ АВТОМОДЕРАЦИИ
WARN_AUTO_MUTE_THRESHOLD = 3
WARN_AUTO_LONG_MUTE_THRESHOLD = 6
WARN_AUTO_KICK_THRESHOLD = 10
WARN_EXPIRY_DAYS = 30

RAID_JOIN_THRESHOLD = 5
RAID_TIME_WINDOW = 300
NEW_ACCOUNT_DAYS = 7

VIP_ROLE_NAMES = ["VIP", "Premium", "Vip", "vip"]
VIP_SPAM_MULTIPLIER = 2
VIP_MENTION_MULTIPLIER = 3

INACTIVE_TICKET_HOURS = 24
INVESTMENT_MIN_AMOUNT = 1000
INVESTMENT_MAX_DAYS = 30
INVESTMENT_BASE_RATE = 0.05
UNAUTHORIZED_CMD_LIMIT = 3
UNAUTHORIZED_MUTE_MINUTES = 1

FAQ_FILE = "faq.json"
FAQ_CATEGORIES = {
    "общее": "📋 Общие вопросы",
    "правила": "📜 Правила",
    "экономика": "💰 Экономика",
    "модерация": "🛡️ Модерация",
    "техника": "🔧 Технические вопросы"
}

ECONOMY_EMOJIS = {
    "balance": "💰",
    "vault": "🏦",
    "daily": "🎁",
    "tax": "📊",
    "rich": "👑",
    "poor": "😢",
    "transfer": "💸",
    "coin": "🪙",
    "bank": "🏛️",
    "chart": "📈",
    "time": "⏰",
    "warning": "⚠️",
    "success": "✅",
    "error": "❌",
    "gift": "🎀",
    "crown": "👑",
    "diamond": "💎",
    "gold": "🪙",
    "silver": "🥈",
    "bronze": "🥉",
    "investment": "📈",
    "profit": "💹",
    "risk": "⚠️",
    "calendar": "📅",
    "twitch": "📺"  # Новый эмодзи для Twitch
}

RARITIES = [
    ("Обычная",     70,  15,  35,  0xA8A8A8, "🪙"),
    ("Редкая",      20,  50,  70,  0x3498DB, "💎"),
    ("Эпическая",    9, 200, 350,  0x9B59B6, "🌟"),
    ("Легендарная",  1, 500,1000,  0xF1C40F, "🔥")
]

BAD_WORDS = [
    "пидор", "пидорас", "пидрила", "пидр", "гей", "хуесос", "ебанат", "дебил", "идиот",
    "тупой", "чмо", "чмошник", "сука", "блядь", "еблан", "мудак", "тварь", "урод"
]

INSULT_PATTERNS = [
    r"\b(ты|тебе|тобой)\s*(пидор|дебил|идиот|тупой|чмо|хуесос|ебанат)\b",
    r"\b(иди|пошёл|пиздец)\s*(нахуй|в пизду|в жопу)\b",
    r"\b(заткнись|заткнулся|молчи)\s*(сука|блядь|ебанат)\b"
]

COLORS = {
    "welcome": 0x57F287,
    "goodbye": 0xF04747,
    "audit": 0x5865F2,
    "mod": 0xFAA61A,
    "economy": 0xFFD700,
    "ticket": 0x9B59B6,
    "faq": 0x3498DB,
    "twitch": 0x9146FF  # Фиолетовый цвет Twitch
}

# ───────────────────────────────────────────────
#   ГЛОБАЛЬНЫЕ ДАННЫЕ
# ───────────────────────────────────────────────
economy_data = {}
warnings_data = {}
cases_data = {}
spam_cache = {}
raid_cache = defaultdict(list)
temp_roles = {}
investments_data = {}
unauthorized_attempts = defaultdict(list)
faq_data = {}

# НОВЫЕ ДАННЫЕ ДЛЯ TWITCH
twitch_subs = {}  # {streamer_name: {"channel_id": discord_channel_id, "message": "...", "last_stream": timestamp, "live": False}}
twitch_live_cache = {}  # Кэш для отслеживания текущих стримов

def load_economy():
    global economy_data
    if os.path.exists(ECONOMY_FILE):
        try:
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                economy_data = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки economy.json: {e}")
            economy_data = {"server_vault": 0}
    else:
        economy_data = {"server_vault": 0}
    
    for user_id in economy_data:
        if user_id != "server_vault" and "investments" not in economy_data[user_id]:
            economy_data[user_id]["investments"] = []

def save_economy():
    with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
        json.dump(economy_data, f, ensure_ascii=False, indent=2)

def load_faq():
    global faq_data
    if os.path.exists(FAQ_FILE):
        try:
            with open(FAQ_FILE, "r", encoding="utf-8") as f:
                faq_data = json.load(f)
        except:
            faq_data = {}
    else:
        faq_data = {}

def save_faq():
    with open(FAQ_FILE, "w", encoding="utf-8") as f:
        json.dump(faq_data, f, ensure_ascii=False, indent=2)

# НОВАЯ ФУНКЦИЯ ДЛЯ ЗАГРУЗКИ ПОДПИСОК TWITCH
def load_twitch_subs():
    global twitch_subs
    if os.path.exists(TWITCH_SUBS_FILE):
        try:
            with open(TWITCH_SUBS_FILE, "r", encoding="utf-8") as f:
                twitch_subs = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки twitch_subs.json: {e}")
            twitch_subs = {}
    else:
        twitch_subs = {}

def save_twitch_subs():
    with open(TWITCH_SUBS_FILE, "w", encoding="utf-8") as f:
        json.dump(twitch_subs, f, ensure_ascii=False, indent=2)

load_economy()
load_faq()
load_twitch_subs()

if "server_vault" not in economy_data:
    economy_data["server_vault"] = 0
    save_economy()

def load_warnings():
    global warnings_data
    if os.path.exists(WARNINGS_FILE):
        try:
            with open(WARNINGS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    warnings_data = {}
                else:
                    warnings_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка чтения warnings.json: {e}")
            warnings_data = {}
    else:
        warnings_data = {}

def save_warnings():
    with open(WARNINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(warnings_data, f, ensure_ascii=False, indent=2)

def load_cases():
    global cases_data
    if os.path.exists(CASES_FILE):
        try:
            with open(CASES_FILE, "r", encoding="utf-8") as f:
                cases_data = json.load(f)
        except:
            cases_data = {}
    else:
        cases_data = {}

def save_cases():
    with open(CASES_FILE, "w", encoding="utf-8") as f:
        json.dump(cases_data, f, ensure_ascii=False, indent=2)

load_warnings()
load_cases()

# ───────────────────────────────────────────────
#   ФУНКЦИИ ДЛЯ TWITCH INTEGRATION
# ───────────────────────────────────────────────

async def get_twitch_token():
    """Получение или обновление токена доступа к Twitch API"""
    global TWITCH_ACCESS_TOKEN, TWITCH_TOKEN_EXPIRY
    
    now = datetime.now().timestamp()
    
    # Если токен ещё действителен, возвращаем его
    if TWITCH_ACCESS_TOKEN and now < TWITCH_TOKEN_EXPIRY - 60:
        return TWITCH_ACCESS_TOKEN
    
    if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
        print("⚠️ Twitch клиент не настроен!")
        return None
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://id.twitch.tv/oauth2/token',
                params={
                    'client_id': TWITCH_CLIENT_ID,
                    'client_secret': TWITCH_CLIENT_SECRET,
                    'grant_type': 'client_credentials'
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    TWITCH_ACCESS_TOKEN = data['access_token']
                    TWITCH_TOKEN_EXPIRY = now + data['expires_in']
                    return TWITCH_ACCESS_TOKEN
                else:
                    print(f"❌ Ошибка получения токена Twitch: {resp.status}")
                    return None
    except Exception as e:
        print(f"❌ Ошибка при получении токена Twitch: {e}")
        return None

async def check_twitch_stream(streamer_name: str):
    """Проверяет, идёт ли стрим у указанного стримера с улучшенной обработкой ошибок"""
    token = await get_twitch_token()
    if not token:
        print("❌ Не удалось получить токен Twitch")
        return None
    
    try:
        headers = {
            'Client-ID': TWITCH_CLIENT_ID,
            'Authorization': f'Bearer {token}'
        }
        
        async with aiohttp.ClientSession() as session:
            # Сначала получаем информацию о пользователе
            user_url = 'https://api.twitch.tv/helix/users'
            async with session.get(
                user_url,
                headers=headers,
                params={'login': streamer_name.lower().strip()}
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"❌ Ошибка Twitch API (users): {resp.status} - {error_text}")
                    return None
                
                user_data = await resp.json()
                
                # Проверяем, найден ли пользователь
                if not user_data.get('data'):
                    print(f"❌ Стример '{streamer_name}' не найден на Twitch")
                    return {'error': 'not_found', 'streamer': streamer_name}
                
                user_info = user_data['data'][0]
                user_id = user_info['id']
                display_name = user_info['display_name']
                profile_image = user_info.get('profile_image_url')
                offline_image = user_info.get('offline_image_url')
            
            # Теперь проверяем, идёт ли стрим
            stream_url = 'https://api.twitch.tv/helix/streams'
            async with session.get(
                stream_url,
                headers=headers,
                params={'user_id': user_id}
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"❌ Ошибка Twitch API (streams): {resp.status} - {error_text}")
                    return {
                        'is_live': False,
                        'display_name': display_name,
                        'profile_image': profile_image,
                        'offline_image': offline_image,
                        'url': f'https://twitch.tv/{streamer_name}',
                        'error': 'stream_check_failed'
                    }
                
                stream_data = await resp.json()
                
                if stream_data.get('data'):
                    stream = stream_data['data'][0]
                    
                    # Формируем URL превью (заменяем размеры)
                    thumbnail = stream['thumbnail_url'].replace('{width}', '1280').replace('{height}', '720')
                    
                    # Добавляем timestamp чтобы избежать кэширования
                    thumbnail = f"{thumbnail}?t={int(datetime.now().timestamp())}"
                    
                    return {
                        'is_live': True,
                        'title': stream['title'],
                        'game': stream['game_name'],
                        'viewers': stream['viewer_count'],
                        'thumbnail': thumbnail,
                        'started_at': stream['started_at'],
                        'display_name': display_name,
                        'profile_image': profile_image,
                        'url': f'https://twitch.tv/{streamer_name}'
                    }
                else:
                    return {
                        'is_live': False,
                        'display_name': display_name,
                        'profile_image': profile_image,
                        'offline_image': offline_image,
                        'url': f'https://twitch.tv/{streamer_name}'
                    }
                    
    except aiohttp.ClientError as e:
        print(f"❌ Сетевая ошибка при проверке Twitch стрима {streamer_name}: {e}")
        return {'error': 'network_error', 'streamer': streamer_name}
    except Exception as e:
        print(f"❌ Неизвестная ошибка при проверке Twitch стрима {streamer_name}: {e}")
        traceback.print_exc()
        return {'error': 'unknown_error', 'streamer': streamer_name}

@tasks.loop(seconds=TWITCH_CHECK_INTERVAL)
async def check_twitch_streams_task():
    """Фоновая задача для проверки стримов с улучшенной обработкой"""
    if not twitch_subs:
        return
    
    print(f"🔍 Проверка стримов: {len(twitch_subs)} стримеров")
    
    for streamer_name, data in list(twitch_subs.items()):
        try:
            # Пропускаем если это не наш гильд (для безопасности)
            guild = bot.get_guild(data.get('guild_id'))
            if not guild:
                print(f"⚠️ Гильдия не найдена для стримера {streamer_name}, удаляем")
                del twitch_subs[streamer_name]
                save_twitch_subs()
                continue
            
            channel = guild.get_channel(data.get('channel_id'))
            if not channel:
                print(f"⚠️ Канал не найден для стримера {streamer_name} на гильдии {guild.name}")
                # Не удаляем, возможно канал временно недоступен
                continue
            
            result = await check_twitch_stream(streamer_name)
            
            # Обрабатываем ошибки
            if not result:
                print(f"⚠️ Нет ответа от API для {streamer_name}")
                continue
                
            if result.get('error'):
                if result['error'] == 'not_found':
                    print(f"⚠️ Стример {streamer_name} больше не существует на Twitch")
                    # Можно уведомить модераторов
                    mod_log = bot.get_channel(MOD_LOG_CHANNEL_ID)
                    if mod_log:
                        embed = discord.Embed(
                            title="⚠️ Стример не найден",
                            description=f"Стример **{streamer_name}** больше не существует на Twitch и будет удалён из списка.",
                            color=0xFAA61A
                        )
                        await mod_log.send(embed=embed)
                    del twitch_subs[streamer_name]
                    save_twitch_subs()
                continue
            
            was_live = data.get('live', False)
            is_live = result['is_live']
            
            # Обновляем display_name если изменился
            if result.get('display_name') and result['display_name'] != data.get('display_name'):
                data['display_name'] = result['display_name']
            
            # Если стрим только начался
            if is_live and not was_live:
                print(f"🔴 {result['display_name']} начал стрим!")
                
                # Отправляем уведомление
                embed = discord.Embed(
                    title=f"📺 {result['display_name']} начал стрим!",
                    url=result['url'],
                    description=f"**{result['title']}**",
                    color=COLORS["twitch"],
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(name="🎮 Игра", value=result['game'] or "Неизвестно", inline=True)
                embed.add_field(name="👁️ Зрители", value=format_number(result['viewers']), inline=True)
                
                if result.get('thumbnail'):
                    embed.set_image(url=result['thumbnail'])
                
                if result.get('profile_image'):
                    embed.set_thumbnail(url=result['profile_image'])
                
                embed.set_footer(text="Нажми на заголовок, чтобы перейти к стриму!")
                
                # Пингуем роль стримера, если она указана
                content = None
                if TWITCH_STREAMER_ROLE_ID:
                    role = guild.get_role(TWITCH_STREAMER_ROLE_ID)
                    if role:
                        content = role.mention
                
                # Отправляем сообщение
                message = await channel.send(content=content, embed=embed)
                
                # Обновляем данные
                data['live'] = True
                data['last_stream'] = datetime.now().timestamp()
                data['last_message_id'] = message.id
                data['last_check'] = datetime.now().timestamp()
                
                # Логируем в мод-канал
                await send_mod_log(
                    title="🔴 Стрим начался",
                    description=f"**Стример:** [{result['display_name']}]({result['url']})\n"
                               f"**Игра:** {result['game']}\n"
                               f"**Зрители:** {format_number(result['viewers'])}",
                    color=COLORS["twitch"]
                )
                
            # Если стрим закончился
            elif not is_live and was_live:
                print(f"⚫ {result['display_name']} закончил стрим")
                data['live'] = False
                data['last_check'] = datetime.now().timestamp()
                
                # Обновляем предыдущее сообщение
                if 'last_message_id' in data:
                    try:
                        last_msg = await channel.fetch_message(data['last_message_id'])
                        if last_msg and last_msg.embeds:
                            new_embed = last_msg.embeds[0]
                            new_embed.color = 0x808080
                            new_embed.set_footer(text="🔴 Стрим завершён")
                            await last_msg.edit(embed=new_embed)
                    except discord.NotFound:
                        pass
                    except Exception as e:
                        print(f"⚠️ Не удалось обновить сообщение: {e}")
            
            else:
                # Просто обновляем время проверки
                data['last_check'] = datetime.now().timestamp()
            
            # Сохраняем изменения
            save_twitch_subs()
            
        except Exception as e:
            print(f"❌ Ошибка при проверке стримера {streamer_name}: {e}")
            traceback.print_exc()

# ───────────────────────────────────────────────
#   ФУНКЦИИ ДЛЯ ПРОВЕРКИ ПРАВ
# ───────────────────────────────────────────────

def is_moderator(member: discord.Member) -> bool:
    """Проверяет, является ли пользователь модератором"""
    return (member.guild_permissions.manage_messages or 
            member.guild_permissions.administrator or 
            member.id == OWNER_ID)

def is_protected_from_automod(member: discord.Member) -> bool:
    """Проверяет, защищен ли пользователь от автомодерации"""
    return (member.guild_permissions.administrator or 
            member.guild_permissions.manage_messages or
            member.guild_permissions.manage_guild or
            member.id == OWNER_ID or
            member.top_role.permissions.administrator)

# ───────────────────────────────────────────────
#   ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ───────────────────────────────────────────────

async def check_unauthorized_commands(user: discord.Member):
    """Проверяет количество попыток использовать команды без прав"""
    if is_moderator(user):
        return False
        
    user_id = str(user.id)
    now = datetime.now(timezone.utc).timestamp()
    
    unauthorized_attempts[user_id] = [t for t in unauthorized_attempts[user_id] if now - t < 3600]
    unauthorized_attempts[user_id].append(now)
    
    if len(unauthorized_attempts[user_id]) >= UNAUTHORIZED_CMD_LIMIT:
        try:
            await user.timeout(timedelta(minutes=UNAUTHORIZED_MUTE_MINUTES), 
                              reason="Превышение лимита попыток использования команд без прав")
            await send_punishment_log(
                member=user,
                punishment_type="🔇 Мут (авто)",
                duration=f"{UNAUTHORIZED_MUTE_MINUTES} мин",
                reason="Превышение лимита попыток использования модераторских команд",
                moderator=bot.user
            )
            unauthorized_attempts[user_id] = []
            return True
        except:
            pass
    return False

def format_number(num: int) -> str:
    return f"{num:,}".replace(",", " ")

def get_rank_emoji(balance: int) -> str:
    if balance >= 100000:
        return "👑"
    elif balance >= 50000:
        return "💎"
    elif balance >= 10000:
        return "💰"
    elif balance >= 5000:
        return "💵"
    elif balance >= 1000:
        return "🪙"
    elif balance >= 100:
        return "🥉"
    else:
        return "🥚"

def create_progress_bar(current: int, max_value: int, length: int = 10) -> str:
    if max_value <= 0:
        return "█" * length
    progress = min(current / max_value, 1.0)
    filled = int(progress * length)
    return "█" * filled + "░" * (length - filled)

def generate_case_id() -> str:
    return str(uuid.uuid4())[:8]

async def create_case(member: discord.Member, moderator: discord.User, action: str, reason: str, duration: str = None):
    case_id = generate_case_id()
    cases_data[case_id] = {
        "id": case_id,
        "user_id": str(member.id),
        "user_name": str(member),
        "moderator_id": str(moderator.id),
        "moderator_name": str(moderator),
        "action": action,
        "reason": reason,
        "duration": duration,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    save_cases()
    return case_id

async def get_case(case_id: str) -> dict:
    return cases_data.get(case_id)

def is_vip(member: discord.Member) -> bool:
    if not member:
        return False
    return any(role.name in VIP_ROLE_NAMES for role in member.roles)

def clean_old_warnings(user_id: str):
    if user_id not in warnings_data:
        return
    
    now = datetime.now(timezone.utc)
    fresh_warnings = []
    
    for warn in warnings_data[user_id]:
        try:
            warn_time = datetime.strptime(warn["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            if (now - warn_time).days < WARN_EXPIRY_DAYS:
                fresh_warnings.append(warn)
        except:
            continue
    
    warnings_data[user_id] = fresh_warnings
    if not fresh_warnings:
        del warnings_data[user_id]
    save_warnings()

def get_warning_count(user_id: str) -> int:
    clean_old_warnings(user_id)
    return len(warnings_data.get(user_id, []))

async def check_auto_punishment(member: discord.Member, reason: str = "Автоматически"):
    """Проверяет количество варнов и применяет наказание (не трогает модераторов)"""
    if not member or is_protected_from_automod(member):
        return
    
    user_id = str(member.id)
    warn_count = get_warning_count(user_id)
    
    if warn_count >= WARN_AUTO_KICK_THRESHOLD:
        try:
            await member.kick(reason=f"Достигнут лимит варнов ({warn_count})")
            case_id = await create_case(member, bot.user, "Авто-кик", f"{warn_count} варнов")
            await send_punishment_log(
                member=member,
                punishment_type="👢 Кик (авто)",
                duration="Навсегда",
                reason=f"Автоматический кик: {warn_count} варнов",
                moderator=bot.user,
                case_id=case_id
            )
        except:
            pass
    
    elif warn_count >= WARN_AUTO_LONG_MUTE_THRESHOLD:
        try:
            await member.timeout(timedelta(hours=24), reason=f"Автоматический мут: {warn_count} варнов")
            case_id = await create_case(member, bot.user, "Авто-мут 24ч", f"{warn_count} варнов", "24 часа")
            await send_punishment_log(
                member=member,
                punishment_type="🔇 Мут 24ч (авто)",
                duration="24 часа",
                reason=f"Автоматический мут: {warn_count} варнов",
                moderator=bot.user,
                case_id=case_id
            )
        except:
            pass
    
    elif warn_count >= WARN_AUTO_MUTE_THRESHOLD:
        try:
            await member.timeout(timedelta(hours=1), reason=f"Автоматический мут: {warn_count} варнов")
            case_id = await create_case(member, bot.user, "Авто-мут 1ч", f"{warn_count} варнов", "1 час")
            await send_punishment_log(
                member=member,
                punishment_type="🔇 Мут 1ч (авто)",
                duration="1 час",
                reason=f"Автоматический мут: {warn_count} варнов",
                moderator=bot.user,
                case_id=case_id
            )
        except:
            pass

async def send_punishment_log(member: discord.Member, punishment_type: str, duration: str, reason: str, moderator: discord.User, case_id: str = None):
    if not MOD_LOG_CHANNEL_ID:
        return
    
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    
    embed = discord.Embed(
        title=f"🛠️ Наказание {f'[#{case_id}]' if case_id else ''}",
        color=COLORS["mod"],
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(name="👤 Кто наказан", value=f"{member.mention}\n{member} ({member.id})", inline=False)
    embed.add_field(name="⚡ Тип", value=punishment_type, inline=True)
    embed.add_field(name="⏰ Время действия", value=duration, inline=True)
    embed.add_field(name="📝 Причина", value=reason, inline=False)
    embed.add_field(name="👮 Модератор", value=moderator.mention, inline=False)
    
    if case_id:
        embed.add_field(name="🔖 ID кейса", value=f"`{case_id}`", inline=False)
    
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"ID: {member.id}")
    
    view = ModActionView(member)
    await log_ch.send(embed=embed, view=view)

async def send_mod_log(title: str, description: str = None, color: int = COLORS["audit"], fields: list = None):
    if not MOD_LOG_CHANNEL_ID:
        return
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return

    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    embed.set_footer(text=f"Время: {datetime.now().strftime('%H:%M:%S')}")
    await log_ch.send(embed=embed)

async def send_error_embed(ctx, error_msg: str):
    embed = discord.Embed(
        title="❌ Ошибка",
        description=error_msg,
        color=0xF04747,
        timestamp=datetime.now(timezone.utc)
    )
    await ctx.send(embed=embed, ephemeral=True)

def is_toxic(content: str) -> bool:
    if not content:
        return False
    content_lower = content.lower()

    for pattern in INSULT_PATTERNS:
        if re.search(pattern, content_lower):
            return True

    words = content_lower.split()
    for word in words:
        if word in BAD_WORDS:
            for i, w in enumerate(words):
                if w == word and i > 0 and words[i-1] in ["ты", "тебе", "тобой", "твой", "твоя", "твоё"]:
                    return True
    return False

def has_full_access(guild_id: int) -> bool:
    return guild_id == FULL_ACCESS_GUILD_ID

async def apply_wealth_tax(user_id: str) -> int:
    if user_id not in economy_data:
        return 0

    balance = economy_data[user_id].get("balance", 0)
    if balance <= TAX_THRESHOLD:
        return 0

    taxable = balance - TAX_THRESHOLD
    tax = int(taxable * TAX_RATE)

    last_msg = economy_data[user_id].get("last_message", 0)
    now = datetime.now(timezone.utc).timestamp()
    if now - last_msg < 86400:
        reduction = random.uniform(0.20, 0.50)
        tax = int(tax * (1 - reduction))

    if tax > 0:
        economy_data[user_id]["balance"] -= tax
        economy_data["server_vault"] = economy_data.get("server_vault", 0) + tax
        save_economy()
        return tax
    return 0

# ───────────────────────────────────────────────
#   КЛАССЫ ДЛЯ UI
# ───────────────────────────────────────────────

class ModActionView(View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=180)
        self.member = member

    @discord.ui.button(label="Предупредить", style=discord.ButtonStyle.secondary, emoji="⚠️")
    async def warn_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
        
        modal = WarnModal(self.member)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Замутить", style=discord.ButtonStyle.danger, emoji="🔇")
    async def mute_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
        
        modal = MuteModal(self.member)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Очистить", style=discord.ButtonStyle.success, emoji="🧹")
    async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
        
        modal = ClearModal(self.member)
        await interaction.response.send_modal(modal)

class WarnModal(Modal, title="Выдать предупреждение"):
    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    reason = TextInput(label="Причина", placeholder="Введите причину предупреждения...", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.send = lambda **kwargs: interaction.response.send_message(**kwargs)
        await warn(ctx, self.member, reason=self.reason.value)

class MuteModal(Modal, title="Замутить пользователя"):
    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    duration = TextInput(label="Длительность", placeholder="1h, 1d, 30m", max_length=10)
    reason = TextInput(label="Причина", placeholder="Введите причину мута...", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.send = lambda **kwargs: interaction.response.send_message(**kwargs)
        
        reason = self.reason.value or "Не указана"
        await mute(ctx, self.member, duration=self.duration.value, reason=reason)

class ClearModal(Modal, title="Очистить сообщения"):
    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    amount = TextInput(label="Количество", placeholder="От 1 до 100", max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount.value)
            if amount < 1 or amount > 100:
                return await interaction.response.send_message("❌ Количество должно быть от 1 до 100!", ephemeral=True)
            
            deleted = await interaction.channel.purge(limit=amount, check=lambda m: m.author == self.member)
            await interaction.response.send_message(f"✅ Удалено {len(deleted)} сообщений {self.member.mention}", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Введите число!", ephemeral=True)

class WelcomeView(View):
    """Красивые кнопки для приветствия"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Правила", style=discord.ButtonStyle.primary, emoji="📜", custom_id="welcome_rules")
    async def rules_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📜 Правила сервера",
            description="""**1.** Уважайте других участников
            **2.** Не спамьте и не флудите
            **3.** Не рекламируйте без разрешения
            **4.** Соблюдайте тематику каналов
            **5.** Слушайтесь модераторов
            **6.** Не используйте оскорбления
            **7.** Запрещен контент 18+""",
            color=COLORS["welcome"]
        )
        embed.set_footer(text="Нарушение правил = наказание")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Команды", style=discord.ButtonStyle.success, emoji="🤖", custom_id="welcome_commands")
    async def commands_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🤖 Основные команды",
            description="""**Для всех:**
            `/help` - помощь по командам
            `/balance` - проверить баланс
            `/daily` - ежедневный бонус
            `/userinfo` - информация о пользователе
            `/stats` - статистика сервера
            `/faq` - частые вопросы
            `/iq` - узнать свой IQ
            `/valute` - курсы валют

            **Экономика:**
            `/pay` - перевести монеты
            `/top` - топ богачей
            `/invest` - инвестировать
            `/investments` - мои инвестиции

            **Twitch:**
            `/twitch add` - добавить стримера для уведомлений
            `/twitch remove` - удалить стримера
            `/twitch list` - список отслеживаемых стримеров""",
            color=COLORS["welcome"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Роли", style=discord.ButtonStyle.secondary, emoji="🏷️", custom_id="welcome_roles")
    async def roles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏷️ Доступные роли",
            description="""**Вы можете получить роли в канале <#РОЛИ>**

            🎮 **Игроки** - @Игрок
            💎 **VIP** - @VIP (требуется поддержка)
            🎨 **Креатив** - @Творец
            🎵 **Музыкант** - @Music Lover
            🎥 **Стример** - @Streamer

            *Роли дают доступ к дополнительным каналам и возможностям*""",
            color=COLORS["welcome"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TicketCategorySelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Техническая проблема", value="tech", emoji="🔧", description="Проблемы с ботом или сервером"),
            discord.SelectOption(label="Жалоба на игрока", value="complaint", emoji="⚠️", description="Пожаловаться на нарушителя"),
            discord.SelectOption(label="Вопрос по серверу", value="question", emoji="❓", description="Общие вопросы о сервере"),
            discord.SelectOption(label="Сотрудничество", value="partner", emoji="🤝", description="Предложения о сотрудничестве"),
            discord.SelectOption(label="Другое", value="other", emoji="📌", description="Другие вопросы")
        ]
        super().__init__(placeholder="Выберите категорию тикета...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            return await interaction.followup.send("❌ Категория тикетов не настроена!", ephemeral=True)

        support_role = guild.get_role(SUPPORT_ROLE_ID)
        if not support_role:
            return await interaction.followup.send("❌ Роль поддержки не настроена!", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, attach_files=True),
            support_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, attach_files=True, manage_messages=True)
        }

        category_emojis = {
            "tech": "🔧",
            "complaint": "⚠️", 
            "question": "❓",
            "partner": "🤝",
            "other": "📌"
        }
        emoji = category_emojis.get(self.values[0], "🎫")
        
        channel_name = f"{emoji}-{self.values[0]}-{interaction.user.name.lower()}"
        ticket_channel = await category.create_text_channel(channel_name, overwrites=overwrites)

        category_descriptions = {
            "tech": "Техническая проблема",
            "complaint": "Жалоба на игрока",
            "question": "Вопрос по серверу",
            "partner": "Сотрудничество",
            "other": "Другое"
        }

        embed = discord.Embed(
            title=f"🎟️ Тикет: {category_descriptions.get(self.values[0], 'Обращение')}",
            description=f"**{interaction.user.mention}**, спасибо за обращение!\n"
                       f"Модератор свяжется с вами в ближайшее время.\n\n"
                       f"**Категория:** {self.values[0]}\n\n"
                       f"🔒 **Закрыть тикет** — нажмите красную кнопку ниже\n"
                       f"⚠️ Тикет будет автоматически закрыт через {INACTIVE_TICKET_HOURS} часов неактивности.",
            color=COLORS["ticket"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"ID: {interaction.user.id}")

        view = TicketControls()
        await ticket_channel.send(content=f"{interaction.user.mention} {support_role.mention}", embed=embed, view=view)

        await interaction.followup.send(f"✅ Тикет создан: {ticket_channel.mention}", ephemeral=True)

        await send_mod_log(
            title="📩 Новый тикет",
            description=f"**Канал:** {ticket_channel.mention}\n**Автор:** {interaction.user}\n**Категория:** {self.values[0]}",
            color=COLORS["ticket"]
        )

class TicketInactivityCheck:
    """Проверка неактивных тикетов"""
    def __init__(self):
        self.ticket_channels = {}

    async def check_inactive_tickets(self):
        for guild in bot.guilds:
            category = guild.get_channel(TICKET_CATEGORY_ID)
            if not category or not isinstance(category, discord.CategoryChannel):
                continue

            for channel in category.text_channels:
                if not channel.name.startswith(("🔧-", "⚠️-", "❓-", "🤝-", "📌-")):
                    continue

                async for msg in channel.history(limit=1):
                    last_msg_time = msg.created_at
                    now = datetime.now(timezone.utc)
                    
                    if (now - last_msg_time).total_seconds() > INACTIVE_TICKET_HOURS * 3600:
                        warning_embed = discord.Embed(
                            title="⚠️ Тикет неактивен",
                            description=f"Этот тикет будет автоматически закрыт через 12 часов из-за неактивности.",
                            color=0xFAA61A
                        )
                        await channel.send(embed=warning_embed)
                        
                        await asyncio.sleep(43200)
                        
                        async for new_msg in channel.history(limit=1):
                            if new_msg.id == msg.id:
                                transcript = await self.create_transcript(channel)
                                await channel.delete()
                                await send_mod_log(
                                    title="📜 Тикет закрыт автоматически",
                                    description=f"**Канал:** {channel.name}\n**Причина:** Неактивность",
                                    color=0x7289DA,
                                    fields=[("Транскрипт", transcript[:1000] + "...", False)]
                                )
                            break
                    break

    async def create_transcript(self, channel) -> str:
        transcript_lines = []
        async for msg in channel.history(limit=100, oldest_first=True):
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = f"{msg.author} ({msg.author.id})"
            content = msg.content or "[пусто]"
            transcript_lines.append(f"[{timestamp}] {author}: {content}")
        
        return "\n".join(transcript_lines)        

class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Создать тикет", style=discord.ButtonStyle.green, emoji="🎟️", custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎫 Выбор категории",
            description="Пожалуйста, выберите категорию вашего обращения:",
            color=COLORS["ticket"]
        )
        
        view = View(timeout=60)
        view.add_item(TicketCategorySelect())
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class TicketControls(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.last_activity = datetime.now(timezone.utc)

    @discord.ui.button(label="Закрыть тикет", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await check_unauthorized_commands(interaction.user)
            return await interaction.response.send_message("❌ Только модераторы могут закрыть тикет.", ephemeral=True)

        await interaction.response.send_message("🔒 Тикет закрывается через 5 секунд...", ephemeral=False)

        transcript_lines = []
        async for msg in interaction.channel.history(limit=1000, oldest_first=True):
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = f"{msg.author} ({msg.author.id})"
            content = msg.content or "[пусто]"
            if msg.attachments:
                content += f"\n📎 Вложения: {', '.join([a.url for a in msg.attachments])}"
            transcript_lines.append(f"[{timestamp}] {author}: {content}")

        transcript_text = "\n".join(transcript_lines) or "[В тикете не было сообщений]"

        filename = f"transcript_{interaction.channel.name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"
        file = discord.File(io.StringIO(transcript_text), filename=filename)

        archive_channel_id = TICKET_ARCHIVE_CHANNEL_ID or MOD_LOG_CHANNEL_ID
        archive_ch = bot.get_channel(archive_channel_id)
        if archive_ch:
            short_embed = discord.Embed(
                title="📜 Тикет закрыт",
                description=f"**Канал:** {interaction.channel.name}\n**Закрыл:** {interaction.user.mention}\n**Сообщений:** {len(transcript_lines)}",
                color=COLORS["ticket"],
                timestamp=datetime.now(timezone.utc)
            )
            await archive_ch.send(embed=short_embed, file=file)

        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Взять тикет", style=discord.ButtonStyle.blurple, emoji="🖐️", custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await check_unauthorized_commands(interaction.user)
            return await interaction.response.send_message("❌ Только модераторы могут взять тикет.", ephemeral=True)
            
        await interaction.response.send_message(f"✅ {interaction.user.mention} взял тикет в работу!", ephemeral=False)
        self.claim_ticket.disabled = True
        await interaction.message.edit(view=self)

class HelpView(View):
    def __init__(self, author: discord.User, is_mod: bool):
        super().__init__(timeout=60)
        self.author = author
        self.current_page = 0
        
        self.categories = [
            {
                "name": "📋 Основное",
                "emoji": "📋",
                "commands": [
                    ("/ping", "Проверить задержку бота"),
                    ("/avatar", "Показать аватар"),
                    ("/userinfo", "Информация о пользователе"),
                    ("/stats", "Статистика сервера"),
                    ("/say", "Написать от лица бота")
                ]
            },
            {
                "name": "💰 Экономика",
                "emoji": "💰",
                "commands": [
                    ("/balance", "Проверить баланс"),
                    ("/daily", "Ежедневный бонус"),
                    ("/pay", "Перевести монеты"),
                    ("/top", "Топ богачей"),
                    ("/vault", "Казна сервера"),
                    ("/invest", "Инвестировать"),
                    ("/investments", "Мои инвестиции")
                ]
            },
            {
                "name": "🎮 Развлечения",
                "emoji": "🎮",
                "commands": [
                    ("/iq", "Узнать свой IQ"),
                    ("/valute", "Курсы валют"),
                    ("/faq", "Часто задаваемые вопросы")
                ]
            },
            {
                "name": "📺 Twitch",
                "emoji": "📺",
                "commands": [
                    ("/twitch add", "Добавить стримера"),
                    ("/twitch remove", "Удалить стримера"),
                    ("/twitch list", "Список стримеров")
                ]
            }
        ]
        
        if is_mod:
            self.categories.extend([
                {
                    "name": "🛡️ Модерация",
                    "emoji": "🛡️",
                    "commands": [
                        ("/warn", "Выдать предупреждение"),
                        ("/warnings", "Список предупреждений"),
                        ("/clearwarn", "Очистить предупреждения"),
                        ("/mute", "Замутить пользователя"),
                        ("/unmute", "Снять мут"),
                        ("/temprole", "Временная роль"),
                        ("/case", "Информация о кейсе"),
                        ("/ban", "Забанить пользователя"),
                        ("/unwarn", "Удалить предупреждение"),
                        ("/faq add", "Добавить вопрос в FAQ")
                    ]
                },
                {
                    "name": "🎫 Тикеты",
                    "emoji": "🎫",
                    "commands": [
                        ("/ticket setup", "Создать панель тикетов"),
                        ("/ticket close", "Закрыть текущий тикет")
                    ]
                }
            ])

    def get_embed(self):
        category = self.categories[self.current_page]
        embed = discord.Embed(
            title=f"{category['emoji']} {category['name']}",
            description="Список доступных команд:",
            color=COLORS["welcome"]
        )
        
        for cmd, desc in category["commands"]:
            embed.add_field(name=cmd, value=desc, inline=False)
        
        embed.set_footer(text=f"Страница {self.current_page + 1} из {len(self.categories)}")
        return embed

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        
        self.current_page = (self.current_page - 1) % len(self.categories)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        
        self.current_page = (self.current_page + 1) % len(self.categories)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="🏠", style=discord.ButtonStyle.success)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        
        is_mod = is_moderator(interaction.user)
        base = "**📋 Основное**\n**💰 Экономика**\n**🎮 Развлечения**\n**📺 Twitch**"
        mod = "\n**🛡️ Модерация**\n**🎫 Тикеты**" if is_mod else ""
        
        embed = discord.Embed(
            title="🤖 Помощь по командам",
            description=f"Используй кнопки для навигации\n\n{base}{mod}",
            color=COLORS["welcome"]
        )
        embed.set_footer(text="Выбери категорию")
        self.current_page = 0
        await interaction.response.edit_message(embed=embed, view=self)

class FAQCategorySelect(Select):
    def __init__(self):
        options = []
        for key, name in FAQ_CATEGORIES.items():
            emoji = "📋" if "общее" in key else "📜" if "правила" in key else "💰" if "экономика" in key else "🛡️" if "модерация" in key else "🔧"
            options.append(discord.SelectOption(label=name, value=key, emoji=emoji))
        
        super().__init__(placeholder="Выберите категорию...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        questions = faq_data.get(category, [])
        
        if not questions:
            return await interaction.response.send_message("❌ В этой категории пока нет вопросов.", ephemeral=True)
        
        view = FAQQuestionsView(category, questions, interaction.user)
        await interaction.response.edit_message(content=f"**{FAQ_CATEGORIES[category]}**\nВыберите вопрос:", embed=None, view=view)

class FAQQuestionsView(View):
    def __init__(self, category: str, questions: list, author: discord.User):
        super().__init__(timeout=60)
        self.category = category
        self.questions = questions
        self.author = author
        self.current_page = 0
        self.items_per_page = 5
        self.add_question_buttons()

    def add_question_buttons(self):
        self.clear_items()
        
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, len(self.questions))
        page_questions = self.questions[start:end]
        
        for i, q in enumerate(page_questions, start=1):
            async def button_callback(interaction: discord.Interaction, question=q):
                if interaction.user.id != self.author.id:
                    return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
                
                embed = discord.Embed(
                    title=f"❓ {question['question']}",
                    description=question['answer'],
                    color=COLORS["faq"]
                )
                embed.set_footer(text=f"Категория: {FAQ_CATEGORIES[self.category]}")
                
                view = View(timeout=60)
                back = Button(label="◀️ Назад", style=discord.ButtonStyle.secondary)
                async def back_cb(interaction: discord.Interaction):
                    await self.show_questions(interaction)
                back.callback = back_cb
                view.add_item(back)
                
                await interaction.response.edit_message(embed=embed, view=view)
            
            button = Button(label=f"{start + i}. {q['question'][:50]}...", style=discord.ButtonStyle.secondary)
            button.callback = button_callback
            self.add_item(button)
        
        if self.current_page > 0:
            prev = Button(label="◀️", style=discord.ButtonStyle.primary)
            prev.callback = self.prev_page
            self.add_item(prev)
        
        if end < len(self.questions):
            next = Button(label="▶️", style=discord.ButtonStyle.primary)
            next.callback = self.next_page
            self.add_item(next)
        
        back_to_cat = Button(label="🏠 Категории", style=discord.ButtonStyle.success)
        back_to_cat.callback = self.back_to_categories
        self.add_item(back_to_cat)

    async def show_questions(self, interaction: discord.Interaction):
        self.add_question_buttons()
        await interaction.response.edit_message(
            content=f"**{FAQ_CATEGORIES[self.category]}**\nВыберите вопрос:",
            embed=None,
            view=self
        )

    async def prev_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        self.current_page -= 1
        self.add_question_buttons()
        await interaction.response.edit_message(view=self)

    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        self.current_page += 1
        self.add_question_buttons()
        await interaction.response.edit_message(view=self)

    async def back_to_categories(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        
        view = FAQView(interaction.user)
        embed = discord.Embed(
            title="📚 Часто задаваемые вопросы",
            description="Выберите категорию вопросов:",
            color=COLORS["faq"]
        )
        await interaction.response.edit_message(embed=embed, view=view)

class FAQView(View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=60)
        self.author = author
        self.add_item(FAQCategorySelect())

# ───────────────────────────────────────────────
#   ИНИЦИАЛИЗАЦИЯ БОТА
# ───────────────────────────────────────────────

intents = discord.Intents(
    guilds=True,
    members=True,
    presences=True,
    message_content=True,
    voice_states=True,
    moderation=True,
    guild_messages=True,
    dm_messages=False
)

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
    case_insensitive=True,
    owner_id=OWNER_ID
)

# ───────────────────────────────────────────────
#   ФОНОВЫЕ ЗАДАЧИ
# ───────────────────────────────────────────────

@tasks.loop(seconds=300)
async def autosave_economy_task():
    save_economy()
    print("[AUTO] Экономика сохранена")

@tasks.loop(hours=1)
async def clean_old_warnings_task():
    global warnings_data
    now = datetime.now(timezone.utc)
    changed = False
    
    for user_id in list(warnings_data.keys()):
        fresh = []
        for warn in warnings_data[user_id]:
            try:
                warn_time = datetime.strptime(warn["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                if (now - warn_time).days < WARN_EXPIRY_DAYS:
                    fresh.append(warn)
            except:
                continue
        
        if len(fresh) != len(warnings_data[user_id]):
            changed = True
            if fresh:
                warnings_data[user_id] = fresh
            else:
                del warnings_data[user_id]
    
    if changed:
        save_warnings()
        print("[AUTO] Старые варны очищены")

@tasks.loop(minutes=1)
async def check_temp_roles_task():
    for guild in bot.guilds:
        for member in guild.members:
            user_id = str(member.id)
            if user_id in temp_roles:
                now = datetime.now(timezone.utc).timestamp()
                to_remove = []
                
                for role_id, expiry in temp_roles[user_id].items():
                    if now >= expiry:
                        role = guild.get_role(int(role_id))
                        if role and role in member.roles:
                            try:
                                await member.remove_roles(role, reason="Временная роль истекла")
                                await send_mod_log(
                                    title="⏱️ Роль снята",
                                    description=f"**Пользователь:** {member.mention}\n**Роль:** {role.mention}",
                                    color=COLORS["audit"]
                                )
                            except:
                                pass
                        to_remove.append(role_id)
                
                for role_id in to_remove:
                    del temp_roles[user_id][role_id]
                
                if not temp_roles[user_id]:
                    del temp_roles[user_id]

@tasks.loop(hours=6)
async def check_investments_task():
    now = datetime.now(timezone.utc).timestamp()
    
    for user_id, data in economy_data.items():
        if user_id == "server_vault" or "investments" not in data:
            continue
        
        active = []
        for inv in data["investments"]:
            if inv["end_time"] <= now:
                profit = inv["profit"]
                data["balance"] += profit
                
                user = bot.get_user(int(user_id))
                if user:
                    embed = discord.Embed(
                        title=f"{ECONOMY_EMOJIS['profit']} Инвестиция завершена",
                        description=f"Ваша инвестиция на {inv['days']} дней завершена!\n"
                                   f"**Прибыль:** +{format_number(profit)} {ECONOMY_EMOJIS['coin']}",
                        color=COLORS["economy"]
                    )
                    try:
                        await user.send(embed=embed)
                    except:
                        pass
            else:
                active.append(inv)
        
        data["investments"] = active
    
    save_economy()
    print("[AUTO] Инвестиции проверены")

@tasks.loop(hours=1)
async def check_inactive_tickets_task():
    checker = TicketInactivityCheck()
    await checker.check_inactive_tickets()

# ───────────────────────────────────────────────
#   СОБЫТИЯ
# ───────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"┌──────────────────────────────────────────────┐")
    print(f"│  Залогинен как    {bot.user}  │")
    print(f"│  ID               {bot.user.id}      │")
    print(f"│  Время запуска    {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} │")
    print(f"└──────────────────────────────────────────────┘")

    await bot.change_presence(
        status=discord.Status.dnd, 
        activity=discord.Activity(type=discord.ActivityType.watching, name="mortisplay.ru")
    )

    try:
        synced = await bot.tree.sync()
        print(f"Команды синхронизированы: {len(synced)} шт")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")

    for guild in bot.guilds:
        await guild.chunk()
        if guild.id == FULL_ACCESS_GUILD_ID:
            bot_member = guild.get_member(bot.user.id)
            if bot_member:
                perms = bot_member.guild_permissions
                if not perms.view_audit_log:
                    print(f"⚠️ НЕТ ПРАВА VIEW_AUDIT_LOG на сервере {guild.name}!")
                else:
                    print(f"✅ Право VIEW_AUDIT_LOG есть на сервере {guild.name}")

    bot.add_view(TicketPanelView())
    bot.add_view(TicketControls())

    # Запускаем задачи
    autosave_economy_task.start()
    clean_old_warnings_task.start()
    check_temp_roles_task.start()
    check_investments_task.start()
    check_inactive_tickets_task.start()
    
    # Запускаем проверку Twitch стримов
    if TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET:
        check_twitch_streams_task.start()
        print("✅ Twitch интеграция активирована")
    else:
        print("⚠️ Twitch интеграция не настроена (нужны CLIENT_ID и CLIENT_SECRET)")

    bot.launch_time = datetime.now(timezone.utc)
    print("Бот полностью готов к работе")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Пропускаем модераторов и администраторов
    if is_protected_from_automod(message.author):
        return await bot.process_commands(message)

    if bot.user in message.mentions:
        await message.channel.send(f"{message.author.mention}, я тут! Используй `/help`")

    user_id = str(message.author.id)
    now = datetime.now(timezone.utc).timestamp()

    # Анти-спам
    spam_threshold = SPAM_THRESHOLD * (VIP_SPAM_MULTIPLIER if is_vip(message.author) else 1)
    mention_limit = 4 * (VIP_MENTION_MULTIPLIER if is_vip(message.author) else 1)

    if user_id not in spam_cache:
        spam_cache[user_id] = []
    spam_cache[user_id] = [t for t in spam_cache[user_id] if now - t < SPAM_TIME]
    spam_cache[user_id].append(now)

    # Спам
    if len(spam_cache[user_id]) >= spam_threshold:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, слишком быстро пишешь!", delete_after=8)
        try: 
            await message.author.timeout(timedelta(minutes=10), reason="Анти-спам")
            case_id = await create_case(message.author, bot.user, "Авто-мут (спам)", "Превышение лимита сообщений", "10 минут")
            await send_punishment_log(
                member=message.author,
                punishment_type="🔇 Мут 10 минут",
                duration="10 минут",
                reason="Превышение лимита сообщений",
                moderator=bot.user,
                case_id=case_id
            )
        except: 
            pass
        return

    # Масс-пинг
    mention_count = len(message.mentions) + len(message.role_mentions)
    
    if ("@everyone" in message.content or "@here" in message.content) and not message.author.guild_permissions.mention_everyone:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, у тебя нет прав на массовые упоминания!", delete_after=8)
        return
    
    if mention_count > mention_limit:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, не спамь упоминаниями! (лимит: {mention_limit})", delete_after=8)
        
        if user_id not in warnings_data:
            warnings_data[user_id] = []
        warnings_data[user_id].append({
            "moderator": "Автомодерация",
            "reason": f"Массовый пинг ({mention_count} упоминаний)",
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        })
        save_warnings()
        
        case_id = await create_case(message.author, bot.user, "Варн (авто)", f"Массовый пинг ({mention_count} упоминаний)")
        await check_auto_punishment(message.author, "Массовый пинг")
        return

    # Капс
    if len(message.content) > 15:
        upper_ratio = sum(1 for c in message.content if c.isupper()) / len(message.content)
        if upper_ratio > 0.75:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, не кричи (капс)!", delete_after=8)
            return

    # Реклама
    if re.search(r"discord\.(gg|com/invite)/", message.content.lower()):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, реклама запрещена!", delete_after=10)
        return

    # Токсичность
    if is_toxic(message.content):
        await message.delete()

        toxic_warnings = [w for w in warnings_data.get(user_id, []) if "токсичность" in w.get("reason", "").lower()]

        if len(toxic_warnings) >= 1:
            try:
                await message.author.timeout(timedelta(hours=24), reason="Повторная токсичность")
                await message.channel.send(
                    f"{message.author.mention}, **мут 24 часа** за повторные оскорбления.",
                    delete_after=10
                )
                case_id = await create_case(message.author, bot.user, "Авто-мут 24ч", "Повторная токсичность", "24 часа")
                await send_punishment_log(
                    member=message.author,
                    punishment_type="🔇 Мут 24ч (авто)",
                    duration="24 часа",
                    reason="Повторная токсичность",
                    moderator=bot.user,
                    case_id=case_id
                )
            except:
                pass
        else:
            try:
                await message.author.timeout(timedelta(hours=1), reason="Токсичность")
                await message.channel.send(
                    f"{message.author.mention}, **мут 1 час** за оскорбления. Повтор → мут 24 часа.",
                    delete_after=10
                )

                if user_id not in warnings_data:
                    warnings_data[user_id] = []
                warnings_data[user_id].append({
                    "moderator": "Автомодерация",
                    "reason": "Токсичность",
                    "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                })
                save_warnings()
                
                case_id = await create_case(message.author, bot.user, "Авто-мут 1ч", "Токсичность", "1 час")
                await send_punishment_log(
                    member=message.author,
                    punishment_type="🔇 Мут 1ч (авто)",
                    duration="1 час",
                    reason="Токсичность",
                    moderator=bot.user,
                    case_id=case_id
                )

            except:
                await message.channel.send(f"{message.author.mention}, удали оскорбления пожалуйста.", delete_after=10)

        return

    # Экономика
    if has_full_access(message.guild.id):
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}

        if now - economy_data[user_id].get("last_message", 0) >= MESSAGE_COOLDOWN:
            earn = random.randint(1, 5)
            economy_data[user_id]["balance"] += earn
            economy_data[user_id]["last_message"] = now
            save_economy()

    await bot.process_commands(message)

# ───────────────────────────────────────────────
#   ПРИВЕТСТВИЯ И ПРОЩАНИЯ
# ───────────────────────────────────────────────

@bot.event
async def on_member_join(member):
    """Красивое приветствие нового участника"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            embed = discord.Embed(
                title="📥 Участник зашёл",
                color=COLORS["welcome"],
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Пользователь", value=member.mention, inline=True)
            embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
            embed.add_field(name="Аккаунт создан", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
            
            account_age = datetime.now(timezone.utc) - member.created_at
            if account_age.days < NEW_ACCOUNT_DAYS:
                embed.add_field(name="⚠️ Внимание", value="Новый аккаунт!", inline=False)
            
            await log_ch.send(embed=embed)
        
        welcome_ch = bot.get_channel(WELCOME_CHANNEL_ID)
        if welcome_ch:
            total = member.guild.member_count
            humans = len([m for m in member.guild.members if not m.bot])
            bots = total - humans
            
            embed = discord.Embed(
                title="🎉 Новый участник!",
                description=f"**{member.mention}**, добро пожаловать на сервер!",
                color=COLORS["welcome"],
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            
            embed.add_field(name="📝 Имя", value=member.name, inline=True)
            embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
            embed.add_field(name="📅 Регистрация", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
            
            embed.add_field(
                name="👥 Статистика",
                value=f"**Всего:** {total}\n👤 **Людей:** {humans}\n🤖 **Ботов:** {bots}",
                inline=True
            )
            
            embed.add_field(
                name="📋 Быстрый старт",
                value="• Ознакомься с правилами\n• Получи роли\n• Начни общаться",
                inline=True
            )
            
            embed.set_footer(text="Спасибо что выбрали нас! 💫", icon_url=member.guild.icon.url if member.guild.icon else None)
            
            view = WelcomeView()
            await welcome_ch.send(embed=embed, view=view)
            
    except Exception as e:
        print(f"Ошибка в on_member_join: {e}")

@bot.event
async def on_member_remove(member):
    """Красивое прощание с участником"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            embed = discord.Embed(
                title="📤 Участник вышел",
                color=COLORS["goodbye"],
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Пользователь", value=str(member), inline=True)
            embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
            embed.add_field(name="На сервере был", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Неизвестно", inline=True)
            await log_ch.send(embed=embed)
        
        goodbye_ch = bot.get_channel(GOODBYE_CHANNEL_ID)
        if goodbye_ch:
            days_on_server = 0
            if member.joined_at:
                days_on_server = (datetime.now(timezone.utc) - member.joined_at).days
            
            total = member.guild.member_count
            
            embed = discord.Embed(
                title="👋 Пока...",
                description=f"**{member.name}** покинул нас",
                color=COLORS["goodbye"],
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            
            if days_on_server > 0:
                embed.add_field(name="⏱️ Пробыл на сервере", value=f"**{days_on_server}** {_plural(days_on_server, 'день', 'дня', 'дней')}", inline=True)
            
            embed.add_field(name="👥 Осталось", value=f"**{total}**", inline=True)
            
            if days_on_server > 30:
                embed.add_field(name="💔 Жаль", value="Надеемся, ты вернешься!", inline=False)
            elif days_on_server > 7:
                embed.add_field(name="😢", value="Будем скучать!", inline=False)
            
            await goodbye_ch.send(embed=embed)
            
    except Exception as e:
        print(f"Ошибка в on_member_remove: {e}")

def _plural(count, one, few, many):
    """Склонение слов"""
    if count % 10 == 1 and count % 100 != 11:
        return one
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return few
    return many

# ───────────────────────────────────────────────
#   УЛУЧШЕННЫЙ АУДИТ-ЛОГ (сокращён для компактности)
# ───────────────────────────────────────────────

async def get_audit_info(guild, action, target_id=None, limit=5):
    try:
        async for entry in guild.audit_logs(limit=limit, action=action):
            if target_id and entry.target.id == target_id:
                return {
                    "moderator": entry.user,
                    "reason": entry.reason,
                    "created_at": entry.created_at
                }
            elif not target_id:
                return {
                    "moderator": entry.user,
                    "reason": entry.reason,
                    "created_at": entry.created_at
                }
    except:
        pass
    return None

@bot.event
async def on_message_delete(message):
    """Лог удаления сообщения"""
    if message.author.bot:
        return
    
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
        
        moderator = None
        reason = None
        
        try:
            async for entry in message.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
                time_diff = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                if (hasattr(entry.extra, 'channel') and 
                    entry.extra.channel.id == message.channel.id and 
                    entry.target.id == message.author.id and
                    time_diff < 10):
                    moderator = entry.user
                    reason = entry.reason
                    break
        except:
            pass
        
        embed = discord.Embed(
            title="🗑 Сообщение удалено",
            color=COLORS["audit"],
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="Автор", value=f"{message.author.mention}\nID: `{message.author.id}`", inline=False)
        embed.add_field(name="Канал", value=message.channel.mention, inline=False)
        
        if moderator:
            embed.add_field(name="Удалил", value=f"{moderator.mention}\nID: `{moderator.id}`", inline=False)
        
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        
        if message.content:
            content = message.content[:900] + ("..." if len(message.content) > 900 else "")
            embed.add_field(name="Содержимое", value=content, inline=False)
        
        if message.attachments:
            files = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
            embed.add_field(name="Вложения", value=files[:1000], inline=False)
        
        embed.set_footer(text=f"ID: {message.id}")
        await log_ch.send(embed=embed)
        
    except Exception as e:
        print(f"Ошибка в on_message_delete: {e}")

@bot.event
async def on_message_edit(before, after):
    """Лог изменения сообщения"""
    if before.author.bot or before.content == after.content:
        return
    
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
        
        embed = discord.Embed(
            title="✏️ Сообщение изменено",
            color=COLORS["audit"],
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="Автор", value=f"{before.author.mention}\nID: `{before.author.id}`", inline=False)
        embed.add_field(name="Канал", value=before.channel.mention, inline=False)
        embed.add_field(name="Было", value=before.content[:500] + ("..." if len(before.content) > 500 else "") or "*Пусто*", inline=False)
        embed.add_field(name="Стало", value=after.content[:500] + ("..." if len(after.content) > 500 else "") or "*Пусто*", inline=False)
        embed.add_field(name="Ссылка", value=f"[Перейти]({after.jump_url})", inline=False)
        
        await log_ch.send(embed=embed)
        
    except Exception as e:
        print(f"Ошибка в on_message_edit: {e}")

# ───────────────────────────────────────────────
#   КОМАНДЫ
# ───────────────────────────────────────────────

@bot.hybrid_command(name="ping", description="Подробная информация о боте")
async def ping(ctx: commands.Context):
    try:
        latency = round(bot.latency * 1000)
        
        uptime = datetime.now(timezone.utc) - bot.launch_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            uptime_str = f"{days}д {hours}ч {minutes}м {seconds}с"
        elif hours > 0:
            uptime_str = f"{hours}ч {minutes}м {seconds}с"
        elif minutes > 0:
            uptime_str = f"{minutes}м {seconds}с"
        else:
            uptime_str = f"{seconds}с"
        
        guild_count = len(bot.guilds)
        user_count = sum(g.member_count for g in bot.guilds if g.member_count)
        channel_count = sum(len(g.channels) for g in bot.guilds)
        
        ping_status = "🟢 Отлично" if latency < 200 else "🟡 Средне" if latency < 300 else "🔴 Плохо"
        
        embed = discord.Embed(
            title="🏓 **ПОНГ!**",
            description="```Статус бота и производительность```",
            color=COLORS["welcome"],
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="📊 **Основная информация**",
            value=f"```yml\n"
                  f"Задержка: {latency}ms\n"
                  f"Состояние: {ping_status}\n"
                  f"Время работы: {uptime_str}\n"
                  f"Серверов: {guild_count}\n"
                  f"Пользователей: {user_count:,}\n"
                  f"Каналов: {channel_count}\n"
                  f"```",
            inline=False
        )
        
        embed.add_field(
            name="⏱️ **Детали задержки**",
            value=f"```diff\n"
                  f"+ WebSocket: {latency}ms\n"
                  f"+ API: ~{latency + 20}ms\n"
                  f"+ База данных: ~{latency + 10}ms\n"
                  f"```",
            inline=True
        )
        
        command_count = len(bot.commands)
        hybrid_count = len([c for c in bot.commands if isinstance(c, commands.HybridCommand)])
        
        embed.add_field(
            name="📋 **Команды**",
            value=f"```css\n"
                  f"Всего: {command_count}\n"
                  f"Гибридных: {hybrid_count}\n"
                  f"Слэш: {command_count}\n"
                  f"```",
            inline=True
        )
        
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        embed.set_footer(
            text=f"MortisPlay • Запросил: {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        view = View(timeout=60)
        button = Button(label="🔄 Обновить", style=discord.ButtonStyle.primary)
        
        async def refresh_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("❌ Это не твоя команда!", ephemeral=True)
            
            new_latency = round(bot.latency * 1000)
            new_uptime = datetime.now(timezone.utc) - bot.launch_time
            new_days = new_uptime.days
            new_hours, new_remainder = divmod(new_uptime.seconds, 3600)
            new_minutes, new_seconds = divmod(new_remainder, 60)
            
            if new_days > 0:
                new_uptime_str = f"{new_days}д {new_hours}ч {new_minutes}м {new_seconds}с"
            elif new_hours > 0:
                new_uptime_str = f"{new_hours}ч {new_minutes}м {new_seconds}с"
            elif new_minutes > 0:
                new_uptime_str = f"{new_minutes}м {new_seconds}с"
            else:
                new_uptime_str = f"{new_seconds}с"
            
            new_ping_status = "🟢 Отлично" if new_latency < 200 else "🟡 Средне" if new_latency < 300 else "🔴 Плохо"
            
            new_embed = discord.Embed(
                title="🏓 **ПОНГ!**",
                description="```Статус бота и производительность```",
                color=COLORS["welcome"],
                timestamp=datetime.now(timezone.utc)
            )
            
            new_embed.add_field(
                name="📊 **Основная информация**",
                value=f"```yml\n"
                      f"Задержка: {new_latency}ms\n"
                      f"Состояние: {new_ping_status}\n"
                      f"Время работы: {new_uptime_str}\n"
                      f"Серверов: {guild_count}\n"
                      f"Пользователей: {user_count:,}\n"
                      f"Каналов: {channel_count}\n"
                      f"```",
                inline=False
            )
            
            new_embed.add_field(
                name="⏱️ **Детали задержки**",
                value=f"```diff\n"
                      f"+ WebSocket: {new_latency}ms\n"
                      f"+ API: ~{new_latency + 20}ms\n"
                      f"+ База данных: ~{new_latency + 10}ms\n"
                      f"```",
                inline=True
            )
            
            new_embed.add_field(
                name="📋 **Команды**",
                value=f"```css\n"
                      f"Всего: {command_count}\n"
                      f"Гибридных: {hybrid_count}\n"
                      f"Слэш: {command_count}\n"
                      f"```",
                inline=True
            )
            
            new_embed.set_thumbnail(url=bot.user.display_avatar.url)
            new_embed.set_footer(
                text=f"MortisPlay • Запросил: {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            
            await interaction.response.edit_message(embed=new_embed, view=view)
        
        button.callback = refresh_callback
        view.add_item(button)
        
        await ctx.send(embed=embed, view=view, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="avatar", description="Показать аватар")
@app_commands.describe(member="Пользователь")
async def avatar(ctx: commands.Context, member: discord.Member = None):
    try:
        member = member or ctx.author
        embed = discord.Embed(title=f"Аватар {member}", color=COLORS["welcome"])
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="userinfo", description="Информация о пользователе")
@app_commands.describe(member="Пользователь")
async def userinfo(ctx: commands.Context, member: discord.Member = None):
    try:
        await ctx.defer(ephemeral=True)
        member = member or ctx.author
        guild = ctx.guild

        fresh_member = guild.get_member(member.id)
        if not fresh_member:
            fresh_member = await guild.fetch_member(member.id)

        status_map = {
            discord.Status.online: ("🟢 Онлайн", 0x43b581),
            discord.Status.idle: ("🟡 Неактивен", 0xfaa61a),
            discord.Status.dnd: ("🔴 Не беспокоить", 0xf04747),
            discord.Status.offline: ("⚫ Оффлайн", 0x747f8d),
            discord.Status.invisible: ("⚫ Невидимка", 0x747f8d)
        }
        status_text, color = status_map.get(fresh_member.status, ("⚫ Неизвестно", 0x747f8d))

        devices = []
        if fresh_member.desktop_status != discord.Status.offline:
            devices.append("🖥️ Desktop")
        if fresh_member.mobile_status != discord.Status.offline:
            devices.append("📱 Mobile")
        if fresh_member.web_status != discord.Status.offline:
            devices.append("🌐 Web")
        devices_str = " • ".join(devices) or "Неизвестно"

        booster_since = fresh_member.premium_since
        booster_text = f"Бустер с {booster_since.strftime('%d.%m.%Y')}" if booster_since else "Не бустит"

        embed = discord.Embed(title=f"👤 {fresh_member.display_name}", color=color)
        embed.set_thumbnail(url=fresh_member.display_avatar.url)

        embed.add_field(name="🆔 ID", value=f"`{fresh_member.id}`", inline=True)
        embed.add_field(name="📛 Ник", value=f"`{fresh_member.name}`", inline=True)
        embed.add_field(name="📅 Регистрация", value=fresh_member.created_at.strftime("%d.%m.%Y %H:%M"), inline=True)
        embed.add_field(name="📅 На сервере", value=fresh_member.joined_at.strftime("%d.%m.%Y %H:%M") if fresh_member.joined_at else "—", inline=True)
        embed.add_field(name="🌐 Статус", value=status_text, inline=True)
        embed.add_field(name="📱 Устройства", value=devices_str, inline=True)
        embed.add_field(name="🚀 Бустер", value=booster_text, inline=True)
        embed.add_field(name="🏆 Высшая роль", value=fresh_member.top_role.mention if fresh_member.top_role != guild.default_role else "Нет", inline=False)

        if fresh_member.id == bot.user.id:
            embed.add_field(name="📝 Биография", value="Я многофункциональный бот для Discord, созданный для автоматизации модерации, экономики и развлечений. Разработан специально для сервера MortisPlay!", inline=False)

        if fresh_member.banner:
            embed.set_image(url=fresh_member.banner.url)

        embed.set_footer(text=f"Запросил: {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed, ephemeral=True)

    except Exception as e:
        await send_error_embed(ctx, f"Не удалось загрузить информацию: {str(e)}")

@bot.hybrid_command(name="stats", description="Статистика сервера")
async def stats(ctx: commands.Context):
    try:
        guild = ctx.guild
        
        total = guild.member_count
        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
        idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
        dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
        offline = total - online
        bots = sum(1 for m in guild.members if m.bot)
        humans = total - bots

        embed = discord.Embed(
            title=f"📊 Статистика {guild.name}",
            color=COLORS["welcome"],
            timestamp=datetime.now(timezone.utc)
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👥 Участники", value=f"**Всего:** {total}\n👤 **Людей:** {humans}\n🤖 **Ботов:** {bots}", inline=True)
        embed.add_field(name="🟢 Онлайн", value=f"**Онлайн:** {online}\n🟡 **Idle:** {idle}\n🔴 **DND:** {dnd}\n⚫ **Offline:** {offline}", inline=True)
        embed.add_field(name="📁 Каналы", value=f"**Текстовых:** {len(guild.text_channels)}\n**Голосовых:** {len(guild.voice_channels)}\n**Категорий:** {len(guild.categories)}", inline=True)
        embed.add_field(name="🎨 Оформление", value=f"**Ролей:** {len(guild.roles)}\n**Эмодзи:** {len(guild.emojis)}", inline=True)
        embed.add_field(name="🚀 Буст", value=f"**Уровень:** {guild.premium_tier}\n**Бустов:** {guild.premium_subscription_count}", inline=True)
        embed.add_field(name="📅 Сервер создан", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
        
        if guild.owner:
            embed.add_field(name="👑 Владелец", value=guild.owner.mention, inline=False)
        
        embed.set_footer(text=f"ID: {guild.id}")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="say", description="Написать от лица бота")
@app_commands.describe(
    text="Текст сообщения",
    embed_title="Заголовок embed",
    embed_description="Описание embed",
    embed_color="Цвет embed (например #FF0000)",
    channel="Канал",
    reply_to="ID сообщения для ответа"
)
@commands.has_permissions(manage_messages=True)
async def say(
    ctx: commands.Context,
    text: str = None,
    embed_title: str = None,
    embed_description: str = None,
    embed_color: str = "#57F287",
    channel: discord.TextChannel = None,
    reply_to: discord.Message = None
):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)

        if not has_full_access(ctx.guild.id):
            return await ctx.send("❌ Команда доступна только на сервере разработчика.", ephemeral=True)

        target = channel or ctx.channel
        if not target.permissions_for(ctx.guild.me).send_messages:
            return await ctx.send("❌ Нет прав писать в этот канал.", ephemeral=True)

        if embed_title and embed_description:
            color = int(embed_color.lstrip("#"), 16) if embed_color.startswith("#") else 0x57F287
            embed = discord.Embed(title=embed_title, description=embed_description, color=color)
            await target.send(embed=embed, reference=reply_to)
        else:
            if not text:
                return await ctx.send("❌ Укажи текст или embed.", ephemeral=True)
            await target.send(text, reference=reply_to)

        await ctx.send(f"✅ Отправлено в {target.mention}", ephemeral=True)

    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   ЭКОНОМИКА (СОКРАЩЕНО ДЛЯ КОМПАКТНОСТИ)
# ───────────────────────────────────────────────

@bot.hybrid_command(name="pay", description="💸 Перевести монеты")
@app_commands.describe(member="Кому", amount="Сумма", comment="Комментарий")
async def pay(ctx: commands.Context, member: discord.Member, amount: int, comment: str = None):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)

        if amount <= 0:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Сумма должна быть > 0.", ephemeral=True)
        
        if member.id == ctx.author.id:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Нельзя перевести себе.", ephemeral=True)

        sender_id = str(ctx.author.id)
        receiver_id = str(member.id)

        if sender_id not in economy_data or economy_data[sender_id].get("balance", 0) < amount:
            bal = economy_data.get(sender_id, {}).get("balance", 0)
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Недостаточно монет! Баланс: {format_number(bal)} {ECONOMY_EMOJIS['coin']}", ephemeral=True)

        tax = await apply_wealth_tax(sender_id)

        if receiver_id not in economy_data:
            economy_data[receiver_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}

        economy_data[sender_id]["balance"] -= amount
        economy_data[receiver_id]["balance"] += amount
        save_economy()

        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['transfer']} Перевод выполнен",
            color=COLORS["economy"],
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="Отправитель", value=f"{ctx.author.mention}\nБаланс: **{format_number(economy_data[sender_id]['balance'])}** {ECONOMY_EMOJIS['coin']}", inline=True)
        embed.add_field(name="Получатель", value=f"{member.mention}\nБаланс: **{format_number(economy_data[receiver_id]['balance'])}** {ECONOMY_EMOJIS['coin']}", inline=True)
        embed.add_field(name="Сумма", value=f"**{format_number(amount)}** {ECONOMY_EMOJIS['coin']}", inline=False)

        if comment:
            embed.add_field(name="📝 Комментарий", value=f"*{comment}*", inline=False)

        if tax > 0:
            embed.add_field(name=f"{ECONOMY_EMOJIS['tax']} Налог", value=f"Списано **-{format_number(tax)}** {ECONOMY_EMOJIS['coin']} (1% > 10к)", inline=False)

        embed.set_footer(text="Экономика v0.1", icon_url=bot.user.display_avatar.url)
        await ctx.send(embed=embed, ephemeral=True)
        
        try:
            dm = discord.Embed(
                title=f"{ECONOMY_EMOJIS['transfer']} Получен перевод",
                description=f"**От:** {ctx.author.mention}\n**Сумма:** {format_number(amount)} {ECONOMY_EMOJIS['coin']}",
                color=COLORS["economy"]
            )
            if comment:
                dm.add_field(name="Комментарий", value=comment, inline=False)
            await member.send(embed=dm)
        except:
            pass
        
        if amount >= 10000:
            await send_mod_log(
                title="💸 Крупный перевод",
                description=f"**От:** {ctx.author.mention}\n**Кому:** {member.mention}\n**Сумма:** {format_number(amount)} {ECONOMY_EMOJIS['coin']}",
                color=COLORS["economy"]
            )
            
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="invest", description="📈 Инвестировать монеты")
@app_commands.describe(amount="Сумма", days="Количество дней (1-30)")
async def invest(ctx: commands.Context, amount: int, days: int):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)

        if amount < INVESTMENT_MIN_AMOUNT:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Минимум: {format_number(INVESTMENT_MIN_AMOUNT)} {ECONOMY_EMOJIS['coin']}", ephemeral=True)
        
        if days < 1 or days > INVESTMENT_MAX_DAYS:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Срок: 1-{INVESTMENT_MAX_DAYS} дней.", ephemeral=True)

        user_id = str(ctx.author.id)
        
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}
        
        if economy_data[user_id]["balance"] < amount:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Недостаточно монет! Баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']}", ephemeral=True)

        rate = INVESTMENT_BASE_RATE * (1 + days / 30)
        profit = int(amount * rate)
        end_time = datetime.now(timezone.utc).timestamp() + (days * 86400)
        
        investment = {
            "amount": amount,
            "days": days,
            "profit": profit,
            "start_time": datetime.now(timezone.utc).timestamp(),
            "end_time": end_time,
            "rate": round(rate * 100, 2)
        }
        
        economy_data[user_id]["balance"] -= amount
        economy_data[user_id].setdefault("investments", []).append(investment)
        save_economy()
        
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['investment']} Инвестиция создана",
            color=COLORS["economy"],
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="💰 Сумма", value=f"{format_number(amount)} {ECONOMY_EMOJIS['coin']}", inline=True)
        embed.add_field(name="📅 Срок", value=f"{days} дней", inline=True)
        embed.add_field(name="📊 Ставка", value=f"{investment['rate']}%", inline=True)
        embed.add_field(name="💹 Прибыль", value=f"+{format_number(profit)} {ECONOMY_EMOJIS['coin']}", inline=True)
        embed.add_field(name="⏰ Завершение", value=f"<t:{int(end_time)}:R>", inline=False)
        
        embed.set_footer(text=f"Баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']}")
        await ctx.send(embed=embed, ephemeral=True)
        
        await send_mod_log(
            title="📈 Новая инвестиция",
            description=f"**Пользователь:** {ctx.author.mention}\n**Сумма:** {format_number(amount)} {ECONOMY_EMOJIS['coin']}\n**Срок:** {days} дней",
            color=COLORS["economy"]
        )
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="investments", description="📊 Мои инвестиции")
async def my_investments(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)

        user_id = str(ctx.author.id)
        
        if user_id not in economy_data or not economy_data[user_id].get("investments"):
            return await ctx.send(f"{ECONOMY_EMOJIS['warning']} У вас нет инвестиций.", ephemeral=True)
        
        now = datetime.now(timezone.utc).timestamp()
        active = []
        completed = []
        
        for inv in economy_data[user_id]["investments"]:
            if inv["end_time"] > now:
                active.append(inv)
            else:
                completed.append(inv)
        
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['investment']} Мои инвестиции",
            color=COLORS["economy"],
            timestamp=datetime.now(timezone.utc)
        )
        
        if active:
            text = ""
            for i, inv in enumerate(active, 1):
                left = inv["end_time"] - now
                days = int(left // 86400)
                hours = int((left % 86400) // 3600)
                text += f"**{i}.** {format_number(inv['amount'])} → +{format_number(inv['profit'])} {ECONOMY_EMOJIS['coin']}\n⏰ Осталось: {days}д {hours}ч\n\n"
            embed.add_field(name="🟢 Активные", value=text, inline=False)
        
        if completed:
            text = ""
            for i, inv in enumerate(completed[-5:], 1):
                text += f"**{i}.** {format_number(inv['amount'])} → +{format_number(inv['profit'])} {ECONOMY_EMOJIS['coin']} ✅\n"
            embed.add_field(name="✅ Завершенные", value=text, inline=False)
        
        total_invested = sum(i["amount"] for i in economy_data[user_id]["investments"])
        total_profit = sum(i["profit"] for i in economy_data[user_id]["investments"])
        
        embed.add_field(
            name="📊 Статистика",
            value=f"**Инвестировано:** {format_number(total_invested)} {ECONOMY_EMOJIS['coin']}\n**Прибыль:** +{format_number(total_profit)} {ECONOMY_EMOJIS['coin']}",
            inline=False
        )
        
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="twitchtest", description="🔧 Тест Twitch API (только для админов)")
@app_commands.describe(streamer="Имя стримера для теста")
async def twitch_test(ctx: commands.Context, streamer: str):
    """Тестовая команда для проверки Twitch API"""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Только для разработчика!", ephemeral=True)
    
    await ctx.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="🔧 Twitch API Test",
        description=f"Проверка стримера: **{streamer}**",
        color=COLORS["twitch"]
    )
    
    # Проверяем наличие переменных
    if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
        embed.add_field(
            name="❌ Конфигурация",
            value="TWITCH_CLIENT_ID или TWITCH_CLIENT_SECRET не заданы!",
            inline=False
        )
        return await ctx.send(embed=embed, ephemeral=True)
    
    embed.add_field(name="Client ID", value=f"`{TWITCH_CLIENT_ID[:10]}...`" if TWITCH_CLIENT_ID else "❌", inline=True)
    embed.add_field(name="Client Secret", value="✅" if TWITCH_CLIENT_SECRET else "❌", inline=True)
    
    # Получаем токен
    token = await get_twitch_token()
    if token:
        embed.add_field(name="Токен", value="✅ Получен", inline=True)
    else:
        embed.add_field(name="Токен", value="❌ Не получен", inline=True)
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Проверяем стримера
    result = await check_twitch_stream(streamer)
    
    if result and result.get('error') == 'not_found':
        embed.add_field(name="Результат", value="❌ Стример не найден", inline=False)
    elif result and result.get('is_live'):
        embed.add_field(name="Результат", value="🔴 **LIVE!**", inline=False)
        embed.add_field(name="Название", value=result['title'][:100], inline=False)
        embed.add_field(name="Игра", value=result['game'], inline=True)
        embed.add_field(name="Зрители", value=format_number(result['viewers']), inline=True)
    elif result:
        embed.add_field(name="Результат", value="⚫ Офлайн", inline=False)
    else:
        embed.add_field(name="Результат", value="❌ Ошибка запроса", inline=False)
    
    if result and result.get('display_name'):
        embed.add_field(name="Отображаемое имя", value=result['display_name'], inline=True)
    
    await ctx.send(embed=embed, ephemeral=True)

# ───────────────────────────────────────────────
#   СИСТЕМА КЕЙСОВ
# ───────────────────────────────────────────────

@bot.hybrid_command(name="case", description="🔍 Информация о кейсе")
@app_commands.describe(case_id="ID кейса")
@commands.has_permissions(manage_messages=True)
async def case_info(ctx: commands.Context, case_id: str):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)

        case = await get_case(case_id)
        if not case:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Кейс `{case_id}` не найден.", ephemeral=True)
        
        embed = discord.Embed(
            title=f"🔍 Кейс #{case_id}",
            color=COLORS["mod"],
            timestamp=datetime.fromisoformat(case['timestamp'])
        )
        
        user = await bot.fetch_user(int(case['user_id'])) if case['user_id'].isdigit() else None
        mod = await bot.fetch_user(int(case['moderator_id'])) if case['moderator_id'].isdigit() else None
        
        embed.add_field(name="👤 Пользователь", value=user.mention if user else case['user_name'], inline=True)
        embed.add_field(name="👮 Модератор", value=mod.mention if mod else case['moderator_name'], inline=True)
        embed.add_field(name="⚡ Действие", value=case['action'], inline=True)
        
        if case['duration']:
            embed.add_field(name="⏰ Длительность", value=case['duration'], inline=True)
        
        embed.add_field(name="📝 Причина", value=case['reason'], inline=False)
        embed.add_field(name="📅 Дата", value=f"<t:{int(datetime.fromisoformat(case['timestamp']).timestamp())}:F>", inline=False)
        
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   УЛУЧШЕННЫЙ /HELP
# ───────────────────────────────────────────────

@bot.hybrid_command(name="help", description="📚 Список команд")
async def help_command(ctx: commands.Context):
    try:
        is_mod = is_moderator(ctx.author)
        
        embed = discord.Embed(
            title="🤖 Помощь по командам",
            description="**📋 Основное**\n**💰 Экономика**\n**🎮 Развлечения**\n**📺 Twitch**" +
                       ("\n**🛡️ Модерация**\n**🎫 Тикеты**" if is_mod else ""),
            color=COLORS["welcome"]
        )
        embed.set_footer(text="Используй кнопки для навигации")
        
        view = HelpView(ctx.author, is_mod)
        await ctx.send(embed=embed, view=view, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   FAQ
# ───────────────────────────────────────────────

@bot.hybrid_command(name="faq", description="📚 Часто задаваемые вопросы")
async def faq(ctx: commands.Context):
    try:
        embed = discord.Embed(
            title="📚 Часто задаваемые вопросы",
            description="Выберите категорию:",
            color=COLORS["faq"]
        )
        view = FAQView(ctx.author)
        await ctx.send(embed=embed, view=view, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="faqadd", description="📚 Добавить вопрос в FAQ")
@app_commands.describe(category="Категория", question="Вопрос", answer="Ответ")
@commands.has_permissions(manage_messages=True)
async def faq_add(ctx: commands.Context, category: str, question: str, *, answer: str):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        
        cat = category.lower()
        if cat not in FAQ_CATEGORIES:
            cats = ", ".join(FAQ_CATEGORIES.keys())
            return await ctx.send(f"❌ Категории: {cats}", ephemeral=True)
        
        faq_data.setdefault(cat, []).append({"question": question, "answer": answer})
        save_faq()
        
        embed = discord.Embed(
            title="✅ Вопрос добавлен",
            description=f"**Категория:** {FAQ_CATEGORIES[cat]}\n**Вопрос:** {question}",
            color=COLORS["faq"]
        )
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   РАЗВЛЕЧЕНИЯ
# ───────────────────────────────────────────────

@bot.hybrid_command(name="iq", description="Узнать свой IQ")
async def iq(ctx: commands.Context):
    try:
        random.seed(ctx.author.id + int(datetime.now().timestamp() // 86400))
        iq = random.randint(70, 130)
        if random.random() < 0.03:
            iq = random.randint(145, 165)
            title = "🧠 ГЕНИЙ!"
            color = 0xFFD700
        elif random.random() < 0.10:
            iq = random.randint(115, 144)
            title = "🌟 Умный"
            color = 0x3498DB
        else:
            title = "🧠 Твой IQ"
            color = 0x2ECC71

        embed = discord.Embed(title=title, description=f"**{ctx.author.mention}, твой IQ: {iq}**", color=color)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Обновляется каждый день")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="valute", description="Курсы валют")
async def valute(ctx: commands.Context):
    await ctx.defer(ephemeral=True)
    
    try:
        apis = [
            "https://api.exchangerate-api.com/v4/latest/USD",
            "https://open.er-api.com/v6/latest/USD",
        ]
        
        data = None
        for url in apis:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            break
            except:
                continue
        
        if not data:
            embed = discord.Embed(
                title="📈 Курсы валют",
                description="API временно недоступны",
                color=COLORS["welcome"]
            )
            embed.add_field(name="🇺🇸 USD", value="1.00", inline=True)
            embed.add_field(name="🇪🇺 EUR", value="0.92", inline=True)
            embed.add_field(name="🇷🇺 RUB", value="92.50", inline=True)
            embed.set_footer(text="Данные могут быть устаревшими")
            await ctx.send(embed=embed, ephemeral=True)
            return

        rates = data.get("rates", {})
        embed = discord.Embed(
            title="📈 Актуальные курсы (к USD)",
            color=COLORS["welcome"],
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="🇺🇸 USD", value="1.00", inline=True)
        embed.add_field(name="🇪🇺 EUR", value=f"{rates.get('EUR', 0.92):.2f}", inline=True)
        embed.add_field(name="🇬🇧 GBP", value=f"{rates.get('GBP', 0.79):.2f}", inline=True)
        embed.add_field(name="🇨🇳 CNY", value=f"{rates.get('CNY', 7.25):.2f}", inline=True)
        embed.add_field(name="🇯🇵 JPY", value=f"{rates.get('JPY', 150.0):.2f}", inline=True)
        embed.add_field(name="🇷🇺 RUB", value=f"{rates.get('RUB', 92.50):.2f}", inline=True)
        
        embed.set_footer(text="Источник: exchangerate-api")
        await ctx.send(embed=embed, ephemeral=True)

    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   МОДЕРАЦИЯ (СОКРАЩЕНО ДЛЯ КОМПАКТНОСТИ)
# ───────────────────────────────────────────────

@bot.hybrid_command(name="warn", description="Выдать предупреждение")
@app_commands.describe(member="Пользователь", reason="Причина")
@commands.has_permissions(manage_messages=True)
async def warn(ctx: commands.Context, member: discord.Member, *, reason: str = "Не указана"):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)

        if is_protected_from_automod(member):
            return await ctx.send("❌ Нельзя выдать предупреждение этому пользователю!", ephemeral=True)

        user_id = str(member.id)
        warnings_data.setdefault(user_id, []).append({
            "moderator": str(ctx.author),
            "reason": reason,
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        })
        save_warnings()
        
        count = get_warning_count(user_id)
        case_id = await create_case(member, ctx.author, "Предупреждение", reason)
        
        await send_punishment_log(
            member=member,
            punishment_type="⚠️ Предупреждение",
            duration="—",
            reason=reason,
            moderator=ctx.author,
            case_id=case_id
        )
        
        embed = discord.Embed(
            title="⚠️ Предупреждение выдано",
            description=f"**Пользователь:** {member.mention}\n**Причина:** {reason}\n**Всего:** {count}",
            color=COLORS["mod"]
        )
        await ctx.send(embed=embed, ephemeral=True)
        
        await check_auto_punishment(member, reason)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="warnings", description="Список предупреждений")
@app_commands.describe(member="Пользователь")
@commands.has_permissions(manage_messages=True)
async def warnings(ctx: commands.Context, member: discord.Member):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)

        user_id = str(member.id)
        clean_old_warnings(user_id)
        warns = warnings_data.get(user_id, [])
        
        if not warns:
            return await ctx.send(f"✅ У {member.mention} нет предупреждений.", ephemeral=True)
        
        embed = discord.Embed(
            title=f"⚠️ Предупреждения {member.display_name}",
            description=f"Всего: **{len(warns)}**",
            color=COLORS["mod"]
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        for i, w in enumerate(warns[-10:], 1):
            embed.add_field(
                name=f"{i}. {w['time']}",
                value=f"**Модератор:** {w['moderator']}\n**Причина:** {w['reason']}",
                inline=False
            )
        
        embed.set_footer(text="Последние 10")
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   НОВЫЕ КОМАНДЫ ДЛЯ TWITCH
# ───────────────────────────────────────────────

@bot.hybrid_group(name="twitch", description="📺 Управление Twitch уведомлениями")
async def twitch(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="📺 Twitch команды",
            description="Использование:\n"
                       "`/twitch add <streamer>` - добавить стримера\n"
                       "`/twitch remove <streamer>` - удалить стримера\n"
                       "`/twitch list` - список стримеров\n"
                       "`/twitch setchannel <канал>` - установить канал для уведомлений\n"
                       "`/twitch setrole <роль>` - установить роль для пинга",
            color=COLORS["twitch"]
        )
        await ctx.send(embed=embed, ephemeral=True)

@twitch.command(name="add", description="Добавить стримера для отслеживания")
@app_commands.describe(streamer="Имя стримера на Twitch", channel="Канал для уведомлений (по умолчанию текущий)")
async def twitch_add(ctx: commands.Context, streamer: str, channel: discord.TextChannel = None):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)

        if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
            embed = discord.Embed(
                title="❌ Twitch не настроен",
                description="Администратор не настроил Twitch интеграцию.\n"
                           "Необходимо добавить переменные окружения:\n"
                           "`TWITCH_CLIENT_ID` и `TWITCH_CLIENT_SECRET`",
                color=0xF04747
            )
            return await ctx.send(embed=embed, ephemeral=True)

        # Отправляем "думаю" сообщение
        await ctx.defer(ephemeral=True)
        
        streamer = streamer.lower().strip()
        channel = channel or ctx.channel
        
        # Проверяем, существует ли такой стример
        result = await check_twitch_stream(streamer)
        
        # Обрабатываем ошибки
        if result and result.get('error') == 'not_found':
            embed = discord.Embed(
                title="❌ Стример не найден",
                description=f"Стример **{streamer}** не найден на Twitch!\n\n"
                           f"**Проверьте:**\n"
                           f"• Правильно ли написано имя?\n"
                           f"• Существует ли такой канал?\n"
                           f"• Попробуйте найти канал на [twitch.tv](https://www.twitch.tv/{streamer})",
                color=0xF04747
            )
            embed.set_footer(text="Имена на Twitch чувствительны к регистру, но мы ищем без учёта регистра")
            return await ctx.send(embed=embed, ephemeral=True)
        
        if result and result.get('error') == 'network_error':
            embed = discord.Embed(
                title="❌ Ошибка сети",
                description=f"Не удалось подключиться к Twitch API. Попробуйте позже.",
                color=0xF04747
            )
            return await ctx.send(embed=embed, ephemeral=True)
        
        if not result:
            embed = discord.Embed(
                title="❌ Ошибка проверки",
                description=f"Не удалось проверить стримера **{streamer}**. Возможные причины:\n"
                           f"• Twitch API временно недоступен\n"
                           f"• Проблемы с подключением\n"
                           f"• Неверные Client ID или Secret",
                color=0xF04747
            )
            return await ctx.send(embed=embed, ephemeral=True)
        
        # Проверяем, не отслеживаем ли мы уже этого стримера
        if streamer in twitch_subs:
            old_data = twitch_subs[streamer]
            if old_data.get('guild_id') == ctx.guild.id:
                embed = discord.Embed(
                    title="⚠️ Уже отслеживается",
                    description=f"Стример **{result.get('display_name', streamer)}** уже отслеживается!\n"
                               f"Канал уведомлений: <#{old_data['channel_id']}>",
                    color=0xFAA61A
                )
                return await ctx.send(embed=embed, ephemeral=True)
            else:
                # Если стример есть в другом сервере, всё равно можем добавить для этого сервера
                pass
        
        # Сохраняем стримера
        twitch_subs[streamer] = {
            "channel_id": channel.id,
            "guild_id": ctx.guild.id,
            "added_by": ctx.author.id,
            "added_at": datetime.now(timezone.utc).timestamp(),
            "live": False,
            "display_name": result.get('display_name', streamer),
            "last_check": datetime.now(timezone.utc).timestamp()
        }
        save_twitch_subs()
        
        # Создаём красивое подтверждение
        embed = discord.Embed(
            title="✅ Стример добавлен!",
            description=f"Теперь я буду отслеживать **{result.get('display_name', streamer)}**",
            color=COLORS["twitch"]
        )
        
        # Добавляем информацию о стримере
        if result.get('profile_image'):
            embed.set_thumbnail(url=result['profile_image'])
        
        embed.add_field(name="📺 Twitch канал", value=f"[{result.get('display_name', streamer)}](https://twitch.tv/{streamer})", inline=True)
        embed.add_field(name="📢 Канал уведомлений", value=channel.mention, inline=True)
        
        # Проверяем, онлайн ли сейчас стример
        if result.get('is_live'):
            embed.add_field(
                name="🔴 Текущий статус", 
                value=f"**LIVE!**\n🎮 {result.get('game', 'Неизвестно')}\n👁️ {format_number(result.get('viewers', 0))} зрителей",
                inline=False
            )
        else:
            embed.add_field(name="⚫ Текущий статус", value="Офлайн", inline=True)
        
        embed.set_footer(text=f"Добавил: {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed, ephemeral=True)
        
        # Логируем в мод-канал
        await send_mod_log(
            title="📺 Добавлен стример",
            description=f"**Стример:** [{result.get('display_name', streamer)}](https://twitch.tv/{streamer})\n"
                       f"**Канал:** {channel.mention}\n"
                       f"**Добавил:** {ctx.author.mention}",
            color=COLORS["twitch"]
        )
        
    except Exception as e:
        print(f"❌ Ошибка в twitch_add: {e}")
        traceback.print_exc()
        
        embed = discord.Embed(
            title="❌ Непредвиденная ошибка",
            description=f"Произошла ошибка при добавлении стримера:\n```{str(e)}```",
            color=0xF04747
        )
        await ctx.send(embed=embed, ephemeral=True)

@twitch.command(name="remove", description="Удалить стримера из отслеживания")
@app_commands.describe(streamer="Имя стримера на Twitch")
async def twitch_remove(ctx: commands.Context, streamer: str):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)

        streamer = streamer.lower()
        
        if streamer not in twitch_subs:
            return await ctx.send(f"❌ Стример **{streamer}** не отслеживается!", ephemeral=True)
        
        # Проверяем, что это тот же сервер
        if twitch_subs[streamer].get('guild_id') != ctx.guild.id:
            return await ctx.send("❌ Этот стример отслеживается на другом сервере!", ephemeral=True)
        
        display_name = twitch_subs[streamer].get('display_name', streamer)
        del twitch_subs[streamer]
        save_twitch_subs()
        
        embed = discord.Embed(
            title="✅ Стример удалён",
            description=f"**{display_name}** больше не отслеживается.",
            color=COLORS["twitch"]
        )
        await ctx.send(embed=embed, ephemeral=True)
        
        await send_mod_log(
            title="📺 Удалён стример",
            description=f"**Стример:** {display_name}\n**Удалил:** {ctx.author.mention}",
            color=COLORS["twitch"]
        )
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@twitch.command(name="list", description="Список отслеживаемых стримеров")
async def twitch_list(ctx: commands.Context):
    try:
        guild_subs = {name: data for name, data in twitch_subs.items() if data.get('guild_id') == ctx.guild.id}
        
        if not guild_subs:
            return await ctx.send("📺 На этом сервере нет отслеживаемых стримеров.", ephemeral=True)
        
        embed = discord.Embed(
            title="📺 Отслеживаемые стримеры",
            color=COLORS["twitch"],
            timestamp=datetime.now(timezone.utc)
        )
        
        for streamer, data in guild_subs.items():
            channel = bot.get_channel(data.get('channel_id'))
            channel_mention = channel.mention if channel else "❌ Канал удалён"
            
            status = "🔴 **LIVE**" if data.get('live') else "⚫ Офлайн"
            
            embed.add_field(
                name=f"{data.get('display_name', streamer)}",
                value=f"**Статус:** {status}\n**Канал:** {channel_mention}\n**Добавлен:** <t:{int(data.get('added_at', 0))}:R>",
                inline=False
            )
        
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@twitch.command(name="setchannel", description="Установить канал для уведомлений о стримах")
@app_commands.describe(streamer="Имя стримера", channel="Новый канал")
async def twitch_setchannel(ctx: commands.Context, streamer: str, channel: discord.TextChannel):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)

        streamer = streamer.lower()
        
        if streamer not in twitch_subs:
            return await ctx.send(f"❌ Стример **{streamer}** не отслеживается!", ephemeral=True)
        
        if twitch_subs[streamer].get('guild_id') != ctx.guild.id:
            return await ctx.send("❌ Этот стример отслеживается на другом сервере!", ephemeral=True)
        
        twitch_subs[streamer]['channel_id'] = channel.id
        save_twitch_subs()
        
        embed = discord.Embed(
            title="✅ Канал обновлён",
            description=f"Для **{twitch_subs[streamer].get('display_name', streamer)}** установлен канал {channel.mention}",
            color=COLORS["twitch"]
        )
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@twitch.command(name="setrole", description="Установить роль для пинга при стриме")
@app_commands.describe(role="Роль для пинга (или 'none' для отключения)")
async def twitch_setrole(ctx: commands.Context, role: discord.Role = None):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)

        global TWITCH_STREAMER_ROLE_ID
        
        if role:
            TWITCH_STREAMER_ROLE_ID = role.id
            text = f"Роль {role.mention} будет пинговаться при начале стрима."
        else:
            TWITCH_STREAMER_ROLE_ID = None
            text = "Пинг роли отключён."
        
        embed = discord.Embed(
            title="✅ Настройки обновлены",
            description=text,
            color=COLORS["twitch"]
        )
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   ЭКОНОМИКА (ПРОДОЛЖЕНИЕ)
# ───────────────────────────────────────────────

@bot.hybrid_command(name="vault", description="🏦 Казна сервера")
async def vault(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Команда только на сервере разработчика.", ephemeral=True)
        if not ctx.author.guild_permissions.manage_messages and ctx.author.id != OWNER_ID:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Нет прав.", ephemeral=True)

        vault = economy_data.get("server_vault", 0)
        users = len([k for k in economy_data.keys() if k != "server_vault"])
        total = sum(v.get("balance", 0) for k, v in economy_data.items() if k != "server_vault")
        avg = total // max(users, 1)
        
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['vault']} Казна сервера",
            color=COLORS["economy"],
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="💰 Накоплено", value=f"**{format_number(vault)}** {ECONOMY_EMOJIS['coin']}", inline=False)
        embed.add_field(
            name="📊 Статистика",
            value=f"**Участников:** {users}\n**Всего монет:** {format_number(total)} {ECONOMY_EMOJIS['coin']}\n**Средний баланс:** {format_number(avg)} {ECONOMY_EMOJIS['coin']}",
            inline=False
        )
        
        embed.set_footer(text="Экономика v0.1", icon_url=bot.user.display_avatar.url)
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="balance", description="💰 Посмотреть баланс")
@app_commands.describe(member="Пользователь")
async def balance(ctx: commands.Context, member: discord.Member = None):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)

        member = member or ctx.author
        user_id = str(member.id)

        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}
            save_economy()

        tax = await apply_wealth_tax(user_id)
        bal = economy_data[user_id]["balance"]
        vault = economy_data.get("server_vault", 0)
        
        users = [(k, v.get("balance", 0)) for k, v in economy_data.items() if k != "server_vault"]
        users.sort(key=lambda x: x[1], reverse=True)
        rank = next((i for i, (uid, _) in enumerate(users, 1) if uid == user_id), len(users) + 1)

        now = datetime.now(timezone.utc).timestamp()
        last = economy_data[user_id].get("last_daily", 0)
        remaining = DAILY_COOLDOWN - (now - last)
        
        if remaining <= 0:
            daily = f"{ECONOMY_EMOJIS['gift']} **Daily доступен!**"
        else:
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            progress = (now - last) / DAILY_COOLDOWN
            bar = create_progress_bar(int(progress * 100), 100)
            daily = f"⏳ До daily: **{hours}ч {minutes}мин**\n`{bar}` **{int(progress * 100)}%**"

        embed = discord.Embed(
            title=f"{get_rank_emoji(bal)} Баланс {member.display_name}",
            color=COLORS["economy"],
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name=f"{ECONOMY_EMOJIS['balance']} Монеты", value=f"**`{format_number(bal)}`** {ECONOMY_EMOJIS['coin']}", inline=True)
        embed.add_field(name="🏆 Место", value=f"**#{rank}** из {len(users)}", inline=True)
        embed.add_field(name=f"{ECONOMY_EMOJIS['bank']} Казна", value=f"`{format_number(vault)}` {ECONOMY_EMOJIS['coin']}", inline=True)

        if tax > 0:
            embed.add_field(name=f"{ECONOMY_EMOJIS['tax']} Налог", value=f"Списано **-{format_number(tax)}** {ECONOMY_EMOJIS['coin']}", inline=False)

        embed.add_field(name=f"{ECONOMY_EMOJIS['gift']} Ежедневный бонус", value=daily, inline=False)
        
        inv = economy_data[user_id].get("investments", [])
        active = sum(1 for i in inv if i["end_time"] > now)
        if active:
            embed.add_field(name=f"{ECONOMY_EMOJIS['investment']} Инвестиции", value=f"Активно: **{active}**", inline=False)

        embed.set_footer(text=f"ID: {member.id}", icon_url=bot.user.display_avatar.url)
        await ctx.send(embed=embed, ephemeral=True)

    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="daily", description="🎁 Ежедневный бонус")
async def daily(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)

        user_id = str(ctx.author.id)
        now = datetime.now(timezone.utc).timestamp()

        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}

        last = economy_data[user_id].get("last_daily", 0)
        if now - last < DAILY_COOLDOWN:
            remaining = int(DAILY_COOLDOWN - (now - last))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            progress = (now - last) / DAILY_COOLDOWN
            bar = create_progress_bar(int(progress * 100), 100)
            
            embed = discord.Embed(
                title=f"{ECONOMY_EMOJIS['time']} Daily на кулдауне",
                description=f"Следующая через **{hours}ч {minutes}мин**",
                color=COLORS["economy"]
            )
            embed.add_field(name="Прогресс", value=f"`{bar}` **{int(progress * 100)}%**", inline=False)
            return await ctx.send(embed=embed, ephemeral=True)

        tax = await apply_wealth_tax(user_id)
        roll = random.randint(1, 100)
        
        rarity = "Обычная"
        min_c   = 15
        max_c   = 35
        color   = 0xA8A8A8
        emoji   = "🪙"
        bonus   = 0

        for r in RARITIES:
            if roll <= r[1]:
                rarity = r[0]
                min_c  = r[2]
                max_c  = r[3]
                color  = r[4]
                emoji  = r[5]
                break

        reward = random.randint(min_c, max_c)

        if last > 0:
            last_date = datetime.fromtimestamp(last, tz=timezone.utc).date()
            today_date = datetime.now(timezone.utc).date()
            if (today_date - last_date).days == 1:
                bonus = int(reward * 0.1)
                reward += bonus

        economy_data[user_id]["balance"] += reward
        economy_data[user_id]["last_daily"] = now
        save_economy()

        embed = discord.Embed(
            title=f"{emoji} {rarity} награда!",
            description=f"**+{format_number(reward)}** {ECONOMY_EMOJIS['coin']}",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        embed.add_field(
            name="📊 Детали", 
            value=f"**Редкость:** {rarity}\n**Диапазон:** {min_c}–{max_c} {ECONOMY_EMOJIS['coin']}", 
            inline=True
        )
        
        if bonus > 0:
            embed.add_field(
                name="🔥 Стрик", 
                value=f"+{format_number(bonus)} (10%)", 
                inline=True
            )

        if tax > 0:
            embed.add_field(
                name=f"{ECONOMY_EMOJIS['tax']} Налог", 
                value=f"**-{format_number(tax)}** {ECONOMY_EMOJIS['coin']}", 
                inline=False
            )

        embed.set_footer(
            text=f"Баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']}"
        )
        
        await ctx.send(embed=embed, ephemeral=True)

    except Exception as e:
        await send_error_embed(ctx, str(e))
        print(f"❌ Ошибка в daily: {e}")
        traceback.print_exc()

@bot.hybrid_command(name="top", description="🏆 Топ богачей")
async def top(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)

        users = [(uid, data.get("balance", 0)) for uid, data in economy_data.items() 
                if uid != "server_vault" and data.get("balance", 0) > 0]
        
        if not users:
            return await ctx.send(f"{ECONOMY_EMOJIS['warning']} Пока нет пользователей с монетами!", ephemeral=True)
        
        users.sort(key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['crown']} Топ богатейших",
            color=COLORS["economy"],
            timestamp=datetime.now(timezone.utc)
        )
        
        text = ""
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (uid, bal) in enumerate(users[:10], 1):
            try:
                user = await bot.fetch_user(int(uid))
                name = user.display_name
            except:
                name = f"ID: {uid}"
            
            medal = medals[i-1] if i <= 3 else f"**{i}.**"
            text += f"{medal} {get_rank_emoji(bal)} **{name}** — `{format_number(bal)}` {ECONOMY_EMOJIS['coin']}\n"
        
        embed.description = text
        
        total = sum(b for _, b in users)
        avg = total // len(users)
        embed.add_field(
            name="📊 Статистика",
            value=f"**Всего монет:** {format_number(total)} {ECONOMY_EMOJIS['coin']}\n**Участников:** {len(users)}\n**Средний баланс:** {format_number(avg)} {ECONOMY_EMOJIS['coin']}",
            inline=False
        )
        
        embed.set_footer(text=f"Показано {min(10, len(users))} из {len(users)}")
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   ЗАПУСК
# ───────────────────────────────────────────────
if __name__ == "__main__":
    bot.launch_time = datetime.now(timezone.utc)
    try:
        print("Запуск бота...")
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Неверный токен.")
    except Exception as e:
        print(f"❌ Ошибка запуска: {type(e).__name__}: {e}")
