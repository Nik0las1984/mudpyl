from mudpyl.library.achaea.afftracker import AffTracker
from mock import Mock, sentinel

def test_creates_triggers_with_patterns_given():
    affpats = [('foo', 'bar', []),
               ('baz', 'qux', [])]
    a = AffTracker(affpats)
    trig_pats = [trig.regex.pattern for trig in a.triggers]
    assert set(trig_pats) == set(['foo', 'baz'])

def test_trigger_calls_afflicted_with_given_name():
    pats = [('foo', 'bar', [sentinel.attack_type])]
    a = AffTracker(pats)
    trig = a.triggers[0]
    a.afflicted = Mock()
    realm = Mock()
    realm.hit_tracker.attack_type = sentinel.attack_type
    trig.func(sentinel.match, realm)
    assert a.afflicted.call_args_list == [(('bar',), {})]

def test_trigger_doesnt_call_afflicted_if_attack_type_is_wrong():
    pats = [('foo', 'bar', [sentinel.attack_type])]
    a = AffTracker(pats)
    trig = a.triggers[0]
    a.afflicted = Mock()
    trig.func(sentinel.match, Mock())
    assert not a.afflicted.called

def test_afflicted_adds_affliction_to_set_for_this_round():
    a = AffTracker([])
    a.afflicted(sentinel.affliction)
    assert a.afflicted_this_round == set([sentinel.affliction])

#XXX: reading data files
