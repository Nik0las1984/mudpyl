from mudpyl.mudconnect import main
from mudpyl import mudconnect

class MockReactor:

    def __init__(self):
        self.calls = []

    def registerWxApp(self, app):
        self.calls.append(('registerWxApp', app))

    def connectTCP(self, host, port, fact):
        self.calls.append(('connectTCP', host, port, fact))

    def run(self):
        self.calls.append(('run',))

class Test_main:

    def setUp(self):
        self.reactor = MockReactor()
        mudconnect.reactor = self.reactor

    def tearDown(self):
        del mudconnect.reactor

    #XXX: actually write some tests? load_file will need to be mocked up.
