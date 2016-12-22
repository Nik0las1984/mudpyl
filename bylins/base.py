#coding: utf-8

from mudpyl.aliases import non_binding_alias, binding_alias
from mudpyl.triggers import non_binding_trigger, binding_trigger, RegexTrigger
from mudpyl.gui.keychords import from_string
from mudpyl.library.html import HTMLLoggingModule
from mudpyl.matchers import BindingPlaceholder, NonbindingPlaceholder, \
                            make_decorator, ProtoMatcher

import importlib
import re

RE_VAR = re.compile(ur'\$([\w\s]+)\$', re.UNICODE)

def fill_vars(s, realm):
    m = RE_VAR.match(s)
    while m:
        for g in m.groups():
            s = s.replace('$%s$' % g, realm.get_var(g))
        m = RE_VAR.match(s)
    return s.replace(';', '\n')


def trace_toggle(realm):
    if realm.tracing:
        realm.tracing = False
    else:
        realm.tracing = True

class BaseTrigger(ProtoMatcher):
   
    def __init__(self, regex = None, func = None, sequence = 0, triggers = []):
        ProtoMatcher.__init__(self, regex, func, sequence)
        self.triggers = triggers
    
    def match(self, metaline):
        for t in self.triggers:
            m = re.match(t[0], metaline.line)
            #print m
            if m:
                c = t[1]
                for g in range(len(m.groups())):
                    c = c.replace('%%%s' % (g+1), m.groups()[g])
                return [c,]
        return []
    
    def func(self, match, realm):
        realm.send_to_mud = False
        c = fill_vars(match, realm)
        realm.write(c)
        return realm.send(c)


class BaseAlias(ProtoMatcher):
   
    def __init__(self, regex = None, func = None, sequence = 0, aliases = []):
        ProtoMatcher.__init__(self, regex, func, sequence)
        self.aliases = aliases
    
    def match(self, line):
        for t in self.aliases:
            m = re.match(t[0], line)
            #print m
            if m:
                c = t[1]
                for g in range(len(m.groups())):
                    c = c.replace('%%%s' % (g+1), m.groups()[g])
                return [c,]
        return []
    
    def func(self, match, realm):
        c = fill_vars(match, realm)
        realm.send_to_mud = False
        realm.write(c)
        return realm.send(c)



class BylinsModule(HTMLLoggingModule):
    logplace = './logs/%%(name)s/%Y-%m-%dT%H:%M:%S.html'
    
    def __init__(self, factory):
        HTMLLoggingModule.__init__(self, factory)
        self.manager.mvars = importlib.import_module(self.triggers_file).mvars
        self.realm = factory
        

    @property
    def triggers(self):
        return [self.login_encoding, self.login_login, self.login_password, self.login_enter, self.mud_map, self.reconnect, self.login_login1, BaseTrigger(triggers = importlib.import_module(self.triggers_file).triggers),
                self.opener,
                self.opener1,
                self.eat1,
                ]
    
    @property
    def aliases(self):
        return [self.repeat,
                self.debug,
                self.info,
                BaseAlias(aliases = importlib.import_module(self.triggers_file).aliases),
                self.print_vars,
                self.set_var,
                ]

    @binding_trigger("^\s+5\) UTF-8")
    def login_encoding(self, match, realm):
        return realm.send("5")
    
    @binding_trigger(u'^\s+Включена поддержка протокола сжатия данных, возьмите клиент с www.mud.ru/files')
    def login_login(self, match, realm):
        return realm.send(self.name)
    
    @binding_trigger(u'^\s+Для более подробной игровой информации посетите www.bylins.su/\?newbies')
    def login_login1(self, match, realm):
        return realm.send(self.name)
        
    @binding_trigger(u'Персонаж с таким именем уже существует.')
    def login_password(self, match, realm):
        return realm.send(self.password)
    
    @binding_trigger(u'^\* В связи с проблемами перевода фразы ANYKEY нажмите ENTER \*')
    def login_enter(self, match, realm):
        return realm.send('')
    
    @binding_trigger(u'^Пересоединяемся.*')
    def reconnect(self, match, realm):
        realm.parent.telnet.msdp.msdp_request('REPORT'.encode('utf-8'), 'ROOM'.encode('utf-8'))
        #realm.send_to_mud = False
    
    @binding_alias(u'^#(\d+) (.+)')
    def repeat(self, match, realm):
        """Repeats a given command a given number of times."""
        for _ in xrange(int(match.group(1))):
            realm.send(match.group(2))
        realm.send_to_mud = False
    
    @binding_trigger('^:(.*)$')
    def mud_map(self, match, realm):
        realm.alterer.insert(0, '#out1 ')
    
    @binding_alias('^#msdp (\w+) (\w+)$')
    def repeat(self, match, realm):
        realm.parent.telnet.msdp.msdp_request(match.group(1).encode('utf-8'), match.group(2).encode('utf-8'))
        realm.send_to_mud = False
    
    @binding_alias(u'^#debug')
    def debug(self, match, realm):
        trace_toggle(realm.parent)
        realm.send_to_mud = False
    
    @binding_alias(u'^#info')
    def info(self, match, realm):
        realm.trace(self.triggers)
        realm.send_to_mud = False
    
    
    
    
    @binding_alias(u'^_пер$')
    def print_vars(self, match, realm):
        realm.parent.print_vars()
        realm.send_to_mud = False
    
    @binding_alias(u'^_пер ([\w\d_]+) (.*)$')
    def set_var(self, match, realm):
        realm.parent.set_var(match.group(1), match.group(2))
        realm.send_to_mud = False
    
    
    # открывалка
    @binding_trigger(u'^Закрыто \((.*)\)\.')
    def opener(self, match, realm):
        c1 = u'отпер %s %s' % (match.group(1)[:3], realm.parent.get_var(u'направление'))
        c2 = u'открыть %s %s' % (match.group(1)[:3], realm.parent.get_var(u'направление'))
        realm.write(c1)
        realm.send(c1)
        realm.write(c2)
        realm.send(c2)
    
    @binding_trigger(u'^Закрыто\.')
    def opener1(self, match, realm):
        c1 = u'отпер дв %s' % (realm.parent.get_var(u'направление'))
        c2 = u'открыть дв %s' % (realm.parent.get_var(u'направление'))
        realm.write(c1)
        realm.send(c1)
        realm.write(c2)
        realm.send(c2)

    
    
    # еда
    @binding_trigger(u'^Вы голодны\.')
    def eat1(self, match, realm):
        if not self.realm.get_var(u'бой'):
            realm.send(u'еда')
    
    # TODO: fix
    @binding_trigger(u'^Вас мучает жажда\.')
    def eat2(self, match, realm):
        if not self.realm.get_var(u'бой'):
            realm.write(u'еда')

