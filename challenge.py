from os import path


class Challenge(object):
    def __init__(self, flag: str, name: str, description='', difficulty=0, reward=0):
        self.flag = flag
        self.description = description
        self.difficulty = difficulty
        self.name = name
        self.reward = reward

    def __str__(self):
        return self.name


class Scoreboard(object):
    def __init__(self, participants=None):
        if participants:
            self.participants = participants
        else:
            self.participants = {}

    def add_participant(self, member):
        if member not in self.participants:
            self.participants[member] = 0

    def add_score(self, member, score: int):
        self.participants[member] += score

    def get_board(self) -> str:
        tmp = ''
        for member in sorted(self.participants, key=self.participants.get, reverse=True):
            tmp += '{}:  {}\n'.format(member.name, self.participants[member])
        return tmp


class Event(object):
    def __init__(self, challenges=None):
        if challenges:
            self.challenges = challenges
        else:
            self.challenges = []
        self.scoreboard = Scoreboard()
        self.solves = {}

    def add_points(self, member, challenge: Challenge) -> bool:
        if member in self.solves and challenge in self.solves[member]:
            return False
        self.scoreboard.add_score(member, challenge.reward)

        # Add challenge to solved challenges
        if member not in self.solves:
            self.solves[member] = [challenge]
        else:
            self.solves[member].append(challenge)
        return True

    def add_challenge(self, challenge: Challenge):
        if isinstance(challenge, Challenge):
            self.challenges.append(challenge)
        else:
            raise TypeError("Type is not a Challenge")

    def load_challenges(self, p: str):
        """
        Load challenges from file
        File format:
        <Flag>|<Name>|<Description>|<Difficulty>|<Reward>\n
        :param p: path to file
        """
        if not path.exists(p):
            return
        with open(p, 'r') as file:
            # Clean old challenges
            self.challenges = []

            data = file.read()

            challenges = data.strip('\n').split('\n')

            for challenge in challenges:
                tmp = challenge.split('|')
                try:
                    self.challenges.append(Challenge(tmp[0], tmp[1], tmp[2], int(tmp[3]), int(tmp[4])))
                except IndexError as e:
                    print('Invalid format: {}'.format(e))

    def check_answer(self, flag: str, challenge_name: str) -> Challenge:
        for challenge in self.challenges:
            if str(challenge).replace(' ', '').lower() == challenge_name.lower():
                if flag == challenge.flag:
                    return challenge
        return None
