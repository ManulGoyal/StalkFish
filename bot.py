import discord
from discord.ext import commands
import os
import logging
import asyncio
from utils import *
from problem_stalk import ProblemStalker
import uuid
from cf_api import CFApi, CF_SOCIAL_SETTINGS_URL
from typing import Tuple, Union, Optional
from mongoengine import *
from documents import *
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CMD_FILENAME = 'commands.txt'
VERIFICATION_TIMEOUT = 20
DB_NAME = 'StalkDB'

connect(DB_NAME)

bot = commands.Bot(command_prefix='!')
command_syntax = read_commands_from_file(CMD_FILENAME)
verification_requests = set()


@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    if not guild:
        raise Exception(f"No server named {GUILD} found")

    logging.info(f"{bot.user} connected to server {guild.name} (ID: {guild.id}) successfully!")
    problem_stalker = ProblemStalker()
    loop = asyncio.get_event_loop()
    task = loop.create_task(problem_stalker.stalk())

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


@bot.command(name='register')
async def register(ctx, cf_handle: str):
    if cf_handle in verification_requests:
        await ctx.send(f"Verification of handle {cf_handle} is already in progress")
        return
    async with CFApi() as cf_api:
        user_info = await cf_api.get_user_info(cf_handle)
        if user_info is None:
            await ctx.send(f"Codeforces handle {cf_handle} not found")
            return

    code = uuid.uuid4().hex
    embed = discord.Embed(color=discord.Color.dark_magenta())
    embed.add_field(name=f'Verification of handle {cf_handle}',
                    value=f"Click [here]({CF_SOCIAL_SETTINGS_URL}) and set "
                          f"your 'First Name' to `{code}`, within {VERIFICATION_TIMEOUT} seconds. "
                          f"You may change it back after verification.",
                    inline=True)
    await ctx.send(embed=embed)
    verification_requests.add(cf_handle)

    (status, error) = await check_user_fname(cf_handle, code)
    print(status, error)
    if status:
        if not User.objects(user_id=ctx.author.id):
            new_user = User(user_id=ctx.author.id, cf_handle=cf_handle)
            new_user.save()
        else:
            User.objects(user_id=ctx.author.id).update(cf_handle=cf_handle)

        embed = discord.Embed(color=discord.Color.green())
        embed.add_field(name='Success', value=f"Codeforces handle {cf_handle} successfully "
                                              f"set for {ctx.author.mention}")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(color=discord.Color.red())
        embed.add_field(name='Failure', value=error)
        await ctx.send(embed=embed)
    verification_requests.remove(cf_handle)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        cmd_name = ctx.message.content.split(' ')[0][1:]
        if cmd_name not in command_syntax:
            await ctx.send(f"Invalid command: ```{cmd_name}```")
        else:
            await ctx.send(f"Correct usage: ```{bot.command_prefix + command_syntax[cmd_name]}```")

bot.run(TOKEN)
