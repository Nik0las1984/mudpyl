from mudpyl.library.imperian.autosipper import Autosipper
from mudpyl.metaline import Metaline
import re

class DummyRealm:
    class root:
        tracing = False

def test_health_update_matching():
    a = Autosipper(10, 10)
    ml = Metaline(' Health   : 5/5     Reserves : 5/5', None, None)
    assert a.health_update.match(ml)

def test_health_update_max_health_setting():
    m = re.match('(\d+)', '42')
    a = Autosipper(10, 10)
    a.health_update(m, DummyRealm())
    assert a.max_health == 42
