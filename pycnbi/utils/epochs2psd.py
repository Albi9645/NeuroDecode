from __future__ import print_function, division

"""
Compute PSD features over a sliding window in epochs

Kyuhwa Lee
Swiss Federal Institute of Technology (EPFL)

"""

import mne
import scipy.io
import numpy as np
import pycnbi.utils.q_common as qc
import pycnbi.utils.pycnbi_utils as pu
from multiprocessing import cpu_count
from pycnbi import logger

mne.set_log_level('ERROR')


def epochs2psd(raw, channel_picks, event_id, tmin, tmax, fmin, fmax, w_len_sec, w_step, excludes='bads', export_dir=None, n_jobs=None, save_matlab=False):
    """
    Compute PSD features over a sliding window in epochs

    Input
    =====
    raw: str | mne.RawArray. If str, it is treated as a file name
    channel_picks: None or list of channel names(str) or indices(int)
    event_id: { label(str) : event_id(int) }
    tmin: start time of the PSD window relative to the event onset
    tmax: end time of the PSD window relative to the event onset
    fmin: minimum PSD frequency
    fmax: maximum PSD frequency
    w_len_sec: sliding window length for computing PSD in seconds (float)
    w_step: sliding window step in time samples (integer)
    excludes: channels to exclude
    export_dir: path to export PSD data. Automatically saved in the same directory of raw if raw is a filename
    n_jobs: number of cores to use for parallel processing
    save_matlab: if True, save the same data in .mat file as well

    Output
    ======
    4-D numpy array: [epochs] x [times] x [channels] x [freqs]

    """

    if n_jobs is None:
        n_jobs = cpu_count()

    # load raw object or file
    if type(raw) == str:
        rawfile = raw.replace('\\', '/')
        raw, events = pu.load_raw(rawfile)
        [export_dir_raw, export_name, _] = qc.parse_path_list(rawfile)
        if export_dir is None:
            export_dir = export_dir_raw
    else:
        if export_dir is None:
            raise ValueError('export_dir must be given if a RawArray object is given as argument')
        export_name = 'raw'
        events = mne.find_events(raw, stim_channel='TRIGGER', shortest_event=1, uint_cast=True, consecutive=True)

    # test writability
    qc.make_dirs(export_dir)
    pklfile = '%s/psd-%s.pkl' % (export_dir, export_name)
    open(pklfile, 'w')

    # pick channels of interest and do epoching
    if channel_picks is None:
        picks = mne.pick_types(raw.info, meg=False, eeg=True, stim=False, eog=False, exclude=excludes)
    elif type(channel_picks[0]) == str:
        picks = []
        for ch in channel_picks:
            picks.append(raw.ch_names.index(ch))
    elif type(channel_picks[0]) == int:
        picks = channel_picks
    else:
        raise ValueError('Unknown data type (%s) in channel_picks' % type(channel_picks[0]))
    epochs = mne.Epochs(raw, events, event_id, tmin=tmin, tmax=tmax, proj=False, picks=picks, baseline=(tmin, tmax), preload=True)

    # compute psd vectors over a sliding window between tmin and tmax
    sfreq = raw.info['sfreq']
    w_len = int(sfreq * w_len_sec)  # window length
    psde = mne.decoding.PSDEstimator(sfreq, fmin=fmin, fmax=fmax, n_jobs=1, adaptive=False)
    epochmat = {e:epochs[e]._data for e in event_id}
    psdmat = {}
    times = {}
    for e in event_id:
        # psd = [epochs] x [windows] x [channels] x [freqs]
        psd, _ = pu.get_psd(epochs[e], psde, w_len, w_step, flatten=False, n_jobs=n_jobs)
        psdmat[e] = psd
        times[e] = []
        w_step_sec = w_step / sfreq
        # we cannot simply use np.arange() because there's no way to include the stop value of the range
        t = tmin + w_len_sec # leading edge is the reference time
        while t <= tmax:
            times[e].append(t)
            t += w_step_sec
        times[e] = np.array(times[e])
        if len(times[e]) != psd.shape[1]:
            raise ValueError('Sorry, unexpected number of PSD vectors. Please debug me!')

    # export data
    data = dict(psds=psdmat, tmin=tmin, tmax=tmax, sfreq=epochs.info['sfreq'],\
                fmin=fmin, fmax=fmax, w_step=w_step, w_len_sec=w_len_sec,
                times=times, labels=list(epochs.event_id.keys()))
    qc.save_obj(pklfile, data)
    logger.info('Exported to %s' % pklfile)
    if save_matlab:
        matfile = '%s/psd-%s.mat' % (export_dir, export_name)
        scipy.io.savemat(matfile, data)
        logger.info('Exported to %s' % matfile)
