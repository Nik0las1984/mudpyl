from mudpyl.gui.keychords import from_string, InvalidSpecialKeyError, \
                                 CantParseThatError, InvalidModifiersError, \
                                 KeyChord

def single_keychord_key_equal(key, chord):
    assert chord.key == key

def test_special_keys_go_through_alright():
    allowed_specials = ["backspace", 
                        "tab", 
                        "return",
                        "enter",
                        "dash",
                        "pause",
                        "escape",
                        "page up",
                        "page down",
                        "end",
                        "home",
                        "left",
                        "up",
                        "right",
                        "down", 
                        "insert",
                        "delete"] + \
                        ['f%d' % n for n in range(1, 13)] + \
                        ['numpad %s' % n for n in range(0, 10) +
                                                  ['add', 'divide', 
                                                   'multiply', 'subtract']]

    for special in allowed_specials:
        yield single_keychord_key_equal, special, from_string('<%s>' % special)

def test_invalid_special_keys_raises_errors():
    invalid_specials = ['foo', 'bar', 'baz']

    for special in invalid_specials:
        try:
            v = from_string('<%s>')
        except InvalidSpecialKeyError:
            pass
        else:
            assert False, v

def test_case_insensitivity_in_special_keys():
    vals = ['escape', 'EsCaPe', 'esCApe', 'ESCAPE']

    for val in vals:
        yield single_keychord_key_equal, 'escape', from_string('<%s>' % val)

def test_case_insensitivity_on_normal_keys():
    assert KeyChord('h', False, False) == KeyChord('H', False, False)
    assert hash(KeyChord('h', False, False)) == hash(KeyChord('H', False,
                                                              False))

def test_blows_up_on_unclosed_special_key():
    try:
        res = from_string('<escape')
    except CantParseThatError:
        pass
    else:
        assert False, res

def test_blows_up_on_unexpected_sequence_of_characters():
    try:
        res = from_string('foo')
    except CantParseThatError:
        pass
    else:
        assert False, res

def test_normal_key_setting():
    assert from_string('f').key == 'f'

def test_normal_key_case_insensitive():
    assert from_string('F').key == 'f'

def test_modifiers_are_case_sensitive():
    try:
        res = from_string('m-f')
    except InvalidModifiersError:
        pass
    else:
        assert False

def test_rejects_unknown_modifier():
    try:
        res = from_string('x-f')
    except InvalidModifiersError:
        pass
    else:
        assert False

def test_rejects_blank_key():
    try:
        res = from_string('')
    except CantParseThatError:
        pass
    else:
        assert False

def test_rejects_blank_key_with_modifier():
    try:
        res = from_string('M-')
    except CantParseThatError:
        pass
    else:
        assert False

def test_rejects_dash_on_its_own():
    try:
        res = from_string('-')
    except (InvalidModifiersError, CantParseThatError):
        pass
    else:
        assert False

def test_sets_Control_key_to_true():
    assert from_string('C-f').control

def test_control_key_flag_is_default_false():
    assert not from_string('f').control

def test_alt_key_flag_is_default_false():
    assert not from_string('f').meta

def test_alt_key_setting_to_true():
    assert from_string('M-f').meta

def test_alt_and_control_work_together():
    c = from_string('C-M-f')
    assert c.meta and c.control

def test_ordering_of_modifiers_doesnt_matter():
    c1 = from_string('C-M-q')
    c2 = from_string('M-C-q')
    assert c1 == c2

def test_equality():
    #XXX: other interesting comparison cases
    kc1 = from_string('f')
    kc2 = from_string('f')
    assert kc1 == kc2, (kc1, kc2)

def test_KeyChord_unicode_and_ascii_characters_are_the_same():
    kc1 = from_string('f')
    kc2 = from_string(u'f')
    assert kc1 == kc2

def test_inequality():
    assert from_string('m') != from_string('r')

def test_equal_chords_hash_the_same():
    assert hash(from_string('f')) == hash(from_string('f'))

def test_plays_nice_with_dict():
    d = {from_string('C-f'): 'foo',
         from_string('M-f'): 'bar',
         from_string('f'): 'baz'}
    assert from_string('C-f') in d
    assert d[from_string('M-f')] == 'bar'
