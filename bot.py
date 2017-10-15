import discord
from challenge import Event, Challenge

from os import path, listdir

import pickle

event_dir = path.join(path.dirname(path.abspath(__file__)), 'events')
challenges_dir = path.join(path.dirname(path.abspath(__file__)), 'challenges')


class Bot(discord.Client):
    """

    Attributes:
    ----------
    events: dict
        Key is server id
        Value is `Event` god-object

    """
    def __init__(self, **options):
        super().__init__(**options)

        self.events = {}

    async def load_modules(self):
        # Load events
        for p, name in [(path.join(event_dir, e), e) for e in listdir(event_dir)]:
            with open(p, 'rb') as file:
                tmp = pickle.load(file)
                if isinstance(tmp, Event):
                    self.events[name.strip('.pkl')] = tmp

        for server in self.servers:
            if server.id not in self.events:
                # Create new event, event is per server
                self.__create_event(server)
            else:
                # Update participants
                for member in server.members:
                    if not member.bot:
                        self.events[server.id].scoreboard.add_participant(member)
                # Remove members not in server
                for member in list(self.events[server.id].scoreboard.participants):
                    if member not in server.members:
                        self.events[server.id].scoreboard.participants.pop(member)
                # Update challenges
                challenge_p = path.join(challenges_dir, server.id)
                self.events[server.id].load_challenges(challenge_p)

        # Update events
        self.save_events()

    def __create_event(self, server: discord.Server) -> None:
        """
        Internal method to load a single event object

        Parameters:
        ----------
        server: `discord.Server`:
            Server to load the object for
        """
        event = Event(server.id)

        challenge_p = path.join(challenges_dir, server.id)
        if path.exists(challenge_p):
            event.load_challenges(challenge_p)

        for member in server.members:
            event.scoreboard.add_participant(member)

        self.events[server.id] = event

    def save_events(self) -> None:
        """
        Serializes event objects and saves them on the disk
        :return:
        """
        for server_id in self.events:
            file = open(path.join(event_dir, server_id + '.pkl'), 'wb')
            pickle.dump(self.events[server_id], file, protocol=pickle.HIGHEST_PROTOCOL)
            file.close()

    async def update_challenge_board(self) -> None:
        """
        Removes the previous list of challenges in every server the bot is in and creates a new one
        :return:
        """
        for server in self.servers:
            for channel in server.channels:
                if channel.name.lower() == 'challenges':
                    # Clean old feed
                    try:
                        await self.purge_from(channel)
                    except discord.HTTPException as e:
                        print(e)

                    flag_submission = discord.Embed(title='How to Submit a Flag',
                                                    description='Send me a private message in this format:\n'
                                                                '<challenge name>:<flag>#{}'.format(server.id),
                                                    color=0x3296d5)
                    await self.send_message(channel, embed=flag_submission)

                    for challenge in self.events[server.id].challenges:
                        challenge_embed = discord.Embed(title=challenge.name, description=challenge.description,
                                                        color=0x3296d5)
                        challenge_embed.add_field(name='Difficulty',
                                                  value=':triangular_flag_on_post:' * challenge.difficulty, inline=True)
                        challenge_embed.add_field(name='Reward',
                                                  value='{} points'.format(challenge.reward), inline=True)
                        challenge_embed.add_field(name='Category',
                                                  value=challenge.category, inline=True)
                        await self.send_message(channel, embed=challenge_embed)

    async def update_score_board(self) -> None:
        """
        Updates the scoreboard of all servers the bot is in by deleting the previous one and sending a new one
        """

        for server in self.servers:
            for channel in server.channels:
                if channel.name.lower() == 'scoreboard':
                    # Clean old feed
                    try:
                        await self.purge_from(channel)
                    except discord.HTTPException as e:
                        print(e)

                    embed = discord.Embed(title="Scoreboard",
                                          description=self.events[server.id].scoreboard.get_board(),
                                          color=0x38bc35)
                    await self.send_message(channel, embed=embed)

    async def update_answer_feed(self, server_id: str, challenge: Challenge, member: discord.User) -> None:
        """
        Updates the answer feed of a single server.
        This method is called whenever a user successfully completes a challenge


        Parameters:
        ----------
        server_id: str
            ID of the server to update
        challenge: `Challenge`
            The challenge that was completed
        """
        server = None
        for s in self.servers:
            if s.id == server_id:
                server = s
        if not server:
            return
        for channel in server.channels:
            if channel.name.lower() == 'feed':
                await self.send_message(channel,
                                        '{} Just solved **{}**! :crown:'
                                        .format(member.name, challenge.name))
                break
