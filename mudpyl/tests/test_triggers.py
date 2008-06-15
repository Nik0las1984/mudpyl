from mudpyl.triggers import LineAlterer
from mudpyl.metaline import Metaline, RunLengthList, simpleml
from mudpyl.colours import HexFGCode, CYAN, WHITE, RED, fg_code
from mock import sentinel

class Test_LineAlterer:

    def setUp(self):
        self.la = LineAlterer()
        self.ml = Metaline('spam eggs ham', 
                           RunLengthList([(0, 'A'), 
                                          (2, 'B'),
                                          (4, 'C')]),
                           RunLengthList([(0, 'D'),
                                          (2, 'E'),
                                          (4, 'F')]))
                           

    def test_delete_deletes_text(self):
        self.la.delete(1, 2)
        res = self.la.apply(self.ml)
        assert res.line == 'sam eggs ham'

    def test_delete_adjusts_fore_indices(self):
        self.la.delete(1, 2)
        res = self.la.apply(self.ml)
        assert res.fores.as_populated_list() == ['A', 'B', 'B', 'C']

    def test_delete_right_on_fore_colour_start_doesnt_remove_colour(self):
        self.la.delete(1, 3)
        res = self.la.apply(self.ml)
        assert res.fores.as_populated_list() == ['A', 'B', 'C']

    def test_delete_over_whole_fore_colour_range_does_remove_colour(self):
        self.la.delete(2, 4)
        res = self.la.apply(self.ml)
        assert res.fores.as_populated_list() == ['A', 'A', 'C']

    def test_delete_adjusts_back_indices(self):
        self.la.delete(1, 2)
        res = self.la.apply(self.ml)
        assert res.backs.as_populated_list() == ['D', 'E', 'E', 'F']

    def test_delete_right_on_back_colour_start_doesnt_remove_colour(self):
        self.la.delete(1, 3)
        res = self.la.apply(self.ml)
        assert res.backs.as_populated_list() == ['D', 'E', 'F']

    def test_delete_over_whole_back_colour_range_does_remove_colour(self):
        self.la.delete(2, 4)
        res = self.la.apply(self.ml)
        assert res.backs.as_populated_list() == ['D', 'D', 'F']

    def test_delete_happens_after_delete_ahead_in_string(self):
        self.la.delete(1, 2)
        self.la.delete(3, 4)
        res = self.la.apply(self.ml)
        assert res.line == 'sa eggs ham', res.line

    def test_delete_happens_after_insertion_ahead_in_string(self):
        self.la.insert(1, 'foo')
        self.la.delete(3, 4)
        res = self.la.apply(self.ml)
        assert res.line == 'sfoopa eggs ham', res.line

    def test_delete_engulfs_inserted_text_inside_range(self):
        self.la.insert(1, 'foo')
        self.la.delete(0, 2)
        res = self.la.apply(self.ml)
        assert res.line == 'am eggs ham', res.line

    def test_delete_doesnt_engulf_inserted_text_outside_range(self):
        self.la.insert(1, 'foo')
        self.la.delete(2, 3)
        res = self.la.apply(self.ml)
        assert res.line == 'sfoopm eggs ham', res.line

    def test_delete_around_previous_delete(self):
        self.la.delete(3, 4)
        self.la.delete(2, 5)
        res = self.la.apply(self.ml)
        assert res.line == 'speggs ham'

    def test_delete_engulfed_by_previous_delete(self):
        self.la.delete(2, 5)
        self.la.delete(3, 4)
        res = self.la.apply(self.ml)
        assert res.line == 'speggs ham'

    def test_insert_after_insert_has_its_index_adjusted(self):
        self.la.insert(2, 'foo')
        self.la.insert(3, 'bar')
        res = self.la.apply(self.ml)
        assert res.line == 'spfooabarm eggs ham'

    def test_insert_then_change_fore_adjusts_expectedly(self):
        self.la.insert(0, "foo")
        self.la.change_fore(1, 4, sentinel.fore)
        res = self.la.apply(self.ml)
        assert res.fores.items() == [(0, 'A'),
                                    (4, sentinel.fore),
                                    (7, 'C')], res.fores.items()

    #XXX: test chaining. Each method must be tested before an insert and a
    #     delete.
    #     Plus, deleting then inserting needs some special cases.

    #that is, do that after the rest of this class' tests are written.
    #Briefly:
    #  - test .apply() copies and applies each change in order.
    #  - test .insert() does what it says on the tin
    #  - test .change_fore() and .change_back()

    def test_change_fore(self):
        self.la.change_fore(0, 9, 'foo')
        res = self.la.apply(self.ml)
        assert res.fores.items() == [(0, 'foo'),
                                                    (9, 'C')], \
               res.fores.items()

    def test_change_fore_with_trailing_colours(self):
        #don't know why, but this test exposed what looked like a quasi-random
        #failure...
        ml = Metaline('foobars eggs.', 
                      RunLengthList([(0, fg_code(CYAN, False)),
                                     (13, fg_code(WHITE, False))]),
                      RunLengthList([(0, None)]))
        self.la.change_fore(0, 7, fg_code(RED, True))
        res = self.la.apply(ml)
        expected = [(0, fg_code(RED, True)),
                    (7, fg_code(CYAN, False)),
                    (13, fg_code(WHITE, False))]
        assert res.fores.items() == expected, \
               res.fores.items()

    def test_change_fore_with_no_right_bound(self):
        ml = Metaline("foobarbaz", RunLengthList([(0, fg_code(WHITE, False))]),
                      RunLengthList([(0, None)]))
        self.la.change_fore(3, None, fg_code(RED, False))
        res = self.la.apply(ml)
        assert res.fores.items() == [(0, fg_code(WHITE, False)),
                                    (3, fg_code(RED, False))]

    def test_insert_metaline(self):
        ml_one = simpleml('foo', 'foo', 'foo')
        self.la.insert_metaline(1, simpleml('bar', 'bar', 'bar'))
        res = self.la.apply(ml_one)
        assert res == Metaline('fbaroo',
                               RunLengthList([(0, 'foo'), (1, 'bar'),
                                              (4, 'foo')]),
                               RunLengthList([(0, 'foo'), (1, 'bar'),
                                              (4, 'foo')]))

    def test_insert_metaline_then_insert_bumps(self):
        ml_ins = simpleml('foo', 'foo', 'foo')
        self.la.insert_metaline(1, ml_ins)
        self.la.insert(2, 'baz')
        res = self.la.apply(simpleml('bar', 'bar', 'bar'))
        assert res.line == 'bfooabazr', res.line

    def test_insert_then_insert_metaline_bumps(self):
        self.la.insert(1, 'foo')
        self.la.insert_metaline(2, simpleml('bar', 'bar', 'bar'))
        res = self.la.apply(simpleml('baz', None, None))
        assert res.line == "bfooabarz", res.line

from mudpyl.triggers import non_binding_trigger

def test_non_binding_trigger():
    ro = object()
    so = object()
    fo = object()
    f = non_binding_trigger(ro, sequence = so)(fo)
    r = f()
    assert r.regex is ro
    assert r.sequence is so
    assert r.func is fo

def test_non_binding_trigger_makes_a_new_instance_each_time():
    f = non_binding_trigger(None)(None)
    assert f() is not f()

def test_trigger_match_returns_list():
    f = non_binding_trigger('foo')(None)
    res = list(f().match(Metaline('foo', None, None)))
    assert res

def test_trigger_non_match_doesnt_return_list():
    f = non_binding_trigger('bar')(None)
    res = list(f().match(Metaline('foo', None, None)))
    assert not res

def test_trigger_matches_multiple_times():
    f = non_binding_trigger('foo')(None)
    res = list(f().match(Metaline('foofoo', None, None)))
    assert len(res) == 2

def test_returns_nothing_if_regex_is_None():
    f = non_binding_trigger(None)(None)
    res = list(f().match(Metaline('foobar', None, None)))
    assert not res

#XXX: not tested - binding_triggers
