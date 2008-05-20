from mudpyl.metaline import Metaline

def test_Metaline_change_fg_sets_colour():
    m = Metaline('foo', RunLengthList([(0, None)]), None)
    m.change_fore(0, 5, 'foo')
    assert m.fores.values == [(0, 'foo'), (5, None)]

def test_Metaline_change_bg_sets_colour():
    m = Metaline("foo", None, RunLengthList([(0, None)]))
    m.change_back(2, 3, 'bar')
    assert m.backs.values == [(0, None), (2, 'bar'), (3, None)], \
                                                  m.backs.values

def test_Metaline_insert_inserts_text():
    m = Metaline('foobaz', RunLengthList([(0, None)]), 
                           RunLengthList([(0, None)]))
    m.insert(3, 'bar')
    assert m.line == 'foobarbaz', m.line

def test_Metaline_insert_at_0_doesnt_leave_start_uncoloured():
    ml = simpleml('foo', sentinel.fore, sentinel.back)
    ml.insert(0, 'bar')
    assert ml.fores.values == [(0, sentinel.fore)]
    assert ml.backs.values == [(0, sentinel.back)]

def test_Metaline_insert_fg_bg_on_too_long():
    fores, backs = RunLengthList([(0, 'foo')]), RunLengthList([(0, 'bar')])
    m = Metaline('foo', fores.copy(), backs.copy())
    m.insert(2, 'bar')
    assert m.fores == fores, m.backs == backs

def test_Metaline_insert_adjustsindices_beyond_span():
    fores = RunLengthList([(0, 'F'), (5, 'B')])
    backs = RunLengthList([(0, 'F'), (5, 'B')])
    m = Metaline('foobar', fores, backs)
    m.insert(3, 'baz')
    assert m.fores.as_populated_list() == list('FFFFFFFFB'), \
                                             m.fores.as_populated_list()
    assert m.backs.as_populated_list() == list('FFFFFFFFB')

def test_Metaline_delete():
    fores = RunLengthList([(0, 'F'), (4, 'B'), (7, 'Z')])
    backs = RunLengthList([(0, 'F'), (4, 'B'), (7, 'Z')])
    m = Metaline('foobarbaz', fores, backs)
    m.delete(3, 6)
    assert m.line == 'foobaz', m.line
    assert m.fores.as_populated_list() == list('FFFBZ') == \
           m.backs.as_populated_list(), m.backs.as_populated_list()

class Test_change_fore:
    
    def test_changes_fg_normally(self):
        metaline = Metaline('foobar', RunLengthList([(0, 'FOO')]), 
                            None)
        metaline.change_fore(1, 3, 'BAR')
        assert metaline.fores.as_populated_list() == ['FOO', 'BAR', 'BAR', 
                                                      'FOO'], \
               metaline.fores.as_populated_list()

    def test_preserves_engulfed_colour_starts(self):
        metaline = Metaline('foobar', RunLengthList([(0, 'FOO'),
                                                     (2, 'BAR')]),
                            None)
        metaline.change_fore(1, 3, 'BAZ')
        assert metaline.fores.as_populated_list() == ['FOO', 'BAZ', 'BAZ',
                                                      'BAR']

    def test_changes_fg_right_at_end(self):
        metaline = Metaline('foobar', RunLengthList([(0, 'FOO')]), 
                            None)
        metaline.change_fore(1, 6, 'BAR')
        assert metaline.fores.as_populated_list() == ['FOO', 'BAR', 'BAR', 
                                                      'BAR', 'BAR', 'BAR',
                                                      'FOO'], \
               metaline.fores.as_populated_list()

def test_Metaline_line_end_is_defaultly_hard():
    m = Metaline("foo", None, None)
    assert m.line_end == 'hard'

def test_equality_simple():
    a = Metaline('foo', RunLengthList([(0, 'foo')]),
                 RunLengthList([(0, 'bar')]))
    b = Metaline('foo', RunLengthList([(0, 'foo')]), 
                 RunLengthList([(0, 'bar')]))
    assert a == b, (a, b)

#XXX: test copying and repr <-> eval

def test_change_fore_with_trailing_colours():
    ml = Metaline('foo bar', RunLengthList([(0, 'foo'), (7, 'bar')]),
                  RunLengthList([(0, 'bar')]))
    ml.change_fore(0, 3, 'baz')
    assert ml.fores.values == [(0, 'baz'), (3, 'foo'), (7, 'bar')]

def test_insert_metaline():
    ml_one = Metaline('foo baz', RunLengthList([(0, 'foo'), (4, 'baz')]),
                      RunLengthList([(0, 'foo'), (4, 'baz')]))
    ml_two = simpleml('bar ', 'bar', 'bar')
    ml_one.insert_metaline(4, ml_two)
    assert ml_one == Metaline("foo bar baz",
                              RunLengthList([(0, 'foo'), (4, 'bar'),
                                             (8, 'baz')]),
                              RunLengthList([(0, 'foo'), (4, 'bar'),
                                             (8, 'baz')]))

def test_insert_metaline_tidies_when_inserted_at_end():
    res = simpleml("foo", sentinel.foofore, sentinel.fooback) + \
          simpleml("bar", sentinel.barfore, sentinel.barback)
    assert res.fores.values == [(0, sentinel.foofore),
                                (3, sentinel.barfore)]
    assert res.backs.values == [(0, sentinel.fooback),
                                (3, sentinel.barback)]
    

from mudpyl.metaline import RunLengthList

def test_RunLengthList_as_populated_list():
    c = RunLengthList([(0, 1), (3, 2), (6, 3)])
    assert c.as_populated_list() == [1, 1, 1, 2, 2, 2, 3]

def test_RunLengthList_as_populated_list_with_redundancy_at_end():
    c = RunLengthList([(0, 1), (3, 2), (6, 3), (6, 4)])
    assert c.as_populated_list() == [1, 1, 1, 2, 2, 2, 4]

def test_RunLengthList_as_populated_list_ending_cycling():
    c = RunLengthList([(0, 'foo'), (2, 'bar')])
    assert c.as_populated_list()[42] == 'bar'

def test_RunLengthList_add_colour():
    c = RunLengthList([(0, 1), (3, 2)])
    c.add_colour(1, 3)
    assert c.values == [(0, 1), (1, 3), (3, 2)]

def test_RunLengthList_add_colour_already_got_index():
    c = RunLengthList([(0, 'foo'), (3, 'bar')])
    c.add_colour(3, 'baz')
    assert c.values == [(0, 'foo'), (3, 'baz')]

def test_RunLengthList_index_adjust():
    c = RunLengthList([(0, 1), (3, 2), (6, 3)])
    c.index_adjust(2, 2)
    assert c.values == [(0, 1), (5, 2), (8, 3)], c.values

def test_RunLengthList_index_adjust_index_collision():
    c = RunLengthList([(0, 1), (3, 2)])
    c.index_adjust(3, 2)
    assert c.values == [(0, 1), (5, 2)], c.values

def test_RunLengthList_index_adjust_negative_adjustment():
    c = RunLengthList([(0, 'f'), (2, 'o'), (3, 'b')])
    c.index_adjust(1, -1)
    assert c.values == [(0, 'f'), (1, 'o'), (2, 'b')]

def test_RunlengthList_index_adjust_negative_adjustment_normalises():
    c = RunLengthList([(0, 'f'), (2, 'o'), (3, 'b')])
    c.index_adjust(1, -2)
    assert c.values == [(0, 'f'), (1, 'b')]

def test_RunLengthList_blank_between():
    c = RunLengthList([(0, 'FOO'), (2, 'BAR'), (3, 'BAZ'), (4, 'QUX')])
    c.blank_between(2, 3)
    assert c.values == [(0, 'FOO'), (3, 'BAZ'), (4, 'QUX')], c.values

def test_RunLengthList_doesnt_choke_on_generator():
    gen = iter([(0, 'foo'), (3, 'bar')])
    c = RunLengthList(gen)
    assert c == RunLengthList([(0, 'foo'), (3, 'bar')])

def test_RunLengthList_simple_equality():
    a = RunLengthList([(0, 'foo')])
    b = RunLengthList([(0, 'foo')])
    assert a == b

def test_RunLengthList_normalises_arguments():
    a = RunLengthList([(0, 'foo'), (3, 'foo')])
    b = RunLengthList([(0, 'foo')])
    assert a == b

def test_RunLengthList_add_colour_normalises_afterwards():
    r = RunLengthList([(0, 'foo')])
    r.add_colour(2, 'foo')
    r.add_colour(1, 'bar')
    assert r.as_populated_list() == ['foo', 'bar']

def test_copy_returns_different_lists():
    r = RunLengthList([(0, 'foo')])
    assert r.values[:] is not r.copy().values

def test_RunLengthList_insertion():
    r1 = RunLengthList([(0, 'foo'), (2, 'qux')])
    r2 = RunLengthList([(0, 'bar'), (2, 'baz')])
    r1.insert_list_at(1, 3, r2)
    assert r1.values == [(0, 'foo'), (1, 'bar'), (3, 'baz'), (4, 'foo'),
                         (5, 'qux')], r1.values

def test_RunLengthList_insertion_normalisation():
    r1 = RunLengthList([(0, 'foo'), (1, 'bar')])
    r2 = RunLengthList([(0, 'foo'), (1, 'bar')])
    r1.insert_list_at(1, 2, r2)
    assert r1.values == [(0, 'foo'), (2, 'bar')], r1.values

def test_inserted_list_gets_chopped_if_not_enough_length():
    r1 = RunLengthList([(0, 'foo'), (1, 'bar')])
    r2 = RunLengthList([(0, 'baz'), (2, 'qux')])
    r1.insert_list_at(1, 1, r2)
    assert r1.values == [(0, 'foo'), (1, 'baz'), (2, 'bar')]
    
#XXX: other equality cases

def test_RunLengthList_repr_evauluates_equal():
    r = RunLengthList([(0, 'foo')])
    assert eval(repr(r)) == r

def test_RunLengthList_copy_copies_non_empty():
    r = RunLengthList([(0, 'foo')])
    assert r == r.copy()
    assert not r.values is r.copy().values

def test_RunLengthList_throws_ValueError_when_given_empty_list():
    try:
        r = RunLengthList([])
    except ValueError:
        pass
    else:
        assert False, r

def test_RunLengthList_throws_ValueError_when_given_gappy_list():
    try:
        r = RunLengthList([(2, 'foo')])
    except ValueError:
        pass
    else:
        assert False, r

def test_as_populated_list_throws_error_if_clearing_start():
    r = RunLengthList([(0, 'foo'), (3, 'bar')])
    try:
        r.blank_between(0, 2)
    except ValueError:
        pass
    else:
        assert False

def test_add_colour_works_on_top_of_existing_colour_definition():
    rl = RunLengthList([(0, 'foo'), (2, +20)])
    rl.add_colour(2, -20) #deliberately try and get it to the left
    assert rl.values == [(0, 'foo'), (2, -20)]

def test_blank_between_second_argument_None_blanks_to_end():
    rl = RunLengthList([(0, 'foo'), (2, 'bar'), (4, 'baz')])
    rl.blank_between(1, None)
    assert rl.values == [(0, 'foo')]

def test_change_between_changes_to_end_if_second_argument_None():
    rl = RunLengthList([(0, 'foo'), (2, 'bar'), (4, 'baz')])
    rl.change_between(1, None, 'qux')
    assert rl.values == [(0, 'foo'), (1, 'qux')]

from mudpyl.metaline import simpleml
from mock import sentinel

def test_simpleml_creates_equivalent_metaline():
    ml = simpleml("foo", sentinel.fore, sentinel.back)
    assert ml == Metaline("foo", RunLengthList([(0, sentinel.fore)]),
                          RunLengthList([(0, sentinel.back)]))

def test_Metaline_addition_normal():
    res = simpleml("foo", sentinel.fore, sentinel.back) + \
          simpleml("bar", sentinel.fore2, sentinel.back2)
    assert res.line == "foobar", res.line
    assert res.fores.values == [(0, sentinel.fore),
                                (3, sentinel.fore2)]
    assert res.backs.values == [(0, sentinel.back),
                                (3, sentinel.back2)]

def test_Metaline_addition_first_has_trailling_colours():
    ml = simpleml("foo", sentinel.foofore, sentinel.fooback)
    ml.change_fore(0, 4, sentinel.foofore2)
    res = ml + simpleml("bar", sentinel.barfore, sentinel.barback)
    assert res.fores.values == [(0, sentinel.foofore2),
                                (3, sentinel.barfore)], res.fores.values
