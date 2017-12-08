from os import path, mkdir
import sqlite3
from typing import List, Dict, Iterable

solved_table_name = 'solved_challenges'
database_directory = path.join(path.dirname(path.abspath(__file__)), 'database')


class Database(object):
    """
    Class representing the bots` database connection
    Contains methods required

    Attributes:
    -----------
    database_path: str
       The absolute path to the database file
    """

    def __init__(self, database_file='ctfbot.db'):
        """
        Constructor for the `Database` class
        Creates the folder that contains the DB file if it does not exist
        """

        self.database_path = path.join(database_directory, database_file)

        if not path.exists(database_directory):
            mkdir(database_directory)

    def __enter__(self):
        """
        Magic method that is called when entering the body of a with statement.
        Creates the database connection object and cursor object.
        """

        self.connection = sqlite3.connect(path.join(database_directory, self.database_path))
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        """
        Magic method that is called when exiting the body of a with statement.
        Destroys the DB connection object.
        """

        self.connection.close()

    def check_create_tables(self) -> None:
        """
        Checks if the tables required for the bot exist in the database. If not, create them.
        """

        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(solved_table_name))

        if self.cursor.fetchone() is None:
            print("Solved challenges table not found. Creating one now")
            self.cursor.execute("""CREATE TABLE {}(
            user varchar(40),
            server_id varchar(40),
            challenge_name varchar(40),
            UNIQUE(user, server_id, challenge_name) );
            """.format(solved_table_name))

    def load_solved(self, events, server_id: str) -> None:
        """
        Writes to `events` all challenges solved in `server`

        Parameters:
        ----------
        events: dict[str, Event]:
            The events dictionary to write data to
        """

        # Select all challenges solved in the server `server_id`
        self.cursor.execute("SELECT user, challenge_name FROM {} WHERE server_id='{}'".format(solved_table_name, server_id))

        for solved_challenge in self.cursor.fetchall():
            user_id = solved_challenge[0]
            challenge_name = solved_challenge[1]

            # If there is no entry for challenges solved by `user_id`, create one with `challenge_name`
            # Otherwise, append `challenge_name` to the list
            if user_id not in events[server_id].solves:
                events[server_id].solves[user_id] = [challenge_name]
            else:
                events[server_id].solves[user_id].append(challenge_name)

    def save_solved_challenges(self, user_solves: Dict[str, List[str]], server_id: str) -> None:
        """
        Updates the database of solved challenges
        The query used does not allow for duplicate entries in the database

        Parameters:
        ----------
        user_solves: dict[str, list[str]]
            Key is member id
            Value is list of solved challenges
        server_id: str
            ID of the server to save
        """

        for member_id, solved_challenges in user_solves.items():
            for challenge in solved_challenges:
                self.cursor.execute("INSERT OR IGNORE INTO {} (user, server_id, challenge_name) VALUES ('{}','{}', '{}')".format(solved_table_name, member_id, server_id, challenge))

        self.connection.commit()

    def remove_redundancies(self, members, challenges) -> None:
        """
        Removes from the database entries of solved challenges by users no longer in the server
        Removes from the database entries of solved challenges no longer defined in the server

        Parameters:
        ----------
        members: Iterable[discord.Member]
            Iterable of members in the server whose records should remain in the DB
        challenges: Iterable[Challenge]
            Iterable of challenges that should remain in the DB
        """

        user_list = ", ".join(map(lambda user: repr(user.id), members))
        challenge_list = ", ".join(map(lambda challenge: repr(challenge), challenges))

        self.cursor.execute("DELETE FROM {} WHERE user NOT IN ({})".format(solved_table_name, user_list))
        self.cursor.execute("DELETE FROM {} WHERE challenge_name NOT IN ({})".format(solved_table_name, challenge_list))

        self.connection.commit()
