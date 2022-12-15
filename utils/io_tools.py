import streamlit as st
import os
import pandas as pd
import random
import time
import timeit
import requests
from urllib import request
from bs4 import BeautifulSoup
import datetime
import zipfile
from subprocess import check_output
from pathlib import Path
import pandas as pd
from stqdm import stqdm
import shutil


def change_extension(filename, ext):
    return '.'.join(filename.split('.')[:-1] + [ext])

def path2tuple(path):
    '''    
    recursively call os.path.split 
    return path components as tuple, preserving hierarchical order

    >>> newdir = r'C:\\temp\\subdir0\\subdir1\\subdir2'
    >>> path2tuple(newdir)
    ('C:\\', 'temp', 'subdir0', 'subdir1', 'suubdir2')
          

    '''
    (a,b) = os.path.split(path)
    if b == '':
        return a,
    else:
        return *path2tuple(a), b

def mkpath(path):
    '''
    Similar to os.mkdir except mkpath also creates implied directory structure as needed.

    For example, suppose the directory "C:\\temp" is empty. Build the hierarchy "C:\\temp\\subdir0\\subdir1\\subdir2" with single call:
    >>> newdir = r'C:\\temp\\subdir0\\subdir1\\subdir2'
    >>> mkpath(newdir)        

    '''
    u = list(path2tuple(path))    
    pth=u[0]

    for i,j in enumerate(u, 1):
        if i < len(u):
            pth = os.path.join(pth,u[i])
            if not any([os.path.isdir(pth), os.path.isfile(pth)]):
                os.mkdir(pth)



def create_temporary_directory():
    
    temp_dir = os.path.join(os.getcwd(), f'TMP{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}')
    if not os.path.isdir(temp_dir):
        mkpath(temp_dir)

    return temp_dir


@st.experimental_memo(show_spinner=False)
def download_by_urlretrieve(filenames, urls, dName, delay_lo, delay_hi, delay=False):
        
    target_count = len(urls)
    not_downloaded = []
    for i, (filename, target_file) in stqdm(enumerate(zip(filenames, urls))):
        print('Downloading (file {} of {} ): {}  ...'.format(i+1, target_count, target_file))
        'Downloading (file {} of {} ): {}  ...'.format(i+1, target_count, target_file)
        fPath = os.path.join(dName, filename)
        fPath = fPath.replace(' ', '_')
        try:
            request.urlretrieve(target_file, filename=fPath)
        except:
            print("  ╚═► Download failed: {}".format(target_file))
            target_file_ = target_file.replace(' ', '%20')
            if target_file_ == target_file:
                not_downloaded.append(target_file)
                continue
            else:
                print('  Downloading (file {} of {} ): {}  ...'.format(i+1, target_count, target_file_))
                try:
                    request.urlretrieve(target_file_, filename=fPath)
                except:
                    print("  ╚═► Download failed: {}".format(target_file_))
                    not_downloaded.append(target_file_)
                    continue
        
        if delay:    
            delta = random.randint(delay_lo,delay_hi)
            time = timeit.timeit('time.sleep(0.01)', number=delta)
            print('[',delta, '] sleeping for ', time,' seconds...')

    return not_downloaded



@st.experimental_memo(show_spinner=False)
def download_by_wget(urls, dName):
    if len(urls) > 0:
        
        # create file containing one target url per line
        with open('urls.txt', 'w') as fout:
            for url in urls:
                fout.write(url + '\n')

        command="wget -i urls.txt --random-wait -P {}".format(dName)
        
        # run command in subprocess
        check_output(command)


def clear_info():

    del st.session_state.message
    del st.session_state.target_info


def zip_dir(dir_path, zip_filename=None, keep_abs_paths=False):
    '''
    create zip file containing all files in dir_path.  
    directory structure is not preserved unless keep_abs_paths is True

    '''

    if zip_filename is None:
        zip_filename = f'archive_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'

    with zipfile.ZipFile(zip_filename,'w') as zip_file:
        if keep_abs_paths:
            count = len([zip_file.write(os.path.join(dir_path,f)) for f in stqdm(os.listdir(dir_path))])
        else:
            count = len([zip_file.write(os.path.join(dir_path,f), os.path.basename(f)) for f in stqdm(os.listdir(dir_path))])

    return zip_filename, count


def zip_files(temp_dir):
    
    st.session_state.zip_filename = zip_dir(temp_dir)


def download_to_archive(filenames, urls, delay_lo=30, delay_hi=120, delay=False):

        temp_dir = create_temporary_directory()

        not_downloaded = download_by_urlretrieve(st.session_state.filenames, st.session_state.urls, temp_dir, delay_lo, delay_hi, delay)

        if len(not_downloaded) > 0:
            print("\n ►►► {} files were not downloaded.  Attempting alternate method ...\n".format(len(not_downloaded)))
            download_by_wget(not_downloaded, temp_dir)

        st.session_state.zip_filename, st.session_state.count_downloaded = zip_dir(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

        # st.session_state.message = f'{st.session_state.count_downloaded} files were downloaded to temporary archive {st.session_state.zip_filename}'

        return st.session_state.zip_filename, st.session_state.count_downloaded
