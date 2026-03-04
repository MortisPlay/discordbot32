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
# НАСТРОЙКИ (БЕЗ ТОКЕНА!)
# ───────────────────────────────────────────────
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
WARN_AUTO_MUTE_THRESHOLD = 3 # 3 варна → мут 1ч
WARN_AUTO_LONG_MUTE_THRESHOLD = 6 # 6 варнов → мут 24ч
WARN_AUTO_KICK_THRESHOLD = 10 # 10 варнов → кик
WARN_EXPIRY_DAYS = 30 # срок действия варна
RAID_JOIN_THRESHOLD = 5 # порог рейда
RAID_TIME_WINDOW = 300 # окно в секундах (5 минут)
NEW_ACCOUNT_DAYS = 7 # возраст нового аккаунта
VIP_ROLE_NAMES = ["VIP", "Premium", "Vip", "vip"]
VIP_SPAM_MULTIPLIER = 2
VIP_MENTION_MULTIPLIER = 3
# НОВЫЕ НАСТРОЙКИ
INACTIVE_TICKET_HOURS = 24
INVESTMENT_MIN_AMOUNT = 1000
INVESTMENT_MAX_DAYS = 30
INVESTMENT_BASE_RATE = 0.05
UNAUTHORIZED_CMD_LIMIT = 3
UNAUTHORIZED_MUTE_MINUTES = 1
# ───────────────────────────────────────────────
# НОВЫЕ НАСТРОЙКИ ЭКОНОМИКИ V0.5.0
# ───────────────────────────────────────────────
VOICE_INCOME_PER_30MIN = 8 # Сколько монет за 30 минут в голосе
VOICE_MIN_SESSION_MINUTES = 10 # Минимальное время сессии
VOICE_DAILY_MAX = 300 # Максимум от войса в сутки
SUPER_DROP_CHANCE = 2 # Шанс супер-дропа в daily (%)
SUPER_DROP_MIN = 50000
SUPER_DROP_MAX = 150000
# Товары в магазине
SHOP_ITEMS = {
    "vip": {
        "name": "VIP роль на 1 месяц",
        "price": 10000,
        "duration_days": 30,
        "description": "×2 ко всем доходам • VIP-чат • ×2 за войс • Приоритет тикетов • Закрытые ивенты"
    },
    "multiplier": {
        "name": "Удвоитель ×1.5 на неделю",
        "price": 1000,
        "duration_days": 7,
        "description": "×1.5 к доходу от сообщений и daily"
    }
}
# ───────────────────────────────────────────────
# Магазин СЕЗОНА (за season_points)
# ───────────────────────────────────────────────
SEASON_SHOP_ITEMS = {
    "xp_boost_24h": {
        "name": "Удвоитель XP на 24 часа",
        "cost": 1200,               # сезонные очки
        "description": "×2 к сезонному опыту на сутки",
        "type": "boost",
        "duration_hours": 24
    },
    "vip_3d": {
        "name": "VIP на 3 дня",
        "cost": 2500,
        "description": "Временная VIP-роль на 3 дня",
        "type": "role",
        "role_name": "VIP",
        "duration_days": 3
    },
    "premium_pass": {
        "name": "Premium Pass",
        "cost": 5000,
        "description": "Активация Premium Track сезона",
        "type": "pass"
    },
    "coins_5000": {
        "name": "5000 MortisCoin",
        "cost": 3000,
        "description": "Прямой перевод в основную валюту",
        "type": "coins",
        "amount": 5000
    }
}
# НАСТРОЙКИ ДЛЯ FAQ
FAQ_FILE = "faq.json"
FAQ_CATEGORIES = {
    "общее": "📋 Общие вопросы",
    "правила": "📜 Правила",
    "экономика": "💰 Экономика",
    "модерация": "🛡️ Модерация",
    "техника": "🔧 Технические вопросы"
}
# НОВОЕ ОФОРМЛЕНИЕ ДЛЯ ЭКОНОМИКИ
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
    "calendar": "📅"
}
RARITIES = [
    ("Обычная", 70, 15, 35, 0xA8A8A8, "🪙"),
    ("Редкая", 20, 50, 70, 0x3498DB, "💎"),
    ("Эпическая", 9, 200, 350, 0x9B59B6, "🌟"),
    ("Легендарная", 1, 500,1000, 0xF1C40F, "🔥")
]

LEVEL_EMOJIS = {
    1: "🥚",      # новичок
    2: "🪶",      # начинающий
    5: "🔥",      # разогрелся
    10: "⚡",     # заряжен
    15: "🌟",     # звезда
    20: "👑",     # король сезона
    30: "💫",     # легенда
    35: "🪐",     # бог сезона
}

# Если уровня нет в словаре — берём ближайший меньший
def get_level_emoji(level: int) -> str:
    for lvl in sorted(LEVEL_EMOJIS.keys(), reverse=True):
        if level >= lvl:
            return LEVEL_EMOJIS[lvl]
    return "🥚"  # дефолт

BAD_WORDS = [
    "пидор", "пидорас", "пидрила", "пидр", "гей", "хуесос", "ебанат", "дебил", "идиот",
    "тупой", "чмо", "чмошник", "сука", "блядь", "еблан", "мудак", "тварь", "урод"
]
INSULT_PATTERNS = [
    r"\b(ты|тебе|тобой)\s*(пидор|дебил|идиот|тупой|чмо|хуесос|ебанат)\b",
    r"\b(иди|пошёл|пиздец)\s*(нахуй|в пизду|в жопу)\b",
    r"\b(заткнись|заткнулся|молчи)\s*(сука|блядь|ебанат)\b"
]
# ЦВЕТА ДЛЯ ОФОРМЛЕНИЯ
COLORS = {
    "welcome": 0x57F287, # Зеленый
    "goodbye": 0xF04747, # Красный
    "audit": 0x5865F2, # Синий
    "mod": 0xFAA61A, # Оранжевый
    "economy": 0xFFD700, # Золотой
    "ticket": 0x9B59B6, # Фиолетовый
    "faq": 0x3498DB # Голубой
}
# Остальной код БЕЗ ИЗМЕНЕНИЙ - вся логика бота остается той же
# Просто удалите старую строку с TOKEN и вставьте весь ваш код сюда
# (весь код после настроек до запуска)
# ───────────────────────────────────────────────
# РОЛЬ ДЛЯ ТЕСТИРОВАНИЯ НОВЫХ ФИЧ
# ───────────────────────────────────────────────
TESTER_ROLE_ID = 1478006121657794715
def is_tester(member: discord.Member) -> bool:
    """Проверяет, есть ли у участника роль Тестировщик"""
    if not member:
        return False
    return any(role.id == TESTER_ROLE_ID for role in member.roles)
# ───────────────────────────────────────────────
# ДЕКОРАТОР ДЛЯ КОМАНД ТОЛЬКО ДЛЯ ТЕСТИРОВЩИКОВ
# ───────────────────────────────────────────────
from functools import wraps
def tester_only(func):
    @wraps(func)
    async def wrapper(ctx: commands.Context, *args, **kwargs):
        if not is_tester(ctx.author):
            embed = discord.Embed(
                title="🔒 Доступ ограничен",
                description=(
                    "Эта команда пока доступна **только участникам с ролью Тестировщик**.\n\n"
                    "Хочешь участвовать в тестировании новых фич? "
                    "Напиши администратору или в канал для тестеров."
                ),
                color=0xE74C3C # красный для акцента
            )
            embed.set_footer(text="Тестирование • MortisPlay")
            await ctx.send(embed=embed, ephemeral=True)
            return
       
        return await func(ctx, *args, **kwargs)
    return wrapper
# ───────────────────────────────────────────────
# ГЛОБАЛЬНЫЕ ДАННЫЕ
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
# ───────────────────────────────────────────────
# СЕЗОННЫЕ ДАННЫЕ
# ───────────────────────────────────────────────
SEASONS_FILE = "seasons.json"
season_data = {} # {user_id: {"season_xp": 0, "season_level": 1, "season_points": 0, "claimed_rewards": []}}
daily_season_xp_earned = {} # {user_id: сколько XP начислено сегодня}
daily_season_xp_reset = {} # {user_id: дата последнего сброса}
current_season = {
    "id": "season_10",
    "name": "Восстание из мертвых",
    "start_date": "2025-12-01",
    "end_date": "2026-03-01",
    "xp_per_message": 3,
    "xp_per_voice_minute": 2,
    "daily_xp_bonus": 150,
    "max_daily_xp": 1000,
    "rewards": {
        "5": {"name": "Редкий значок", "type": "cosmetic", "cost": 500},
        "10": {"name": "Сезонная рамка", "type": "cosmetic", "cost": 1200},
        "20": {"name": "×1.2 буст на неделю", "type": "boost", "cost": 2500},
        "35": {"name": "Эксклюзивная роль 'Season Pioneer'", "type": "role", "cost": 4500, "role_id": None}
    }
}
# ───────────────────────────────────────────────
# ЕЖЕДНЕВНЫЕ ЗАДАНИЯ (простая реализация)
# ───────────────────────────────────────────────
DAILY_TASKS = {
    "messages": {
        "goal": 50,
        "xp": 200,
        "desc": "Отправить 50 сообщений"
    },
    "voice": {
        "goal": 30,           # минут в голосе
        "xp": 300,
        "desc": "Провести 30 минут в голосе"
    },
    "daily": {
        "goal": 1,
        "xp": 100,
        "desc": "Использовать команду /daily"
    }
}

# Прогресс заданий за текущий день
# Формат: {user_id: {"messages": 12, "voice": 45, "daily": 1, "date": "2026-03-03"}}
daily_tasks_progress = {}

def load_seasons():
    global season_data
    if os.path.exists(SEASONS_FILE):
        try:
            with open(SEASONS_FILE, "r", encoding="utf-8") as f:
                season_data = json.load(f)
            print(f"[SEASONS] Загружено {len(season_data)} участников")
        except Exception as e:
            print(f"Ошибка загрузки seasons.json: {e}")
            season_data = {}
    else:
        season_data = {}
        print("[SEASONS] Файл не найден → создан пустой")
def save_seasons():
    with open(SEASONS_FILE, "w", encoding="utf-8") as f:
        json.dump(season_data, f, ensure_ascii=False, indent=2)
# Загружаем при старте
load_seasons()

# ───────────────────────────────────────────────
# ЕЖЕДНЕВНЫЕ ЗАДАНИЯ — сохранение и загрузка
# ───────────────────────────────────────────────
DAILY_TASKS_FILE = "daily_tasks.json"

def load_daily_tasks():
    global daily_tasks_progress
    if os.path.exists(DAILY_TASKS_FILE):
        try:
            with open(DAILY_TASKS_FILE, "r", encoding="utf-8") as f:
                daily_tasks_progress = json.load(f)
            print(f"[DAILY TASKS] Загружено {len(daily_tasks_progress)} прогрессов заданий")
        except Exception as e:
            print(f"Ошибка загрузки daily_tasks.json: {e}")
            daily_tasks_progress = {}
    else:
        daily_tasks_progress = {}
        print("[DAILY TASKS] Файл не найден → создан пустой")

def save_daily_tasks():
    with open(DAILY_TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(daily_tasks_progress, f, ensure_ascii=False, indent=2)

# Загружаем при старте
load_daily_tasks()
# Для античита голосового дохода
voice_start_time = {} # {user_id: timestamp}
daily_voice_earned = {} # {user_id: сумма сегодня}
daily_voice_reset = {} # {user_id: дата последнего ресета}
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
   
    # ─── Инициализация новых полей для всех пользователей ───
    for user_id in list(economy_data.keys()):
        if user_id == "server_vault":
            continue
            
        user_data = economy_data[user_id]
        
        # Старые поля (на всякий случай)
        user_data.setdefault("balance", 0)
        user_data.setdefault("last_daily", 0)
        user_data.setdefault("last_message", 0)
        user_data.setdefault("investments", [])
        
        # Новые поля для сезона и Premium Pass
        user_data.setdefault("season_points", 0)
        user_data.setdefault("season_purchases", [])
        user_data.setdefault("premium_track_active", False)   # ← вот наш новый флаг
        
        # Если investments нет — создаём пустой список
        if "investments" not in user_data:
            user_data["investments"] = []
    
    print("[ECONOMY] Данные загружены и поля инициализированы")
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
load_economy()
load_faq()
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
# ФУНКЦИИ ДЛЯ ПРОВЕРКИ ПРАВ
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
def can_punish(executor: discord.Member, target: discord.Member) -> bool:
    """Строгая защита: можно ли executor наказывать target"""
    if not executor or not target:
        return False
    if executor.id == target.id: # себя
        return False
    if target.id == OWNER_ID: # владельца бота
        return False
    if target == target.guild.owner: # владельца сервера
        return False
    if target.guild_permissions.administrator: # любого администратора
        return False
    # Защита по иерархии ролей (кроме OWNER_ID)
    if target.top_role >= executor.top_role and executor.id != OWNER_ID:
        return False
    return True
# ───────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
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
# КЛАССЫ ДЛЯ UI
# ───────────────────────────────────────────────
class ModActionView(View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=180)
        self.member = member
    @discord.ui.button(label="Предупредить", style=discord.ButtonStyle.secondary, emoji="⚠️")
    async def warn_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not can_punish(interaction.user, self.member):
            return await interaction.response.send_message(
                "❌ Нельзя наказывать владельца сервера, администраторов или самого себя!",
                ephemeral=True
            )
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
       
        modal = WarnModal(self.member)
        await interaction.response.send_modal(modal)
    @discord.ui.button(label="Замутить", style=discord.ButtonStyle.danger, emoji="🔇")
    async def mute_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not can_punish(interaction.user, self.member):
            return await interaction.response.send_message(
                "❌ Нельзя наказывать владельца сервера, администраторов или самого себя!",
                ephemeral=True
            )
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
            `/investments` - мои инвестиции""",
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
                # Проверяем последнее сообщение
                async for msg in channel.history(limit=1):
                    last_msg_time = msg.created_at
                    now = datetime.now(timezone.utc)
                   
                    if (now - last_msg_time).total_seconds() > INACTIVE_TICKET_HOURS * 3600:
                        # Отправляем предупреждение
                        warning_embed = discord.Embed(
                            title="⚠️ Тикет неактивен",
                            description=f"Этот тикет будет автоматически закрыт через 12 часов из-за неактивности.",
                            color=0xFAA61A
                        )
                        await channel.send(embed=warning_embed)
                       
                        # Ждем 12 часов
                        await asyncio.sleep(43200) # 12 часов
                       
                        # Проверяем снова
                        async for new_msg in channel.history(limit=1):
                            if new_msg.id == msg.id:
                                # Все еще нет новых сообщений - закрываем
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
        base = "**📋 Основное**\n**💰 Экономика**\n**🎮 Развлечения**"
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
# Магазин с кнопками, подтверждением, проверкой "уже куплено" и обновлением баланса
# ───────────────────────────────────────────────
class ShopConfirmModal(Modal, title="Подтверждение покупки"):
    def __init__(self, item_key: str, item_name: str, price: int, final_price: int):
        super().__init__()
        self.item_key = item_key
        self.item_name = item_name
        self.price = price
        self.final_price = final_price
        self.add_item(TextInput(
            label="Подтвердите покупку",
            placeholder=f"Напишите 'подтверждаю' для покупки {item_name}",
            style=discord.TextStyle.short,
            required=True
        ))
    async def on_submit(self, interaction: discord.Interaction):
        if self.children[0].value.lower().strip() != "подтверждаю":
            return await interaction.response.send_message("❌ Покупка отменена. Нужно написать 'подтверждаю'.", ephemeral=True)
        user_id = str(interaction.user.id)
        shop_item = SHOP_ITEMS[self.item_key]
        # Финальная проверка баланса (на случай race-condition)
        if user_id not in economy_data or economy_data[user_id].get("balance", 0) < self.final_price:
            return await interaction.response.send_message(
                f"{ECONOMY_EMOJIS['error']} Недостаточно монет! Требуется {format_number(self.final_price)}", ephemeral=True
            )
        # Списание
        economy_data[user_id]["balance"] -= self.final_price
        save_economy()
        # Выдача товара
        if self.item_key == "vip":
            role = discord.utils.get(interaction.guild.roles, name="VIP")
            if role:
                await interaction.user.add_roles(role)
                temp_roles.setdefault(user_id, {})[str(role.id)] = datetime.now(timezone.utc).timestamp() + (shop_item["duration_days"] * 86400)
                msg = f"{ECONOMY_EMOJIS['success']} **VIP** на 1 месяц куплен! 🎉\n×2 доход • VIP-чат • ×2 войс • приоритет"
            else:
                msg = f"{ECONOMY_EMOJIS['error']} Роль VIP не найдена! Монеты списаны, но роль не выдана."
        elif self.item_key == "multiplier":
            if "multiplier_end" not in economy_data[user_id]:
                economy_data[user_id]["multiplier_end"] = 0
            economy_data[user_id]["multiplier_end"] = datetime.now(timezone.utc).timestamp() + (shop_item["duration_days"] * 86400)
            save_economy()
            msg = f"{ECONOMY_EMOJIS['success']} Удвоитель ×1.5 активирован на 7 дней! 🚀"
        await interaction.response.send_message(msg, ephemeral=True)
        # Лог
        await send_mod_log(
            title="🛒 Покупка в магазине",
            description=f"**Пользователь:** {interaction.user.mention}\n**Товар:** {self.item_name}\n**Цена:** {format_number(self.final_price)}",
            color=COLORS["economy"]
        )
class SeasonConfirmModal(Modal, title="Подтверждение покупки"):
    def __init__(self, item_key: str, item_name: str, price: int):
        super().__init__()
        self.item_key = item_key
        self.item_name = item_name
        self.price = price
        self.add_item(TextInput(
            label="Подтвердите покупку",
            placeholder=f"Напишите 'подтверждаю' для покупки {item_name}",
            style=discord.TextStyle.short,
            required=True
        ))

    async def on_submit(self, interaction: discord.Interaction):
        if self.children[0].value.lower().strip() != "подтверждаю":
            return await interaction.response.send_message("❌ Покупка отменена.", ephemeral=True)

        user_id = str(interaction.user.id)
        item = SEASON_SHOP_ITEMS[self.item_key]

        # Финальная проверка баланса сезонных очков
        if economy_data[user_id]["season_points"] < self.price:
            return await interaction.response.send_message(
                f"{ECONOMY_EMOJIS['error']} Недостаточно очков! (изменилось за время ожидания)",
                ephemeral=True
            )

        # Списание очков
        economy_data[user_id]["season_points"] -= self.price
        economy_data[user_id].setdefault("season_purchases", []).append(self.item_key)

        # ─── Выдача награды в зависимости от типа ───
        msg = ""
        if item["type"] == "coins":
            economy_data[user_id]["balance"] += item["amount"]
            msg = f"✅ Получено **+{format_number(item['amount'])}** MortisCoin!"
            save_economy()

        elif item["type"] == "boost":
            # Пока заглушка — можно потом добавить поле xp_boost_end
            msg = f"✅ **{item['name']}** активирован на 24 часа!"

        elif item["type"] == "role":
            role = discord.utils.get(interaction.guild.roles, name=item["role_name"])
            if role:
                await interaction.user.add_roles(role)
                # Временная роль
                temp_roles.setdefault(user_id, {})[str(role.id)] = (
                    datetime.now(timezone.utc).timestamp() + (item["duration_days"] * 86400)
                )
                msg = f"✅ Роль **{role.name}** выдана на {item['duration_days']} дня!"
            else:
                msg = f"{ECONOMY_EMOJIS['error']} Роль {item['role_name']} не найдена!"

        elif item["type"] == "pass":
            # ─── АКТИВАЦИЯ PREMIUM PASS ───
            economy_data[user_id]["premium_track_active"] = True
            economy_data[user_id]["season_points"] += 500  # +500 очков сразу
            save_economy()

            msg = (
                "✨ **Premium Pass успешно активирован!**\n\n"
                f"Тебе мгновенно начислено **+500** сезонных очков!\n"
                "Теперь ты получаешь:\n"
                "• **+50% к сезонному опыту** (все источники)\n"
                "• **+200 MortisCoin** к ежедневному бонусу\n"
                "• Эксклюзивные награды на уровнях\n"
                "• Роль **Season Pass Holder** при достижении 30 уровня"
            )

        await interaction.response.send_message(msg, ephemeral=True)

        # Лог покупки в мод-канал
        await send_mod_log(
            title="🛒 Покупка в магазине сезона",
            description=f"**{interaction.user.mention}** купил **{self.item_name}** за {format_number(self.price)} сезонных очков",
            color=COLORS["economy"]
        )

        # Лог покупки
        await send_mod_log(
            title="🛒 Покупка в магазине сезона",
            description=f"**Пользователь:** {interaction.user.mention}\n**Товар:** {self.item_name}\n**Цена:** {format_number(self.price)} сезонных очков",
            color=COLORS["economy"]
        )

class ShopView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=300) # 5 минут
        self.author_id = author_id
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
            return False
        return True
    @discord.ui.button(label="Обновить баланс", style=discord.ButtonStyle.grey, emoji="🔄", row=1)
    async def refresh_balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        balance = economy_data.get(user_id, {}).get("balance", 0)
        await interaction.response.send_message(
            f"💰 Ваш текущий баланс: **{format_number(balance)}** {ECONOMY_EMOJIS['coin']}",
            ephemeral=True
        )
    @discord.ui.button(label="Купить VIP", style=discord.ButtonStyle.green, emoji="💎", custom_id="shop_vip", row=0)
    async def buy_vip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_button(interaction, "vip")
    @discord.ui.button(label="Купить ×1.5", style=discord.ButtonStyle.blurple, emoji="🚀", custom_id="shop_multiplier", row=0)
    async def buy_multiplier(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_button(interaction, "multiplier")
    async def _handle_button(self, interaction: discord.Interaction, item_key: str):
        shop_item = SHOP_ITEMS[item_key]
        user_id = str(interaction.user.id)
        balance = economy_data.get(user_id, {}).get("balance", 0)
        # Проверка "уже куплено"
        already_owned = False
        if item_key == "vip":
            role = discord.utils.get(interaction.guild.roles, name="VIP")
            already_owned = role in interaction.user.roles if role else False
        elif item_key == "multiplier":
            if "multiplier_end" in economy_data.get(user_id, {}):
                end = economy_data[user_id]["multiplier_end"]
                already_owned = end > datetime.now(timezone.utc).timestamp()
        if already_owned:
            return await interaction.response.send_message(
                f"{ECONOMY_EMOJIS['warning']} У вас уже есть **{shop_item['name']}**!", ephemeral=True
            )
        # Цена (пока без скидок, потом добавим)
        price = shop_item["price"]
        if balance < price:
            return await interaction.response.send_message(
                f"{ECONOMY_EMOJIS['error']} Недостаточно монет! Нужно {format_number(price)}, у вас {format_number(balance)}",
                ephemeral=True
            )
        # Модалка подтверждения
        modal = ShopConfirmModal(item_key, shop_item["name"], price, price)
        await interaction.response.send_modal(modal)

class SeasonShopView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=300)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="Обновить баланс", style=discord.ButtonStyle.grey, emoji="🔄", row=1)
    async def refresh_balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        points = economy_data.get(user_id, {}).get("season_points", 0)
        await interaction.response.send_message(
            f"🌟 Текущий баланс сезонных очков: **{format_number(points)}**",
            ephemeral=True
        )

    @discord.ui.button(label="Удвоитель XP 24ч", style=discord.ButtonStyle.green, row=0)
    async def buy_xp_boost(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._buy_item(interaction, "xp_boost_24h")

    @discord.ui.button(label="VIP на 3 дня", style=discord.ButtonStyle.green, row=0)
    async def buy_vip_3d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._buy_item(interaction, "vip_3d")

    @discord.ui.button(label="Premium Pass", style=discord.ButtonStyle.blurple, row=0)
    async def buy_premium_pass(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._buy_item(interaction, "premium_pass")

    @discord.ui.button(label="5000 MortisCoin", style=discord.ButtonStyle.green, row=0)
    async def buy_coins_5000(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._buy_item(interaction, "coins_5000")

    async def _buy_item(self, interaction: discord.Interaction, item_key: str):
        item = SEASON_SHOP_ITEMS[item_key]
        user_id = str(interaction.user.id)
        points = economy_data[user_id]["season_points"]

        if item_key in economy_data[user_id]["season_purchases"]:
            return await interaction.response.send_message(
                f"{ECONOMY_EMOJIS['warning']} Ты уже купил **{item['name']}**!",
                ephemeral=True
            )

        if points < item["cost"]:
            return await interaction.response.send_message(
                f"{ECONOMY_EMOJIS['error']} Недостаточно очков! Нужно {format_number(item['cost'])}, у тебя {format_number(points)}",
                ephemeral=True
            )

        modal = SeasonConfirmModal(item_key, item["name"], item["cost"])
        await interaction.response.send_modal(modal)


class SeasonConfirmModal(Modal, title="Подтверждение покупки"):
    def __init__(self, item_key: str, item_name: str, price: int):
        super().__init__()
        self.item_key = item_key
        self.item_name = item_name
        self.price = price
        self.add_item(TextInput(
            label="Подтвердите покупку",
            placeholder="Напишите 'подтверждаю'",
            style=discord.TextStyle.short,
            required=True
        ))

    async def on_submit(self, interaction: discord.Interaction):
        if self.children[0].value.lower().strip() != "подтверждаю":
            return await interaction.response.send_message("❌ Покупка отменена.", ephemeral=True)

        user_id = str(interaction.user.id)
        item = SEASON_SHOP_ITEMS[self.item_key]

        # Финальная проверка
        if economy_data[user_id]["season_points"] < self.price:
            return await interaction.response.send_message(
                f"{ECONOMY_EMOJIS['error']} Недостаточно очков (изменилось)!",
                ephemeral=True
            )

        # Списание
        economy_data[user_id]["season_points"] -= self.price
        economy_data[user_id]["season_purchases"].append(self.item_key)
        save_economy()

        # Выдача
        msg = ""
        if item["type"] == "coins":
            economy_data[user_id]["balance"] += item["amount"]
            save_economy()
            msg = f"✅ +{format_number(item['amount'])} MortisCoin зачислено!"

        elif item["type"] == "role":
            role = discord.utils.get(interaction.guild.roles, name=item["role_name"])
            if role:
                await interaction.user.add_roles(role)
                temp_roles.setdefault(user_id, {})[str(role.id)] = (
                    datetime.now(timezone.utc).timestamp() + item["duration_days"] * 86400
                )
                msg = f"✅ Роль **{role.name}** выдана на {item['duration_days']} дня!"
            else:
                msg = f"{ECONOMY_EMOJIS['error']} Роль не найдена!"

        elif item["type"] == "boost":
            # Пока заглушка — можно добавить поле xp_boost_end
            msg = f"✅ **{item['name']}** активирован!"

        elif item["type"] == "pass":
            # Пока заглушка
            msg = "✅ Premium Pass активирован! (в разработке)"

        await interaction.response.send_message(msg, ephemeral=True)

        # Лог
        await send_mod_log(
            title="🛒 Покупка в магазине сезона",
            description=f"**{interaction.user.mention}** купил **{self.item_name}** за {format_number(self.price)} сезонных очков",
            color=COLORS["economy"]
        )        
# ───────────────────────────────────────────────
# ИНИЦИАЛИЗАЦИЯ БОТА
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
async def check_and_level_up(user_id: str, member: discord.Member = None):
    """
    Проверяет, достиг ли пользователь нового уровня в сезоне.
    Если да — повышает уровень, выдаёт награды, сохраняет данные и отправляет уведомления.
    """
    if user_id not in season_data:
        return

    player = season_data[user_id]
    current_xp = player["season_xp"]
    old_level = player["season_level"]

    # Вычисляем актуальный уровень
    new_level = 1
    while get_xp_for_level(new_level + 1) <= current_xp:
        new_level += 1

    # Если уровень не вырос — выходим
    if new_level <= old_level:
        return

    # Уровень повышен
    player["season_level"] = new_level

    # ─── Выдача наград за все новые уровни ───
    claimed = player.setdefault("claimed_rewards", [])  # список строковых ID уровней

    for lvl in range(old_level + 1, new_level + 1):
        lvl_str = str(lvl)  # для claimed_rewards храним как строки

        # Проверяем, есть ли награда для этого уровня (ключ — int!)
        if lvl in current_season["rewards"]:
            reward = current_season["rewards"][lvl]

            # Помечаем награду как полученную (в claimed храним строки)
            if lvl_str not in claimed:
                claimed.append(lvl_str)

            # Выдаём награду в зависимости от типа
            if reward["type"] == "role" and "role_id" in reward and reward["role_id"]:
                try:
                    # member может быть передан из события, но если нет — ищем по ID
                    if not member:
                        guild = bot.get_guild(FULL_ACCESS_GUILD_ID)
                        if guild:
                            member = guild.get_member(int(user_id))

                    if member:
                        role = member.guild.get_role(int(reward["role_id"]))
                        if role:
                            await member.add_roles(role, reason=f"Сезонная награда — уровень {lvl}")

                            # Уведомление в ЛС
                            try:
                                embed_role = discord.Embed(
                                    title="🎉 Новая роль получена!",
                                    description=(
                                        f"Ты достиг **уровня {lvl}** в сезоне **{current_season['name']}**!\n"
                                        f"Получена роль: **{role.name}**"
                                    ),
                                    color=0xFFD700,
                                    timestamp=datetime.now(timezone.utc)
                                )
                                embed_role.set_thumbnail(url=member.display_avatar.url)
                                embed_role.set_footer(text="MortisPlay • Сезон")
                                await member.send(embed=embed_role)
                            except discord.Forbidden:
                                pass  # ЛС закрыты
                            except Exception as e:
                                print(f"[LEVEL-REWARD DM] Ошибка отправки ЛС роли {lvl}: {e}")

                except Exception as e:
                    print(f"Ошибка выдачи роли уровня {lvl} для {user_id}: {e}")

            elif reward["type"] == "boost":
                # Заглушка — можно добавить логику буста позже
                pass

            elif reward["type"] == "cosmetic":
                try:
                    user = bot.get_user(int(user_id))
                    if not user:
                        user = await bot.fetch_user(int(user_id))

                    embed_cos = discord.Embed(
                        title="✨ Косметическая награда!",
                        description=(
                            f"Уровень {lvl}: **{reward['name']}** получен!\n"
                            f"Поздравляем в сезоне **{current_season['name']}**!"
                        ),
                        color=0x9B59B6,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed_cos.set_thumbnail(url=user.display_avatar.url)
                    await user.send(embed=embed_cos)
                except Exception as e:
                    print(f"[COSMETIC DM] Ошибка для {user_id} уровня {lvl}: {e}")

    # ─── Сохраняем изменения ───
    save_seasons()

    # ─── ЛС уведомление о новом уровне ───
    try:
        user = bot.get_user(int(user_id))
        if not user:
            user = await bot.fetch_user(int(user_id))

        embed_level = discord.Embed(
            title="🌟 Уровень повышен!",
            description=(
                f"Поздравляю! Ты достиг **уровня {new_level}** в сезоне **{current_season['name']}**!\n"
                "Проверь награды в `/season info` или в магазине сезона!"
            ),
            color=0xFFD700,
            timestamp=datetime.now(timezone.utc)
        )
        embed_level.add_field(
            name="Текущий опыт",
            value=f"{format_number(current_xp):,} XP",
            inline=True
        )
        embed_level.add_field(
            name="До следующего",
            value=f"{format_number(get_xp_for_level(new_level + 1) - current_xp):,} XP",
            inline=True
        )
        embed_level.set_thumbnail(url=user.display_avatar.url)
        embed_level.set_footer(text="MortisPlay • Сезон")
        await user.send(embed=embed_level)

    except discord.Forbidden:
        print(f"[LEVEL-UP DM] Пользователь {user_id} закрыл ЛС")
    except Exception as e:
        print(f"[LEVEL-UP DM] Ошибка для {user_id}: {type(e).__name__}: {e}")

    # ─── Публичное объявление (если есть member) ───
    if member and member.guild:
        try:
            channel = (
                member.guild.system_channel or
                bot.get_channel(WELCOME_CHANNEL_ID) or
                member.guild.text_channels[0]  # запасной вариант
            )
            if channel:
                await channel.send(
                    f"🎉 {member.mention} только что достиг **уровня {new_level}** в сезоне **{current_season['name']}**! 🚀"
                )
        except Exception as e:
            print(f"[LEVEL-UP announce] Ошибка для {user_id}: {e}")
# ───────────────────────────────────────────────
# ФОНОВЫЕ ЗАДАЧИ
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
@tasks.loop(minutes=30)
async def voice_income_task():
    now = datetime.now(timezone.utc).timestamp()
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            if "afk" in vc.name.lower():
                continue
           
            # Считаем активных участников заранее (не боты, не заглушенные)
            active_members = [
                m for m in vc.members
                if not m.bot
                and not (m.voice.mute or m.voice.self_mute or m.voice.self_deaf or m.voice.deaf)
            ]
           
            # Если меньше 2 активных — доход никому не идёт
            if len(active_members) < 2:
                continue
           
            for member in active_members:
                user_id = str(member.id)
                if user_id not in economy_data:
                    continue
               
                # Античит: минимальное время сессии
                if user_id in voice_start_time:
                    minutes_in_voice = (now - voice_start_time[user_id]) / 60
                    if minutes_in_voice < VOICE_MIN_SESSION_MINUTES:
                        continue
                   
                    # Начисляем
                    earn = VOICE_INCOME_PER_30MIN
                    if is_vip(member):
                        earn = int(earn * 2) # VIP получает ×2
                   
                    # Дневной лимит
                    if user_id not in daily_voice_earned:
                        daily_voice_earned[user_id] = 0
                   
                    if daily_voice_earned[user_id] + earn > VOICE_DAILY_MAX:
                        remaining = VOICE_DAILY_MAX - daily_voice_earned[user_id]
                        if remaining <= 0:
                            # Уведомляем только если лимит только что достигнут
                            if daily_voice_earned[user_id] < VOICE_DAILY_MAX:
                                try:
                                    user = bot.get_user(int(user_id))
                                    if user:
                                        await user.send(
                                            embed=discord.Embed(
                                                title="🎤 Дневной лимит войса достигнут!",
                                                description=(
                                                    f"Сегодня вы заработали максимум **{VOICE_DAILY_MAX}** монет "
                                                    f"в голосовых каналах.\nЗавтра в 00:00 UTC лимит обновится — "
                                                    f"возвращайтесь! 🚀"
                                                ),
                                                color=0xF1C40F,
                                                timestamp=datetime.now(timezone.utc)
                                            ).set_footer(text="MortisPlay • Экономика")
                                        )
                                except:
                                    pass # ЛС закрыты или ошибка — пропускаем
                            continue
                        earn = remaining
                   
                    # Начисляем
                    economy_data[user_id]["balance"] += earn
                    daily_voice_earned[user_id] += earn
                   
                    # Сохраняем сразу после начисления
                    save_economy()
@tasks.loop(minutes=5) # каждые 5 минут проверяем и начисляем XP
async def voice_season_xp_task():
    now = datetime.now(timezone.utc).timestamp()
   
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            if "afk" in vc.name.lower():
                continue
            active_members = [
                m for m in vc.members
                if not m.bot
                and not (m.voice.mute or m.voice.self_mute or m.voice.self_deaf or m.voice.deaf)
            ]
            if len(active_members) < 2:
                continue
            for member in active_members:
                user_id = str(member.id)
               
                # Пропускаем, если не заходил в голос (нет таймера)
                if user_id not in voice_start_time:
                    continue
                # Сколько минут прошло с последнего входа
                minutes_in_voice = (now - voice_start_time[user_id]) / 60
               
                # Начисляем только за полные минуты
                if minutes_in_voice < 1:
                    continue
                # Базовое значение XP за минуту
                xp_per_min = current_season["xp_per_voice_minute"]
                if is_vip(member):
                    xp_per_min *= 2 # VIP получает ×2
                # За 5 минут начисляем примерно это количество
                xp_to_add = int(xp_per_min * 5)
                # Проверка дневного лимита сезонного XP
                today_str = datetime.now(timezone.utc).date().isoformat()
                if user_id not in daily_season_xp_reset or daily_season_xp_reset[user_id] != today_str:
                    daily_season_xp_earned[user_id] = 0
                    daily_season_xp_reset[user_id] = today_str
                remaining_xp = current_season["max_daily_xp"] - daily_season_xp_earned.get(user_id, 0)
                if xp_to_add > remaining_xp:
                    xp_to_add = max(0, remaining_xp)
                if xp_to_add > 0:
                    # Начисляем
                    season_data[user_id]["season_xp"] += xp_to_add
                    await check_and_level_up(user_id, member)
                    daily_season_xp_earned[user_id] += xp_to_add
                                        # Прогресс голосового задания
                    prog = daily_tasks_progress.setdefault(user_id, {
                        "messages": 0, "voice": 0, "daily": 0, "date": today_str
                    })
                    if prog["date"] != today_str:
                        prog.update({"messages": 0, "voice": 0, "daily": 0, "date": today_str})
                        daily_tasks_progress[user_id] = prog

                    prog["voice"] += 5  # начисляем за каждые 5 минут
                    if prog["voice"] >= DAILY_TASKS["voice"]["goal"]:
                        extra_xp = DAILY_TASKS["voice"]["xp"]
                        season_data[user_id]["season_xp"] += extra_xp
                        await check_and_level_up(user_id, member)
                        try:
                            await member.send(
                                f"✓ Выполнено задание **{DAILY_TASKS['voice']['desc']}** → +{extra_xp} XP!"
                            )
                        except:
                            pass
                   
                    # Сохраняем
                    save_seasons()
                    save_daily_tasks()
                    # Опционально: уведомление каждые 500 XP за сессию
                    if xp_to_add >= 500:
                        try:
                            await member.send(
                                embed=discord.Embed(
                                    title="🌟 Сезонный прогресс!",
                                    description=f"Ты получил **+{xp_to_add}** сезонного XP за голосовой онлайн!\n"
                                                f"Сегодня уже: **{daily_season_xp_earned[user_id]:,} / {current_season['max_daily_xp']:,}** XP",
                                    color=0x9B59B6,
                                    timestamp=datetime.now(timezone.utc)
                                ).set_footer(text="MortisPlay • Сезон")
                            )
                        except:
                            pass # ЛС закрыты — ничего страшного
# ───────────────────────────────────────────────
# СОБЫТИЯ
# ───────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"┌──────────────────────────────────────────────┐")
    print(f"│ Залогинен как {bot.user} │")
    print(f"│ ID {bot.user.id} │")
    print(f"│ Время запуска {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} │")
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
    autosave_economy_task.start()
    clean_old_warnings_task.start()
    check_temp_roles_task.start()
    check_investments_task.start()
    check_inactive_tickets_task.start()
   
    voice_income_task.start()
    voice_season_xp_task.start()
    autosave_seasons_task.start()
    bot.launch_time = datetime.now(timezone.utc)
    print("Бот полностью готов к работе")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    now = datetime.now(timezone.utc).timestamp()

    # ====================== АНТИ-СПАМ, ТОКСИЧНОСТЬ, МОДЕРАЦИЯ ======================
    protected = is_protected_from_automod(message.author)

    # Объявляем переменные заранее, чтобы избежать UnboundLocalError
    spam_threshold = SPAM_THRESHOLD
    mention_limit = 4  # базовое значение

    if not protected:
        spam_threshold *= (VIP_SPAM_MULTIPLIER if is_vip(message.author) else 1)
        mention_limit   *= (VIP_MENTION_MULTIPLIER if is_vip(message.author) else 1)

    if user_id not in spam_cache:
        spam_cache[user_id] = []
    spam_cache[user_id] = [t for t in spam_cache[user_id] if now - t < SPAM_TIME]
    spam_cache[user_id].append(now)

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
        user_id = str(message.author.id)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        last_toxic = None
        for warn in warnings_data.get(user_id, []):
            if "токсичность" in warn.get("reason", "").lower():
                last_toxic = datetime.strptime(warn["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                break

        if last_toxic and (datetime.now(timezone.utc) - last_toxic).total_seconds() < 300:
            await message.channel.send(
                f"{message.author.mention}, без оскорблений, пожалуйста 😅 (слишком быстро)",
                delete_after=8
            )
            return

        toxic_count = sum(
            1 for w in warnings_data.get(user_id, [])
            if "токсичность" in w.get("reason", "").lower()
            and (datetime.now(timezone.utc) - datetime.strptime(w["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)).days < 7
        )

        reason = "Токсичность / личное оскорбление"

        if toxic_count == 0:
            warnings_data.setdefault(user_id, []).append({
                "moderator": "Автомодерация",
                "reason": reason,
                "time": now_str
            })
            save_warnings()
            await message.channel.send(
                f"{message.author.mention}, эй, без оскорблений, ок? 😅\n"
                f"Это первое предупреждение. Следующее → мут.",
                delete_after=12
            )
            case_id = await create_case(
                message.author, bot.user, "Предупреждение (авто)", reason
            )
            await send_punishment_log(
                member=message.author,
                punishment_type="⚠️ Предупреждение (авто)",
                duration="—",
                reason=reason + " (1-е)",
                moderator=bot.user,
                case_id=case_id
            )

        elif toxic_count == 1:
            warnings_data.setdefault(user_id, []).append({
                "moderator": "Автомодерация",
                "reason": reason,
                "time": now_str
            })
            save_warnings()
            try:
                await message.author.timeout(timedelta(minutes=30), reason="Повторная токсичность")
                await message.channel.send(
                    f"{message.author.mention}, **мут 30 минут** за повторные оскорбления.\n"
                    f"Третье → мут 2 часа.",
                    delete_after=15
                )
                case_id = await create_case(
                    message.author, bot.user, "Мут 30 мин (авто)", reason + " (2-е)", "30 минут"
                )
                await send_punishment_log(
                    member=message.author,
                    punishment_type="🔇 Мут 30 мин (авто)",
                    duration="30 минут",
                    reason=reason + " (2-е нарушение)",
                    moderator=bot.user,
                    case_id=case_id
                )
            except:
                pass

        else:
            warnings_data.setdefault(user_id, []).append({
                "moderator": "Автомодерация",
                "reason": reason,
                "time": now_str
            })
            save_warnings()
            try:
                await message.author.timeout(timedelta(hours=2), reason="Многократная токсичность")
                await message.channel.send(
                    f"{message.author.mention}, **мут 2 часа** за многократные оскорбления.",
                    delete_after=15
                )
                case_id = await create_case(
                    message.author, bot.user, "Мут 2ч (авто)", reason + f" ({toxic_count+1}-е)", "2 часа"
                )
                await send_punishment_log(
                    member=message.author,
                    punishment_type="🔇 Мут 2ч (авто)",
                    duration="2 часа",
                    reason=f"{reason} ({toxic_count+1}-е нарушение)",
                    moderator=bot.user,
                    case_id=case_id
                )
                await send_mod_log(
                    title="⚠️ Многократная токсичность",
                    description=f"**Пользователь:** {message.author.mention}\n"
                                f"**Нарушений:** {toxic_count+1}\n"
                                f"**Последнее сообщение:** удалено\n"
                                f"**Причина:** {reason}",
                    color=0xe74c3c
                )
            except:
                pass

        await check_auto_punishment(message.author, reason)
        return

    # ====================== ЭКОНОМИКА + СЕЗОННЫЙ XP (для ВСЕХ) ======================
    if has_full_access(message.guild.id) or message.author.id == OWNER_ID:
        # Инициализация
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}
        if user_id not in season_data:
            season_data[user_id] = {"season_xp": 0, "season_level": 1, "season_points": 0, "claimed_rewards": []}
        if user_id not in daily_season_xp_earned:
            daily_season_xp_earned[user_id] = 0
            daily_season_xp_reset[user_id] = datetime.now(timezone.utc).date().isoformat()

        # Начисление за сообщение
        if now - economy_data[user_id].get("last_message", 0) >= MESSAGE_COOLDOWN:
            # Монеты
            earn_coins = random.randint(1, 5)
            economy_data[user_id]["balance"] += earn_coins
            economy_data[user_id]["last_message"] = now

            # Сезонный XP
            xp_per_msg = current_season["xp_per_message"]
            if is_vip(message.author):
                xp_per_msg = int(xp_per_msg * 2)

            today_str = datetime.now(timezone.utc).date().isoformat()
            if daily_season_xp_reset.get(user_id) != today_str:
                daily_season_xp_earned[user_id] = 0
                daily_season_xp_reset[user_id] = today_str

            can_add_xp = daily_season_xp_earned[user_id] + xp_per_msg <= current_season["max_daily_xp"]
            if can_add_xp:
                season_data[user_id]["season_xp"] += xp_per_msg
                await check_and_level_up(user_id, message.author)
                daily_season_xp_earned[user_id] += xp_per_msg
                            # Прогресс ежедневного задания "messages"
            prog = daily_tasks_progress.setdefault(user_id, {
                "messages": 0, "voice": 0, "daily": 0, "date": today_str
            })
            if prog["date"] != today_str:
                prog.update({"messages": 0, "voice": 0, "daily": 0, "date": today_str})
                daily_tasks_progress[user_id] = prog

            prog["messages"] += 1
            if prog["messages"] == DAILY_TASKS["messages"]["goal"]:
                extra_xp = DAILY_TASKS["messages"]["xp"]
                season_data[user_id]["season_xp"] += extra_xp
                await check_and_level_up(user_id, message.author)
                await message.channel.send(
                    f"{message.author.mention} ✓ Задание выполнено: **{DAILY_TASKS['messages']['desc']}** → +{extra_xp} XP!",
                    delete_after=10
                )
                print(f"[XP SUCCESS] +{xp_per_msg} XP → {user_id} (всего {season_data[user_id]['season_xp']})")

            save_economy()
            save_seasons()
            save_daily_tasks()

    # В самом конце обрабатываем команды
    await bot.process_commands(message)
# ───────────────────────────────────────────────
# ПРИВЕТСТВИЯ И ПРОЩАНИЯ
# ───────────────────────────────────────────────
@bot.event
async def on_member_join(member):
    """Красивое приветствие нового участника"""
    try:
        # Лог в мод-канал
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
       
        # Приветствие в общий канал
        welcome_ch = bot.get_channel(WELCOME_CHANNEL_ID)
        if welcome_ch:
            # Статистика сервера
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
        # Лог в мод-канал
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
       
        # Прощание в общий канал
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
# УЛУЧШЕННЫЙ АУДИТ-ЛОГ
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
    """Лог изменения сообщения — улучшенная версия"""
    if before.author.bot:
        return
    # Пропускаем, если контент не изменился (самый частый случай)
    if before.content == after.content:
        return
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
        # Пытаемся найти, кто отредактировал (через аудит-лог)
        moderator = None
        reason = None
        try:
            async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_update):
                time_diff = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                if (entry.target.id == after.author.id and
                    hasattr(entry.extra, 'channel') and
                    entry.extra.channel.id == after.channel.id and
                    time_diff < 15): # увеличил окно до 15 сек
                    moderator = entry.user
                    reason = entry.reason
                    break
        except discord.Forbidden:
            print("Нет прав VIEW_AUDIT_LOG — лог редактирования не работает")
        except Exception as e:
            print(f"Ошибка при чтении audit_logs в on_message_edit: {e}")
        embed = discord.Embed(
            title="✏️ Сообщение изменено",
            color=COLORS["audit"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Автор", value=f"{before.author.mention}\nID: `{before.author.id}`", inline=False)
        embed.add_field(name="Канал", value=before.channel.mention, inline=False)
        # Контент "Было" / "Стало"
        before_text = before.content[:500] + ("..." if len(before.content) > 500 else "") or "*Пусто*"
        after_text = after.content[:500] + ("..." if len(after.content) > 500 else "") or "*Пусто*"
        embed.add_field(name="Было", value=before_text, inline=False)
        embed.add_field(name="Стало", value=after_text, inline=False)
        embed.add_field(name="Ссылка", value=f"[Перейти]({after.jump_url})", inline=False)
        if moderator:
            embed.add_field(name="Изменил", value=f"{moderator.mention}\nID: `{moderator.id}`", inline=False)
        else:
            embed.add_field(name="Изменил", value="Неизвестно (нет прав на аудит или ручное редактирование)", inline=False)
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        # Если изменились вложения
        if before.attachments != after.attachments:
            att_before = ", ".join([a.filename for a in before.attachments]) or "Нет"
            att_after = ", ".join([a.filename for a in after.attachments]) or "Нет"
            embed.add_field(name="Вложения", value=f"Было: {att_before}\nСтало: {att_after}", inline=False)
        embed.set_footer(text=f"Сообщение ID: {after.id}")
        await log_ch.send(embed=embed)
    except Exception as e:
        print(f"Критическая ошибка в on_message_edit: {e}")
        traceback.print_exc()
@bot.event
async def on_member_update(before, after):
    """Лог изменений участника"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
       
        # Никнейм
        if before.nick != after.nick:
            embed = discord.Embed(
                title="👤 Никнейм изменён",
                color=COLORS["audit"],
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Пользователь", value=after.mention, inline=False)
            embed.add_field(name="Было", value=before.nick or "*Не указан*", inline=True)
            embed.add_field(name="Стало", value=after.nick or "*Не указан*", inline=True)
           
            audit = await get_audit_info(after.guild, discord.AuditLogAction.member_update, after.id)
            if audit and audit["moderator"]:
                embed.add_field(name="Изменил", value=audit["moderator"].mention, inline=False)
           
            await log_ch.send(embed=embed)
       
        # Роли
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles and r.name != "@everyone"]
            removed = [r for r in before.roles if r not in after.roles and r.name != "@everyone"]
           
            if added or removed:
                embed = discord.Embed(
                    title="👤 Роли изменены",
                    color=COLORS["audit"],
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Пользователь", value=after.mention, inline=False)
                if added:
                    embed.add_field(name="✅ Добавлены", value=", ".join([r.mention for r in added]), inline=False)
                if removed:
                    embed.add_field(name="❌ Удалены", value=", ".join([r.mention for r in removed]), inline=False)
               
                audit = await get_audit_info(after.guild, discord.AuditLogAction.member_role_update, after.id)
                if audit and audit["moderator"]:
                    embed.add_field(name="Изменил", value=audit["moderator"].mention, inline=False)
               
                await log_ch.send(embed=embed)
       
        # Мут/таймаут
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until:
                duration = after.timed_out_until - datetime.now(timezone.utc)
                hours = duration.days * 24 + duration.seconds // 3600
                minutes = (duration.seconds % 3600) // 60
                duration_text = f"{hours}ч {minutes}м"
               
                audit = await get_audit_info(after.guild, discord.AuditLogAction.member_update, after.id)
                moderator = audit["moderator"] if audit else None
               
                case_id = await create_case(after, moderator or bot.user, "Мут", "Автоматически", duration_text)
               
                embed = discord.Embed(
                    title="🔇 Пользователь замучен",
                    color=COLORS["audit"],
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Пользователь", value=after.mention, inline=False)
                embed.add_field(name="Длительность", value=duration_text, inline=True)
                embed.add_field(name="До", value=f"<t:{int(after.timed_out_until.timestamp())}:R>", inline=True)
                if moderator:
                    embed.add_field(name="Модератор", value=moderator.mention, inline=True)
                embed.add_field(name="Кейс", value=f"`{case_id}`", inline=False)
                await log_ch.send(embed=embed)
            else:
                audit = await get_audit_info(after.guild, discord.AuditLogAction.member_update, after.id)
                moderator = audit["moderator"] if audit else None
               
                case_id = await create_case(after, moderator or bot.user, "Снятие мута", "Автоматически")
                embed = discord.Embed(
                    title="🔊 Мут снят",
                    color=COLORS["audit"],
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Пользователь", value=after.mention, inline=False)
                if moderator:
                    embed.add_field(name="Модератор", value=moderator.mention, inline=True)
                embed.add_field(name="Кейс", value=f"`{case_id}`", inline=False)
                await log_ch.send(embed=embed)
               
    except Exception as e:
        print(f"Ошибка в on_member_update: {e}")
@bot.event
async def on_member_ban(guild, user):
    """Лог бана"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
       
        moderator = None
        reason = None
       
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    reason = entry.reason
                    break
        except:
            pass
       
        case_id = await create_case(user, moderator or bot.user, "Бан", reason or "Не указана")
       
        embed = discord.Embed(
            title="🔨 Пользователь забанен",
            color=COLORS["audit"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Пользователь", value=f"{user} (`{user.id}`)", inline=False)
        if moderator:
            embed.add_field(name="Модератор", value=f"{moderator.mention}\nID: `{moderator.id}`", inline=False)
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        embed.add_field(name="Кейс", value=f"`{case_id}`", inline=False)
       
        await log_ch.send(embed=embed)
    except Exception as e:
        print(f"Ошибка в on_member_ban: {e}")
@bot.event
async def on_member_unban(guild, user):
    """Лог разбана"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
       
        moderator = None
       
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
                if entry.target.id == user.id:
                    moderator = entry.user
                    break
        except:
            pass
       
        embed = discord.Embed(
            title="🔓 Пользователь разбанен",
            color=COLORS["audit"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Пользователь", value=f"{user} (`{user.id}`)", inline=False)
        if moderator:
            embed.add_field(name="Модератор", value=f"{moderator.mention}\nID: `{moderator.id}`", inline=False)
       
        await log_ch.send(embed=embed)
    except Exception as e:
        print(f"Ошибка в on_member_unban: {e}")
@bot.event
async def on_guild_channel_create(channel):
    """Лог создания канала"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
       
        moderator = None
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id:
                    moderator = entry.user
                    break
        except:
            pass
       
        embed = discord.Embed(
            title="📢 Канал создан",
            color=COLORS["audit"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Название", value=channel.mention, inline=True)
        embed.add_field(name="Тип", value="Текстовый" if isinstance(channel, discord.TextChannel) else "Голосовой", inline=True)
        embed.add_field(name="Категория", value=channel.category.name if channel.category else "Нет", inline=True)
        if moderator:
            embed.add_field(name="Создал", value=moderator.mention, inline=True)
       
        await log_ch.send(embed=embed)
    except Exception as e:
        print(f"Ошибка в on_guild_channel_create: {e}")
@bot.event
async def on_guild_channel_delete(channel):
    """Лог удаления канала"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
       
        moderator = None
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    moderator = entry.user
                    break
        except:
            pass
       
        embed = discord.Embed(
            title="🗑 Канал удалён",
            color=COLORS["audit"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Название", value=channel.name, inline=True)
        embed.add_field(name="Тип", value="Текстовый" if isinstance(channel, discord.TextChannel) else "Голосовой", inline=True)
        if moderator:
            embed.add_field(name="Удалил", value=moderator.mention, inline=True)
       
        await log_ch.send(embed=embed)
    except Exception as e:
        print(f"Ошибка в on_guild_channel_delete: {e}")
@bot.event
async def on_guild_channel_update(before, after):
    """Лог изменения канала"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
       
        changes = []
       
        if before.name != after.name:
            changes.append(f"**Название:** {before.name} → {after.name}")
       
        if before.category != after.category:
            before_cat = before.category.name if before.category else "Нет"
            after_cat = after.category.name if after.category else "Нет"
            changes.append(f"**Категория:** {before_cat} → {after_cat}")
       
        if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
            if before.topic != after.topic:
                changes.append(f"**Тема изменена**")
       
        if changes:
            moderator = None
            try:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                    if entry.target.id == after.id:
                        moderator = entry.user
                        break
            except:
                pass
           
            embed = discord.Embed(
                title="✏️ Канал изменён",
                description="\n".join(changes),
                color=COLORS["audit"],
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Канал", value=after.mention, inline=True)
            if moderator:
                embed.add_field(name="Изменил", value=moderator.mention, inline=True)
           
            await log_ch.send(embed=embed)
           
    except Exception as e:
        print(f"Ошибка в on_guild_channel_update: {e}")
@bot.event
async def on_voice_state_update(member, before, after):
    """Лог голосовых каналов + учёт времени для дохода"""
    if member.bot:
        return
    user_id = str(member.id)
    now = datetime.now(timezone.utc).timestamp()
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        # Логируем события (как было раньше)
        if before.channel is None and after.channel is not None:
            # Зашёл в голос
            if log_ch and "afk" not in after.channel.name.lower():
                embed = discord.Embed(
                    title="🔊 Подключился к голосовому",
                    color=COLORS["audit"],
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Пользователь", value=member.mention, inline=True)
                embed.add_field(name="Канал", value=after.channel.mention, inline=True)
                await log_ch.send(embed=embed)
            # Запоминаем время входа (для античита и дохода)
            if "afk" not in after.channel.name.lower():
                voice_start_time[user_id] = now
        elif before.channel is not None and after.channel is None:
            # Вышел из голоса
            if log_ch:
                embed = discord.Embed(
                    title="🔇 Отключился от голосового",
                    color=COLORS["audit"],
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Пользователь", value=member.mention, inline=True)
                embed.add_field(name="Канал", value=before.channel.mention, inline=True)
                await log_ch.send(embed=embed)
            # Убираем таймер входа
            if user_id in voice_start_time:
                del voice_start_time[user_id]
        elif before.channel != after.channel and before.channel is not None and after.channel is not None:
            # Перешёл из одного канала в другой
            if log_ch:
                embed = discord.Embed(
                    title="🔄 Переместился в голосовом",
                    color=COLORS["audit"],
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Пользователь", value=member.mention, inline=False)
                embed.add_field(name="Было", value=before.channel.mention, inline=True)
                embed.add_field(name="Стало", value=after.channel.mention, inline=True)
                await log_ch.send(embed=embed)
            # Обновляем время входа в новый канал (если не AFK)
            if "afk" not in after.channel.name.lower():
                voice_start_time[user_id] = now
            else:
                if user_id in voice_start_time:
                    del voice_start_time[user_id]
    except Exception as e:
        print(f"Ошибка в on_voice_state_update (лог): {e}")
@bot.event
async def on_guild_role_create(role):
    """Лог создания роли"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
       
        moderator = None
        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id:
                    moderator = entry.user
                    break
        except:
            pass
       
        embed = discord.Embed(
            title="🎨 Роль создана",
            color=role.color if role.color.value != 0 else COLORS["audit"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Название", value=role.mention, inline=True)
        embed.add_field(name="Цвет", value=f"#{role.color.value:06x}" if role.color.value != 0 else "Стандартный", inline=True)
        if moderator:
            embed.add_field(name="Создал", value=moderator.mention, inline=True)
       
        await log_ch.send(embed=embed)
    except Exception as e:
        print(f"Ошибка в on_guild_role_create: {e}")
@bot.event
async def on_guild_role_delete(role):
    """Лог удаления роли"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
       
        moderator = None
        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    moderator = entry.user
                    break
        except:
            pass
       
        embed = discord.Embed(
            title="🗑 Роль удалена",
            color=COLORS["audit"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Название", value=role.name, inline=True)
        if moderator:
            embed.add_field(name="Удалил", value=moderator.mention, inline=True)
       
        await log_ch.send(embed=embed)
    except Exception as e:
        print(f"Ошибка в on_guild_role_delete: {e}")
@bot.event
async def on_guild_role_update(before, after):
    """Лог изменения роли"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
       
        changes = []
       
        if before.name != after.name:
            changes.append(f"**Название:** {before.name} → {after.name}")
       
        if before.color != after.color:
            before_color = f"#{before.color.value:06x}" if before.color.value != 0 else "Стандартный"
            after_color = f"#{after.color.value:06x}" if after.color.value != 0 else "Стандартный"
            changes.append(f"**Цвет:** {before_color} → {after_color}")
       
        if before.permissions != after.permissions:
            changes.append(f"**Права изменены**")
       
        if changes:
            moderator = None
            try:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                    if entry.target.id == after.id:
                        moderator = entry.user
                        break
            except:
                pass
           
            embed = discord.Embed(
                title="✏️ Роль изменена",
                description="\n".join(changes),
                color=after.color if after.color.value != 0 else COLORS["audit"],
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Роль", value=after.mention, inline=True)
            if moderator:
                embed.add_field(name="Изменил", value=moderator.mention, inline=True)
           
            await log_ch.send(embed=embed)
           
    except Exception as e:
        print(f"Ошибка в on_guild_role_update: {e}")
@bot.event
async def on_guild_update(before, after):
    """Лог изменений сервера"""
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
       
        changes = []
       
        if before.name != after.name:
            changes.append(f"**Название:** {before.name} → {after.name}")
       
        if before.icon != after.icon:
            changes.append(f"**Иконка изменена**")
       
        if before.premium_tier != after.premium_tier:
            changes.append(f"**Уровень буста:** {before.premium_tier} → {after.premium_tier}")
       
        if changes:
            embed = discord.Embed(
                title="🔧 Сервер изменён",
                description="\n".join(changes),
                color=COLORS["audit"],
                timestamp=datetime.now(timezone.utc)
            )
            await log_ch.send(embed=embed)
           
    except Exception as e:
        print(f"Ошибка в on_guild_update: {e}")
# ───────────────────────────────────────────────
# КОМАНДЫ
# ───────────────────────────────────────────────
@bot.hybrid_command(name="ping", description="Подробная информация о боте")
async def ping(ctx: commands.Context):
    try:
        # Задержки
        latency = round(bot.latency * 1000)
       
        # Время работы
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
       
        # Статистика
        guild_count = len(bot.guilds)
        user_count = sum(g.member_count for g in bot.guilds if g.member_count)
        channel_count = sum(len(g.channels) for g in bot.guilds)
       
        # Пинг в разных регионах (эмуляция)
        ping_status = "🟢 Отлично" if latency < 200 else "🟡 Средне" if latency < 300 else "🔴 Плохо"
       
        # Создаем красивый embed
        embed = discord.Embed(
            title="🏓 **ПОНГ!**",
            description="```Статус бота и производительность```",
            color=COLORS["welcome"],
            timestamp=datetime.now(timezone.utc)
        )
       
        # Основная информация
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
       
        # Детали задержки
        embed.add_field(
            name="⏱️ **Детали задержки**",
            value=f"```diff\n"
                  f"+ WebSocket: {latency}ms\n"
                  f"+ API: ~{latency + 20}ms\n"
                  f"+ База данных: ~{latency + 10}ms\n"
                  f"```",
            inline=True
        )
       
        # Статистика команд
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
       
        # Красивое оформление
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        embed.set_footer(
            text=f"MortisPlay • Запросил: {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
       
        # Добавляем кнопку для проверки
        view = View(timeout=60)
        button = Button(label="🔄 Обновить", style=discord.ButtonStyle.primary)
       
        async def refresh_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("❌ Это не твоя команда!", ephemeral=True)
           
            # Обновляем данные
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
        # Добавляем биографию для бота
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
# ЭКОНОМИКА
# ───────────────────────────────────────────────
@bot.hybrid_command(name="pay", description="💸 Перевести монеты с подтверждением и комиссией")
@app_commands.describe(
    member="Кому перевести",
    amount="Сумма (целое число)",
    comment="Сообщение получателю (опционально)"
)
async def pay(ctx: commands.Context, member: discord.Member, amount: int, comment: str = None):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)
        if amount <= 0:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Сумма должна быть больше 0.", ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Нельзя переводить себе.", ephemeral=True)
        if member.bot:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Нельзя переводить ботам.", ephemeral=True)
        sender_id = str(ctx.author.id)
        receiver_id = str(member.id)
        # Проверка баланса
        if sender_id not in economy_data or economy_data[sender_id].get("balance", 0) < amount:
            bal = economy_data.get(sender_id, {}).get("balance", 0)
            return await ctx.send(
                f"{ECONOMY_EMOJIS['error']} Недостаточно монет!\nБаланс: **{format_number(bal)}** {ECONOMY_EMOJIS['coin']}",
                ephemeral=True
            )
        # Лимит переводов (5 в сутки, VIP без лимита)
        now = datetime.now(timezone.utc).timestamp()
        if not is_vip(ctx.author):
            if "pay_history" not in economy_data.setdefault(sender_id, {}):
                economy_data[sender_id]["pay_history"] = []
            economy_data[sender_id]["pay_history"] = [
                t for t in economy_data[sender_id]["pay_history"] if now - t < 86400
            ]
            if len(economy_data[sender_id]["pay_history"]) >= 5:
                next_time = economy_data[sender_id]["pay_history"][0] + 86400
                remaining = int(next_time - now)
                hours = remaining // 3600
                mins = (remaining % 3600) // 60
                return await ctx.send(
                    f"{ECONOMY_EMOJIS['error']} Лимит 5 переводов в сутки.\nСледующий через **{hours}ч {mins}мин**.",
                    ephemeral=True
                )
        # Комиссия 1% при >5000
        transfer_tax = max(1, int(amount * 0.01)) if amount > 5000 else 0
        final_amount = amount - transfer_tax
        class PayConfirm(View):
            def __init__(self, author_id: int):
                super().__init__(timeout=120) # увеличил до 120 сек для надёжности
                self.author_id = author_id
            @discord.ui.button(label="Подтвердить перевод", style=discord.ButtonStyle.green, emoji="💸")
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.author_id:
                    return await interaction.response.send_message("Это не твоя команда!", ephemeral=True)
                await interaction.response.defer(ephemeral=False) # важно!
                try:
                    # Списание и начисление
                    economy_data[sender_id]["balance"] -= amount
                    if receiver_id not in economy_data:
                        economy_data[receiver_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}
                    economy_data[receiver_id]["balance"] += final_amount
                    if transfer_tax > 0:
                        economy_data["server_vault"] = economy_data.get("server_vault", 0) + transfer_tax
                    # История
                    economy_data[sender_id].setdefault("pay_history", []).append(now)
                    save_economy()
                    # Успешный эмбед
                    success_embed = discord.Embed(
                        title=f"{ECONOMY_EMOJIS['gift']} Подарок доставлен! 🎁",
                        description=f"**{interaction.user.mention}** → **{member.mention}**",
                        color=0x2ecc71,
                        timestamp=datetime.now(timezone.utc)
                    )
                    success_embed.add_field(name="Сумма", value=f"**{format_number(final_amount)}** {ECONOMY_EMOJIS['coin']}", inline=True)
                    if transfer_tax > 0:
                        success_embed.add_field(name=f"{ECONOMY_EMOJIS['tax']} Комиссия", value=f"-{format_number(transfer_tax)} (1%)", inline=True)
                    success_embed.add_field(
                        name="Баланс отправителя", value=f"**{format_number(economy_data[sender_id]['balance'])}** {ECONOMY_EMOJIS['coin']}", inline=False
                    )
                    success_embed.add_field(
                        name="Баланс получателя", value=f"**{format_number(economy_data[receiver_id]['balance'])}** {ECONOMY_EMOJIS['coin']}", inline=False
                    )
                    if comment:
                        success_embed.add_field(name="📝 Сообщение", value=f"*{comment}*", inline=False)
                    success_embed.set_thumbnail(url="https://media.giphy.com/media/l0HlRnAWXxn0MhKLK/giphy.gif")
                    success_embed.set_footer(text=f"MortisPlay • Перевод #{len(economy_data[sender_id]['pay_history'])}")
                    # Отправляем новое сообщение вместо редактирования
                    await interaction.followup.send(embed=success_embed)
                    # Автоудаление оригинального сообщения предпросмотра
                    try:
                        await interaction.message.delete(delay=5)
                    except:
                        pass
                    # ЛС получателю
                    try:
                        dm = discord.Embed(
                            title=f"{ECONOMY_EMOJIS['gift']} Вам прислали подарок!",
                            description=f"От: {interaction.user.mention}\nСумма: **{format_number(final_amount)}** {ECONOMY_EMOJIS['coin']}",
                            color=0x2ecc71
                        )
                        if comment:
                            dm.add_field(name="Сообщение", value=comment, inline=False)
                        await member.send(embed=dm)
                    except:
                        pass
                    # Лог крупного
                    if amount >= 10000:
                        await send_mod_log(
                            title="💰 Крупный перевод!",
                            description=f"**От:** {interaction.user.mention}\n**Кому:** {member.mention}\n**Сумма:** {format_number(amount)} → {format_number(final_amount)}",
                            color=0xffd700
                        )
                except Exception as inner_e:
                    error_embed = discord.Embed(
                        title=f"{ECONOMY_EMOJIS['error']} Ошибка при переводе",
                        description=str(inner_e),
                        color=0xe74c3c
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
            @discord.ui.button(label="Отмена", style=discord.ButtonStyle.red, emoji="✖️")
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.author_id:
                    return await interaction.response.send_message("Это не твоя команда!", ephemeral=True)
                await interaction.response.defer(ephemeral=False)
                cancel_embed = discord.Embed(
                    title=f"{ECONOMY_EMOJIS['error']} Перевод отменён",
                    color=0xe74c3c,
                    timestamp=datetime.now(timezone.utc)
                )
                await interaction.followup.send(embed=cancel_embed)
                try:
                    await interaction.message.delete(delay=3)
                except:
                    pass
        # Предпросмотр (теперь обычное сообщение)
        preview_embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['transfer']} Подтвердите перевод",
            description=f"**{format_number(amount)}** {ECONOMY_EMOJIS['coin']} → {member.mention}",
            color=0x3498db,
            timestamp=datetime.now(timezone.utc)
        )
        if transfer_tax > 0:
            preview_embed.add_field(name=f"{ECONOMY_EMOJIS['tax']} Комиссия", value=f"{format_number(transfer_tax)} (1%)", inline=False)
        preview_embed.add_field(name="Получатель получит", value=f"**{format_number(final_amount)}** {ECONOMY_EMOJIS['coin']}", inline=False)
        if comment:
            preview_embed.add_field(name="Сообщение", value=f"*{comment}*", inline=False)
        preview_embed.set_footer(text="Действие в течение 120 секунд • Лимит: 5/сутки (VIP — без лимита)")
        view = PayConfirm(author_id=ctx.author.id)
        await ctx.send(embed=preview_embed, view=view) # БЕЗ ephemeral=True !
    except Exception as e:
        await send_error_embed(ctx, f"Ошибка при подготовке перевода: {str(e)}")
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
# ───────────────────────────────────────────────
# СИСТЕМА КЕЙСОВ
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
# УЛУЧШЕННЫЙ /HELP
# ───────────────────────────────────────────────
@bot.hybrid_command(name="help", description="📚 Список команд")
async def help_command(ctx: commands.Context):
    try:
        is_mod = is_moderator(ctx.author)
       
        embed = discord.Embed(
            title="🤖 Помощь по командам",
            description="**📋 Основное**\n**💰 Экономика**\n**🎮 Развлечения**" +
                       ("\n**🛡️ Модерация**\n**🎫 Тикеты**" if is_mod else ""),
            color=COLORS["welcome"]
        )
        embed.set_footer(text="Используй кнопки для навигации")
       
        view = HelpView(ctx.author, is_mod)
        await ctx.send(embed=embed, view=view, ephemeral=True)
       
    except Exception as e:
        await send_error_embed(ctx, str(e))
# ───────────────────────────────────────────────
# FAQ
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
# РАЗВЛЕЧЕНИЯ
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
@bot.hybrid_command(name="valute", description="Курсы валют + курс внутреннего коина")
async def valute(ctx: commands.Context):
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
            except Exception:
                continue
        embed = discord.Embed(
            title="📈 Курсы валют + MortisCoin",
            color=COLORS["welcome"],
            timestamp=datetime.now(timezone.utc)
        )
        if data:
            rates = data.get("rates", {})
            embed.add_field(name="🇺🇸 USD", value="1.00", inline=True)
            embed.add_field(name="🇪🇺 EUR", value=f"{rates.get('EUR', 0.92):.2f}", inline=True)
            embed.add_field(name="🇬🇧 GBP", value=f"{rates.get('GBP', 0.79):.2f}", inline=True)
            embed.add_field(name="🇷🇺 RUB", value=f"{rates.get('RUB', 92.50):.2f}", inline=True)
            embed.add_field(name=" ", value=" ", inline=False) # разделитель
        else:
            embed.description = "⚠️ Внешние курсы временно недоступны"
        # Внутренний коин всегда показываем
        embed.add_field(
            name=f"{ECONOMY_EMOJIS['coin']} MortisCoin (внутренний)",
            value="**1 MortisCoin = 1 🪙**\nФиксированный курс внутри сервера",
            inline=False
        )
        embed.set_footer(text="MortisCoin — валюта сервера • Внешние данные: exchangerate-api")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
# ───────────────────────────────────────────────
# МОДЕРАЦИЯ
# ───────────────────────────────────────────────
@bot.hybrid_command(name="warn", description="Выдать предупреждение")
@app_commands.describe(member="Пользователь", reason="Причина")
@commands.has_permissions(manage_messages=True)
async def warn(ctx: commands.Context, member: discord.Member, *, reason: str = "Не указана"):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя наказывать владельца сервера, администраторов или самого себя!", ephemeral=True)
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
@bot.hybrid_command(name="clearwarn", description="Очистить предупреждения")
@app_commands.describe(member="Пользователь", warn_id="all или номер")
@commands.has_permissions(administrator=True)
async def clearwarn(ctx: commands.Context, member: discord.Member, warn_id: str = "all"):
    try:
        if not ctx.author.guild_permissions.administrator:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя очищать предупреждения у владельца сервера или администратора!", ephemeral=True)
        user_id = str(member.id)
        if user_id not in warnings_data or not warnings_data[user_id]:
            return await ctx.send(f"✅ У {member.mention} нет предупреждений.", ephemeral=True)
       
        if warn_id.lower() == "all":
            del warnings_data[user_id]
            save_warnings()
            await ctx.send(f"✅ Все предупреждения {member.mention} удалены.", ephemeral=True)
            await send_mod_log(
                title="🧹 Очистка предупреждений",
                description=f"**Модератор:** {ctx.author.mention}\n**Пользователь:** {member.mention}",
                color=COLORS["mod"]
            )
        else:
            await ctx.send("❌ Удаление конкретного предупреждения пока не реализовано.", ephemeral=True)
           
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="mute", description="Замутить пользователя")
@app_commands.describe(member="Пользователь", duration="1h, 1d, 30m", reason="Причина")
@commands.has_permissions(manage_messages=True)
async def mute(ctx: commands.Context, member: discord.Member, duration: str, *, reason: str = "Не указана"):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя наказывать владельца сервера, администраторов или самого себя!", ephemeral=True)
       
        seconds = 0
        if duration.endswith("h"):
            seconds = int(duration[:-1]) * 3600
        elif duration.endswith("d"):
            seconds = int(duration[:-1]) * 86400
        elif duration.endswith("m"):
            seconds = int(duration[:-1]) * 60
        elif duration.endswith("s"):
            seconds = int(duration[:-1])
        else:
            seconds = int(duration) * 60
       
        if seconds <= 0:
            return await ctx.send("❌ Некорректная длительность!", ephemeral=True)
       
        delta = timedelta(seconds=seconds)
        await member.timeout(delta, reason=reason)
       
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        dur_text = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
       
        case_id = await create_case(member, ctx.author, "Мут", reason, dur_text)
       
        await send_punishment_log(
            member=member,
            punishment_type="🔇 Мут",
            duration=dur_text,
            reason=reason,
            moderator=ctx.author,
            case_id=case_id
        )
       
        embed = discord.Embed(
            title="🔇 Пользователь замучен",
            description=f"**Пользователь:** {member.mention}\n**Длительность:** {dur_text}\n**Причина:** {reason}",
            color=COLORS["mod"]
        )
        await ctx.send(embed=embed, ephemeral=True)
       
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="unmute", description="Снять мут")
@app_commands.describe(member="Пользователь", reason="Причина")
@commands.has_permissions(manage_messages=True)
async def unmute(ctx: commands.Context, member: discord.Member, *, reason: str = "Не указана"):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя снимать мут с владельца сервера или администратора!", ephemeral=True)
        await member.timeout(None, reason=reason)
        case_id = await create_case(member, ctx.author, "Снятие мута", reason)
       
        await send_punishment_log(
            member=member,
            punishment_type="🔊 Мут снят",
            duration="—",
            reason=reason,
            moderator=ctx.author,
            case_id=case_id
        )
       
        embed = discord.Embed(
            title="🔊 Мут снят",
            description=f"**Пользователь:** {member.mention}\n**Причина:** {reason}",
            color=COLORS["mod"]
        )
        await ctx.send(embed=embed, ephemeral=True)
       
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="temprole", description="Временная роль")
@app_commands.describe(member="Пользователь", role="Роль", duration="1h, 1d, 30m")
@commands.has_permissions(manage_roles=True)
async def temprole(ctx: commands.Context, member: discord.Member, role: discord.Role, duration: str):
    try:
        if not ctx.author.guild_permissions.manage_roles:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя выдавать временную роль владельцу сервера, администраторам или самому себе!", ephemeral=True)
        if role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send("❌ Нельзя выдать роль выше своей!", ephemeral=True)
       
        seconds = 0
        if duration.endswith("h"):
            seconds = int(duration[:-1]) * 3600
        elif duration.endswith("d"):
            seconds = int(duration[:-1]) * 86400
        elif duration.endswith("m"):
            seconds = int(duration[:-1]) * 60
        else:
            seconds = int(duration) * 60
       
        if seconds <= 0:
            return await ctx.send("❌ Некорректная длительность!", ephemeral=True)
       
        await member.add_roles(role, reason=f"Временная роль от {ctx.author}")
       
        user_id = str(member.id)
        temp_roles.setdefault(user_id, {})[str(role.id)] = datetime.now(timezone.utc).timestamp() + seconds
       
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        dur_text = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
       
        embed = discord.Embed(
            title="⏱️ Временная роль",
            description=f"**Пользователь:** {member.mention}\n**Роль:** {role.mention}\n**Длительность:** {dur_text}",
            color=COLORS["mod"]
        )
        await ctx.send(embed=embed, ephemeral=True)
       
        await send_mod_log(
            title="⏱️ Временная роль",
            description=f"**Модератор:** {ctx.author.mention}\n**Пользователь:** {member.mention}\n**Роль:** {role.mention}\n**Длительность:** {dur_text}",
            color=COLORS["mod"]
        )
       
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="ticket", description="Управление тикетами")
@app_commands.describe(action="setup / close")
@commands.has_permissions(manage_channels=True)
async def ticket(ctx: commands.Context, action: str = "setup"):
    try:
        if not ctx.author.guild_permissions.manage_channels:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not has_full_access(ctx.guild.id):
            return await ctx.send("❌ Команда только на сервере разработчика.", ephemeral=True)
        action = action.lower()
        if action == "setup":
            embed = discord.Embed(
                title="🎫 Система тикетов",
                description="Нажми кнопку, чтобы создать тикет",
                color=COLORS["ticket"]
            )
            view = TicketPanelView()
            await ctx.send(embed=embed, view=view)
            await ctx.send("✅ Панель создана!", delete_after=10)
        elif action == "close":
            if not any(ctx.channel.name.startswith(p) for p in ["🔧-", "⚠️-", "❓-", "🤝-", "📌-"]):
                return await ctx.send("❌ Это не тикет!", ephemeral=True)
            await ctx.send("🔒 Закрываю...")
            await asyncio.sleep(5)
            await ctx.channel.delete()
        else:
            await ctx.send("Использование: `/ticket setup` или `/ticket close`")
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="ban", description="Забанить пользователя")
@app_commands.describe(member="Пользователь", reason="Причина", delete_message_days="Удалить сообщения за N дней")
@commands.has_permissions(ban_members=True)
async def ban(ctx: commands.Context, member: discord.Member, reason: str = "Не указана", delete_message_days: int = 0):
    try:
        if not ctx.author.guild_permissions.ban_members:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя наказывать владельца сервера, администраторов или самого себя!", ephemeral=True)
       
        await member.ban(reason=reason, delete_message_days=delete_message_days)
        case_id = await create_case(member, ctx.author, "Бан", reason)
       
        await send_punishment_log(
            member=member,
            punishment_type="🔨 Бан",
            duration="Навсегда",
            reason=reason,
            moderator=ctx.author,
            case_id=case_id
        )
       
        embed = discord.Embed(
            title="🔨 Пользователь забанен",
            description=f"**Пользователь:** {member.mention}\n**Причина:** {reason}\n**Удалено сообщений за:** {delete_message_days} дней",
            color=COLORS["mod"]
        )
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="unwarn", description="Удалить предупреждение")
@app_commands.describe(member="Пользователь", warn_index="Номер предупреждения")
@commands.has_permissions(manage_messages=True)
async def unwarn(ctx: commands.Context, member: discord.Member, warn_index: int):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя удалять предупреждения у владельца сервера или администратора!", ephemeral=True)
       
        user_id = str(member.id)
        if user_id not in warnings_data or not warnings_data[user_id]:
            return await ctx.send(f"✅ У {member.mention} нет предупреждений.", ephemeral=True)
       
        if warn_index < 1 or warn_index > len(warnings_data[user_id]):
            return await ctx.send(f"❌ Неверный номер. Всего: {len(warnings_data[user_id])}", ephemeral=True)
       
        removed = warnings_data[user_id].pop(warn_index - 1)
        if not warnings_data[user_id]:
            del warnings_data[user_id]
        save_warnings()
       
        await send_mod_log(
            title="🧹 Предупреждение удалено",
            description=f"**Модератор:** {ctx.author.mention}\n**Пользователь:** {member.mention}\n**Номер:** {warn_index}\n**Причина:** {removed['reason']}",
            color=COLORS["mod"]
        )
       
        await ctx.send(f"✅ Предупреждение #{warn_index} для {member.mention} удалено.", ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
# ───────────────────────────────────────────────
# ЭКОНОМИКА (ПРОДОЛЖЕНИЕ)
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
       
        embed.set_footer(text="Экономика v0.1.7", icon_url=bot.user.display_avatar.url)
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
       
        embed.add_field(
            name=f"{ECONOMY_EMOJIS['balance']} Монеты",
            value=f"**`{format_number(bal)}`** {ECONOMY_EMOJIS['coin']}",
            inline=True
        )
        embed.add_field(name="🏆 Место", value=f"**#{rank}** из {len(users)}", inline=True)
        embed.add_field(
            name=f"{ECONOMY_EMOJIS['bank']} Казна",
            value=f"`{format_number(vault)}` {ECONOMY_EMOJIS['coin']}",
            inline=True
        )
       
        if tax > 0:
            embed.add_field(
                name=f"{ECONOMY_EMOJIS['tax']} Налог",
                value=f"Списано **-{format_number(tax)}** {ECONOMY_EMOJIS['coin']}",
                inline=False
            )
       
        embed.add_field(
            name=f"{ECONOMY_EMOJIS['gift']} Ежедневный бонус",
            value=daily,
            inline=False
        )
       
        # Новое поле: заработок от войса сегодня
        voice_today = daily_voice_earned.get(user_id, 0)
        voice_progress = f"{format_number(voice_today)} / {VOICE_DAILY_MAX}"
        if voice_today >= VOICE_DAILY_MAX:
            voice_progress += " (лимит достигнут)"
        embed.add_field(
            name="🎤 Заработано в голосе сегодня",
            value=f"**{voice_progress}** {ECONOMY_EMOJIS['coin']}",
            inline=True
        )
       
        # Новое поле: активный буст ×1.5
        if "multiplier_end" in economy_data[user_id]:
            end = economy_data[user_id]["multiplier_end"]
            if end > now:
                remaining_sec = int(end - now)
                remaining_h = remaining_sec // 3600
                remaining_m = (remaining_sec % 3600) // 60
                embed.add_field(
                    name="🚀 Активный буст ×1.5",
                    value=f"Действует на сообщения и daily\nОсталось: **{remaining_h}ч {remaining_m}мин**",
                    inline=True
                )
       
        inv = economy_data[user_id].get("investments", [])
        active = sum(1 for i in inv if i["end_time"] > now)
        if active:
            embed.add_field(
                name=f"{ECONOMY_EMOJIS['investment']} Инвестиции",
                value=f"Активно: **{active}**",
                inline=False
            )
       
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
        today_str = datetime.now(timezone.utc).date().isoformat()

        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}

        last = economy_data[user_id].get("last_daily", 0)

        # Кулдаун
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
            embed.set_footer(text=f"Баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']}")
            return await ctx.send(embed=embed, ephemeral=True)

        # Налог (если есть)
        tax = await apply_wealth_tax(user_id)

        # Шанс супер-дропа
        roll = random.randint(1, 100)
        is_super_drop = roll <= SUPER_DROP_CHANCE

        if is_super_drop:
            title = "ЭПИЧЕСКИЙ ДРОП!!!"
            reward = random.randint(SUPER_DROP_MIN, SUPER_DROP_MAX)
            color = 0xFF4500
            emoji = "🌟🔥"
            rarity_text = "🌟🔥 ЛЕГЕНДАРНЫЙ СУПЕР-ДРОП!!!"
        else:
            rarity = "Обычная"
            min_c, max_c = 15, 35
            color = 0xA8A8A8
            emoji = "🪙"

            for r in RARITIES:
                if roll <= r[1]:
                    rarity = r[0]
                    min_c = r[2]
                    max_c = r[3]
                    color = r[4]
                    emoji = r[5]
                    break

            reward = random.randint(min_c, max_c)
            title = f"{emoji} {rarity} награда!"
            rarity_text = f"**Редкость:** {rarity} ({min_c}–{max_c} {ECONOMY_EMOJIS['coin']})"

        # Стрик-бонус 10%
        bonus = 0
        if last > 0:
            last_date = datetime.fromtimestamp(last, tz=timezone.utc).date()
            today_date = datetime.now(timezone.utc).date()
            if (today_date - last_date).days == 1:
                bonus = int(reward * 0.1)
                reward += bonus

        # Начисляем монеты
        economy_data[user_id]["balance"] += reward
        economy_data[user_id]["last_daily"] = now
        save_economy()

        # Создаём основной embed один раз
        embed = discord.Embed(
            title=title,
            description=f"**+{format_number(reward)}** {ECONOMY_EMOJIS['coin']}",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        # Супер-дроп или обычная информация
        if is_super_drop:
            embed.add_field(
                name="🎉 СУПЕР-ДРОП!",
                value=f"Ты словил легендарный бонус!\nШанс был всего **{SUPER_DROP_CHANCE}%** 🔥",
                inline=False
            )
        else:
            embed.add_field(name="📊 Детали", value=rarity_text, inline=True)

        # Стрик
        if bonus > 0:
            embed.add_field(
                name="🔥 Стрик",
                value=f"+{format_number(bonus)} (10%)",
                inline=True
            )

        # Налог
        if tax > 0:
            embed.add_field(
                name=f"{ECONOMY_EMOJIS['tax']} Налог",
                value=f"**-{format_number(tax)}** {ECONOMY_EMOJIS['coin']}",
                inline=False
            )

        # ─── Сезонный XP за daily ───
        daily_xp = current_season["daily_xp_bonus"]
        if is_vip(ctx.author):
            daily_xp = int(daily_xp * 2)

        if user_id not in daily_season_xp_reset or daily_season_xp_reset[user_id] != today_str:
            daily_season_xp_earned[user_id] = 0
            daily_season_xp_reset[user_id] = today_str

        remaining_xp = current_season["max_daily_xp"] - daily_season_xp_earned.get(user_id, 0)
        xp_to_add = min(daily_xp, remaining_xp)

        if xp_to_add > 0:
            season_data[user_id]["season_xp"] += xp_to_add
            await check_and_level_up(user_id, ctx.author)
            daily_season_xp_earned[user_id] += xp_to_add

            # Ежедневное задание /daily
            prog = daily_tasks_progress.setdefault(user_id, {
                "messages": 0, "voice": 0, "daily": 0, "date": today_str
            })
            if prog["date"] != today_str:
                prog.update({"messages": 0, "voice": 0, "daily": 0, "date": today_str})
                daily_tasks_progress[user_id] = prog

            if prog["daily"] == 0:
                prog["daily"] = 1
                extra_xp = DAILY_TASKS["daily"]["xp"]
                season_data[user_id]["season_xp"] += extra_xp
                await check_and_level_up(user_id, ctx.author)
                embed.add_field(
                    name="✓ Ежедневное задание",
                    value=f"**{DAILY_TASKS['daily']['desc']}** → +{extra_xp} XP",
                    inline=False
                )

            save_seasons()
            save_daily_tasks()

            embed.add_field(
                name="🌟 Сезонный бонус",
                value=f"+{xp_to_add} XP за daily (сегодня: {daily_season_xp_earned[user_id]:,} / {current_season['max_daily_xp']:,})",
                inline=False
            )

            if daily_season_xp_earned[user_id] >= current_season["max_daily_xp"] * 0.9:
                embed.set_footer(
                    text=f"Баланс: {format_number(economy_data[user_id]['balance'])} • Почти достигнут лимит XP!"
                )

        # Финальный футер (если не переопределён выше)
        if not embed.footer.text:
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
        # Правильная фильтрация: только строковые user_id и только те, у кого есть словарь с балансом > 0
        users = []
        for uid, data in economy_data.items():
            if uid == "server_vault":
                continue
            if isinstance(data, dict) and "balance" in data and data["balance"] > 0:
                users.append((uid, data["balance"]))
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
        avg = total // len(users) if users else 0
        embed.add_field(
            name="📊 Статистика",
            value=f"**Всего монет:** {format_number(total)} {ECONOMY_EMOJIS['coin']}\n**Участников:** {len(users)}\n**Средний баланс:** {format_number(avg)} {ECONOMY_EMOJIS['coin']}",
            inline=False
        )
       
        embed.set_footer(text=f"Показано {min(10, len(users))} из {len(users)}")
        await ctx.send(embed=embed, ephemeral=True)
       
    except Exception as e:
        await send_error_embed(ctx, f"Ошибка в /top: {str(e)}")
        print(f"Ошибка в /top: {e}")
@bot.hybrid_command(name="shop", description="🛒 Магазин бустов и ролей")
async def shop(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)
        user_id = str(ctx.author.id)
        balance = economy_data.get(user_id, {}).get("balance", 0)
        embed = discord.Embed(
            title="🛒 Магазин MortisPlay",
            description=f"**Ваш баланс:** {format_number(balance)} {ECONOMY_EMOJIS['coin']}\nВыберите товар ниже",
            color=COLORS["economy"]
        )
        for key, item in SHOP_ITEMS.items():
            owned = False
            if key == "vip":
                role = discord.utils.get(ctx.guild.roles, name="VIP")
                owned = role in ctx.author.roles if role else False
            elif key == "multiplier":
                if "multiplier_end" in economy_data.get(user_id, {}):
                    end = economy_data[user_id]["multiplier_end"]
                    owned = end > datetime.now(timezone.utc).timestamp()
            status = "✅ Уже куплено" if owned else f"Цена: {format_number(item['price'])} {ECONOMY_EMOJIS['coin']}"
            embed.add_field(
                name=f"{item['name']} {'(Куплено)' if owned else ''}",
                value=f"{status}\n{item['description']}",
                inline=False
            )
        embed.set_footer(text="Нажмите кнопку → подтвердите в модалке • Баланс обновляется кнопкой внизу")
        view = ShopView(author_id=ctx.author.id)
        await ctx.send(embed=embed, view=view, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(
    name="season",
    description="Сезон, пропуск, квесты, магазин, топ и помощь"
)
@app_commands.describe(action="Что посмотреть")
@app_commands.choices(action=[
    app_commands.Choice(name="Информация о сезоне",     value="info"),
    app_commands.Choice(name="Пропуск сезона",          value="pass"),
    app_commands.Choice(name="Задания",                 value="tasks"),
    app_commands.Choice(name="Магазин сезона",          value="shop"),
    app_commands.Choice(name="Топ игроков сезона",      value="top"),
    app_commands.Choice(name="Помощь по сезону",        value="help"),
])
@tester_only
async def season(ctx: commands.Context, action: str = "info"):
    await ctx.defer(ephemeral=True)

    user_id = str(ctx.author.id)

    # ─── Инициализация данных ───
    if user_id not in season_data:
        season_data[user_id] = {
            "season_xp": 0,
            "season_level": 1,
            "season_points": 0,
            "claimed_rewards": []
        }
        save_seasons()

    if user_id not in economy_data:
        economy_data[user_id] = {"balance": 0}

    # Важно: инициализируем новые поля
    economy_data[user_id].setdefault("season_points", 0)
    economy_data[user_id].setdefault("season_purchases", [])
    economy_data[user_id].setdefault("premium_track_active", False)   # ← наш главный флаг

    # ─── Удобные переменные ───
    season_player    = season_data[user_id]
    season_xp        = season_player["season_xp"]
    season_level     = season_player["season_level"]
    season_points    = economy_data[user_id]["season_points"]
    season_purchases = economy_data[user_id]["season_purchases"]
    has_premium      = economy_data[user_id]["premium_track_active"]   # ← удобно
    claimed_rewards  = season_player["claimed_rewards"]

    embed = discord.Embed(color=0x9B59B6)

    if action == "info":
        current_level = 1
        while get_xp_for_level(current_level + 1) <= season_xp and current_level < 30:
            current_level += 1

        xp_current = get_xp_for_level(current_level)
        xp_next    = get_xp_for_level(current_level + 1)
        progress   = season_xp - xp_current
        needed     = xp_next - xp_current or 1
        percent    = min(100, int((progress / needed) * 100))

        bar = create_progress_bar(progress, needed, length=14)
        emoji = get_level_emoji(current_level)

        embed.title = f"{emoji} Сезон «{current_season['name']}» — Уровень {current_level}"
        embed.description = (
            f"**{ctx.author.mention}**, ты в эпичном сезоне **{current_season['name']}**!\n"
            f"Сезон завершится **{current_season['end_date']}**."
        )

        embed.add_field(name="🏅 Уровень", value=f"**{current_level}** → **{current_level + 1}**", inline=True)
        embed.add_field(name="✨ Опыт", value=f"**{format_number(season_xp)}** / **{format_number(xp_next)}** XP", inline=True)
        embed.add_field(name="Прогресс", value=f"`{bar}` **{percent}%**", inline=False)

        embed.add_field(name="🏆 Сезонные очки", value=f"**{format_number(season_points)}**", inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"MortisPlay • Сезон v1 • ID: {user_id}")

    elif action == "shop":
        # (твой старый код shop без изменений)
        embed.title = "🛍 Магазин сезона"
        embed.description = f"У тебя **{format_number(season_points)}** сезонных очков\nВыбери товар ниже"
        embed.color = 0xE67E22

        for item_id, item in SEASON_SHOP_ITEMS.items():
            owned = item_id in season_purchases
            status = "✅ Куплено" if owned else f"Цена: **{format_number(item['cost'])}** очков"
            embed.add_field(
                name=f"{item['name']} {'(Куплено)' if owned else ''}",
                value=f"{status}\n{item['description']}",
                inline=False
            )

        embed.set_footer(text="Нажми кнопку → подтверди покупку")
        view = SeasonShopView(author_id=ctx.author.id)
        await ctx.send(embed=embed, view=view, ephemeral=True)
        return

    elif action == "pass":
        # ──────────────────────── НОВЫЙ КРАСИВЫЙ БЛОК ────────────────────────
        if has_premium:
            embed.title = "✨ Premium Pass — Активен!"
            embed.color = 0xF1C40F
            embed.description = f"**{ctx.author.mention}**, ты уже на **Premium Track**! 🔥"
            
            embed.add_field(
                name="✅ Твои активные бонусы",
                value=(
                    "• **+50% к сезонному опыту** (сообщения, голос, daily)\n"
                    "• **+200 MortisCoin** к каждому `/daily`\n"
                    "• **+500** сезонных очков (получено при покупке)\n"
                    "• Эксклюзивные награды на уровнях\n"
                    "• Роль **Season Pass Holder** при 30 уровне"
                ),
                inline=False
            )
            embed.set_footer(text="Ты в элите сезона • MortisPlay Premium")
        else:
            embed.title = "✨ Premium Pass — Элитный трек сезона"
            embed.color = 0xFFD700
            embed.description = (
                f"**{ctx.author.mention}**, открой полный потенциал сезона **{current_season['name']}**!\n\n"
                "Купи Premium Pass и получи мощные преимущества:"
            )
            
            embed.add_field(
                name="Что даёт Premium Pass",
                value=(
                    "• **+50% к сезонному опыту** (всё быстрее)\n"
                    "• **+200 MortisCoin** к каждому `/daily`\n"
                    "• **+500** сезонных очков сразу\n"
                    "• Эксклюзивные награды и роли\n"
                    "• Роль **Season Pass Holder** при 30 уровне"
                ),
                inline=False
            )
            embed.add_field(name="Стоимость", value="**5000** MortisCoin 🪙\n(одноразово на весь сезон)", inline=True)
            embed.add_field(name="Статус", value="Не приобретён", inline=True)
            embed.set_footer(text="Купи сейчас — стань легендой сезона!")

    elif action == "tasks":
        # (твой старый код без изменений)
        embed.title = "📜 Ежедневные и еженедельные задания"
        embed.color = 0x2ECC71
        embed.description = "Выполняй задания каждый день — получай опыт и очки!"

        embed.add_field(
            name="Ежедневные задания",
            value=(
                "• Отправить **50 сообщений** → **+200 XP**\n"
                "• Провести **30 минут** в голосовом → **+300 XP**\n"
                "• Использовать `/daily` → **+100 XP**"
            ),
            inline=False
        )
        embed.add_field(
            name="Еженедельные задания",
            value=(
                "• Набрать **5000 XP** за неделю → **+1500 очков**\n"
                "• Купить что-либо в магазине сезона → **+800 очков**"
            ),
            inline=False
        )
        embed.set_footer(text="Обновление ежедневных заданий → 00:00 UTC")

    elif action == "top":
        embed.title = "🏆 Топ игроков сезона"
        embed.description = "Пока топ не реализован полностью.\nСкоро здесь будет топ-10 по уровням и очкам!"
        embed.color = 0x3498DB
        embed.add_field(name="Твой текущий ранг", value="Пока не в топ-100 (нужно больше активности!)", inline=False)
        embed.set_footer(text="Обновляется каждые 30 минут • Скоро будет полный топ")

    elif action == "help":
        # (можно оставить как было, или слегка улучшить — оставил твой вариант)
        embed.title = "❓ Помощь по сезону"
        embed.color = 0x3498DB
        embed.description = (
            f"**{ctx.author.mention}**, вот краткое руководство по сезону **{current_season['name']}**:\n\n"
            "1. **Как зарабатывать опыт (XP)?**\n"
            "   • Пиши сообщения → +3 XP (Premium: +4.5)\n"
            "   • Будь в голосовом → +2 XP/мин (Premium: +3)\n"
            "   • Выполняй `/daily` → +150 XP (Premium: +225 +200 монет)\n\n"
            "2. **Premium Pass (5000 MortisCoin)**\n"
            "   • +50% XP • +500 очков сразу • +200 монет к daily\n"
            "   • Эксклюзивная роль на 30 уровне\n\n"
            "3. **Как посмотреть прогресс?**\n"
            "   → `/season info` — уровень и XP\n"
            "   → `/season pass` — статус Premium\n"
            "   → `/season shop` — магазин\n"
            "   → `/season tasks` — задания"
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="MortisPlay • Сезон v1 • Задавай вопросы модераторам!")

    # Одна отправка для всех случаев, кроме shop
    await ctx.send(embed=embed, ephemeral=True)

@tasks.loop(minutes=10)
async def autosave_seasons_task():
    save_seasons()
    print("[AUTO] Сезонные данные сохранены")
def get_xp_for_level(level: int) -> int:
    """
    Формула XP для достижения уровня.
    Сейчас: 100 * level^1.5 — мягкий рост, можно потом поменять.
    """
    return int(100 * (level ** 1.5))
def get_current_level_and_progress(xp: int) -> tuple[int, int, int]:
    """
    Возвращает: (текущий уровень, XP на текущем уровне, XP до следующего уровня)
    """
    level = 1
    while True:
        xp_needed = get_xp_for_level(level + 1)
        if xp < xp_needed:
            break
        level += 1
   
    xp_for_current = get_xp_for_level(level)
    xp_for_next = get_xp_for_level(level + 1)
    progress_xp = xp - xp_for_current
    needed_for_next = xp_for_next - xp_for_current
   
    return level, progress_xp, needed_for_next

# ───────────────────────────────────────────────
# ПЕРЕОПРЕДЕЛЕНИЕ get_xp_for_level (правильная версия)
# ───────────────────────────────────────────────
def get_xp_for_level(level: int) -> int:
    """
    Возвращает общее количество XP, необходимое для достижения уровня level.
    Уровень 1 = 0 XP, уровень 2 = 100×2^1.5 и т.д.
    """
    if level <= 1:
        return 0
    return int(100 * (level ** 1.5))
# ───────────────────────────────────────────────
# ЗАПУСК
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
