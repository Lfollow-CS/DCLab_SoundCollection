# Script for preparing the segan training and test data. 
# The desired window size needs to be defined (opts ['window_size'])

import tensorflow as tf
from data_ops import *
import scipy.io.wavfile as wavfile
import numpy as np
import os
import hdf5storage

def slice_1dsignal(signal, window_size, minlength, stride=0.5):
    """ 
    Return windows of the given signal by sweeping in stride fractions
    of window
    Slices that are less than minlength are omitted
    """
    n_samples = signal.shape[0]
    offset = int(window_size * stride)
    num_slices = (n_samples)
    slices = np.array([]).reshape(0, window_size) # initialize empty array
    for beg_i in range(0, n_samples, offset):
        end_i = beg_i + window_size
        if n_samples - beg_i < minlength :
            break
        if end_i <= n_samples :
            slice_ = np.array([signal[beg_i:end_i]])
        else :
            slice_ = np.concatenate((np.array([signal[beg_i:]]), np.zeros((1, end_i - n_samples))), axis=1)
        slices = np.concatenate((slices, slice_), axis=0)
    return slices.astype('float32')

def read_and_slice1d(wavfilename, window_size, minlength, stride=0.5):
    """
      Reads and slices the wavfile into windowed chunks
    """
    fs, signal =  wavfile.read(wavfilename)
    if fs != 16000:
        raise ValueError('Sampling rate is expected to be 16kHz!')
    sliced = slice_1dsignal(signal, window_size, minlength, stride=stride)
    return sliced

def prepare_sliced_data1d(opts):
    wavfolder = opts['wavfolder']
    window_size = opts['window_size']
    stride = opts['stride']
    minlength = opts['minlength']
    filenames = opts['filenames']

    full_sliced = [] # initialize empty array
    dfi = []
    dfi_begin = 0
    with open(filenames) as f:
        wav_files = f.read().splitlines() # to get rid of the \n while using readlines()
    print ("**** Reading from " + wavfolder)
    print ("**** The folder has " + str(len(wav_files)) + " files.")
    for ind, wav_file in enumerate(wav_files):
        if ind % 10 == 0 :
            print("Processing " + str(ind) + " of " + str(len(wav_files)) + " files.")
        wavfilename = os.path.join(wavfolder, wav_file)
        sliced = read_and_slice1d(wavfilename, window_size, minlength, stride=stride)
        full_sliced.append(sliced)
        dfi.append(np.array([[dfi_begin, dfi_begin + sliced.shape[0]]]))
        dfi_begin += sliced.shape[0]

    full_slicedstack = np.vstack(full_sliced)
    dfistack = np.vstack(dfi)

    return full_slicedstack, dfistack.astype('int')

if __name__ == '__main__':

    opts = {}
    opts ['datafolder'] = "./data/"
    opts ['window_size'] = 2**8
    opts['stride']= 0.5
    opts['minlength']= 0.5 * opts['window_size']
    testfilenames = os.path.join(opts['datafolder'], "test_wav.txt")
    trainfilenames = os.path.join(opts['datafolder'], "train_wav.txt")
  
    # for test set 
    opts['filenames'] = testfilenames
    # for clean set
    opts['wavfolder'] = os.path.join(opts['datafolder'], "clean_testset_wav_16kHz")
    clean_test_sliced, dfi = prepare_sliced_data1d(opts)
    # for noisy set
    opts['wavfolder'] = os.path.join(opts['datafolder'], "noisy_testset_wav_16kHz")
    noisy_test_sliced, dfi = prepare_sliced_data1d(opts) 
    if clean_test_sliced.shape[0] != noisy_test_sliced.shape[0] :
        raise ValueError('Clean sliced and noisy sliced are not of the same size!')
    if clean_test_sliced.shape[0] != dfi[-1,1] :
        raise ValueError('Sliced matrices have a different size than mentioned in dfi !')
    
    matcontent={}
    matcontent[u'feat_data'] = clean_test_sliced
    matcontent[u'dfi'] = dfi
    dir_temp = "./data/"
    destinationfilenameclean = os.path.join(dir_temp,"clean_test_segan1d_%s.mat" % opts['window_size'])
    hdf5storage.savemat(destinationfilenameclean, matcontent)

    matcontent={}
    matcontent[u'feat_data'] = noisy_test_sliced
    matcontent[u'dfi'] = dfi
    destinationfilenamenoisy = os.path.join(dir_temp,"noisy_test_segan1d_%s.mat" % opts['window_size'])
    hdf5storage.savemat(destinationfilenamenoisy, matcontent)
  

    # for train set 
    opts['filenames'] = trainfilenames
    # for clean set
    opts['wavfolder'] = os.path.join(opts['datafolder'], "clean_trainset_wav_16kHz")
    clean_train_sliced, dfi = prepare_sliced_data1d(opts)
    # for noisy set
    opts['wavfolder'] = os.path.join(opts['datafolder'], "noisy_trainset_wav_16kHz")
    noisy_train_sliced, dfi = prepare_sliced_data1d(opts)
    if clean_train_sliced.shape[0] != noisy_train_sliced.shape[0] :
        raise ValueError('Clean sliced and noisy sliced are not of the same size!')
    if clean_train_sliced.shape[0] != dfi[-1,1] :
        raise ValueError('Sliced matrices have a different size than mentioned in dfi !')
    
    matcontent={}
    matcontent[u'feat_data'] = clean_train_sliced
    matcontent[u'dfi'] = dfi
    destinationfilenameclean = os.path.join(dir_temp,"clean_train_segan1d_%s.mat" % opts['window_size'])
    hdf5storage.savemat(destinationfilenameclean, matcontent)

    matcontent={}
    matcontent[u'feat_data'] = noisy_train_sliced
    matcontent[u'dfi'] = dfi
    dir_temp = "./data/"
    destinationfilenamenoisy = os.path.join(dir_temp,"noisy_train_segan1d_%s.mat" % opts['window_size'])
    hdf5storage.savemat(destinationfilenamenoisy, matcontent)
 
    
