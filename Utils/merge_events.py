from __future__ import print_function, division

"""
Merge different events

left/right initiation -> initiation (TriggerDef.OS)
left/right termination -> termination (TriggerDef.TE)

See triggerdef_gait.py for event definition

Kyuhwa Lee, 2015
"""

EEG_IN= 'D:/work/ecog-gait/data/04OVGf/all/trial3_04OVGf_12-raw-withevents.fif'

# LTE, RTE, others
EVENTS= {'OTHERS':['LO', 'RO', 'LT', 'RT', 'LOS', 'ROS']}
EEG_OUT= 'D:/work/ecog-gait/data/04OVGf/trial3_04OVGf_12-raw-lte-rte-others.fif'


import pycnbi_config
import math, mne, csv
import numpy as np
import q_common as qc
from triggerdef_gait import TriggerDef

tdef= TriggerDef()
raw, eve= pu.load_raw( EEG_IN )

print('\nEvents before merging')
for key in np.unique(eve[:,2]):
	print('%s: %d'% (tdef.by_value[key], len( np.where( eve[:,2] == key )[0] )) )

for key in EVENTS:
	ev_src= EVENTS[key]
	ev_out= tdef.by_key[key]
	x= []
	for e in ev_src:
		x.append( np.where( eve[:,2] == tdef.by_key[e] )[0] )
	eve[np.concatenate(x), 2]= ev_out


# sanity check
dups= np.where( 0 == np.diff( eve[:,0] ) )[0]
assert len( dups ) == 0
assert max( eve[:,2] ) <= max( tdef.by_value.keys() )

# reset trigger channel
raw._data[0] *= 0
raw.add_events( eve, 'TRIGGER' )
raw.save(EEG_OUT)

print('\nResulting events')
for key in np.unique(eve[:,2]):
	print('%s: %d'% (tdef.by_value[key], len( np.where( eve[:,2] == key )[0] )) )