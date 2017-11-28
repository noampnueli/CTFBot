import discord
from bot import Bot
import sys

token_path = 'token.txt'
if len(sys.argv) > 1:
    token_path = sys.argv[1]

with open(token_path) as token_file:
    token = token_file.read().strip('\n')

bot = Bot()


@bot.event
async def on_ready() -> None:
    """
    From discord.py documentation:
    ```
    Called when the client is done preparing the data received from Discord. Usually after login is successful and the
    Client.servers and co. are filled up.
    ```
    """
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    await bot.load_modules()
    await bot.update_challenge_board()
    await bot.update_score_board()


@bot.event
async def on_member_join(member: discord.Member) -> None:
    """
    Called when someone has joined the server(New blood)
    """
    event = bot.events[member.server.id]
    event.scoreboard.add_participant(member)


@bot.event
async def on_message(message: discord.Message) -> None:
    """
    Called whenever a message was sent in one of the servers the bot is in
    If the message was a PM this method checks if it was a flag submission and it verifiers the solution
    If the message was a global message this method checks if the sender is an admin that requested a reload of the bot
    """
    if message.author.bot:
        return
    if message.channel.is_private:
        # Answer format: <challenge name>:<flag>#<server ID>
        try:
            answer, server_id = message.content.split('#')
            challenge_name, flag = answer.replace(' ', '').split(':')
        except ValueError as e:
            print(e)
            await bot.send_message(message.channel,
                                   '{} Please send your answer in the following format: '
                                   '<challenge name>:<flag>#SERVER_ID'.format(message.author.mention))
        else:

            if server_id not in bot.events:
                await bot.send_message(message.channel, "{} This bot is not in the server with the ID {}".format(message.author.mention, server_id))
                return

            event = bot.events[server_id]
            challenge = event.check_answer(flag, challenge_name)
            # Correct answer
            if challenge:
                if event.add_points(message.author, challenge):
                    await bot.send_message(message.channel,
                                           '{} Correct! Here are {} points'.format(message.author.mention,
                                                                                   challenge.reward))
                    print("Solved challenge name: {}, server_id: {}", challenge.name, server_id)
                    bot.save_events()
                    await bot.update_score_board()
                    await bot.update_answer_feed(server_id, challenge, message.author)
                else:
                    await bot.send_message(message.channel,
                                           '{} You already solved this challenge!'.format(message.author.mention))
            else:
                await bot.send_message(message.channel,
                                       '{} Incorrect flag or there is no such challenge :('.format(
                                           message.author.mention))
    elif message.content == '!reload':  # TODO: reload only for one specific server
        if message.author.server.owner.top_role in message.author.roles:
            await bot.load_modules()
            await bot.update_challenge_board()
            await bot.update_score_board()


bot.run(token)
