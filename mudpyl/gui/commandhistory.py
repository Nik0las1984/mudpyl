"""A class for storing the history of what the user has entered into the 
client.
"""
from collections import deque

class CommandHistory(object):

    """The history of what the user's entered."""

    def __init__(self, size):
        self.size = size
        self.commands = deque()
        self.ind = -1

    def add_command(self, command):
        """Add a new command to the history, possibly deleting an old one at
        the same time.
        """
        self.ind = -1
        if command and not command.isspace():
            if self.commands and command == self.commands[0]:
                #stop dupes
                return
            self.commands.appendleft(command)
            if len(self.commands) > self.size:
                self.commands.pop()

    def advance(self):
        """Go forwards one command in the history.
        
        (ie, go forwards in the list of commands, but backwards in time).
        """
        if not self.commands:
            return ''
        #stop overflow
        self.ind = min(self.ind + 1, len(self.commands) - 1)
        res = self.commands[self.ind]
        return res

    def retreat(self):
        """Go back one command, and return the new command.
        
        (backwards in the list of commands, but forwards in time)."""
        #stop underflow - this wouldn't even trigger an IndexError, but go 
        #straight to the end of the list, as it'd be a negative number
        self.ind = max(self.ind - 1, -1)
        if self.ind == -1:
            return ''
        else:
            res = self.commands[self.ind]
            return res
