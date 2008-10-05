from mudpyl.library.secreter import Secreter
from mock import Mock, sentinel

class TestSecreting:

    def setUp(self):
        self.secreter = Secreter(Mock())

    def test_sends_secrete_command_to_realm(self):
        realm = Mock()
        self.secreter.secrete('sumac', realm)
        assert realm.send.call_args_list == [(("secrete sumac",), {})]

    def test_sets_self_venom_to_venom(self):
        self.secreter.secrete("sumac", Mock())
        assert self.secreter.venom == "sumac"

    def test_self_venom_is_defaultly_None(self):
        assert self.secreter.venom is None

    def test_purges_if_secreting_different_venom(self):
        self.secreter.venom = 'foo'
        realm = Mock()
        self.secreter.secrete("sumac", realm)
        assert realm.send.call_args_list == [(('purge',), {}),
                                             (('secrete sumac',), {})]

    def test_doesnt_purge_if_secreting_same_venom(self):
        self.secreter.venom = 'sumac'
        realm = Mock()
        self.secreter.secrete('sumac', realm)
        assert realm.send.call_args_list == [], realm.send.call_args_list

    def test_secreting_aliases(self):
        for alias, venom in {'sum': 'sumac',
                             'xen': 'xentio',
                             'kal': 'kalmia',
                             'cur': 'curare',
                             'dar': 'darkshade',
                             'ole': 'oleander',
                             'eur': 'eurypteria',
                             'dgi': 'digitalis',
                             'ept': 'epteth',
                             'pre': 'prefarar',
                             'mon': 'monkshood',
                             'eup': 'euphorbia',
                             'col': 'colocasia',
                             'ocu': 'oculus',
                             'cam': 'camus',
                             'ver': 'vernalius',
                             'eps': 'epseth',
                             'lar': 'larkspur',
                             'sli': 'slike',
                             'voy': 'voyria',
                             'del': 'delphinium',
                             'not': 'notechis',
                             'var': 'vardrax',
                             'lok': 'loki',
                             'aco': 'aconite',
                             'sel': 'selarnia',
                             'gec': 'gecko',
                             'scy': 'scytherus',
                             'nec': 'nechamandra'}.items():
            ms = list(self.secreter.secrete_alias.match(alias))
            assert len(ms) == 1
            realm = Mock()
            self.secreter.venom = None
            self.secreter.secrete_alias(ms[0], realm)
            assert realm.send.call_args_list == [(("secrete " + venom,), {})]

    def test_alias_doesnt_match_when_not_alone(self):
        assert not list(self.secreter.secrete_alias.match("snot"))
        assert not list(self.secreter.secrete_alias.match("note"))

    def test_purge_clears_self_venom(self):
        self.secreter.venom = sentinel.venom
        self.secreter.purge_alias(Mock(), Mock())
        assert self.secreter.venom is None

    def test_purge_alias_matching(self):
        assert len(list(self.secreter.purge_alias.match("pu"))) == 1
        assert not list(self.secreter.purge_alias.match("purge"))
        assert not list(self.secreter.purge_alias.match("foopu"))

    def test_aliases_are_listed_in_self_alias(self):
        assert self.secreter.purge_alias in self.secreter.aliases
        assert self.secreter.secrete_alias in self.secreter.aliases
