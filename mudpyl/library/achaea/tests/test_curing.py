from mudpyl.library.achaea.curing import Curer
from mock import Mock, sentinel, patch

@patch(Curer, 'load_csv')
def test_loads_files(our_load_csv):
    our_load_csv.return_value = []
    c = Curer(afflictions_file = sentinel.afflictions,
              attacks_file = sentinel.attacks,
              attack_messages_file = sentinel.attack_messages,
              affliction_classes_file = sentinel.affliction_classes)
    loaded = set(args[0] for args, kwargs in c.load_csv.call_args_list)
    assert loaded == set([sentinel.afflictions, sentinel.attacks,
                          sentinel.attack_messages,
                          sentinel.affliction_classes]), loaded

@patch(Curer, 'load_csv', Mock())
@patch(Curer, 'make_aff_trigger', Mock())
def test_affliction_trigger_make_gets_called_with_rows_of_csv():
    expected = [(sentinel.message1, sentinel.affliction1,
                 sentinel.aff_classes1, sentinel.prereq_affs1),
                (sentinel.message2, sentinel.affliction2,
                 sentinel.aff_classes2, sentinel.preref_affs2)]
    def our_load_csv(self, filename):
        if filename == sentinel.afflictions:
            return expected
        return []
    Curer.load_csv = our_load_csv
    c = Curer(afflictions_file = sentinel.afflictions)
    call_args = [args for args, kw in c.make_aff_trigger.call_args_list]
    assert (call_args == expected)

@patch(Curer, 'load_csv', Mock())
def test_creates_affliction_triggers_with_patterns_given():
    def our_load_csv(self, filename):
        if filename == sentinel.afflictions:
            return [('foo', None, None, []),
                    ('bar', None, None, [])]
        return []
    Curer.load_csv = our_load_csv
    c = Curer(afflictions_file = sentinel.afflictions)
    trig_pats = [trig.regex.pattern for trig in c.triggers]
    assert set(trig_pats) >= set(['foo', 'bar'])

@patch(Curer, 'load_csv')
@patch(Curer, 'afflicted', Mock())
def test_trigger_calls_afflicted_with_given_name(our_load_csv):
    our_load_csv.return_value = []
    c = Curer()
    t = c.make_aff_trigger(None, sentinel.affliction_name, [], [])
    t.func(None, None)
    assert c.afflicted.call_args_list == [((sentinel.affliction_name,), {})]

@patch(Curer, 'load_csv')
@patch(Curer, 'afflicted', Mock())
def test_trigger_sets_illusion_if_attack_type_is_wrong(our_load_csv):
    our_load_csv.return_value = []
    c = Curer()
    c.aff_classes = {'foo': ['bar']}
    t = c.make_aff_trigger(None, sentinel.affliction_name, ['foo'],
                           [])
    c.attacks_this_round.append('baz')
    t.func(None, None)
    assert c.illusioned

@patch(Curer, 'load_csv')
@patch(Curer, 'afflicted', Mock())
def test_trigger_sets_illusioned_if_not_afflicted_right(our_load_csv):
    our_load_csv.return_value = []
    c = Curer()
    t = c.make_aff_trigger(None, sentinel.affliction_name, [], ['bar'])
    t.func(None, None)
    assert c.illusioned

@patch(Curer, 'load_csv')
@patch(Curer, 'afflicted', Mock())
def test_triger_doesnt_set_illusioned_if_afflicted_right_and_attacked_right\
        (our_load_csv):
    our_load_csv.return_value = []
    c = Curer()
    c.afflictions.add("bar")
    c.aff_classes = {'foo': ['spam']}
    c.attacks_this_round.append('spam')
    t = c.make_aff_trigger(None, sentinel.affliction_name, ['foo'], ['bar'])
    t.func(None, None)
    assert not c.illusioned

@patch(Curer, 'load_csv')
def test_afflicted_adds_affliction_to_set_for_round_if_not_in_afflictions\
        (our_load_csv):
    our_load_csv.return_value = []
    c = Curer()
    c.afflicted(sentinel.affliction)
    assert c.afflicted_this_round == set([sentinel.affliction])

@patch(Curer, 'load_csv')
def test_afflicted_adds_affliction_to_afflictions(our_load_csv):
    our_load_csv.return_value = []
    c = Curer()
    c.afflicted(sentinel.affliction)
    assert sentinel.affliction in c.afflictions

@patch(Curer, 'load_csv')
def test_afflicted_doesnt_add_to_this_round_set_if_already_in_afflictions\
        (our_load_csv):
    our_load_csv.return_value = []
    c = Curer()
    c.afflictions.add(sentinel.affliction)
    c.afflicted(sentinel.affliction)
    assert sentinel.affliction not in c.afflicted_this_round

#XXX: reading data files

@patch(Curer, 'load_csv', Mock())
@patch(Curer, 'make_hit_trigger', Mock())
def test_calls_make_hit_trigger_with_each_row_of_csv():
    expected = [(sentinel.message1, sentinel.attack1),
                (sentinel.message2, sentinel.attack2)]
    def our_load_csv(self, filename):
        if filename == sentinel.attack_message:
            return expected
        return []
    Curer.load_csv = our_load_csv
    c = Curer(attack_messages_file = sentinel.attack_message)
    calls = [args for args, kwargs in c.make_hit_trigger.call_args_list]
    assert calls == expected

@patch(Curer, 'load_csv', Mock())
def test_makes_hit_triggers_with_given_patterns():
    def our_load_csv(self, filename):
        if filename == sentinel.attack_message:
            return [('foo', None), ('bar', None)]
        return []
    Curer.load_csv = our_load_csv
    c = Curer(attack_messages_file = sentinel.attack_messages)
    pats = set(trig.regex.pat for trig in c.triggers)
    assert pats <= set(['foo', 'bar'])

class Test_hit_tracking:

    @patch(Curer, 'load_csv')
    def setUp(self, our_load_csv):
        our_load_csv.return_value = []
        self.curer = Curer()

    def test_hit_sets_attacks_type(self):
        self.curer.hit('foo')
        assert self.curer.attack_type == 'foo'

    def test_hit_appends_to_attacks_this_round(self):
        self.curer.hit('foo')
        assert ['foo'] ==  self.curer.attacks_this_round

    def test_attack_type_is_none_with_no_attacks(self):
        assert self.curer.attack_type == 'none'

    def test_made_trigger_calls_hit_with_given_attack(self):
        self.curer.attacks['foo'] = set(), False, ['none']
        t = self.curer.make_hit_trigger(None, 'foo')
        self.curer.hit = Mock()
        t.func(None, None)
        assert self.curer.hit.call_args_list == [(('foo',), {})]

    def test_made_trigger_sets_illusioned_if_not_afflicted_right(self):
        self.curer.attacks['foo'] = set(['spam']), False, ['none']
        t = self.curer.make_hit_trigger(None, 'foo')
        t.func(None, None)
        assert self.curer.illusioned

    def test_made_trigger_sets_illusioned_if_preceding_attack_not_right(self):
        self.curer.attacks['foo'] = set(), False, ['spam']
        t = self.curer.make_hit_trigger(None, 'foo')
        t.func(None, None)
        assert self.curer.illusioned

    def test_made_trigger_doesnt_set_illusion_normally(self):
        self.curer.attacks['foo'] = set(), False, ['none']
        t = self.curer.make_hit_trigger(None, 'foo')
        t.func(None, None)
        assert not self.curer.illusioned

@patch(Curer, 'load_csv')
def test_aff_trigger_goes_before_hit_trigger(our_load_csv):
    our_load_csv.return_value = []
    c = Curer()
    c.attacks[None] = None, None, None
    at = c.make_aff_trigger(None, None, None, [])
    ht = c.make_hit_trigger(None, None)
    assert at.sequence < ht.sequence

@patch(Curer, 'load_csv', Mock())
def test_turns_attacks_to_dict():
    attacks = [(sentinel.attack1, [sentinel.prereqs1], 'true',
                sentinel.attacks_can_follow1),
               (sentinel.attack2, [sentinel.prereqs2], 'false',
                sentinel.attacks_can_follow2)]
    def our_load_csv(self, filename):
        if filename == sentinel.attacks:
            return attacks
        return []
    Curer.load_csv = our_load_csv
    c = Curer(attacks_file = sentinel.attacks)
    assert c.attacks == {sentinel.attack1: (set([sentinel.prereqs1]),
                                            True,
                                            sentinel.attacks_can_follow1),
                         sentinel.attack2: (set([sentinel.prereqs2]),
                                            False,
                                            sentinel.attacks_can_follow2)}

@patch(Curer, 'load_csv', Mock())
def test_turns_aff_classes_to_dict():
    aff_classes = [(sentinel.affliction_class1, [sentinel.attack1]),
                   (sentinel.affliction_class2, [sentinel.attack2])]
    def our_load_csv(self, filename):
        if filename == sentinel.affliction_classes:
            return aff_classes
        return []
    Curer.load_csv = our_load_csv
    c = Curer(affliction_classes_file = sentinel.affliction_classes)
    expected =  {sentinel.affliction_class1: set([sentinel.attack1]),
                 sentinel.affliction_class2: set([sentinel.attack2])}
    assert c.aff_classes == expected
