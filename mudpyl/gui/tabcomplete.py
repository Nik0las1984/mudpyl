"""Utilities for implementing tab-completion.
"""
import re

class _ordereddict(dict):

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._key_order = []

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        if key in self._key_order:
            self._key_order.remove(key)
        self._key_order.append(key)
        
    #only implement the bits we really need sorted
    def __iter__(self):
        return iter(self._key_order)

    def keys(self):
        return self._key_order[:]

class Trie(_ordereddict):
    """A tree of dictionaries, representing a set of strings sorted by prefix
    """

    #um, what? Pylint doesn't seem very good at picking up class variables
    #pylint: disable-msg= E0602

    splitting_chars = ' .,()*\'"!?:;\r\n'
    splitting_pattern = re.compile('(?:%s)+' % '|'.join(re.escape(c)
                                                  for c in splitting_chars))

    #pylint: enable-msg= E0602

    def _fetch(self, key, extend = False):
        """Retrieve a string based on a prefix."""
        if not key:
            primkey = self.keys()[-1]
            if primkey != '':
                desc = self[primkey]
                return primkey + desc._fetch('', extend)
            elif extend and len(self) > 1:
                #this can happen if we've just been the very final node in a 
                #trace, where self.primkey represents that we're a leaf node,
                #possibly amongst other things.
                desc_key = self.keys()[-2]
                return desc_key + self[desc_key]._fetch('')
            else:
                #primkey is ''; we're a leaf node.
                return ''
        else:
            if key[0] in self:
                return key[0] + self[key[0]]._fetch(key[1:], extend)
            else:
                raise KeyError("%s not found!" % key)

    def _add_word(self, key):
        """Add a new key to the trie casefully."""
        trie = self
        for char in key:
            #use this construct rather than .get() because constructing a Trie
            #is expensive when it gets run a lot
            if char in trie:
                child = trie[char]
            else:
                child = Trie()
            trie[char] = child
            trie = child
        trie[''] = Trie()
            
    #pylint: enable-msg = E1101, W0212

    def add_word(self, key):
        """Add a word to the trie caselessly."""
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
        oldword_raw = line[wordstart:wordend]
        #all our keys are lowercase. Ditto values.
        oldword = oldword_raw.lower()
        try:
            newword = self._fetch(oldword)
            if newword == oldword:
                #try and find a word that's longer.
                newword = self._fetch(oldword, True)
        except KeyError:
            pass
        else:
            #try and preserve the user's capitalisation.
            if len(oldword_raw) > 1 and oldword_raw.isupper():
                newword = newword.upper()
            else:
                newword = oldword_raw + newword[len(oldword):]
            line = line[:wordstart] + newword + line[wordend:]
            #cursor is now at the end of the new word. We must minus one, 
            #because len(newword) points us to the end, which is to the right 
            #of the interesting character, as opposed to the left (where we 
            #are).
            ind = len(newword) + wordstart - 1
        return line, ind + 1

