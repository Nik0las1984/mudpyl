from mudpyl.aliases import binding_alias

class Test_binding_lias:

    @binding_alias('foo')
    def alias_1(self, match, info):
        pass

    def test_match(self):
        assert self.alias_1.match("foo")

    def test_multiple_matching(self):
        assert len(self.alias_1.match('foo foo')) == 2

    def test_identity_of_different_accesses_are_the_same(self):
        assert self.alias_1 is self.alias_1

from mudpyl.aliases import AliasMatchingRealm

class Test_AliasMatchingRealm:

    def test_default_is_to_send_to_mud(self):
        a = AliasMatchingRealm(None, None, None, None)
        assert a.send_to_mud

    def test_echo_setting(self):
        o = object()
        a = AliasMatchingRealm(None, o, None, None)
        assert a.echo is o

    def test_setting_line(self):
        o = object()
        a = AliasMatchingRealm(o, None, None, None)
        assert a.line is o

    def test_setting_parent(self):
        o = object()
        a = AliasMatchingRealm(None, None, parent = o, root = None)
        assert a.parent is o

    def test_setting_root(self):
        o = object()
        a = AliasMatchingRealm(None, None, parent = None, root = o)
        assert a.root is o
