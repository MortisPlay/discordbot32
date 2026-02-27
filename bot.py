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

# ───────────────────────────────────────────────
#   НАСТРОЙКИ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ───────────────────────────────────────────────
# Токен бота (обязательно)
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    print("❌ Ошибка: Не найден токен бота в переменных окружения!")
    print("Пожалуйста, установите переменную DISCORD_BOT_TOKEN")
    print("Пример для Windows (CMD): set DISCORD_BOT_TOKEN=ваш_токен")
    print("Пример для Windows (PowerShell): $env:DISCORD_BOT_TOKEN='ваш_токен'")
    print("Пример для Linux/Mac: export DISCORD_BOT_TOKEN='ваш_токен'")
    exit(1)

# ID владельца бота (можно оставить как есть или тоже вынести в переменные)
OWNER_ID = int(os.getenv('OWNER_ID', '765476979792150549'))

# ID сервера с полным доступом
FULL_ACCESS_GUILD_ID = int(os.getenv('FULL_ACCESS_GUILD_ID', '1474623510268739790'))

# ID каналов
MOD_LOG_CHANNEL_ID = int(os.getenv('MOD_LOG_CHANNEL_ID', '1475291899672657940'))
TICKET_ARCHIVE_CHANNEL_ID = int(os.getenv('TICKET_ARCHIVE_CHANNEL_ID', '1475338423513649347'))

# ID категории тикетов и роли поддержки
TICKET_CATEGORY_ID = int(os.getenv('TICKET_CATEGORY_ID', '1475334525344157807'))
SUPPORT_ROLE_ID = int(os.getenv('SUPPORT_ROLE_ID', '1475331888163066029'))
# ───────────────────────────────────────────────
#   ОСТАЛЬНЫЕ НАСТРОЙКИ
# ───────────────────────────────────────────────
PREFIX = "!"
WARNINGS_FILE = "warnings.json"
ECONOMY_FILE = "economy.json"
CASES_FILE = "cases.json"

SPAM_THRESHOLD = 5
SPAM_TIME = 8
ECONOMY_AUTOSAVE_INTERVAL = 300

DAILY_COOLDOWN = 86400
MESSAGE_COOLDOWN = 60
TAX_THRESHOLD = 10000
TAX_RATE = 0.01

# НАСТРОЙКИ ДЛЯ НОВЫХ ФУНКЦИЙ
WARN_AUTO_MUTE_THRESHOLD = 3      # 3 варна → мут 1ч
WARN_AUTO_LONG_MUTE_THRESHOLD = 6  # 6 варнов → мут 24ч
WARN_AUTO_KICK_THRESHOLD = 10      # 10 варнов → кик
WARN_EXPIRY_DAYS = 30              # срок действия варна

RAID_JOIN_THRESHOLD = 5            # порог рейда
RAID_TIME_WINDOW = 300             # окно в секундах (5 минут)
NEW_ACCOUNT_DAYS = 7                # возраст нового аккаунта

VIP_ROLE_NAMES = ["VIP", "Premium", "Vip", "vip"] # роли с повышенными лимитами
VIP_SPAM_MULTIPLIER = 2             # в 2 раза больше сообщений
VIP_MENTION_MULTIPLIER = 3          # в 3 раза больше упоминаний

# НОВЫЕ НАСТРОЙКИ
INACTIVE_TICKET_HOURS = 24          # через сколько часов тикет считается неактивным
INVESTMENT_MIN_AMOUNT = 1000        # минимальная сумма для инвестиций
INVESTMENT_MAX_DAYS = 30            # максимальный срок инвестиций
INVESTMENT_BASE_RATE = 0.05         # базовая процентная ставка (5%)
UNAUTHORIZED_CMD_LIMIT = 3          # количество попыток использовать команды без прав до мута
UNAUTHORIZED_MUTE_MINUTES = 1        # длительность мута за превышение лимита

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

# ───────────────────────────────────────────────
#   ГЛОБАЛЬНЫЕ ДАННЫЕ
# ───────────────────────────────────────────────
economy_data = {}
warnings_data = {}
cases_data = {}  # {case_id: case_info}
spam_cache = {}
raid_cache = defaultdict(list)
temp_roles = {}
investments_data = {}  # {user_id: [investment]}
unauthorized_attempts = defaultdict(list)  # Отслеживание попыток использовать команды без прав
faq_data = {}  # {category: [{"question": str, "answer": str}]}

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
    
    # Инициализируем investments если нет
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
#   ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ───────────────────────────────────────────────

async def check_unauthorized_commands(user: discord.Member):
    """Проверяет количество попыток использовать команды без прав"""
    user_id = str(user.id)
    now = datetime.utcnow().timestamp()
    
    # Очищаем старые попытки (старше 1 часа)
    unauthorized_attempts[user_id] = [t for t in unauthorized_attempts[user_id] if now - t < 3600]
    unauthorized_attempts[user_id].append(now)
    
    if len(unauthorized_attempts[user_id]) >= UNAUTHORIZED_CMD_LIMIT:
        # Мутим пользователя
        try:
            await user.timeout(timedelta(minutes=UNAUTHORIZED_MUTE_MINUTES), reason="Превышение лимита попыток использования команд без прав")
            await send_punishment_log(
                member=user,
                punishment_type="🔇 Мут (авто)",
                duration=f"{UNAUTHORIZED_MUTE_MINUTES} мин",
                reason="Превышение лимита попыток использования модераторских команд",
                moderator=bot.user
            )
            # Очищаем попытки после мута
            unauthorized_attempts[user_id] = []
            return True
        except:
            pass
    return False

def format_number(num: int) -> str:
    """Форматирует число с разделителями тысяч"""
    return f"{num:,}".replace(",", " ")

def get_rank_emoji(balance: int) -> str:
    """Возвращает эмодзи в зависимости от баланса"""
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
    """Создает прогресс-бар"""
    if max_value <= 0:
        return "█" * length
    progress = min(current / max_value, 1.0)
    filled = int(progress * length)
    bar = "█" * filled + "░" * (length - filled)
    return bar

def generate_case_id() -> str:
    """Генерирует уникальный ID для кейса"""
    return str(uuid.uuid4())[:8]

async def create_case(member: discord.Member, moderator: discord.User, action: str, reason: str, duration: str = None):
    """Создает запись о наказании"""
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
        "timestamp": datetime.utcnow().isoformat()
    }
    save_cases()
    return case_id

async def get_case(case_id: str) -> dict:
    """Получает информацию о кейсе"""
    return cases_data.get(case_id)

def is_vip(member: discord.Member) -> bool:
    """Проверяет, есть ли у пользователя VIP роль"""
    if not member:
        return False
    for role in member.roles:
        if role.name in VIP_ROLE_NAMES:
            return True
    return False

def clean_old_warnings(user_id: str):
    """Удаляет варны старше WARN_EXPIRY_DAYS"""
    if user_id not in warnings_data:
        return
    
    now = datetime.utcnow()
    fresh_warnings = []
    
    for warn in warnings_data[user_id]:
        try:
            warn_time = datetime.strptime(warn["time"], "%Y-%m-%d %H:%M:%S")
            if (now - warn_time).days < WARN_EXPIRY_DAYS:
                fresh_warnings.append(warn)
        except:
            continue
    
    warnings_data[user_id] = fresh_warnings
    if not fresh_warnings:
        del warnings_data[user_id]
    save_warnings()

def get_warning_count(user_id: str) -> int:
    """Возвращает количество активных варнов пользователя"""
    clean_old_warnings(user_id)
    return len(warnings_data.get(user_id, []))

async def check_auto_punishment(member: discord.Member, reason: str = "Автоматически"):
    """Проверяет количество варнов и применяет наказание"""
    if not member:
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
    """Отправляет лог наказания в мод-лог с кнопками"""
    if not MOD_LOG_CHANNEL_ID:
        return
    
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    
    embed = discord.Embed(
        title=f"🛠️ Наказание {f'[#{case_id}]' if case_id else ''}",
        color=0xF04747,
        timestamp=datetime.utcnow()
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
    
    # Создаем кнопки для быстрых действий
    view = ModActionView(member)
    await log_ch.send(embed=embed, view=view)

async def send_mod_log(title: str, description: str = None, color: int = 0x5865F2, fields: list = None):
    if not MOD_LOG_CHANNEL_ID:
        return
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return

    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
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

def is_protected(member: discord.Member, ctx: commands.Context) -> bool:
    if member.id == OWNER_ID or member.guild_permissions.administrator:
        return True
    if member.top_role >= ctx.author.top_role:
        return True
    return False

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
    now = datetime.utcnow().timestamp()
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
#   КЛАССЫ ДЛЯ НОВЫХ ФУНКЦИЙ
# ───────────────────────────────────────────────

class ModActionView(View):
    """Кнопки для быстрых модераторских действий"""
    def __init__(self, member: discord.Member):
        super().__init__(timeout=180)
        self.member = member

    @discord.ui.button(label="Предупредить", style=discord.ButtonStyle.secondary, emoji="⚠️")
    async def warn_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
        
        modal = WarnModal(self.member)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Замутить", style=discord.ButtonStyle.danger, emoji="🔇")
    async def mute_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
        
        modal = MuteModal(self.member)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Очистить", style=discord.ButtonStyle.success, emoji="🧹")
    async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
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
        
        # Вызываем команду warn
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

class TicketCategorySelect(Select):
    """Выбор категории тикета"""
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
        
        # Создаем тикет с выбранной категорией
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

        # Определяем эмодзи для категории
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

        # Описания категорий
        category_descriptions = {
            "tech": "Техническая проблема",
            "complaint": "Жалоба на игрока",
            "question": "Вопрос по серверу",
            "partner": "Сотрудничество",
            "other": "Другое"
        }

        embed = discord.Embed(
            title=f"🎟️ Тикет: {category_descriptions.get(self.values[0], 'Обращение')}",
            description=f"Спасибо, {interaction.user.mention}!\nМодератор уже в пути.\n\n**Категория:** {self.values[0]}\n\n**Закрыть тикет — нажми красную кнопку ниже.**\n\n"
                       f"⚠️ Тикет будет автоматически закрыт через {INACTIVE_TICKET_HOURS} часов неактивности.",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"ID пользователя: {interaction.user.id}")

        view = TicketControls()
        await ticket_channel.send(content=f"{interaction.user.mention} {support_role.mention}", embed=embed, view=view)

        await interaction.followup.send(f"✅ Тикет создан: {ticket_channel.mention}", ephemeral=True)

        await send_mod_log(
            title="📩 Новый тикет создан",
            description=f"**Канал:** {ticket_channel.mention}\n**Автор:** {interaction.user}\n**Категория:** {self.values[0]}",
            color=0x57F287
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
                    now = datetime.utcnow()
                    
                    if (now - last_msg_time).total_seconds() > INACTIVE_TICKET_HOURS * 3600:
                        # Отправляем предупреждение
                        warning_embed = discord.Embed(
                            title="⚠️ Тикет неактивен",
                            description=f"Этот тикет будет автоматически закрыт через 12 часов из-за неактивности.",
                            color=0xFAA61A
                        )
                        await channel.send(embed=warning_embed)
                        
                        # Ждем 12 часов
                        await asyncio.sleep(43200)  # 12 часов
                        
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

class FAQCategorySelect(Select):
    """Выбор категории FAQ"""
    def __init__(self):
        options = []
        for key, name in FAQ_CATEGORIES.items():
            # Определяем эмодзи для каждой категории
            if "общее" in key:
                emoji = "📋"
            elif "правила" in key:
                emoji = "📜"
            elif "экономика" in key:
                emoji = "💰"
            elif "модерация" in key:
                emoji = "🛡️"
            elif "техника" in key:
                emoji = "🔧"
            else:
                emoji = "❓"
            
            options.append(discord.SelectOption(label=name, value=key, emoji=emoji))
        
        super().__init__(placeholder="Выберите категорию вопросов...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        questions = faq_data.get(category, [])
        
        if not questions:
            return await interaction.response.send_message("❌ В этой категории пока нет вопросов.", ephemeral=True)
        
        # Создаем новое view с вопросами
        view = FAQQuestionsView(category, questions, interaction.user)
        await interaction.response.edit_message(content=f"**{FAQ_CATEGORIES[category]}**\nВыберите вопрос:", embed=None, view=view)

class FAQQuestionsView(View):
    """View с вопросами FAQ"""
    def __init__(self, category: str, questions: list, author: discord.User):
        super().__init__(timeout=60)
        self.category = category
        self.questions = questions
        self.author = author
        self.current_page = 0
        self.items_per_page = 5
        self.add_question_buttons()

    def add_question_buttons(self):
        # Очищаем старые кнопки
        self.clear_items()
        
        # Добавляем кнопки с вопросами
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, len(self.questions))
        page_questions = self.questions[start:end]
        
        for i, q in enumerate(page_questions, start=1):
            # Создаем callback для каждой кнопки
            async def button_callback(interaction: discord.Interaction, question=q):
                if interaction.user.id != self.author.id:
                    return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
                
                embed = discord.Embed(
                    title=f"❓ {question['question']}",
                    description=question['answer'],
                    color=0x57F287
                )
                embed.set_footer(text=f"Категория: {FAQ_CATEGORIES[self.category]}")
                
                # Кнопка "Назад"
                view = View(timeout=60)
                back_button = Button(label="◀️ Назад к списку", style=discord.ButtonStyle.secondary)
                
                async def back_callback(interaction: discord.Interaction):
                    await self.show_questions(interaction)
                
                back_button.callback = back_callback
                view.add_item(back_button)
                
                await interaction.response.edit_message(embed=embed, view=view)
            
            button = Button(label=f"{start + i}. {q['question'][:50]}...", style=discord.ButtonStyle.secondary)
            button.callback = button_callback
            self.add_item(button)
        
        # Добавляем кнопки навигации
        if self.current_page > 0:
            prev_button = Button(label="◀️", style=discord.ButtonStyle.primary)
            prev_button.callback = self.prev_page
            self.add_item(prev_button)
        
        if end < len(self.questions):
            next_button = Button(label="▶️", style=discord.ButtonStyle.primary)
            next_button.callback = self.next_page
            self.add_item(next_button)
        
        # Кнопка назад к категориям
        back_to_cat_button = Button(label="🏠 К категориям", style=discord.ButtonStyle.success)
        back_to_cat_button.callback = self.back_to_categories
        self.add_item(back_to_cat_button)

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
            color=0x57F287
        )
        await interaction.response.edit_message(embed=embed, view=view)

class FAQView(View):
    """Главное меню FAQ"""
    def __init__(self, author: discord.User):
        super().__init__(timeout=60)
        self.author = author
        self.add_item(FAQCategorySelect())

class TicketPanelView(View):
    """Обновленная панель тикетов с категориями"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Создать тикет", style=discord.ButtonStyle.green, emoji="🎟️", custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Показываем выбор категории
        embed = discord.Embed(
            title="🎫 Выбор категории тикета",
            description="Пожалуйста, выберите категорию вашего обращения:",
            color=0x57F287
        )
        
        view = View(timeout=60)
        view.add_item(TicketCategorySelect())
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class TicketControls(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.last_activity = datetime.utcnow()

    @discord.ui.button(label="Закрыть тикет", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            # Отслеживаем попытку использования без прав
            await check_unauthorized_commands(interaction.user)
            return await interaction.response.send_message("❌ Только модераторы могут закрыть тикет.", ephemeral=True)

        await interaction.response.send_message("🔒 Тикет закрывается через 5 секунд... (готовим транскрипт)", ephemeral=False)

        transcript_lines = []
        async for msg in interaction.channel.history(limit=1000, oldest_first=True):
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = f"{msg.author} ({msg.author.id})"
            content = msg.content or "[пустое сообщение]"
            attachments = "\n".join([a.url for a in msg.attachments]) if msg.attachments else ""
            if attachments:
                content += f"\nВложения: {attachments}"
            transcript_lines.append(f"[{timestamp}] {author}:\n{content}\n{'─'*60}\n")

        transcript_text = "".join(transcript_lines) or "[В тикете не было сообщений]"

        filename = f"транскрипт_{interaction.channel.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        file = discord.File(io.StringIO(transcript_text), filename=filename)

        archive_channel_id = TICKET_ARCHIVE_CHANNEL_ID or MOD_LOG_CHANNEL_ID
        archive_ch = bot.get_channel(archive_channel_id)
        if archive_ch:
            short_embed = discord.Embed(
                title="📜 Тикет закрыт — транскрипт",
                description=f"**Канал:** {interaction.channel.name}\n**Закрыл:** {interaction.user.mention}",
                color=0x7289DA,
                timestamp=datetime.utcnow()
            )
            short_embed.set_footer(text=f"Сообщений: {len(transcript_lines)}")
            await archive_ch.send(embed=short_embed, file=file)
        else:
            await send_mod_log(
                title="📜 Транскрипт тикета (архив не найден)",
                description=f"Канал: {interaction.channel.name}\nЗакрыл: {interaction.user}",
                color=0x7289DA
            )

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
    """Красивое меню помощи с разделением по правам"""
    def __init__(self, author: discord.User, is_mod: bool):
        super().__init__(timeout=60)
        self.author = author
        self.current_page = 0
        
        # Базовые категории для всех
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
                    ("/invest", "Инвестировать монеты"),
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
        
        # Модераторские категории (только для модераторов)
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
                        ("/faqadd", "Добавить вопрос в FAQ")
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
            color=0x57F287
        )
        
        for cmd, desc in category["commands"]:
            embed.add_field(name=cmd, value=desc, inline=False)
        
        embed.set_footer(text=f"Страница {self.current_page + 1} из {len(self.categories)} • Используй кнопки для навигации")
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
        
        is_mod = interaction.user.guild_permissions.manage_messages or interaction.user.guild_permissions.administrator
        base_categories = "**📋 Основное** - общие команды\n**💰 Экономика** - команды экономики\n**🎮 Развлечения** - развлекательные команды"
        mod_categories = "\n**🛡️ Модерация** - модераторские команды\n**🎫 Тикеты** - система тикетов" if is_mod else ""
        
        embed = discord.Embed(
            title="🤖 Помощь по командам",
            description=f"Используй кнопки ниже для навигации по категориям\n\n{base_categories}{mod_categories}",
            color=0x57F287
        )
        embed.set_footer(text="Выбери категорию стрелками")
        self.current_page = 0
        await interaction.response.edit_message(embed=embed, view=self)

# ───────────────────────────────────────────────
#   ИНИЦИАЛИЗАЦИЯ БОТА
# ───────────────────────────────────────────────

intents = discord.Intents(
    guilds=True,
    members=True,
    presences=True,
    message_content=True,
    voice_states=True,
    moderation=True
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
    """Очищает старые варны раз в час"""
    global warnings_data
    now = datetime.utcnow()
    changed = False
    
    for user_id in list(warnings_data.keys()):
        fresh_warnings = []
        for warn in warnings_data[user_id]:
            try:
                warn_time = datetime.strptime(warn["time"], "%Y-%m-%d %H:%M:%S")
                if (now - warn_time).days < WARN_EXPIRY_DAYS:
                    fresh_warnings.append(warn)
            except:
                continue
        
        if len(fresh_warnings) != len(warnings_data[user_id]):
            changed = True
            if fresh_warnings:
                warnings_data[user_id] = fresh_warnings
            else:
                del warnings_data[user_id]
    
    if changed:
        save_warnings()
        print("[AUTO] Старые варны очищены")

@tasks.loop(minutes=1)
async def check_temp_roles_task():
    """Проверяет и удаляет истекшие временные роли"""
    for guild in bot.guilds:
        for member in guild.members:
            user_id = str(member.id)
            if user_id in temp_roles:
                now = datetime.utcnow().timestamp()
                to_remove = []
                
                for role_id, expiry in temp_roles[user_id].items():
                    if now >= expiry:
                        role = guild.get_role(int(role_id))
                        if role and role in member.roles:
                            try:
                                await member.remove_roles(role, reason="Временная роль истекла")
                                await send_mod_log(
                                    title="⏱️ Временная роль снята",
                                    description=f"**Пользователь:** {member.mention}\n**Роль:** {role.mention}",
                                    color=0x7289DA
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
    """Проверяет и выплачивает проценты по инвестициям"""
    now = datetime.utcnow().timestamp()
    
    for user_id, data in economy_data.items():
        if user_id == "server_vault" or "investments" not in data:
            continue
        
        active_investments = []
        for inv in data["investments"]:
            if inv["end_time"] <= now:
                # Инвестиция завершена - выплачиваем
                profit = inv["profit"]
                data["balance"] += profit
                
                # Логируем
                user = bot.get_user(int(user_id))
                if user:
                    embed = discord.Embed(
                        title=f"{ECONOMY_EMOJIS['profit']} Инвестиция завершена",
                        description=f"Ваша инвестиция на {inv['days']} дней завершена!\n"
                                   f"**Прибыль:** +{format_number(profit)} {ECONOMY_EMOJIS['coin']}",
                        color=0x57F287
                    )
                    try:
                        await user.send(embed=embed)
                    except:
                        pass
            else:
                active_investments.append(inv)
        
        data["investments"] = active_investments
    
    save_economy()
    print("[AUTO] Инвестиции проверены")

@tasks.loop(hours=1)
async def check_inactive_tickets_task():
    """Проверяет неактивные тикеты"""
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

    await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.watching, name="mortisplay.ru"))

    try:
        synced = await bot.tree.sync()
        print(f"Команды синхронизированы: {len(synced)} шт")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")

    for guild in bot.guilds:
        await guild.chunk()

    bot.add_view(TicketPanelView())
    bot.add_view(TicketControls())

    autosave_economy_task.start()
    clean_old_warnings_task.start()
    check_temp_roles_task.start()
    check_investments_task.start()
    check_inactive_tickets_task.start()

    bot.launch_time = datetime.now(timezone.utc)
    print("Бот полностью готов к работе")

@bot.event
async def on_member_join(member):
    if member.guild.system_channel:
        # Создаем красивое приветствие с подробной информацией
        embed = discord.Embed(
            title="🎉 Новый участник!",
            description=f"**{member.mention}**, добро пожаловать на сервер **{member.guild.name}**!",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Добавляем подробную информацию
        account_age = datetime.utcnow() - member.created_at
        days = account_age.days
        hours = account_age.seconds // 3600
        
        embed.add_field(
            name="📅 Возраст аккаунта",
            value=f"**{days}** дней, **{hours}** часов",
            inline=True
        )
        
        embed.add_field(
            name="👥 Участников теперь",
            value=f"**{member.guild.member_count}**",
            inline=True
        )
        
        # Проверка на новый аккаунт
        if days < NEW_ACCOUNT_DAYS:
            embed.add_field(
                name="⚠️ Внимание",
                value="Аккаунт создан недавно! Рекомендуем ознакомиться с правилами.",
                inline=False
            )
        
        # Добавляем полезные советы
        embed.add_field(
            name="📋 Что делать?",
            value="• Ознакомься с правилами в канале правил\n• Представься в канале приветствий\n• Заходи в голосовые каналы",
            inline=False
        )
        
        embed.set_footer(text=f"ID: {member.id}")
        
        await member.guild.system_channel.send(embed=embed)
    
    # Проверка на новый аккаунт (логирование)
    account_age = datetime.utcnow() - member.created_at
    if account_age.days < NEW_ACCOUNT_DAYS:
        await send_mod_log(
            title="🆕 Новый аккаунт",
            description=f"**Пользователь:** {member.mention}\n**Возраст аккаунта:** {account_age.days} дней",
            color=0xFAA61A
        )

@bot.event
async def on_member_remove(member):
    if member.guild.system_channel:
        # Улучшенное прощание
        embed = discord.Embed(
            title="👋 Пользователь покинул нас",
            description=f"**{member}** покинул сервер...",
            color=0xF04747,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Время на сервере
        if member.joined_at:
            time_on_server = datetime.utcnow() - member.joined_at
            days = time_on_server.days
            embed.add_field(
                name="⏱️ Провел на сервере",
                value=f"**{days}** дней",
                inline=True
            )
        
        embed.add_field(
            name="👥 Осталось участников",
            value=f"**{member.guild.member_count}**",
            inline=True
        )
        
        embed.set_footer(text=f"ID: {member.id}")
        
        await member.guild.system_channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.guild_permissions.administrator or message.author.id == OWNER_ID:
        return await bot.process_commands(message)

    if bot.user in message.mentions:
        await message.channel.send(f"{message.author.mention}, я тут! Используй `/help`")

    user_id = str(message.author.id)
    now = datetime.utcnow().timestamp()

    # Анти-спам с учетом VIP ролей
    spam_threshold = SPAM_THRESHOLD
    mention_limit = 4
    
    if is_vip(message.author):
        spam_threshold = SPAM_THRESHOLD * VIP_SPAM_MULTIPLIER
        mention_limit = 4 * VIP_MENTION_MULTIPLIER

    if user_id not in spam_cache:
        spam_cache[user_id] = []
    spam_cache[user_id] = [t for t in spam_cache[user_id] if now - t < SPAM_TIME]
    spam_cache[user_id].append(now)

    # Проверка на спам
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

    # Проверка на массовые упоминания
    mention_count = len(message.mentions) + len(message.role_mentions)
    
    # Проверка на @everyone/@here
    if ("@everyone" in message.content or "@here" in message.content) and not message.author.guild_permissions.mention_everyone:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, у тебя нет прав на массовые упоминания!", delete_after=8)
        return
    
    # Анти-масс-пинг
    if mention_count > mention_limit:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, не спамь упоминаниями! (лимит: {mention_limit})", delete_after=8)
        
        # Добавляем варн за масс-пинг
        if user_id not in warnings_data:
            warnings_data[user_id] = []
        warnings_data[user_id].append({
            "moderator": "Автомодерация",
            "reason": f"Массовый пинг ({mention_count} упоминаний)",
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_warnings()
        
        # Создаем кейс
        case_id = await create_case(message.author, bot.user, "Варн (авто)", f"Массовый пинг ({mention_count} упоминаний)")
        
        # Проверяем на авто-наказание
        await check_auto_punishment(message.author, "Массовый пинг")
        return

    if len(message.content) > 15:
        upper_ratio = sum(1 for c in message.content if c.isupper()) / len(message.content)
        if upper_ratio > 0.75:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, не кричи (капс)!", delete_after=8)
            return

    if re.search(r"discord\.(gg|com/invite)/", message.content.lower()):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, реклама запрещена!", delete_after=10)
        return

    if is_toxic(message.content):
        await message.delete()

        toxic_warnings = [w for w in warnings_data.get(user_id, []) if "токсичность" in w.get("reason", "").lower()]

        if len(toxic_warnings) >= 1:
            try:
                await message.author.timeout(timedelta(hours=24), reason="Повторная токсичность / оскорбления")
                await message.channel.send(
                    f"{message.author.mention}, **мут 24 часа** за повторные оскорбления.\n"
                    "Правила сервера: без перехода на личности и токсичности."
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
                await message.author.timeout(timedelta(hours=1), reason="Токсичность / оскорбления")
                await message.channel.send(
                    f"{message.author.mention}, **мут 1 час** за оскорбления/токсичность.\n"
                    "Мат разрешён в дружеской беседе, но **без перехода на личности**.\n"
                    "Повтор → мут 24 часа."
                )

                if user_id not in warnings_data:
                    warnings_data[user_id] = []
                warnings_data[user_id].append({
                    "moderator": "Автомодерация",
                    "reason": "Токсичность / оскорбления",
                    "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                })
                save_warnings()
                
                case_id = await create_case(message.author, bot.user, "Авто-мут 1ч", "Токсичность/оскорбления", "1 час")
                await send_punishment_log(
                    member=message.author,
                    punishment_type="🔇 Мут 1ч (авто)",
                    duration="1 час",
                    reason="Токсичность / оскорбления",
                    moderator=bot.user,
                    case_id=case_id
                )

            except:
                await message.channel.send(f"{message.author.mention}, удали оскорбления пожалуйста, иначе будет мут.")

        return

    if has_full_access(message.guild.id):
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}

        if now - economy_data[user_id].get("last_message", 0) >= MESSAGE_COOLDOWN:
            earn = random.randint(1, 5)
            economy_data[user_id]["balance"] += earn
            economy_data[user_id]["last_message"] = now
            save_economy()

    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if message.author.bot or not MOD_LOG_CHANNEL_ID: return
    await send_mod_log(
        title="🗑 Сообщение удалено",
        description=f"**Автор:** {message.author}\n**Канал:** {message.channel.mention}",
        color=0xF04747,
        fields=[("Содержимое", message.content[:900] or "[пусто / embed]", False)]
    )

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content or not MOD_LOG_CHANNEL_ID: return
    await send_mod_log(
        title="✏️ Сообщение изменено",
        description=f"**Автор:** {before.author}\n**Канал:** {before.channel.mention}",
        color=0xFAA61A,
        fields=[
            ("Было", before.content[:500] or "[пусто]", False),
            ("Стало", after.content[:500] or "[пусто]", False)
        ]
    )


# ───────────────────────────────────────────────
#   НОВАЯ СИСТЕМА ЛОГИРОВАНИЯ (ВМЕСТО АУДИТА)
# ───────────────────────────────────────────────

@bot.event
async def on_message_delete(message):
    """Логирование удаления сообщений"""
    if message.author.bot or not MOD_LOG_CHANNEL_ID:
        return
    
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    
    embed = discord.Embed(
        title="🗑 Сообщение удалено",
        color=0xF04747,
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(name="Автор", value=message.author.mention, inline=True)
    embed.add_field(name="Канал", value=message.channel.mention, inline=True)
    embed.add_field(name="ID автора", value=f"`{message.author.id}`", inline=True)
    
    if message.content:
        embed.add_field(name="Содержимое", value=message.content[:900] + ("..." if len(message.content) > 900 else ""), inline=False)
    else:
        embed.add_field(name="Содержимое", value="*Пустое сообщение или медиа*", inline=False)
    
    await log_ch.send(embed=embed)


@bot.event
async def on_message_edit(before, after):
    """Логирование изменения сообщений"""
    if before.author.bot or before.content == after.content or not MOD_LOG_CHANNEL_ID:
        return
    
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    
    embed = discord.Embed(
        title="✏️ Сообщение изменено",
        color=0xFAA61A,
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(name="Автор", value=before.author.mention, inline=True)
    embed.add_field(name="Канал", value=before.channel.mention, inline=True)
    embed.add_field(name="ID автора", value=f"`{before.author.id}`", inline=True)
    
    embed.add_field(name="Было", value=before.content[:500] + ("..." if len(before.content) > 500 else "") or "*Пусто*", inline=False)
    embed.add_field(name="Стало", value=after.content[:500] + ("..." if len(after.content) > 500 else "") or "*Пусто*", inline=False)
    
    await log_ch.send(embed=embed)


@bot.event
async def on_member_update(before, after):
    """Логирование изменений участников"""
    if not MOD_LOG_CHANNEL_ID:
        return
    
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    
    # Проверка изменения ника
    if before.nick != after.nick:
        embed = discord.Embed(
            title="👤 Никнейм изменён",
            color=0xFAA61A,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Пользователь", value=after.mention, inline=True)
        embed.add_field(name="ID", value=f"`{after.id}`", inline=True)
        embed.add_field(name="Было", value=before.nick or "*Не указан*", inline=True)
        embed.add_field(name="Стало", value=after.nick or "*Не указан*", inline=True)
        await log_ch.send(embed=embed)
    
    # Проверка изменения ролей
    if before.roles != after.roles:
        added_roles = [role for role in after.roles if role not in before.roles and role.name != "@everyone"]
        removed_roles = [role for role in before.roles if role not in after.roles and role.name != "@everyone"]
        
        if added_roles or removed_roles:
            embed = discord.Embed(
                title="👤 Роли изменены",
                color=0xFAA61A,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Пользователь", value=after.mention, inline=True)
            embed.add_field(name="ID", value=f"`{after.id}`", inline=True)
            
            if added_roles:
                embed.add_field(name="✅ Добавлены", value=", ".join([r.mention for r in added_roles]), inline=False)
            if removed_roles:
                embed.add_field(name="❌ Удалены", value=", ".join([r.mention for r in removed_roles]), inline=False)
            
            await log_ch.send(embed=embed)
    
    # Проверка мута/таймаута
    if before.timed_out_until != after.timed_out_until:
        if after.timed_out_until:
            # Рассчитываем длительность
            duration = after.timed_out_until - datetime.utcnow()
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            duration_text = f"{hours}ч {minutes}м"
            
            case_id = await create_case(after, bot.user, "Мут", "Автоматически", duration_text)
            
            embed = discord.Embed(
                title="🔇 Пользователь замучен",
                color=0xF04747,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Пользователь", value=after.mention, inline=True)
            embed.add_field(name="ID", value=f"`{after.id}`", inline=True)
            embed.add_field(name="Длительность", value=duration_text, inline=True)
            embed.add_field(name="До", value=f"<t:{int(after.timed_out_until.timestamp())}:R>", inline=True)
            embed.add_field(name="Кейс", value=f"`{case_id}`", inline=False)
            
            await log_ch.send(embed=embed)
        else:
            case_id = await create_case(after, bot.user, "Снятие мута", "Автоматически")
            
            embed = discord.Embed(
                title="🔊 Мут снят",
                color=0x57F287,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Пользователь", value=after.mention, inline=True)
            embed.add_field(name="ID", value=f"`{after.id}`", inline=True)
            embed.add_field(name="Кейс", value=f"`{case_id}`", inline=False)
            
            await log_ch.send(embed=embed)


@bot.event
async def on_member_ban(guild, user):
    """Логирование бана"""
    if not MOD_LOG_CHANNEL_ID:
        return
    
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    
    # Пытаемся получить информацию из аудит лога (если повезет)
    reason = "Не указана"
    moderator = "Неизвестно"
    
    try:
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            if entry.target.id == user.id:
                reason = entry.reason or "Не указана"
                moderator = entry.user.mention if entry.user else "Неизвестно"
                break
    except:
        pass
    
    case_id = await create_case(user, bot.user, "Бан", reason)
    
    embed = discord.Embed(
        title="🔨 Бан",
        color=0xF04747,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Пользователь", value=f"{user.mention if hasattr(user, 'mention') else user}", inline=True)
    embed.add_field(name="ID", value=f"`{user.id}`", inline=True)
    embed.add_field(name="Модератор", value=moderator, inline=True)
    embed.add_field(name="Причина", value=reason, inline=False)
    embed.add_field(name="Кейс", value=f"`{case_id}`", inline=False)
    
    await log_ch.send(embed=embed)


@bot.event
async def on_member_unban(guild, user):
    """Логирование разбана"""
    if not MOD_LOG_CHANNEL_ID:
        return
    
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    
    embed = discord.Embed(
        title="🔓 Разбан",
        color=0x57F287,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Пользователь", value=f"{user.mention if hasattr(user, 'mention') else user}", inline=True)
    embed.add_field(name="ID", value=f"`{user.id}`", inline=True)
    
    await log_ch.send(embed=embed)


@bot.event
async def on_member_join(member):
    """Логирование входа (уже есть, просто добавим в канал логов)"""
    # Отправляем в системный канал (как уже есть)
    if member.guild.system_channel:
        embed = discord.Embed(
            title="🎉 Новый участник!",
            description=f"**{member.mention}**, добро пожаловать на сервер **{member.guild.name}**!",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        account_age = datetime.utcnow() - member.created_at
        days = account_age.days
        
        embed.add_field(name="📅 Возраст аккаунта", value=f"**{days}** дней", inline=True)
        embed.add_field(name="👥 Участников теперь", value=f"**{member.guild.member_count}**", inline=True)
        
        if days < NEW_ACCOUNT_DAYS:
            embed.add_field(name="⚠️ Внимание", value="Аккаунт создан недавно!", inline=False)
        
        embed.set_footer(text=f"ID: {member.id}")
        await member.guild.system_channel.send(embed=embed)
    
    # Отправляем в канал логов
    if MOD_LOG_CHANNEL_ID:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            embed = discord.Embed(
                title="📥 Участник зашёл",
                color=0x57F287,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Пользователь", value=member.mention, inline=True)
            embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
            embed.add_field(name="Возраст аккаунта", value=f"{days} дней", inline=True)
            await log_ch.send(embed=embed)


@bot.event
async def on_member_remove(member):
    """Логирование выхода"""
    # Отправляем в системный канал (как уже есть)
    if member.guild.system_channel:
        embed = discord.Embed(
            title="👋 Пользователь покинул нас",
            description=f"**{member}** покинул сервер...",
            color=0xF04747,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        if member.joined_at:
            time_on_server = datetime.utcnow() - member.joined_at
            days = time_on_server.days
            embed.add_field(name="⏱️ Провел на сервере", value=f"**{days}** дней", inline=True)
        
        embed.add_field(name="👥 Осталось участников", value=f"**{member.guild.member_count}**", inline=True)
        embed.set_footer(text=f"ID: {member.id}")
        await member.guild.system_channel.send(embed=embed)
    
    # Отправляем в канал логов
    if MOD_LOG_CHANNEL_ID:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            embed = discord.Embed(
                title="📤 Участник вышел",
                color=0xF04747,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Пользователь", value=str(member), inline=True)
            embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
            
            if member.joined_at:
                time_on_server = datetime.utcnow() - member.joined_at
                days = time_on_server.days
                embed.add_field(name="Провел на сервере", value=f"{days} дней", inline=True)
            
            await log_ch.send(embed=embed)


@bot.event
async def on_guild_channel_create(channel):
    """Логирование создания канала"""
    if not MOD_LOG_CHANNEL_ID:
        return
    
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    
    embed = discord.Embed(
        title="📢 Канал создан",
        color=0x57F287,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Канал", value=channel.mention, inline=True)
    embed.add_field(name="Название", value=channel.name, inline=True)
    embed.add_field(name="Тип", value=str(channel.type), inline=True)
    
    await log_ch.send(embed=embed)


@bot.event
async def on_guild_channel_delete(channel):
    """Логирование удаления канала"""
    if not MOD_LOG_CHANNEL_ID:
        return
    
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    
    embed = discord.Embed(
        title="🗑 Канал удалён",
        color=0xF04747,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Название", value=channel.name, inline=True)
    embed.add_field(name="Тип", value=str(channel.type), inline=True)
    embed.add_field(name="ID", value=f"`{channel.id}`", inline=True)
    
    await log_ch.send(embed=embed)


@bot.event
async def on_guild_channel_update(before, after):
    """Логирование изменения канала"""
    if not MOD_LOG_CHANNEL_ID or before.name == after.name:
        return
    
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    
    embed = discord.Embed(
        title="✏️ Канал изменён",
        color=0xFAA61A,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Канал", value=after.mention, inline=True)
    embed.add_field(name="Было", value=before.name, inline=True)
    embed.add_field(name="Стало", value=after.name, inline=True)
    
    await log_ch.send(embed=embed)


@bot.event
async def on_voice_state_update(member, before, after):
    """Логирование голосовой активности"""
    if not MOD_LOG_CHANNEL_ID or member.bot:
        return
    
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    
    # Зашёл в голосовой канал
    if before.channel is None and after.channel is not None:
        embed = discord.Embed(
            title="🔊 Зашёл в голосовой канал",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Пользователь", value=member.mention, inline=True)
        embed.add_field(name="Канал", value=after.channel.mention, inline=True)
        await log_ch.send(embed=embed)
    
    # Вышел из голосового канала
    elif before.channel is not None and after.channel is None:
        embed = discord.Embed(
            title="🔇 Вышел из голосового канала",
            color=0xF04747,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Пользователь", value=member.mention, inline=True)
        embed.add_field(name="Канал", value=before.channel.mention, inline=True)
        await log_ch.send(embed=embed)
    
    # Переключился между каналами
    elif before.channel != after.channel and before.channel is not None and after.channel is not None:
        embed = discord.Embed(
            title="🔄 Переключил голосовой канал",
            color=0xFAA61A,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Пользователь", value=member.mention, inline=True)
        embed.add_field(name="Из", value=before.channel.mention, inline=True)
        embed.add_field(name="В", value=after.channel.mention, inline=True)
        await log_ch.send(embed=embed)
# ───────────────────────────────────────────────
#   КОМАНДЫ (ОСНОВНЫЕ)
# ───────────────────────────────────────────────

@bot.hybrid_command(name="ping", description="Проверить задержку бота и другую полезную информацию")
async def ping(ctx: commands.Context):
    try:
        latency = round(bot.latency * 1000)
        api_latency = round(bot.ws.latency * 1000) if bot.ws else latency

        uptime = datetime.now(timezone.utc) - bot.launch_time
        uptime_str = str(uptime).split('.')[0]

        guild_count = len(bot.guilds)
        user_count = sum(g.member_count for g in bot.guilds if g.member_count)

        embed = discord.Embed(
            title="🏓 Pong! Статус бота",
            description="Вот всё, что тебе нужно знать о моей производительности прямо сейчас",
            color=0x57F287,
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(name="Задержка (WebSocket)", value=f"**{latency} мс**", inline=True)
        embed.add_field(name="Задержка API", value=f"**{api_latency} мс**", inline=True)
        embed.add_field(name="Время работы", value=f"**{uptime_str}**", inline=True)
        embed.add_field(name="Серверов", value=f"**{guild_count}**", inline=True)
        embed.add_field(name="Пользователей", value=f"**{user_count:,}**", inline=True)

        embed.set_footer(text="MortisPlay • mortisplay.ru", icon_url=bot.user.display_avatar.url)
        embed.set_thumbnail(url=bot.user.display_avatar.url)

        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="avatar", description="Показать аватар пользователя")
@app_commands.describe(member="Пользователь (по умолчанию — ты)")
async def avatar(ctx: commands.Context, member: discord.Member = None):
    try:
        member = member or ctx.author
        embed = discord.Embed(title=f"Аватар {member}", color=0x7289DA)
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="userinfo", description="Информация о пользователе")
@app_commands.describe(member="Пользователь (по умолчанию — ты)")
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
        
        # Собираем подробную статистику
        total_members = guild.member_count
        online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
        idle_members = sum(1 for m in guild.members if m.status == discord.Status.idle)
        dnd_members = sum(1 for m in guild.members if m.status == discord.Status.dnd)
        offline_members = sum(1 for m in guild.members if m.status == discord.Status.offline)
        
        bot_count = sum(1 for m in guild.members if m.bot)
        human_count = total_members - bot_count
        
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        roles_count = len(guild.roles)
        emojis_count = len(guild.emojis)
        
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        
        # Создаем красивый embed
        embed = discord.Embed(
            title=f"📊 Статистика сервера {guild.name}",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Основная информация
        embed.add_field(
            name="👥 Участники",
            value=f"**Всего:** {total_members}\n"
                  f"**Людей:** {human_count}\n"
                  f"**Ботов:** {bot_count}",
            inline=True
        )
        
        embed.add_field(
            name="🟢 Онлайн",
            value=f"**Онлайн:** {online_members}\n"
                  f"**Неактивен:** {idle_members}\n"
                  f"**Не беспокоить:** {dnd_members}\n"
                  f"**Оффлайн:** {offline_members}",
            inline=True
        )
        
        embed.add_field(
            name="📁 Каналы",
            value=f"**Текстовых:** {text_channels}\n"
                  f"**Голосовых:** {voice_channels}\n"
                  f"**Категорий:** {categories}",
            inline=True
        )
        
        embed.add_field(
            name="🎨 Оформление",
            value=f"**Ролей:** {roles_count}\n"
                  f"**Эмодзи:** {emojis_count}",
            inline=True
        )
        
        embed.add_field(
            name="🚀 Буст",
            value=f"**Уровень:** {boost_level}\n"
                  f"**Бустов:** {boost_count}",
            inline=True
        )
        
        embed.add_field(
            name="📅 Сервер создан",
            value=f"<t:{int(guild.created_at.timestamp())}:D>",
            inline=True
        )
        
        # Владелец сервера
        if guild.owner:
            embed.add_field(
                name="👑 Владелец",
                value=guild.owner.mention,
                inline=False
            )
        
        embed.set_footer(text=f"ID сервера: {guild.id}")
        
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

    
@bot.hybrid_command(name="say", description="Написать от лица бота (поддержка embed + ответ на сообщение)")
@app_commands.describe(
    text="Обычный текст сообщения",
    embed_title="Заголовок embed (если хочешь embed)",
    embed_description="Описание embed",
    embed_color="Цвет embed в HEX (например #FF0000)",
    channel="Канал, куда отправить (по умолчанию текущий)",
    reply_to="Сообщение, на которое нужно ответить (ответь на него и используй команду)"
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
        # Проверка прав
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ У тебя нет прав на использование этой команды!", ephemeral=True)

        if not has_full_access(ctx.guild.id):
            return await ctx.send("❌ Эта команда доступна только на сервере разработчика.", ephemeral=True)

        target_channel = channel or ctx.channel

        if not target_channel.permissions_for(ctx.guild.me).send_messages:
            return await ctx.send("❌ У меня нет прав писать в этот канал.", ephemeral=True)

        reference = reply_to

        if embed_title and embed_description:
            color_int = int(embed_color.lstrip("#"), 16) if embed_color.startswith("#") else 0x57F287
            embed = discord.Embed(title=embed_title, description=embed_description, color=color_int)
            await target_channel.send(embed=embed, reference=reference)
        else:
            if not text:
                return await ctx.send("❌ Укажи текст или embed_title + embed_description.", ephemeral=True)
            await target_channel.send(text, reference=reference)

        await ctx.send(f"✅ Сообщение успешно отправлено в {target_channel.mention}", ephemeral=True)

    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   ЭКОНОМИКА (обновленная)
# ───────────────────────────────────────────────

@bot.hybrid_command(name="pay", description="💸 Перевести монеты другому с комментарием")
@app_commands.describe(member="Кому", amount="Сумма", comment="Комментарий к переводу (необязательно)")
async def pay(ctx: commands.Context, member: discord.Member, amount: int, comment: str = None):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика доступна только на сервере разработчика.", ephemeral=True)

        if amount <= 0:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Сумма должна быть больше 0.", ephemeral=True)
        
        if member.id == ctx.author.id:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Нельзя перевести монеты самому себе.", ephemeral=True)

        sender_id = str(ctx.author.id)
        receiver_id = str(member.id)

        if sender_id not in economy_data or economy_data[sender_id]["balance"] < amount:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Недостаточно монет! Твой баланс: {format_number(economy_data.get(sender_id, {}).get('balance', 0))} {ECONOMY_EMOJIS['coin']}", ephemeral=True)

        tax = await apply_wealth_tax(sender_id)

        if receiver_id not in economy_data:
            economy_data[receiver_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}

        # Списание и зачисление
        economy_data[sender_id]["balance"] -= amount
        economy_data[receiver_id]["balance"] += amount
        save_economy()

        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['transfer']} Перевод выполнен",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Отправитель",
            value=f"{ctx.author.mention}\nБаланс: **{format_number(economy_data[sender_id]['balance'])}** {ECONOMY_EMOJIS['coin']}",
            inline=True
        )
        
        embed.add_field(
            name="Получатель",
            value=f"{member.mention}\nБаланс: **{format_number(economy_data[receiver_id]['balance'])}** {ECONOMY_EMOJIS['coin']}",
            inline=True
        )
        
        embed.add_field(
            name="Сумма",
            value=f"**{format_number(amount)}** {ECONOMY_EMOJIS['coin']}",
            inline=False
        )

        if comment:
            embed.add_field(
                name="📝 Комментарий",
                value=f"*{comment}*",
                inline=False
            )

        if tax > 0:
            embed.add_field(
                name=f"{ECONOMY_EMOJIS['tax']} Налог",
                value=f"Списано **-{format_number(tax)}** {ECONOMY_EMOJIS['coin']} (1% > 10к)",
                inline=False
            )

        embed.set_footer(text=f"Экономика v0.11.0 • mortisplay.ru", icon_url=bot.user.display_avatar.url)
        
        await ctx.send(embed=embed, ephemeral=True)
        
        # Отправляем уведомление получателю
        try:
            dm_embed = discord.Embed(
                title=f"{ECONOMY_EMOJIS['transfer']} Получен перевод",
                description=f"**От:** {ctx.author.mention}\n**Сумма:** {format_number(amount)} {ECONOMY_EMOJIS['coin']}",
                color=0x57F287
            )
            if comment:
                dm_embed.add_field(name="Комментарий", value=comment, inline=False)
            await member.send(embed=dm_embed)
        except:
            pass
        
        # Логирование крупных переводов
        if amount >= 10000:
            await send_mod_log(
                title="💸 Крупный перевод",
                description=f"**От:** {ctx.author.mention}\n**Кому:** {member.mention}\n**Сумма:** {format_number(amount)} {ECONOMY_EMOJIS['coin']}\n**Комментарий:** {comment or 'Нет'}",
                color=0x57F287
            )
            
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="invest", description="📈 Инвестировать монеты")
@app_commands.describe(amount="Сумма", days="Количество дней (1-30)")
async def invest(ctx: commands.Context, amount: int, days: int):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика доступна только на сервере разработчика.", ephemeral=True)

        if amount < INVESTMENT_MIN_AMOUNT:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Минимальная сумма инвестиций: {format_number(INVESTMENT_MIN_AMOUNT)} {ECONOMY_EMOJIS['coin']}", ephemeral=True)
        
        if days < 1 or days > INVESTMENT_MAX_DAYS:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Срок инвестиций должен быть от 1 до {INVESTMENT_MAX_DAYS} дней.", ephemeral=True)

        user_id = str(ctx.author.id)
        
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}
        
        if economy_data[user_id]["balance"] < amount:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Недостаточно монет! Баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']}", ephemeral=True)

        # Расчет процента (чем дольше срок, тем выше процент)
        base_rate = INVESTMENT_BASE_RATE
        rate_multiplier = 1 + (days / 30)  # Максимум x2 за 30 дней
        profit_rate = base_rate * rate_multiplier
        profit = int(amount * profit_rate)
        
        end_time = datetime.utcnow().timestamp() + (days * 86400)
        
        investment = {
            "amount": amount,
            "days": days,
            "profit": profit,
            "start_time": datetime.utcnow().timestamp(),
            "end_time": end_time,
            "rate": round(profit_rate * 100, 2)
        }
        
        # Списание средств
        economy_data[user_id]["balance"] -= amount
        
        if "investments" not in economy_data[user_id]:
            economy_data[user_id]["investments"] = []
        
        economy_data[user_id]["investments"].append(investment)
        save_economy()
        
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['investment']} Инвестиция создана",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="💰 Сумма", value=f"{format_number(amount)} {ECONOMY_EMOJIS['coin']}", inline=True)
        embed.add_field(name="📅 Срок", value=f"{days} дней", inline=True)
        embed.add_field(name="📊 Ставка", value=f"{investment['rate']}%", inline=True)
        embed.add_field(name="💹 Прибыль", value=f"+{format_number(profit)} {ECONOMY_EMOJIS['coin']}", inline=True)
        embed.add_field(name="⏰ Завершение", value=f"<t:{int(end_time)}:R>", inline=False)
        
        embed.set_footer(text=f"Новый баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']}")
        
        await ctx.send(embed=embed, ephemeral=True)
        
        # Логирование
        await send_mod_log(
            title="📈 Новая инвестиция",
            description=f"**Пользователь:** {ctx.author.mention}\n**Сумма:** {format_number(amount)} {ECONOMY_EMOJIS['coin']}\n**Срок:** {days} дней\n**Прибыль:** {format_number(profit)} {ECONOMY_EMOJIS['coin']}",
            color=0x57F287
        )
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="investments", description="📊 Мои инвестиции")
async def my_investments(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика доступна только на сервере разработчика.", ephemeral=True)

        user_id = str(ctx.author.id)
        
        if user_id not in economy_data or "investments" not in economy_data[user_id] or not economy_data[user_id]["investments"]:
            return await ctx.send(f"{ECONOMY_EMOJIS['warning']} У вас нет активных инвестиций.", ephemeral=True)
        
        now = datetime.utcnow().timestamp()
        active = []
        completed = []
        
        for inv in economy_data[user_id]["investments"]:
            if inv["end_time"] > now:
                active.append(inv)
            else:
                completed.append(inv)
        
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['investment']} Мои инвестиции",
            color=0x57F287,
            timestamp=datetime.utcnow()
        )
        
        if active:
            active_text = ""
            for i, inv in enumerate(active, 1):
                time_left = inv["end_time"] - now
                days_left = int(time_left // 86400)
                hours_left = int((time_left % 86400) // 3600)
                
                active_text += f"**{i}.** {format_number(inv['amount'])} {ECONOMY_EMOJIS['coin']} → +{format_number(inv['profit'])} {ECONOMY_EMOJIS['coin']}\n"
                active_text += f"⏰ Осталось: {days_left}д {hours_left}ч\n\n"
            
            embed.add_field(name="🟢 Активные", value=active_text, inline=False)
        
        if completed:
            completed_text = ""
            for i, inv in enumerate(completed[-5:], 1):  # Последние 5 завершенных
                completed_text += f"**{i}.** {format_number(inv['amount'])} {ECONOMY_EMOJIS['coin']} → +{format_number(inv['profit'])} {ECONOMY_EMOJIS['coin']} ✅\n"
            
            embed.add_field(name="✅ Завершенные", value=completed_text, inline=False)
        
        # Общая статистика
        total_invested = sum(inv["amount"] for inv in economy_data[user_id]["investments"])
        total_profit = sum(inv["profit"] for inv in economy_data[user_id]["investments"])
        
        embed.add_field(
            name="📊 Статистика",
            value=f"**Всего инвестировано:** {format_number(total_invested)} {ECONOMY_EMOJIS['coin']}\n"
                  f"**Общая прибыль:** +{format_number(total_profit)} {ECONOMY_EMOJIS['coin']}",
            inline=False
        )
        
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   СИСТЕМА КЕЙСОВ
# ───────────────────────────────────────────────

@bot.hybrid_command(name="case", description="🔍 Информация о кейсе наказания")
@app_commands.describe(case_id="ID кейса")
@commands.has_permissions(manage_messages=True)
async def case_info(ctx: commands.Context, case_id: str):
    try:
        # Проверка прав
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ У тебя нет прав на использование этой команды!", ephemeral=True)

        case = await get_case(case_id)
        
        if not case:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Кейс с ID `{case_id}` не найден.", ephemeral=True)
        
        embed = discord.Embed(
            title=f"🔍 Кейс #{case_id}",
            color=0x57F287,
            timestamp=datetime.fromisoformat(case['timestamp'])
        )
        
        # Получаем пользователей
        user = await bot.fetch_user(int(case['user_id'])) if case['user_id'].isdigit() else None
        moderator = await bot.fetch_user(int(case['moderator_id'])) if case['moderator_id'].isdigit() else None
        
        embed.add_field(name="👤 Пользователь", value=user.mention if user else case['user_name'], inline=True)
        embed.add_field(name="👮 Модератор", value=moderator.mention if moderator else case['moderator_name'], inline=True)
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

@bot.hybrid_command(name="help", description="📚 Показать список команд")
async def help_command(ctx: commands.Context):
    try:
        # Проверяем, является ли пользователь модератором
        is_mod = ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator
        
        embed = discord.Embed(
            title="🤖 Помощь по командам",
            description="Используй кнопки ниже для навигации по категориям\n\n"
                       "**📋 Основное** - общие команды\n"
                       "**💰 Экономика** - команды экономики\n"
                       "**🎮 Развлечения** - развлекательные команды" +
                       ("\n**🛡️ Модерация** - модераторские команды\n**🎫 Тикеты** - система тикетов" if is_mod else ""),
            color=0x57F287
        )
        embed.set_footer(text="Выбери категорию стрелками")
        
        view = HelpView(ctx.author, is_mod)
        await ctx.send(embed=embed, view=view, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   НОВЫЕ КОМАНДЫ
# ───────────────────────────────────────────────

@bot.hybrid_command(name="faq", description="📚 Часто задаваемые вопросы")
async def faq(ctx: commands.Context):
    try:
        embed = discord.Embed(
            title="📚 Часто задаваемые вопросы",
            description="Выберите категорию вопросов:",
            color=0x57F287
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
            return await ctx.send("❌ У тебя нет прав на использование этой команды!", ephemeral=True)
        
        # Приводим категорию к нижнему регистру для сравнения
        category_lower = category.lower()
        if category_lower not in FAQ_CATEGORIES:
            categories = ", ".join(FAQ_CATEGORIES.keys())
            return await ctx.send(f"❌ Неверная категория! Доступные: {categories}", ephemeral=True)
        
        if category_lower not in faq_data:
            faq_data[category_lower] = []
        
        faq_data[category_lower].append({
            "question": question,
            "answer": answer
        })
        save_faq()
        
        embed = discord.Embed(
            title="✅ Вопрос добавлен",
            description=f"**Категория:** {FAQ_CATEGORIES[category_lower]}\n**Вопрос:** {question}",
            color=0x57F287
        )
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="iq", description="Узнать свой честный IQ 😏")
async def iq(ctx: commands.Context):
    try:
        user_id = ctx.author.id
        random.seed(user_id + int(datetime.now().timestamp() // 86400))

        base_iq = random.randint(70, 130)
        if random.random() < 0.03:
            iq_value = random.randint(145, 165)
            title = "🧠 ГЕНИЙ!"
            color = 0xFFD700
        elif random.random() < 0.10:
            iq_value = random.randint(115, 144)
            title = "🌟 Умный человек"
            color = 0x3498DB
        else:
            iq_value = base_iq
            title = "🧠 Твой IQ"
            color = 0x2ECC71

        embed = discord.Embed(title=title, description=f"**{ctx.author.mention}, твой IQ: {iq_value}**", color=color)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Тест честный и научный (шучу, рандом каждый день новый) 😄")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="valute", description="Курсы валют (view — свежие курсы)")
@app_commands.describe(action="view — показать курсы")
async def valute(ctx: commands.Context, action: str = "view"):
    # Сразу отвечаем, чтобы interaction не истек
    await ctx.defer(ephemeral=True)
    
    try:
        if action.lower() != "view":
            await ctx.send("Использование: `/valute view`", ephemeral=True)
            return

        # Пробуем несколько API по очереди
        apis = [
            "https://api.exchangerate-api.com/v4/latest/USD",
            "https://open.er-api.com/v6/latest/USD",
            "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
        ]
        
        data = None
        last_error = None
        
        for api_url in apis:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            break
                        else:
                            last_error = f"API вернул код {resp.status}"
            except asyncio.TimeoutError:
                last_error = "Таймаут соединения"
                continue
            except aiohttp.ClientError as e:
                last_error = f"Ошибка соединения: {str(e)}"
                continue
            except Exception as e:
                last_error = str(e)
                continue
        
        if not data:
            # Если все API недоступны, используем локальные данные
            embed = discord.Embed(
                title="📈 Курсы валют (автономный режим)",
                description="API временно недоступны. Показаны курсы с последнего обновления.",
                color=0xFAA61A,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Примерные курсы (можно обновлять вручную)
            embed.add_field(name="🇺🇸 USD", value="1.00", inline=True)
            embed.add_field(name="🇪🇺 EUR", value="0.92", inline=True)
            embed.add_field(name="🇨🇳 CNY", value="7.25", inline=True)
            embed.add_field(name="🇬🇧 GBP", value="0.79", inline=True)
            embed.add_field(name="🇷🇺 RUB", value="92.50", inline=True)
            
            embed.set_footer(text="Данные могут быть устаревшими • Обновите позже")
            
            await ctx.send(embed=embed, ephemeral=True)
            return

        # Парсим данные в зависимости от API
        if "rates" in data:
            # exchangerate-api или open.er-api
            usd = 1
            eur = data["rates"].get("EUR", 0.92)
            cny = data["rates"].get("CNY", 7.25)
            gbp = data["rates"].get("GBP", 0.79)
            rub = data["rates"].get("RUB", 92.50)
        elif "usd" in data:
            # currency-api
            rates = data["usd"]
            usd = 1
            eur = rates.get("eur", 0.92)
            cny = rates.get("cny", 7.25)
            gbp = rates.get("gbp", 0.79)
            rub = rates.get("rub", 92.50)
        else:
            # fallback значения
            usd, eur, cny, gbp, rub = 1, 0.92, 7.25, 0.79, 92.50

        embed = discord.Embed(
            title="📈 Актуальные курсы валют (к USD)",
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="🇺🇸 USD", value=f"{usd:.2f}", inline=True)
        embed.add_field(name="🇪🇺 EUR", value=f"{eur:.2f}", inline=True)
        embed.add_field(name="🇨🇳 CNY", value=f"{cny:.2f}", inline=True)
        embed.add_field(name="🇬🇧 GBP", value=f"{gbp:.2f}", inline=True)
        embed.add_field(name="🇷🇺 RUB", value=f"{rub:.2f}", inline=True)
        
        embed.set_footer(text="Источник: currency-api • Обновлено")
        
        await ctx.send(embed=embed, ephemeral=True)

    except asyncio.CancelledError:
        # Игнорируем отмену задачи
        pass
    except Exception as e:
        error_msg = f"Ошибка получения курсов: {str(e)}"
        
        # Создаем embed с ошибкой
        embed = discord.Embed(
            title="❌ Ошибка",
            description=error_msg,
            color=0xF04747,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Пробуем отправить через обычный send (поскольку мы уже сделали defer)
        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            # Если совсем ничего не работает, хотя бы залогируем
            print(f"Ошибка в valute: {error_msg}")

@bot.hybrid_command(name="shop", description="🛒 Магазин (в разработке)")
async def shop(ctx: commands.Context):
    try:
        embed = discord.Embed(
            title="🛒 Магазин",
            description="Магазин будет доступен в версии **1.0.0**\n\nСледи за обновлениями!",
            color=0x3498DB
        )
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="guildsettings", description="⚙️ Настройки сервера (в разработке)")
async def guildsettings(ctx: commands.Context):
    try:
        embed = discord.Embed(
            title="⚙️ Настройки сервера",
            description="Здесь будут настройки сервера и кастомный античит\n\nВ разработке",
            color=0x7289DA
        )
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   НОВЫЕ МОДЕРАТОРСКИЕ КОМАНДЫ
# ───────────────────────────────────────────────

@bot.hybrid_command(name="warn", description="Выдать предупреждение пользователю")
@app_commands.describe(member="Пользователь", reason="Причина предупреждения")
@commands.has_permissions(manage_messages=True)
async def warn(ctx: commands.Context, member: discord.Member, *, reason: str = "Не указана"):
    try:
        # Проверка прав
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ У тебя нет прав на использование этой команды!", ephemeral=True)

        if is_protected(member, ctx):
            return await ctx.send("❌ Нельзя выдать предупреждение этому пользователю!", ephemeral=True)

        user_id = str(member.id)
        
        if user_id not in warnings_data:
            warnings_data[user_id] = []
        
        warnings_data[user_id].append({
            "moderator": str(ctx.author),
            "reason": reason,
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_warnings()
        
        warn_count = get_warning_count(user_id)
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
            description=f"**Пользователь:** {member.mention}\n**Причина:** {reason}\n**Всего предупреждений:** {warn_count}",
            color=0xFAA61A
        )
        await ctx.send(embed=embed, ephemeral=True)
        
        # Проверяем на авто-наказание
        await check_auto_punishment(member, reason)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="warnings", description="Показать предупреждения пользователя")
@app_commands.describe(member="Пользователь")
@commands.has_permissions(manage_messages=True)
async def warnings(ctx: commands.Context, member: discord.Member):
    try:
        # Проверка прав
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ У тебя нет прав на использование этой команды!", ephemeral=True)

        user_id = str(member.id)
        clean_old_warnings(user_id)
        
        user_warnings = warnings_data.get(user_id, [])
        
        if not user_warnings:
            return await ctx.send(f"✅ У {member.mention} нет предупреждений.", ephemeral=True)
        
        embed = discord.Embed(
            title=f"⚠️ Предупреждения • {member.display_name}",
            description=f"Всего: **{len(user_warnings)}**",
            color=0xFAA61A
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        for i, warn in enumerate(user_warnings[-10:], 1):  # Показываем последние 10
            embed.add_field(
                name=f"{i}. {warn['time']}",
                value=f"**Модератор:** {warn['moderator']}\n**Причина:** {warn['reason']}",
                inline=False
            )
        
        embed.set_footer(text="Показаны последние 10 предупреждений")
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="clearwarn", description="Очистить предупреждения пользователя")
@app_commands.describe(member="Пользователь", warn_id="ID предупреждения (или all для всех)")
@commands.has_permissions(administrator=True)
async def clearwarn(ctx: commands.Context, member: discord.Member, warn_id: str = "all"):
    try:
        # Проверка прав
        if not ctx.author.guild_permissions.administrator:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ У тебя нет прав на использование этой команды!", ephemeral=True)

        user_id = str(member.id)
        
        if user_id not in warnings_data or not warnings_data[user_id]:
            return await ctx.send(f"✅ У {member.mention} нет предупреждений.", ephemeral=True)
        
        if warn_id.lower() == "all":
            del warnings_data[user_id]
            save_warnings()
            await ctx.send(f"✅ Все предупреждения {member.mention} удалены.", ephemeral=True)
            await send_mod_log(
                title="🧹 Очистка предупреждений",
                description=f"**Модератор:** {ctx.author.mention}\n**Пользователь:** {member.mention}\n**Действие:** Все предупреждения удалены",
                color=0x57F287
            )
        else:
            # TODO: удаление конкретного предупреждения по индексу
            await ctx.send("❌ Удаление конкретного предупреждения пока не реализовано.", ephemeral=True)
            
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="mute", description="Замутить пользователя")
@app_commands.describe(member="Пользователь", duration="Длительность (1h, 1d, 30m)", reason="Причина")
@commands.has_permissions(manage_messages=True)
async def mute(ctx: commands.Context, member: discord.Member, duration: str, *, reason: str = "Не указана"):
    try:
        # Проверка прав
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ У тебя нет прав на использование этой команды!", ephemeral=True)

        if is_protected(member, ctx):
            return await ctx.send("❌ Нельзя замутить этого пользователя!", ephemeral=True)
        
        # Парсим длительность
        duration_seconds = 0
        if duration.endswith("h"):
            duration_seconds = int(duration[:-1]) * 3600
        elif duration.endswith("d"):
            duration_seconds = int(duration[:-1]) * 86400
        elif duration.endswith("m"):
            duration_seconds = int(duration[:-1]) * 60
        elif duration.endswith("s"):
            duration_seconds = int(duration[:-1])
        else:
            duration_seconds = int(duration) * 60  # По умолчанию минуты
        
        if duration_seconds <= 0:
            return await ctx.send("❌ Некорректная длительность!", ephemeral=True)
        
        duration_delta = timedelta(seconds=duration_seconds)
        
        await member.timeout(duration_delta, reason=reason)
        
        # Форматируем время для отображения
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        if hours > 0:
            duration_text = f"{hours}ч {minutes}м"
        else:
            duration_text = f"{minutes}м"
        
        case_id = await create_case(member, ctx.author, "Мут", reason, duration_text)
        
        await send_punishment_log(
            member=member,
            punishment_type="🔇 Мут",
            duration=duration_text,
            reason=reason,
            moderator=ctx.author,
            case_id=case_id
        )
        
        embed = discord.Embed(
            title="🔇 Пользователь замучен",
            description=f"**Пользователь:** {member.mention}\n**Длительность:** {duration_text}\n**Причина:** {reason}",
            color=0xF04747
        )
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="unmute", description="Снять мут с пользователя")
@app_commands.describe(member="Пользователь", reason="Причина")
@commands.has_permissions(manage_messages=True)
async def unmute(ctx: commands.Context, member: discord.Member, *, reason: str = "Не указана"):
    try:
        # Проверка прав
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ У тебя нет прав на использование этой команды!", ephemeral=True)

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
            color=0x57F287
        )
        await ctx.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="temprole", description="Выдать временную роль")
@app_commands.describe(member="Пользователь", role="Роль", duration="Длительность (1h, 1d, 30m)")
@commands.has_permissions(manage_roles=True)
async def temprole(ctx: commands.Context, member: discord.Member, role: discord.Role, duration: str):
    try:
        # Проверка прав
        if not ctx.author.guild_permissions.manage_roles:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ У тебя нет прав на использование этой команды!", ephemeral=True)

        if role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send("❌ Нельзя выдать роль выше своей!", ephemeral=True)
        
        # Парсим длительность
        duration_seconds = 0
        if duration.endswith("h"):
            duration_seconds = int(duration[:-1]) * 3600
        elif duration.endswith("d"):
            duration_seconds = int(duration[:-1]) * 86400
        elif duration.endswith("m"):
            duration_seconds = int(duration[:-1]) * 60
        elif duration.endswith("s"):
            duration_seconds = int(duration[:-1])
        else:
            duration_seconds = int(duration) * 60  # По умолчанию минуты
        
        if duration_seconds <= 0:
            return await ctx.send("❌ Некорректная длительность!", ephemeral=True)
        
        # Выдаем роль
        await member.add_roles(role, reason=f"Временная роль от {ctx.author}")
        
        # Сохраняем во временные роли
        user_id = str(member.id)
        if user_id not in temp_roles:
            temp_roles[user_id] = {}
        
        expiry = datetime.utcnow().timestamp() + duration_seconds
        temp_roles[user_id][str(role.id)] = expiry
        
        # Форматируем время для отображения
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        if hours > 0:
            duration_text = f"{hours}ч {minutes}м"
        else:
            duration_text = f"{minutes}м"
        
        embed = discord.Embed(
            title="⏱️ Временная роль выдана",
            description=f"**Пользователь:** {member.mention}\n**Роль:** {role.mention}\n**Длительность:** {duration_text}",
            color=0x57F287
        )
        await ctx.send(embed=embed, ephemeral=True)
        
        await send_mod_log(
            title="⏱️ Временная роль",
            description=f"**Модератор:** {ctx.author.mention}\n**Пользователь:** {member.mention}\n**Роль:** {role.mention}\n**Длительность:** {duration_text}",
            color=0x57F287
        )
        
    except Exception as e:
        await send_error_embed(ctx, str(e))

# Команда raidmode УДАЛЕНА

@bot.hybrid_command(name="ticket", description="Управление тикетами")
@app_commands.describe(action="setup / close")
@commands.has_permissions(manage_channels=True)
async def ticket(ctx: commands.Context, action: str = "setup"):
    try:
        # Проверка прав
        if not ctx.author.guild_permissions.manage_channels:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ У тебя нет прав на использование этой команды!", ephemeral=True)

        if not has_full_access(ctx.guild.id):
            return await ctx.send("❌ Эта команда доступна только на сервере разработчика.", ephemeral=True)

        action = action.lower()
        if action == "setup":
            embed = discord.Embed(
                title="🎫 Система тикетов",
                description="Нажми кнопку ниже, чтобы создать тикет с выбором категории.",
                color=0x57F287
            )
            view = TicketPanelView()
            await ctx.send(embed=embed, view=view)
            await ctx.send("✅ Панель тикетов с категориями создана!", delete_after=10)
        elif action == "close":
            if not any(ctx.channel.name.startswith(prefix) for prefix in ["🔧-", "⚠️-", "❓-", "🤝-", "📌-"]):
                return await ctx.send("❌ Эту команду можно использовать только внутри тикета!", ephemeral=True)
            await ctx.send("🔒 Тикет закрывается через 5 секунд...")
            await asyncio.sleep(5)
            await ctx.channel.delete()
        else:
            await ctx.send("Использование: `/ticket setup` или `/ticket close`")
    except Exception as e:
        await send_error_embed(ctx, str(e))

# ───────────────────────────────────────────────
#   ОСТАЛЬНЫЕ КОМАНДЫ (без изменений)
# ───────────────────────────────────────────────

@bot.hybrid_command(name="vault", description="🏦 Казна сервера")
async def vault(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Эта команда доступна только на сервере разработчика.", ephemeral=True)
        if not ctx.author.guild_permissions.manage_messages and ctx.author.id != OWNER_ID:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} У тебя нет прав на просмотр казны.", ephemeral=True)

        vault = economy_data.get("server_vault", 0)
        
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['vault']} Казна сервера",
            description=f"**Накоплено:** `{format_number(vault)}` {ECONOMY_EMOJIS['coin']}",
            color=0xFFD700
        )
        
        # Статистика казны
        total_users = len([k for k in economy_data.keys() if k != "server_vault"])
        total_balance = sum(v.get("balance", 0) for k, v in economy_data.items() if k != "server_vault")
        
        embed.add_field(
            name="📊 Статистика",
            value=f"**Участников:** {total_users}\n"
                  f"**Всего монет:** {format_number(total_balance)} {ECONOMY_EMOJIS['coin']}\n"
                  f"**Средний баланс:** {format_number(total_balance // max(total_users, 1))} {ECONOMY_EMOJIS['coin']}",
            inline=False
        )
        
        embed.set_footer(text="Экономика v0.11.0 • mortisplay.ru", icon_url=bot.user.display_avatar.url)
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="balance", description="💰 Посмотреть баланс")
@app_commands.describe(member="Пользователь (по умолчанию — ты)")
async def balance(ctx: commands.Context, member: discord.Member = None):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика доступна только на сервере разработчика.", ephemeral=True)

        member = member or ctx.author
        user_id = str(member.id)

        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}
            save_economy()

        tax = await apply_wealth_tax(user_id)

        bal = economy_data[user_id]["balance"]
        vault = economy_data.get("server_vault", 0)
        
        # Получаем топ для сравнения
        all_users = [(k, v.get("balance", 0)) for k, v in economy_data.items() if k != "server_vault"]
        sorted_users = sorted(all_users, key=lambda x: x[1], reverse=True)
        
        # Находим место пользователя
        user_rank = 1
        for i, (uid, _) in enumerate(sorted_users, 1):
            if uid == user_id:
                user_rank = i
                break

        now = datetime.utcnow().timestamp()
        last_daily = economy_data[user_id].get("last_daily", 0)
        remaining = DAILY_COOLDOWN - (now - last_daily)
        
        if remaining <= 0:
            daily_status = f"{ECONOMY_EMOJIS['gift']} **Daily доступен!** Используй `/daily`"
            daily_color = 0x57F287
        else:
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            
            # Прогресс-бар для daily
            progress = (now - last_daily) / DAILY_COOLDOWN
            bar = create_progress_bar(int(progress * 100), 100)
            percent = int(progress * 100)
            
            daily_status = f"⏳ До daily: **{hours}ч {minutes}мин**\n`{bar}` **{percent}%**"

        embed = discord.Embed(
            title=f"{get_rank_emoji(bal)} Баланс • {member.display_name}",
            color=0xFFD700 if bal >= 10000 else 0x3498DB,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Основная информация
        embed.add_field(
            name=f"{ECONOMY_EMOJIS['balance']} Монеты",
            value=f"**`{format_number(bal)}`** {ECONOMY_EMOJIS['coin']}",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Место в топе",
            value=f"**#{user_rank}** из {len(sorted_users)}",
            inline=True
        )
        
        embed.add_field(
            name=f"{ECONOMY_EMOJIS['bank']} Казна",
            value=f"`{format_number(vault)}` {ECONOMY_EMOJIS['coin']}",
            inline=True
        )

        if tax > 0:
            embed.add_field(
                name=f"{ECONOMY_EMOJIS['tax']} Налог",
                value=f"Списано **-{format_number(tax)}** {ECONOMY_EMOJIS['coin']} (1% > 10к)",
                inline=False
            )

        embed.add_field(
            name=f"{ECONOMY_EMOJIS['gift']} Ежедневный бонус",
            value=daily_status,
            inline=False
        )
        
        # Добавляем информацию о инвестициях
        if "investments" in economy_data[user_id] and economy_data[user_id]["investments"]:
            active_investments = len([i for i in economy_data[user_id]["investments"] if i["end_time"] > now])
            if active_investments > 0:
                embed.add_field(
                    name=f"{ECONOMY_EMOJIS['investment']} Инвестиции",
                    value=f"Активно: **{active_investments}**",
                    inline=False
                )

        embed.set_footer(text=f"ID: {member.id} • Экономика v0.11.0", icon_url=bot.user.display_avatar.url)
        
        await ctx.send(embed=embed, ephemeral=True)

    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="daily", description="🎁 Получить ежедневную награду")
async def daily(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика доступна только на сервере разработчика.", ephemeral=True)

        user_id = str(ctx.author.id)
        now = datetime.utcnow().timestamp()

        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}

        last = economy_data[user_id].get("last_daily", 0)
        if now - last < DAILY_COOLDOWN:
            remaining = int(DAILY_COOLDOWN - (now - last))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60

            progress = (now - last) / DAILY_COOLDOWN
            bar = create_progress_bar(int(progress * 100), 100)
            percent = int(progress * 100)

            embed = discord.Embed(
                title=f"{ECONOMY_EMOJIS['time']} Daily на кулдауне",
                description=f"Следующая награда через **{hours}ч {minutes}мин**",
                color=0xFAA61A
            )
            embed.add_field(
                name="Прогресс",
                value=f"`{bar}` **{percent}%**",
                inline=False
            )
            embed.set_footer(text=f"Экономика v0.11.0 • mortisplay.ru", icon_url=bot.user.display_avatar.url)
            return await ctx.send(embed=embed, ephemeral=True)

        tax = await apply_wealth_tax(user_id)

        roll = random.randint(1, 100)
        
        # Выбор редкости
        if roll <= 70:
            rarity_name, _, min_coins, max_coins, color, emoji = RARITIES[0]
        elif roll <= 90:
            rarity_name, _, min_coins, max_coins, color, emoji = RARITIES[1]
        elif roll <= 99:
            rarity_name, _, min_coins, max_coins, color, emoji = RARITIES[2]
        else:
            rarity_name, _, min_coins, max_coins, color, emoji = RARITIES[3]

        reward = random.randint(min_coins, max_coins)
        
        # Бонус за стрик (если забирает каждый день)
        streak_bonus = 0
        last_daily_date = datetime.fromtimestamp(last).date() if last > 0 else None
        today = datetime.utcnow().date()
        
        if last_daily_date and (today - last_daily_date).days == 1:
            streak_bonus = int(reward * 0.1)  # +10% за стрик
            reward += streak_bonus

        economy_data[user_id]["balance"] += reward
        economy_data[user_id]["last_daily"] = now
        save_economy()

        embed = discord.Embed(
            title=f"{emoji} {rarity_name} награда!",
            description=f"**+{format_number(reward)}** {ECONOMY_EMOJIS['coin']}",
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        # Информация о награде
        embed.add_field(
            name="📊 Детали",
            value=f"**Редкость:** {rarity_name}\n**Диапазон:** {min_coins}-{max_coins} {ECONOMY_EMOJIS['coin']}",
            inline=True
        )
        
        if streak_bonus > 0:
            embed.add_field(
                name="🔥 Стрик",
                value=f"+{format_number(streak_bonus)} (10%)",
                inline=True
            )

        if tax > 0:
            embed.add_field(
                name=f"{ECONOMY_EMOJIS['tax']} Налог",
                value=f"**-{format_number(tax)}** {ECONOMY_EMOJIS['coin']} (1% > 10к)",
                inline=False
            )

        embed.set_footer(
            text=f"Новый баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']} • Экономика v0.11.0",
            icon_url=bot.user.display_avatar.url
        )
        
        await ctx.send(embed=embed, ephemeral=True)

    except Exception as e:
        await send_error_embed(ctx, str(e))

@bot.hybrid_command(name="top", description="🏆 Топ богатейших пользователей")
async def top(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика доступна только на сервере разработчика.", ephemeral=True)

        # Собираем данные
        users = []
        for user_id, data in economy_data.items():
            if user_id != "server_vault" and data.get("balance", 0) > 0:
                users.append((user_id, data.get("balance", 0)))
        
        if not users:
            return await ctx.send(f"{ECONOMY_EMOJIS['warning']} Пока нет пользователей с монетами!", ephemeral=True)
        
        # Сортируем по балансу
        users.sort(key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['crown']} Топ богатейших",
            color=0xFFD700,
            timestamp=datetime.utcnow()
        )
        
        # Формируем топ-10
        top_text = ""
        medals = ["🥇", "🥈", "🥉"]
        
        for i, (user_id, balance) in enumerate(users[:10], 1):
            try:
                user = await bot.fetch_user(int(user_id))
                name = user.display_name
            except:
                name = f"ID: {user_id}"
            
            medal = medals[i-1] if i <= 3 else f"**{i}.**"
            emoji = get_rank_emoji(balance)
            
            top_text += f"{medal} {emoji} **{name}** — `{format_number(balance)}` {ECONOMY_EMOJIS['coin']}\n"
        
        embed.description = top_text
        
        # Добавляем статистику
        total_balance = sum(b for _, b in users)
        avg_balance = total_balance // len(users)
        
        embed.add_field(
            name="📊 Статистика",
            value=f"**Всего монет:** {format_number(total_balance)} {ECONOMY_EMOJIS['coin']}\n"
                  f"**Участников:** {len(users)}\n"
                  f"**Средний баланс:** {format_number(avg_balance)} {ECONOMY_EMOJIS['coin']}",
            inline=False
        )
        
        embed.set_footer(text=f"Экономика v0.11.0 • Показано {min(10, len(users))} из {len(users)}", 
                        icon_url=bot.user.display_avatar.url)
        
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
        print("Неверный токен.")
    except Exception as e:
        print(f"Ошибка запуска: {type(e).__name__}: {e}")
