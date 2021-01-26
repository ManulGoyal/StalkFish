from typing import Dict, Optional
import discord
import random
from documents import *

COLORS = [discord.Color.blue(), discord.Color.green(), discord.Color.magenta(), discord.Color.purple(),
          discord.Color.orange(), discord.Color.dark_gold(), discord.Color.teal()]
ROLES = ['senior', 'junior', 'sophomore', 'freshman', 'pg']
EMOJIS = [':100:', ':ok_hand:', ':clap:', ':bouquet:', ':fire:']
CONGRATS_MESSAGES = ['Congratulations to the top performers!', 'Way to go guys! Keep it up!',
                     'Yay! You rule guys! Keep it up!', 'Well done guys! Never stop practising!',
                     'Awesome performance! Remember, practice makes a man perfect!']
RANK_NUM_EMOJIS = [':first_place:', ':second_place:', ':third_place:']
SEP_EMOJI = ':small_orange_diamond:'
CF_TIERS = {1000: 'Pupil', 1200: 'Apprentice', 1400: 'Specialist', 1600: 'Expert', 1900: 'Candidate Master',
            2100: 'Master', 2300: 'International Master', 2400: 'Grandmaster', 2600: 'International Grandmaster',
            3000: 'Legendary Grandmaster'}
GITHUB_LINK = 'https://github.com/ManulGoyal/StalkFish'


def get_cf_tier(rating: int) -> str:
    if rating < 1000:
        return 'Newbie'
    if rating >= 3000:
        return 'Legendary Grandmaster'
    for r, t in CF_TIERS.items():
        if rating >= r:
            tier = t
        else:
            return tier


def read_commands_from_file(filename: str) -> Dict[str, str]:
    commands = {}
    with open(filename, 'r') as file:
        for line in file:
            cmd_name = line.split(' ')[0]
            commands[cmd_name] = line
    file.close()
    return commands


def get_problem_url(problem):
    return f"https://codeforces.com/contest/{problem['contestId']}/problem/{problem['index']}"


def get_submission_embed(username: str, cf_handle: str, problem: dict) -> discord.Embed:
    embed = discord.Embed(title=f"{username} solved {problem['name']}!",
                          color=random.choice(COLORS), url=get_problem_url(problem))
    # embed.set_author(name='StalkFish', icon_url='https://www.chessprogramming.org/images/0/09/Stockfish-logo.png')
    # embed.set_footer(text=f'StalkFish ©. Stalking since 2021. [Github]({GITHUB_LINK})')
    embed.add_field(name="Handle", value=cf_handle)
    if 'rating' in problem:
        embed.add_field(name="Problem Rating", value=f"{problem['rating']}", inline=True)
    if 'tags' in problem and len(problem['tags']) > 0:
        embed.add_field(name="Tags", value=', '.join(problem['tags']), inline=False)
    # embed.add_field(name="Link", value=get_problem_url(problem))
    return embed


def get_contest_embed(rating_changes: dict, contest_id: int, contest_name: str, top: int = 3)\
        -> Optional[discord.Embed]:
    user_results = {}
    for role in ROLES:
        user_results[role] = []
    for change in rating_changes:
        if len(user_results[change['user']['role']]) == top\
                or change['rating_change']['oldRating'] > change['rating_change']['newRating']:
            continue
        user_results[change['user']['role']].append(change)
    embed = discord.Embed(title=f"{contest_name} Results", color=random.choice(COLORS),
                          url=f"https://codeforces.com/contests/{contest_id}")
    embed.set_author(name='StalkFish', icon_url='https://www.chessprogramming.org/images/0/09/Stockfish-logo.png')
    embed.set_footer(text=f'StalkFish ©. Stalking since 2021.')

    empty = True
    for role in ROLES:
        if len(user_results[role]) == 0:
            continue
        empty = False
        # embed.add_field(name=role.capitalize(), value=f"{random.choice(CONGRATS_MESSAGES)} "
        #                                               f"{random.choice(EMOJIS)}{random.choice(EMOJIS)}", inline=False)
        rank_str = ""
        name_str = ""
        handle_str = ""
        rating_str = ""
        ranklist_str = ""

        for i, result in enumerate(user_results[role]):
            ranklist_str += f"{RANK_NUM_EMOJIS[i]} **{result['user']['name']}** " \
                      f"([{result['rating_change']['handle']}]" \
                      f"(https://codeforces.com/profile/{result['rating_change']['handle']})) {SEP_EMOJI} " \
                      f"**Rank:** {result['rating_change']['rank']} {SEP_EMOJI} **Rating:** " \
                      f"{result['rating_change']['oldRating']} ➯ {result['rating_change']['newRating']}"

            if get_cf_tier(result['rating_change']['oldRating']) != get_cf_tier(result['rating_change']['newRating']):
                ranklist_str += f" {SEP_EMOJI} Congrats on becoming **{get_cf_tier(result['rating_change']['newRating'])}**!"
            ranklist_str += '\n\n'
            rank_str += f"{result['rating_change']['rank']}\n"
            name_str += f"[{result['user']['name']}]" \
                        f"(https://codeforces.com/profile/{result['rating_change']['handle']})\n"
            handle_str += f"{result['rating_change']['handle']}\n"
            rating_str += f"{result['rating_change']['oldRating']} ➯ {result['rating_change']['newRating']}"

        # embed.add_field(name="Rank", value=rank_str, inline=True)
        # embed.add_field(name="Name", value=name_str, inline=True)
        # embed.add_field(name="Handle", value=handle_str, inline=True)
        # embed.add_field(name="Rating", value=rating_str, inline=True)
        embed.add_field(name=role.capitalize(), value=f"{random.choice(CONGRATS_MESSAGES)} "
                                                      f"{random.choice(EMOJIS)}{random.choice(EMOJIS)}\n\n"
                                                      f"{ranklist_str}", inline=False)
    if not empty:
        return embed
    else:
        return None


def fetch_user_roles(guild: discord.Guild, **kwargs) -> Dict[str, Dict[str, str]]:
    user_roles = {}
    users = User.objects(**kwargs)

    for user in users:
        discord_user = discord.utils.get(guild.members, id=user.user_id)
        discord_user_roles = [role.name.lower() for role in discord_user.roles]

        for role in ROLES:
            if role in discord_user_roles:
                user_roles[user.cf_handle] = {'name': discord_user.name, 'mention': discord_user.mention, 'role': role}
                break
    return user_roles

