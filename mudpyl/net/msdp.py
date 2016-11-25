"""
http://tintin.sourceforge.net/msdp/
"""


MSDP             = chr(69)

MSDP_VAR         = chr(1)
MSDP_VAL         = chr(2)

MSDP_TABLE_OPEN  = chr(3)
MSDP_TABLE_CLOSE = chr(4)

MSDP_ARRAY_OPEN  = chr(5)
MSDP_ARRAY_CLOSE = chr(6)

class MSDPParser():
    def __init__(self, protocol):
        self.protocol = protocol
        self.listeners = []
    
    def msdp_request(self, var, val):
        data  = MSDP_VAR + str(var) + MSDP_VAL + str(val)
        self.protocol.factory.realm.info('MSDP REQUEST: %s' % data)
        self.protocol.requestNegotiation(MSDP, data)
    
    def add_listener(self, l):
        self.listeners.append(l)
    
    def negotiation(self, data):
        #self.protocol.factory.realm.info('%s' % data)
        v = self.parse_var(data)
        for i in self.listeners:
            i.msdp_var(v)
    
    def parse_var(self, data):
        if data[0] == MSDP_VAR:
            vi = data.index(MSDP_VAL)
            name = "".join(data[1:vi])
            var = {name: self.parse_val(data[vi+1:]), }
            self.protocol.factory.realm.info('%s' % var)
            return var
        else:
            self.protocol.factory.realm.info('Invalid MSDP var: %s ' % data)
            
    def parse_val(self, data):
        data = ''.join(data)
        #self.protocol.factory.realm.info('Parse data: ' + data)
        if data[0] == MSDP_ARRAY_OPEN:
            data = data[2:-1]
            vals = []
            for i in data.split(MSDP_VAL):
                vals.append(self.parse_val(i))
            return vals
        elif data[0] == MSDP_TABLE_OPEN:
            data = data[1:-1]
            d = {}
            cnt = 0
            while len(data) > 0:
                if data[0] == MSDP_VAR:
                    ival = data.find(MSDP_VAL)
                    name = data[1:ival]
                    data = data[ival:]
                    if data[1] == MSDP_TABLE_OPEN:
                        val = self.parse_val(data[1:data.find(MSDP_TABLE_CLOSE)+1])
                        d[name] = val
                        data = data[data.find(MSDP_TABLE_CLOSE)+1:]
                    else:
                        ivar = data.find(MSDP_VAR)
                        val = data[1:]
                        if ivar > 0:
                            val = data[1:ivar]
                            data = data[ivar:]
                        else:
                            data = ''
                        d[name] = val
            return d
        else:
            return data
