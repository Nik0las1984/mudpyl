from mudpyl.modules import BaseModule
from mudpyl.aliases import binding_alias

#TODO: puring from bites, timely reminders to purge, etc

venom_shorts = {'sum': 'sumac',
                'xen': 'xentio',
                'kal': 'kalmia',
                'cur': 'curare',
                'dar': 'darkshade',
                'ole': 'oleander',
                'eur': 'eurypteria',
                'dgi': 'digitalis',
                'ept': 'epteth',
                'pre': 'prefarar',
                'mon': 'monkshood',
                'eup': 'euphorbia',
                'col': 'colocasia',
                'ocu': 'oculus',
                'cam': 'camus',
                'ver': 'vernalius',
                'eps': 'epseth',
                'lar': 'larkspur',
                'sli': 'slike',
                'voy': 'voyria',
                'del': 'delphinium',
                'not': 'notechis',
                'var': 'vardrax',
                'lok': 'loki',
                'aco': 'aconite',
                'sel': 'selarnia',
                'gec': 'gecko',
                'scy': 'scytherus',
                'nec': 'nechamandra'}

class Secreter(BaseModule):
    
    def __init__(self, manager):
        self.venom = None
        BaseModule.__init__(self, manager)

    def secrete(self, venom, realm):
        if venom != self.venom:
            if self.venom is not None:
                realm.send("purge")
            self.venom = venom
            realm.send("secrete " + venom)

    @binding_alias("^(%s)$" % '|'.join(venom_shorts))
    def secrete_alias(self, match, realm):
        venom = venom_shorts[match.group(1)]
        self.secrete(venom, realm)

    @binding_alias("^pu$")
    def purge_alias(self, match, realm):
        self.venom = None
        realm.send("purge")

    @property
    def aliases(self):
        return [self.secrete_alias, self.purge_alias]
