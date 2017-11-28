
class Challenge(object):
    """
    Class representing a challenge in the server

    Attributes:
    -----------
    flag: str
        The flag(solution) of the challenge
    name: str
        The name of the challenge
    category: str
        The category of the challenge
    description: str
        The description of the challenge
    difficulty: int
        The difficulty of the challenge(number of :triangular_flag_on_post: displayed)
    reward: int
        Number of points awarded for completing the challenge
    """
    def __init__(self, flag: str, name: str, category: str, description='', difficulty=0, reward=0):
        self.flag = flag
        self.description = description
        self.difficulty = difficulty
        self.name = name
        self.reward = reward
        self.category = category

    def __str__(self) -> str:
        return self.name


class Scoreboard(object):
    """
    Class representing the servers' scoreboard

    Attributes:
    ----------
    participants: dict
        Dictionary of the servers' members.
        The key is of type `discord.Member`.
        The value is the members' score.
    """
    def __init__(self, participants=None):
        if participants:
            self.participants = participants
        else:
            self.participants = {}

    def add_participant(self, member) -> None:
        """
        Adds `member` to the internal list of challenge participants if they are not already in the list

        Parameters:
        ----------
        member: `discord.Member`
            Member to add to the internal list
        """
        if member not in self.participants:
            self.participants[member] = 0

    def add_score(self, member, score: int) -> None:
        """
        Adds `score` points to the members' current score

        Parameters:
        ---------
        member: `discord.Member`
            Member to add points to
        score: int
            How many points should be added to the score
        """
        self.participants[member] += score

    def get_board(self) -> str:
        """
        Returns a string representation of the scoreboard sorted from the highest score to the lowest
        """

        scoreboard = ''
        for member in sorted(self.participants, key=self.participants.get, reverse=True):
            if not member.bot:
                scoreboard += '{}:  {}\n'.format(member.display_name, self.participants[member])
        return scoreboard


class Event(object):
    """
    This class is basically a god-object

    Attributes:
    ----------
    challenges: list
        Internal list of challenges
    scoreboard: `Scoreboard`
        The scoreboard object of the server
    solves: dict
        Dictionary of challenges solved by a server member
        Key is member id
        Value is list of solved challenges in all server. Each list item is of the form <Challenge Name><Server Id>
    server_id: str
        The server id
    """
    def __init__(self, server_id: str, challenges=None):
        if challenges:
            self.challenges = challenges
        else:
            self.challenges = []
        self.scoreboard = Scoreboard()
        self.solves = {}
        self.server_id = server_id

    def add_points(self, member, challenge: Challenge) -> bool:
        """
        Checks if the user `member` had already completed the challenge and tries to add to his score
        If the challenge has already been solved returns False
        If the challenge is yet to be solved returns True and adds the appropriate number of points to the users' score

        Parameters:
        ----------
        member: `discord.Member`
            Member to check
        challenge: `Challenge`
            Challenge to check

        """
        if member.id in self.solves and challenge.name + self.server_id in self.solves[member.id]:
            return False
        self.scoreboard.add_score(member, challenge.reward)

        # Add challenge to solved challenges
        if member.id not in self.solves:
            self.solves[member.id] = [challenge.name + self.server_id]
        else:
            self.solves[member.id].append(challenge.name + self.server_id)
        return True

    def add_challenge(self, challenge: Challenge) -> None:
        """
        Adds a challenge to the internal list of challenges if and only if the challenge is an instance of `Challenge`

        This function is not actually called anywhere...

        Parameters:
        ----------
        challenge: `Challenge`
            The challenge to add
        """
        if isinstance(challenge, Challenge):
            self.challenges.append(challenge)
        else:
            raise TypeError("Type is not a Challenge")

    def load_challenges(self, p: str) -> None:
        """
        Load challenges from file
        File format:
        <Flag>|<Name>|<Category>|<Description>|<Difficulty>|<Reward>\n
        :param p: path to file
        """

        with open(p, 'r') as file:
            # Clean old challenges
            self.challenges = []

            data = file.read()

            challenges = data.strip('\n').split('\n')

            for challenge in challenges:
                tmp = challenge.split('|')
                try:
                    self.challenges.append(Challenge(tmp[0], tmp[1], tmp[2], tmp[3], int(tmp[4]), int(tmp[5])))
                except IndexError as e:
                    print('Invalid format: {}'.format(e))

    def check_answer(self, flag: str, challenge_name: str) -> Challenge:
        """
        Checks if the answer which was given to the challenge.
        If the answer is correct, returns the Challenge object. Otherwise, None is returned

        Parameters:
        ----------
        flag: str
            The flag to the challenge
        challenge_name: str
            The challenge the answer was given to. Challenge names are case-insensitive
        """
        for challenge in self.challenges:
            if str(challenge).replace(' ', '').lower() == challenge_name.lower():
                if flag == challenge.flag:
                    return challenge
        return None
