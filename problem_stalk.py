import asyncio
import discord
from documents import *
from cf_api import CFApi
from utils import *
import logging


class ProblemStalker:

    def __init__(self, channel: discord.abc.GuildChannel, guild: discord.Guild,
                 interval: int = 60, recency: int = 5) -> None:
        self.interval = interval
        self.recency = recency
        self.guild = guild
        self.channel = channel

    async def stalk(self):
        while True:
            users = User.objects(problem_stalk=True)

            async with CFApi() as cf_api:
                for user in users:
                    submissions = await cf_api.get_user_submissions(user.cf_handle, self.recency)
                    if submissions is None:
                        logging.error(f"Error while fetching {user.cf_handle}'s submissions")
                        continue
                    username = discord.utils.get(self.guild.members, id=user.user_id).name
                    for submission in submissions:
                        if 'problem' in submission and 'contestId' in submission['problem'] \
                                and 'index' in submission['problem'] and submission['verdict'] == 'OK':
                            problem_id = f"{submission['problem']['contestId']}{submission['problem']['index']}"
                            if problem_id not in user.solved_problems:
                                user.solved_problems.append(problem_id)
                                await self.channel.send(embed=get_submission_embed(username, user.cf_handle,
                                                                                   submission['problem']))
                    user.save()

            await asyncio.sleep(self.interval)
