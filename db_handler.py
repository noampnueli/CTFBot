from os import path, mkdir
import sqlite3
from typing import List, Dict

solved_table_name = 'solved_challenges'
database_directory = path.join(path.dirname(path.abspath(__file__)), 'database')


class Database(object):

    def __init__(self, database_file='ctfbot.db'):
        self.database_file = database_file

        if not path.exists(database_directory):
            mkdir(database_directory)

    def __enter__(self):
        self.connection = sqlite3.connect(path.join(database_directory, self.database_file))
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_traceback):
        self.connection.close()

    def check_create_tables(self) -> None:
        """
        This method checks if the tables required for the bot exist in the database.
        It creates them if they are not found
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

    def load_solved(self, events) -> None:
        """
        Writes to `events` all challenges solved across all servers

        Parameters:
        ----------
        events: dict[str, Event]:
            The events dictionary to write data to

        """

        for server_id in events:

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
                print("Inserting(or ignoring) solved challenges {0} to table".format(challenge))
                self.cursor.execute("INSERT OR IGNORE INTO {} (user, server_id, challenge_name) VALUES ('{}','{}', '{}')".format(solved_table_name, member_id, server_id, challenge))

        print("Updated row count: {0}".format(self.cursor.rowcount))
        self.connection.commit()
