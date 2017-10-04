import discord
from challenge import Event

from os import path, listdir

import pickle

event_dir = path.join(path.dirname(path.abspath(__file__)), 'events')
challenges_dir = path.join(path.dirname(path.abspath(__file__)), 'challenges')


class Bot(discord.Client):
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
                    self.events[server.id].scoreboard.add_participant(member)
                # Update challenges
                challenge_p = path.join(challenges_dir, server.id)
                self.events[server.id].load_challenges(challenge_p)

        # Update events
        self.save_events()

    def __create_event(self, server: discord.Server):
        event = Event()

        challenge_p = path.join(challenges_dir, server.id)
        if path.exists(challenge_p):
            event.load_challenges(challenge_p)

        for member in server.members:
            event.scoreboard.add_participant(member)

        self.events[server.id] = event

    def save_events(self):
        for server_id in self.events:
            file = open(path.join(event_dir, server_id + '.pkl'), 'wb')
            pickle.dump(self.events[server_id], file, protocol=pickle.HIGHEST_PROTOCOL)
            file.close()

    async def update_challenge_board(self):
        for server in self.servers:
            for channel in server.channels:
                if channel.name.lower() == 'challenges':
                    # Clean old feed
                    try:
                        await self.purge_from(channel, limit=100)
                    except discord.HTTPException as e:
                        print(e)

                    for challenge in self.events[server.id].challenges:
                        embed = discord.Embed(title=challenge.name, description=challenge.description,
                                              color=0x3296d5)
                        embed.add_field(name='Difficulty',
                                        value=':triangular_flag_on_post:' * challenge.difficulty, inline=True)
                        embed.add_field(name='Reward',
                                        value='{} points'.format(challenge.reward), inline=True)
                        await self.send_message(channel, embed=embed)

    async def update_score_board(self):
        for server in self.servers:
            for channel in server.channels:
                if channel.name.lower() == 'scoreboard':
                    # Clean old feed
                    try:
                        await self.purge_from(channel, limit=100)
                    except discord.HTTPException as e:
                        print(e)

                    embed = discord.Embed(title="Scoreboard",
                                          description=self.events[server.id].scoreboard.get_board(),
                                          color=0x38bc35)
                    await self.send_message(channel, embed=embed)
