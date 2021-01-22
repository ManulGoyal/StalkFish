import asyncio, datetime
import discord
from documents import *
from cf_api import CFApi
import logging
from utils import *


class ContestStalker:

    def __init__(self, channel: discord.abc.GuildChannel, guild: discord.Guild,
                 interval: int = 600, recency: int = 5) -> None:
        self.interval = interval
        self.recency =recency
        self.guild = guild
        self.channel = channel

    async def stalk(self):
        while True:

            # now = datetime.datetime.now()
            # next_time = datetime.datetime.combine(now.date(), self.time)
            # if now >= next_time:
            #     next_time += datetime.timedelta(days=1)
            # # print(now, next_time, (next_time-now).total_seconds())
            # await asyncio.sleep((next_time - now).total_seconds())

            async with CFApi() as cf_api:
                contests = await cf_api.get_contests(gym=False)
                if contests is None or len(contests) == 0:
                    logging.error(f"Error while fetching list of contests")
                    await asyncio.sleep(self.interval)
                    continue

                for contest in contests[0:self.recency]:
                    if not Contest.objects(contest_id=contest['id']):
                        rating_changes = await cf_api.get_rating_changes(contest['id'])
                        if rating_changes is None:
                            continue
                        new_contest = Contest(contest_id=contest['id'])
                        new_contest.save()

                        user_roles = fetch_user_roles(self.guild, contest_stalk=True)
                        desired_rating_changes = []

                        for change in rating_changes:
                            if change['handle'] in user_roles:
                                desired_rating_changes.append({'user': user_roles[change['handle']],
                                                               'rating_change': change})

                        if len(desired_rating_changes) > 0:
                            desired_rating_changes = sorted(desired_rating_changes,
                                                            key=lambda i: i['rating_change']['rank'], reverse=True)
                            embed = get_contest_embed(desired_rating_changes, contest['id'],
                                                      contest['name'], top=3)
                            await self.channel.send(embed=embed)
                        break
                    else:
                        break

            # now = datetime.datetime.now()
            # next_time = datetime.datetime.combine(now.date(), self.time)
            # if now.time() >= next_time.time():
            #     next_time += datetime.timedelta(days=1)
            # await asyncio.sleep((next_time - now).total_seconds())
            await asyncio.sleep(self.interval)
