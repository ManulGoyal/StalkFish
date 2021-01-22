import aiohttp
import asyncio
import json
import logging
from typing import Union, Optional, Dict

logging.basicConfig(level=logging.INFO)

CF_SOCIAL_SETTINGS_URL = 'https://codeforces.com/settings/social'
CF_API_URL = 'https://codeforces.com/api'


class CFApi:

    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def __aenter__(self) -> 'CFApi':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get_user_info(self, cf_handle: str) -> Optional[dict]:
        async with self.session.get(f"{CF_API_URL}/user.info?handles={cf_handle}") as resp:
            resp_json = json.loads(await resp.text())
            if resp_json['status'] == 'FAILED':
                logging.error(f"User with handle {cf_handle} not found")
                return None
            else:
                return resp_json['result'][0]

    async def get_user_fname(self, cf_handle: str) -> Optional[str]:
        user_info = await self.get_user_info(cf_handle)
        if not user_info:
            return None
        elif 'firstName' not in user_info:
            return ''
        else:
            return user_info['firstName']

    async def get_user_submissions(self, cf_handle: str, count: int) -> Optional[dict]:
        async with self.session.get(f'{CF_API_URL}/user.status?handle={cf_handle}'
                                    f'&from=1&count={count}') as resp:
            resp_json = json.loads(await resp.text())
            if resp_json['status'] == 'FAILED':
                logging.error(f"User with handle {cf_handle} not found")
                return None
            else:
                return resp_json['result']

    async def get_contests(self, gym: bool = False) -> Optional[dict]:
        async with self.session.get(f'{CF_API_URL}/contest.list?gym={str(gym).lower()}') as resp:
            resp_json = json.loads(await resp.text())
            if resp_json['status'] == 'FAILED':
                logging.error(f"Some error occurred while fetching contests")
                return None
            else:
                return resp_json['result']

    async def get_rating_changes(self, contest_id) -> Optional[dict]:
        async with self.session.get(f'{CF_API_URL}/contest.ratingChanges?contestId={contest_id}') as resp:
            resp_json = json.loads(await resp.text())
            if resp_json['status'] == 'FAILED':
                # logging.error(f"Some error occurred while fetching rating changes for contest {contest_id}")
                return None
            else:
                return resp_json['result']

    async def close(self):
        await self.session.close()


# async def main():
#     async with CFApi() as cf_api:
#         print(await cf_api.get_user_fname('_the_cake_is_a_lie'))
#     # cf_api = CFApi()
#     # print(await cf_api.get_user_fname('_the_cake_is_a_lie'))
#     # await cf_api.close()
#
# asyncio.run(main())