from mudpyl.colours import HexFGCode, HexBGCode

def test_different_HexFGCodes_hash_differently():
    assert hash(HexFGCode(3, 5, 7)) != hash(HexFGCode(59, 1, 42))

def test_same_colour_but_different_instances_hash_the_same():
    assert hash(HexFGCode(9, 8, 7)) == hash(HexFGCode(9, 8, 7))

def test_HexBGCode_and_HexFGCode_with_equal_colours_hash_different():
    assert hash(HexFGCode(2, 2, 2)) != hash(HexBGCode(2, 2, 2))

def test_HexBGCOde_ground_is_back():
    assert HexBGCode(0, 0, 0).ground == 'back'

def test_HexFGCode_ground_is_fore():
    assert HexFGCode(0, 0, 0).ground == 'fore'

def test_as_hex():
    c = HexFGCode(10, 26, 255)
    assert c.as_hex.lower() == "0a1aff", c.as_hex
