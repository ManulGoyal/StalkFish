import discord
from discord.ext import commands
import os
import logging
import asyncio
from utils import *
from problem_stalk import ProblemStalker
from contest_stalk import ContestStalker
import uuid
from cf_api import CFApi, CF_SOCIAL_SETTINGS_URL
from typing import Tuple, Union, Optional
from mongoengine import *
from documents import *
from dotenv import load_dotenv
import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
PROBLEM_STALK_CHANNEL = os.getenv('PROBLEM_STALK_CHANNEL')
CONTEST_STALK_CHANNEL = os.getenv('CONTEST_STALK_CHANNEL')
BOT_CMD_CHANNEL = os.getenv('BOT_CMD_CHANNEL')
DB_PASSWORD = os.getenv('DB_PASSWORD')
CMD_FILENAME = 'commands.txt'
VERIFICATION_TIMEOUT = 20
DB_NAME = 'StalkDB'

guild = None
bot_cmd_channel = None
# print(f"mongodb+srv://manul:{DB_PASSWORD}@cluster0.nvmh3.mongodb.net/{DB_NAME}?retryWrites=true&w=majority")
connect(host=f"mongodb+srv://manul:{DB_PASSWORD}@cluster0.nvmh3.mongodb.net/{DB_NAME}?retryWrites=true&w=majority")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
command_syntax = read_commands_from_file(CMD_FILENAME)
verification_requests = set()


@bot.event
async def on_ready():
    global guild
    global bot_cmd_channel

    guild = discord.utils.get(bot.guilds, name=GUILD)
    if not guild:
        raise Exception(f"No server named {GUILD} found")

    logging.info(f"{bot.user} connected to server {guild.name} (ID: {guild.id}) successfully!")

    bot_cmd_channel = discord.utils.get(guild.channels, name=BOT_CMD_CHANNEL)
    if not bot_cmd_channel:
        raise Exception(f"No channel named {BOT_CMD_CHANNEL} found in server {guild.name}")

    problem_stalk_channel = discord.utils.get(guild.channels, name=PROBLEM_STALK_CHANNEL)
    if not problem_stalk_channel:
        raise Exception(f"No channel named {PROBLEM_STALK_CHANNEL} found in server {guild.name}")

    contest_stalk_channel = discord.utils.get(guild.channels, name=CONTEST_STALK_CHANNEL)
    if not contest_stalk_channel:
        raise Exception(f"No channel named {CONTEST_STALK_CHANNEL} found in server {guild.name}")

    problem_stalker = ProblemStalker(problem_stalk_channel, guild)
    contest_stalker = ContestStalker(contest_stalk_channel, guild, datetime.time(hour=16, minute=0))
    loop = asyncio.get_event_loop()
    task = loop.create_task(problem_stalker.stalk())
    loop.create_task(contest_stalker.stalk())

    # try:
    #     loop.run_until_complete(task)
    # except asyncio.CancelledError:
    #     pass


async def check_user_fname(cf_handle: str, code: str) -> Tuple[bool, Optional[str]]:
    await asyncio.sleep(VERIFICATION_TIMEOUT)

    async with CFApi() as cf_api:
        fname = await cf_api.get_user_fname(cf_handle)
        if fname is None:
            return False, f'User with Codeforces handle {cf_handle} does not exist'
        elif fname == '':
            return False, f'First name for user {cf_handle} was not set within the time limit. Please try again.'
        elif fname != code:
            return False, f'First name for user {cf_handle} does not match `{code}`. Please try again.'
        else:
            return True, None


@bot.command(name='register', help='Register your CF handle with the bot. Usage: !register <cf_handle>')
async def register(ctx: discord.ext.commands.Context, cf_handle: str):
    if (not ctx.guild == guild or not ctx.channel == bot_cmd_channel) \
            and not isinstance(ctx.channel, discord.channel.DMChannel):
        return
    if cf_handle in verification_requests:
        await ctx.send(f"Verification of handle {cf_handle} is already in progress")
        return
    verification_requests.add(cf_handle)
    async with CFApi() as cf_api:
        user_info = await cf_api.get_user_info(cf_handle)
        if user_info is None:
            verification_requests.remove(cf_handle)
            await ctx.send(f"Codeforces handle {cf_handle} not found")
            return

    # code = uuid.uuid4().hex
    # embed = discord.Embed(color=discord.Color.dark_magenta())
    # embed.add_field(name=f'Verification of handle {cf_handle}',
    #                 value=f"Click [here]({CF_SOCIAL_SETTINGS_URL}) and set "
    #                       f"your 'First Name' to `{code}`, within {VERIFICATION_TIMEOUT} seconds. "
    #                       f"You may change it back after verification.",
    #                 inline=True)
    # await ctx.send(embed=embed)
    # verification_requests.add(cf_handle)

    # (status, error) = await check_user_fname(cf_handle, code)
    # print(status, error)
    # if status:
    if not User.objects(user_id=ctx.author.id):
        new_user = User(user_id=ctx.author.id, cf_handle=cf_handle)
        new_user.save()
    else:
        User.objects(user_id=ctx.author.id).update(cf_handle=cf_handle)

    embed = discord.Embed(color=discord.Color.green())
    embed.add_field(name='Success', value=f"Codeforces handle {cf_handle} successfully "
                                          f"set for {ctx.author.mention}")
    await ctx.send(embed=embed)
    # else:
    #     embed = discord.Embed(color=discord.Color.red())
    #     embed.add_field(name='Failure', value=error)
    #     await ctx.send(embed=embed)
    verification_requests.remove(cf_handle)


@bot.command(name='stalk', help='Turn problem or contest stalking on or off. '
                                'Usage: !stalk problem on/off OR !stalk contest on/off')
async def stalk(ctx: discord.ext.commands.Context, choice: str, setting: bool):
    if (not ctx.guild == guild or not ctx.channel == bot_cmd_channel) \
            and not isinstance(ctx.channel, discord.channel.DMChannel):
        return
    if choice not in ['problem', 'contest']:
        raise commands.BadArgument
    kwargs = {f"{choice}_stalk": setting}
    User.objects(user_id=ctx.author.id).update(**kwargs)
    if setting:
        await ctx.send(f"Successfully turned on {choice} stalking for {ctx.author.name}")
    else:
        await ctx.send(f"Successfully turned off {choice} stalking for {ctx.author.name}")


@bot.event
async def on_command_error(ctx, error):
    if (not ctx.guild == guild or not ctx.channel == bot_cmd_channel) \
            and not isinstance(ctx.channel, discord.channel.DMChannel):
        return
    if isinstance(error, commands.errors.MissingRequiredArgument)\
            or isinstance(error, commands.errors.BadArgument):
        cmd_name = ctx.message.content.split(' ')[0][1:]
        if cmd_name not in command_syntax:
            await ctx.send(f"Invalid command: ```{cmd_name}```")
        else:
            await ctx.send(f"Correct usage: ```{bot.command_prefix + command_syntax[cmd_name]}```")


bot.run(TOKEN)
