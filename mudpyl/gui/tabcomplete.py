"""Utilities for implementing tab-completion.
"""
import re

class Trie(object):
    """A tree of dictionaries, representing a set of strings sorted by prefix
    """

    #um, what? Pylint doesn't seem very good at picking up class variables
    #pylint: disable-msg= E0602

    splitting_chars = ' .,()*\'"!?:;\r\n'
    splitting_pattern = re.compile('(?:%s)+' % '|'.join(re.escape(c)
                                                  for c in splitting_chars))

    #pylint: enable-msg= E0602

    def __init__(self):
        self.primkey = ''
        self.sorted_keys = []
        self.descs = {}

    def get(self, key, extend = False):
        """Retrieve a string based on a prefix."""
        if not key:
            primkey = self.sorted_keys[-1]
            if primkey != '':
                desc = self.descs[primkey]
                return primkey + desc.get('', extend = True)
            elif extend and len(self.sorted_keys) > 1:
                #this can happen if we've just been the very final node in a 
                #trace, where self.primkey represents that we're a leaf node,
                #possibly amongst other things.
                desc_key = self.sorted_keys[-2]
                return desc_key + self.descs[desc_key]['']
            else:
                #primkey is ''; we're a leaf node.
                return ''
        else:
            if key[0] in self.descs:
                return key[0] + self.descs[key[0]].get(key[1:], extend)
            else:
                raise KeyError("%s not found!" % key)

    def __getitem__(self, key):
        return self.get(key)

    def _add_word(self, key):
        """Add a new key to the trie."""
        #slice to get the empty string, not an IndexError, if the key is
        #empty.
        first = key[0:1]
        if first in self.sorted_keys:
            self.sorted_keys.remove(first)
        self.sorted_keys.append(first)
        if first:
            if first not in self.descs:
                self.descs[first] = Trie()
            self.descs[first]._add_word(key[1:])

    def add_word(self, key):
        self._add_word(key.lower())

    def add_line(self, line):
        """Split the line up and add words individually."""
        words = self.splitting_pattern.split(line)
        for word in words:
            if word:
                self.add_word(word)

    def complete(self, line, ind):
        """Try and extend the word under the index based on what's in the trie

        ind is the position of the cursor: it is defined as the zero-based 
        index of the character to its right.
        """
        #make indexing into strings more friendly: we're actually concerned 
        #with the character to the cursor's left.
        ind -= 1
        #if ind is -1, we're at the very first character.
        if not line or ind == -1 or line[ind] in self.splitting_chars:
            return line, ind + 1
        wordstart = max(line.rfind(c, 0, ind) 
                        for c in self.splitting_chars) + 1
        try:
            wordend = min(line.find(c, ind) for c in self.splitting_chars 
                            if c in line[ind:])
        except ValueError: #none in the line beyond the index
            wordend = len(line)
        #all our keys are lowercase. Ditto values.
        oldword = line[wordstart:wordend].lower()
        try:
            newword = self[oldword]
            if newword == oldword:
                #try and find a word that's longer.
                newword = self.get(oldword, True)
        except KeyError:
            pass
        else:
            #try and preserve the user's capitalisation.
            if line[wordstart].isupper():
                newword = newword.capitalize()
            line = line[:wordstart] + newword + line[wordend:]
            #cursor is now at the end of the new word. We must minus one, 
            #because len(newword) points us to the end, which is to the right 
            #of the interesting character, as opposed to the left (where we 
            #are).
            ind = len(newword) + wordstart - 1
        return line, ind + 1

