from mudpyl.library.rifttracker import RiftTracker
from mudpyl.metaline import Metaline, RunLengthList
from mudpyl.realms import RootRealm, AliasMatchingRealm, TriggerMatchingRealm
import re

class Test_RiftTracker:

    def setUp(self):
        self.r = RootRealm(None)
        self.rt = RiftTracker(self.r)

    def test_ignores_rift_information_if_not_asked_for(self):
        m = re.match('\[(5)\] (ginseng root)', '[5] ginseng root')
        tmr = TriggerMatchingRealm(None, self.r, self.r)
        self.rt.herb_trigger.func(m, tmr)
        assert self.rt.herbs_seen['ginseng'] == 0

    def test_picks_up_rift_information_if_asked_for(self):
        self.rt.looking_for_herbs = True
        m = re.match('\[(5)\] (ginseng root)', '[5] ginseng root')
        tmr = TriggerMatchingRealm(None, self.r, self.r)
        self.rt.herb_trigger.func(m, tmr)
        assert self.rt.herbs_seen['ginseng'] == 5

    def test_herb_trigger_matches(self):
        ml = Metaline('[ 100] goldenseal root', None, None)
        assert list(self.rt.herb_trigger.match(ml))

    def test_herb_trigger_matches_multiple_times(self):
        ml = Metaline('[ 100] goldenseal root  [   2] ginseng root',
                      None, None)
        assert len(list(self.rt.herb_trigger.match(ml))) == 2

    def test_turns_on_looking_with_alias(self):
        amr = AliasMatchingRealm(None, None, self.r, self.r)
        self.rt.info_rift_alias.func(None, amr)
        assert self.rt.looking_for_herbs == True

    def test_still_sends_ir_to_MUD(self):
        amr = AliasMatchingRealm(None, None, self.r, self.r)
        self.rt.info_rift_alias.func(None, amr)
        assert amr.send_to_mud

    def test_alias_matches_on_ir(self):
        assert list(self.rt.info_rift_alias.match('ir'))

    def test_prompt_trigger_matches_on_prompt(self):
        ml = Metaline('42h, 23m, 5e, 17w cexkdb@-', None, None)      
        assert list(self.rt.prompt_trigger.match(ml))

    def test_count_vials_counts_non_doubled_herbs_right(self):
        self.rt.herbs_seen['ginseng'] = 50
        self.rt.herbs_seen['myrrh'] = 260
        self.rt.herbs_seen['goldenseal'] = 48
        self.rt.herbs_seen['valerian'] = 51
        self.rt.count_vials()
        print self.rt.max_vials['health']
        assert self.rt.max_vials['health'] == 12  # 48 // 4

    def test_count_vials_counts_doubled_herbs_right(self):
        self.rt.herbs_seen['echinacea'] = 12
        self.rt.herbs_seen['sac'] = 10
        self.rt.herbs_seen['ash'] = 12
        self.rt.count_vials()
        assert self.rt.max_vials['immunity'] == 1

    #XXX: not tested - sending the notes, making the bottleneck things.
