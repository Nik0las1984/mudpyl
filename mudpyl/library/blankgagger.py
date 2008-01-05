"""Gags the blank lines after prompts for IRE MUDS."""
from mudpyl.triggers import binding_trigger
from mudpyl.modules import EarlyInitialisingModule
import re

class BlankLineGagger(EarlyInitialisingModule):

    """Gag IRE MUDs' extra blank lines after prompts."""

    def __init__(self, prompt_received_line = 
                          r'^(\d+)h, (\d+)m, (\d+)e, (\d+)w c?e?x?k?d?b?-$'):
        self.on_prompt = False
        self.prompt_received.regex = re.compile(prompt_received_line)

#pylint likes complaining about the unused arguments in the callbacks, which
#are actually perfectly harmless.
#pylint: disable-msg=W0613

    @binding_trigger(None)
    def prompt_received(self, match, realm):
        """We've had a prompt."""
        self.on_prompt = True

    #must fire before that prompt trigger, else we'll just hit the prompt,
    #notice it's not empty, and set on_prompt to False, undoing the other
    #trigger's work.
    @binding_trigger('^.*$', sequence = -1)
    def something_received(self, match, realm):
        """If the line is blank and the previous line was a prompt, it's
        an extra blank line.

        Gag it, then.
        """
        if self.on_prompt:
            realm.display_line = bool(realm.metaline.line)
            self.on_prompt = False

#pylint: enable-msg=W0613

    @property
    def triggers(self):
        """The triggers we need added."""
        return [self.prompt_received,
                self.something_received]
