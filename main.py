import discord
from bot import Bot

import sys

token_path = 'token.txt'
if len(sys.argv) > 1:
    token_path = sys.argv[1]

token = open(token_path).read().strip('\n')
bot = Bot()


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    await bot.load_modules()
    await bot.update_challenge_board()
    await bot.update_score_board()


@bot.event
async def on_message(message):
    if message.content.startswith('!ctf'):
        # Make sure no one sees the flag!
        await bot.delete_message(message)

        # Answer format: <challenge name>:<flag>
        try:
            challenge_name, flag = message.content[4:].replace(' ', '').split(':')
        except ValueError as e:
            print(e)
            await bot.send_message(message.channel,
                                   '{} Please send your answer in the following format: '
                                   '<challenge name>:<flag>'.format(message.author.mention))
        else:
            event = bot.events[message.channel.server.id]
            challenge = event.check_answer(flag, challenge_name)
            # Correct answer
            if challenge:
                if event.add_points(message.author, challenge):
                    await bot.send_message(message.channel,
                                           '{} Correct! Here are {} points'.format(message.author.mention,
                                                                                   challenge.reward))
                    bot.save_events()
                    await bot.update_score_board()
                else:
                    await bot.send_message(message.channel,
                                           '{} You already solved this challenge!'.format(message.author.mention))
            else:
                await bot.send_message(message.channel,
                                       '{} Incorrect flag :('.format(message.author.mention))
bot.run(token)
