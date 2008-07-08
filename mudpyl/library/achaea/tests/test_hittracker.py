from mudpyl.library.achaea.hittracker import HitTracker
from mock import Mock

def test_creates_triggers_from_given_attacks():
    attacks = [('foo', 'bar', []),
               ('baz', 'qux', [])]
    ht = HitTracker(attacks)
    assert set(trig.regex.pattern for trig in ht.triggers) == set(['foo',
                                                                   'baz'])

def test_calls_hit_when_afflictions_contains_appropriate_afflictions():
    realm = Mock()
    realm.root.aff_tracker.afflictions = set(['spam'])
    attacks = [('foo', 'bar', ['spam'])]
    ht = HitTracker(attacks)
    ht.hit = Mock()
    trig = ht.triggers[0]
    trig.func(Mock(), realm)
    assert ht.hit.call_args_list == [(('bar',), {})]

def test_sets_illusioned_to_false_when_afflicted_properly():
    realm = Mock()
    realm.root.aff_tracker.afflictions = set(['spam', 'eggs'])
    attacks = [('foo', 'bar', ['spam'])]
    ht = HitTracker(attacks)
    trig = ht.triggers[0]
    trig.func(Mock(), realm)
    assert not ht.illusioned
    
def test_still_calls_hit_when_not_afflicted_correctly():
    realm = Mock()
    realm.root.aff_tracker.afflictions = set(['eggs'])
    attacks = [('foo', 'bar', ['spam'])]
    ht = HitTracker(attacks)
    ht.hit = Mock()
    trig = ht.triggers[0]
    trig.func(Mock(), realm)
    assert ht.hit.called

def test_sets_illusioned_true_if_not_afflicted_properly():
    realm = Mock()
    realm.root.aff_tracker.afflictions = set()
    attacks = [('foo', 'bar', ['spam'])]
    ht = HitTracker(attacks)
    trig = ht.triggers[0]
    trig.func(Mock(), realm)
    assert ht.illusioned
    
def test_hit_sets_attacks_type():
    ht = HitTracker([])
    ht.hit('foo')
    assert ht.attack_type == 'foo'

def test_adds_itself_as_hit_tracker_to_the_root_realm():
    ht = HitTracker([])
    realm = Mock()
    ht(realm)
    assert realm.hit_tracker is ht

def test_hit_appends_to_attacks_this_round():
    ht = HitTracker([])
    ht.hit('foo')
    assert ['foo'] ==  ht.attacks_this_round

def test_attack_type_is_None_with_no_attacks():
    ht = HitTracker([])
    assert ht.attack_type is None
