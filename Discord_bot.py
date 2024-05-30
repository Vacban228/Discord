
import discord
from discord.ext import commands
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.members = True  # Необходимо для отслеживания участников
intents.guilds = True  # Необходимо для получения информации о серверах
intents.messages = True  # Необходимо для отправки и обработки сообщений
intents.message_content = True  # Необходимо для доступа к содержимому сообщений

bot = commands.Bot(command_prefix='/', intents=intents)

# Словарь для хранения социального рейтинга участников
social_ratings = {}

# Список русских матов
forbidden_words = [
    'хуй', 'пизда', 'ебать', 'блять', 'пиздец', 'сука', 'нахуй', 'ебаный', 'ебанутый', 'еблан', 'выебать', 'выебон',
    'ебло', 'ебать-колотить', 'охуеть', 'хуево', 'хуёво', 'охуенный', 'пиздато', 'пиздатый', 'пиздёж', 'пидорас',
    'пидор', 'пидорасина', 'гандон', 'манда', 'мандавошка', 'хуесос', 'хуйня', 'хуйню', 'хуёк'
]

# Словарь для отслеживания времени последнего сообщения пользователя (для спама)
last_message_times = {}
spam_threshold = 5  # Порог времени (в секундах) между сообщениями для определения спама

initial_rating = 1000
penalty_points = 150

async def restore_rating(user_id, member):
    await asyncio.sleep(86400)  # Ждем 1 день (86400 секунд)
    new_rating = max(100, int(social_ratings[user_id] * 0.85))
    social_ratings[user_id] = new_rating
    channel = discord.utils.get(member.guild.text_channels, name='for-boat-tester')
    if channel:
        await channel.send(f'{member.mention}, ваш социальный рейтинг восстановлен до {new_rating} после окончания тайм-аута.')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    # Отправка сообщения только в текстовый канал for-boat-tester на всех серверах
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name='for-boat-tester')
        if channel:
            try:
                await channel.send("Бот запущен и готов к работе! Всем выдаются 1000 очков социального рейтинга.")
            except discord.Forbidden:
                print(f'Нет прав на отправку сообщений в канал {channel.name} на сервере {guild.name}')

@bot.event
async def on_member_join(member):
    # Выдать новому участнику 1000 очков рейтинга
    social_ratings[member.id] = initial_rating
    channel = discord.utils.get(member.guild.text_channels, name='for-boat-tester')
    if channel:
        try:
            await channel.send(f'{member.mention} присоединился к серверу! Ему выдано 1000 очков социального рейтинга.')
        except discord.Forbidden:
            print(f'Нет прав на отправку сообщений в канал {channel.name} на сервере {member.guild.name}')
    await member.send(f'Добро пожаловать на сервер! Вам выдано 1000 очков социального рейтинга.')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = message.author.id
    now = message.created_at.timestamp()

    # Инициализация рейтинга для новых пользователей
    if user_id not in social_ratings:
        social_ratings[user_id] = initial_rating

    # Проверка на использование мата
    if any(word in message.content.lower() for word in forbidden_words):
        social_ratings[user_id] -= penalty_points
        channel = discord.utils.get(message.guild.text_channels, name='for-boat-tester')
        if channel:
            await channel.send(f'{message.author.mention} - -{penalty_points} очков социального рейтинга за использование запрещённых слов.')

    # Проверка на спам
    if user_id in last_message_times:
        time_diff = now - last_message_times[user_id]
        if time_diff < spam_threshold:
            social_ratings[user_id] -= penalty_points
            channel = discord.utils.get(message.guild.text_channels, name='for-boat-tester')
            if channel:
                await channel.send(f'{message.author.mention} - -{penalty_points} очков социального рейтинга за спам.')

    last_message_times[user_id] = now

    # Проверка на нулевой рейтинг
    if social_ratings[user_id] <= 0:
        # Применение тайм-аута
        try:
            await message.author.edit(timeout=discord.utils.utcnow() + timedelta(days=1), reason='Нулевой социальный рейтинг')
            channel = discord.utils.get(message.guild.text_channels, name='for-boat-tester')
            if channel:
                await channel.send(f'{message.author.mention} получил тайм-аут на 1 день за достижение нулевого социального рейтинга.')
            await restore_rating(user_id, message.author)
        except discord.Forbidden:
            print(f'Нет прав для выдачи тайм-аута пользователю {message.author.name}')
        except discord.HTTPException as e:
            print(f'Ошибка при выдаче тайм-аута пользователю {message.author.name}: {e}')

    await bot.process_commands(message)

# Команда для проверки рейтинга
@bot.command()
async def show_soc_rating(ctx, member: discord.Member = None):
    if ctx.channel.name == 'for-boat-tester':
        if member is None:
            member = ctx.author
        await ctx.send(f'{member.mention}, ваш социальный рейтинг: {social_ratings.get(member.id, initial_rating)}')
    else:
        await ctx.send('Эту команду можно использовать только в канале for-boat-tester.')

async def main():
    while True:
        try:
            await bot.start('MTI0NTQzMzY5NzUyMDMyMDUzMg.GSJmOi.N_eQ-O5cUlOZjfzccK9d0-zvIpK0vwhA7rCwCg')
        except Exception as e:
            logging.error(f'Bot crashed with exception: {e}')
            await bot.close()
            await asyncio.sleep(10)  # Ждём 10 секунд перед перезапуском

if __name__ == '__main__':
    asyncio.run(main())