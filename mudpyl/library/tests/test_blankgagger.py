from mudpyl.library.blankgagger import BlankLineGagger

def test_setting_prompt_regex():
    blg = BlankLineGagger('foo42')
    assert blg.prompt_received.regex.pattern == 'foo42'
