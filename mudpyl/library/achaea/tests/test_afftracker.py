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
    realm.root.hit_tracker.attack_type = sentinel.attack_type
    trig.func(sentinel.match, realm)
    assert a.afflicted.call_args_list == [(('bar',), {})]

def test_trigger_doesnt_call_afflicted_if_attack_type_is_wrong():
    pats = [('foo', 'bar', [sentinel.attack_type])]
    a = AffTracker(pats)
    trig = a.triggers[0]
    a.afflicted = Mock()
    trig.func(sentinel.match, Mock())
    assert not a.afflicted.called

def test_afflicted_adds_affliction_to_set_for_round_if_not_in_afflictions():
    a = AffTracker([])
    a.afflicted(sentinel.affliction)
    assert a.afflicted_this_round == set([sentinel.affliction])

def test_afflicted_adds_affliction_to_afflictions():
    a = AffTracker([])
    a.afflicted(sentinel.affliction)
    assert sentinel.affliction in a.afflictions

def test_afflicted_doesnt_add_to_this_round_set_if_already_in_afflictions():
    a = AffTracker([])
    a.afflictions.add(sentinel.affliction)
    a.afflicted(sentinel.affliction)
    assert sentinel.affliction not in a.afflicted_this_round

def test_adds_itself_to_the_realm_root_when_loaded():
    a = AffTracker([])
    realm = Mock()
    a(realm)
    assert realm.aff_tracker is a

#XXX: reading data files
