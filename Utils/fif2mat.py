from __future__ import print_function, division

"""
Export fif data into mat files.

"""

# path to fif file(s)
DATADIR= 'D:/rex/Down/fif'

import pycnbi_config
import pycnbi_utils as pu
import scipy.io, mne
import numpy as np
import q_common as qc

if __name__=='__main__':
	for rawfile in qc.get_file_list(DATADIR, fullpath=True):
		if rawfile[-4:] != '.fif': continue
		raw, events= pu.load_raw(rawfile)
		sfreq= raw.info['sfreq']
		data= dict(signals=raw._data, events=events, sfreq=sfreq)
		matfile= '.'.join( rawfile.split('.')[:-1] ) + '.mat'
		scipy.io.savemat(matfile, data)
		print('\nExported to %s'% matfile)
	print('\nDone.')