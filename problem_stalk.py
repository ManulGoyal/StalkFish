import asyncio
from documents import *
from cf_api import CFApi


class ProblemStalker:

    def __init__(self, interval=10):
        self.interval = interval

    async def stalk(self):
        while True:
            users = User.objects(problem_stalk=True)
            print(users)
            async with CFApi() as cf_api:
                for user in users:
                    sub = await cf_api.get_user_submissions(user.cf_handle, 5)
                    print(sub)

            await asyncio.sleep(self.interval)

