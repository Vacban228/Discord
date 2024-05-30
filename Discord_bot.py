import discord
from discord.ext import commands
from datetime import timedelta
import re

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Социальный рейтинг участников
social_ratings = {}

# Список запрещенных слов (список содержит основные русские маты)
forbidden_words = [
    'блять', 'блядь', 'сука', 'хуй', 'пизда', 'ебать', 'мудак', 'гандон', 'пидор', 'ебло',
    'жопа', 'хуев', 'мразь', 'уебок', 'уебище', 'хуесос', 'ебаный', 'ебанутый', 'еблан', 'хуило',
    'пидорас', 'пиздец', 'пизду', 'выблядок', 'пидар', 'хуеплет', 'хуета', 'ебучий', 'соси', 'залупа'
]

# Функция для проверки спама
def is_spam(message, user_messages, threshold=5, time_frame=10):
    now = message.created_at
    user_messages = [msg for msg in user_messages if (now - msg.created_at).seconds < time_frame]
    user_messages.append(message)
    return len(user_messages) > threshold, user_messages

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    channel = discord.utils.get(bot.get_all_channels(), name='for-boat-tester')
    if channel:
        await channel.send('Бот запущен и готов к работе!')
        for member in bot.get_all_members():
            social_ratings[member.id] = 1000
        await channel.send('Всем участникам выдано 1000 очков соц. рейтинга.')

@bot.event
async def on_member_join(member):
    social_ratings[member.id] = 1000

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = message.author.id
    if user_id not in social_ratings:
        social_ratings[user_id] = 1000

    if any(word in message.content.lower() for word in forbidden_words):
        social_ratings[user_id] -= 150
        await message.channel.send(f'{message.author.mention} -150 соц. рейтинга за использование запрещенных слов.')

    user_messages = getattr(message.author, 'recent_messages', [])
    is_spamming, user_messages = is_spam(message, user_messages)
    setattr(message.author, 'recent_messages', user_messages)

    if is_spamming:
        social_ratings[user_id] -= 150
        await message.channel.send(f'{message.author.mention} -150 соц. рейтинга за спам.')

    if social_ratings[user_id] <= 0:
        social_ratings[user_id] = max(1000 - 150 * len(user_messages), 0)
        await message.author.edit(timed_out_until=discord.utils.utcnow() + timedelta(days=1), reason='Нулевой социальный рейтинг')
        await message.channel.send(f'{message.author.mention} получил тайм-аут на 1 день за нулевой социальный рейтинг.')

    await bot.process_commands(message)

@bot.command()
async def show_soc_rating(ctx, member: discord.Member = None):
    member = member or ctx.author
    rating = social_ratings.get(member.id, 'Неизвестно')
    await ctx.send(f'Соц. рейтинг {member.mention}: {rating}')

bot.run('MTI0NTQzMzY5NzUyMDMyMDUzMg.GUYjkm.ZRdslv1Ka403TYfDtqd_BKZOuLsEZrNqH8_1IE')
