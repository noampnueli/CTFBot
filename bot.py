import discord
from challenge import Event, Challenge

from os import path

from db_handler import Database

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

        for server in self.servers:

            # Creates self.events[server.id]
            self.__create_event(server)

            # Initialize the scoreboard participant list
            for member in server.members:
                if not member.bot:
                    self.events[server.id].scoreboard.add_participant(member)

            # TODO: Need to check if DB has entries for members no longer in the server

        with Database() as db:
            db.check_create_tables()
            db.load_solved(self.events)
            self.compute_scores_servers()

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

    def get_reward_challenge(self, challenge_name, server_id) -> int:
        """
        Returns the reward of the challenge represented by `challenge_name` in  the server `server_id`
        """

        # for every challenge in the collection of challenges
        for challenge in self.events[server_id].challenges:
            # if the challenges` name is the name of the solved challenge
            if (challenge.name + server_id) == challenge_name:
                return challenge.reward

    def compute_score_user(self, server_id, user_id) -> int:
        """
        Returns the score of `user_id` in `server_id`

        """

        score = 0

        # for every solved challenge
        for solved_challenge in self.events[server_id].solves[user_id]:
            score += self.get_reward_challenge(solved_challenge, server_id)

        return score

    def compute_scores_servers(self) -> None:
        """
        Compute scores of all servers
        """

        # for each server
        for server_id in self.events:
            # for each user in the server
            for user_id in self.events[server_id].solves:
                self.events[server_id].scoreboard.participants[self.get_server(server_id).get_member(user_id)] = self.compute_score_user(server_id, user_id)

    def save_events(self) -> None:
        """
        Saves the solved challenges to the database
        """

        with Database() as db:
            for event in self.events.values():
                db.save_solved_challenges(event.solves, event.server_id)

    async def safe_delete_messages(self, channel: discord.Channel) -> None:
        """
        Deletes 100 messages from `channel`

        This function is useful because `discord.Client.purge_from` fails to delete messages older than 14 days

        Parameters:
        ----------
        channel: `discord.Channel`:
            Channel do delete messages from
        """

        # TODO: Handle situation where message count is larger than the default limit(currently 100)
        async for message in self.logs_from(channel):
            await self.delete_message(message)

    async def update_challenge_board(self) -> None:
        """
        Removes the previous list of challenges in every server the bot is in and creates a new one
        """

        for server in self.servers:
            for channel in server.channels:
                if channel.name.lower() == 'challenges':
                    # Clean old feed
                    try:
                        await self.safe_delete_messages(channel)
                    except discord.HTTPException as e:
                        print(e)
                    else:
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
                        await self.safe_delete_messages(channel)
                    except discord.HTTPException as e:
                        print(e)
                    else:
                        scoreboard_embed = discord.Embed(title="Scoreboard",
                                                         description=self.events[server.id].scoreboard.get_board(),
                                                         color=0x38bc35)
                        await self.send_message(channel, embed=scoreboard_embed)

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

        for channel in server.channels:
            if channel.name.lower() == 'feed':
                await self.send_message(channel,
                                        '{} Just solved **{}**! :crown:'
                                        .format(member.name, challenge.name))
                break
