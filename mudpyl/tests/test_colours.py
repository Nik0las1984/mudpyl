from mudpyl.colours import HexFGCode, HexBGCode

def test_different_HexFGCodes_hash_differently():
    assert hash(HexFGCode(3, 5, 7)) != hash(HexFGCode(59, 1, 42))

def test_same_colour_but_different_instances_hash_the_same():
    assert hash(HexFGCode(9, 8, 7)) == hash(HexFGCode(9, 8, 7))

def test_HexBGCode_and_HexFGCode_with_equal_colours_hash_different():
    assert hash(HexFGCode(2, 2, 2)) != hash(HexBGCode(2, 2, 2))
