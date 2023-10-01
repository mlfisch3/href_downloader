import streamlit as st
import os
import pandas as pd
import random
import time
import timeit
import requests
import re
from urllib import request, parse
from bs4 import BeautifulSoup
import datetime
import zipfile
from subprocess import check_output, CalledProcessError
from pathlib import Path
import pandas as pd
from stqdm import stqdm
import shutil
from utils.logging import timestamp

#20230606 introduced function parameter to toggle on/off (default is "off", i.e. False) curl and wget download methods until automatic posix/nt newline handling is fully tested

NEWLINE = "\n"
if os.name == "nt":
    NEWLINE = "\r\n"


def change_extension(filename, ext):
    return ".".join(filename.split(".")[:-1] + [ext])


def path2tuple(path):
    """
    recursively call os.path.split
    return path components as tuple, preserving hierarchical order

    >>> newdir = r'C:\\temp\\subdir0\\subdir1\\subdir2'
    >>> path2tuple(newdir)
    ('C:\\', 'temp', 'subdir0', 'subdir1', 'suubdir2')


    """
    (a, b) = os.path.split(path)
    if b == "":
        return (a,)
    else:
        return *path2tuple(a), b


def mkpath(path):
    """
    Similar to os.mkdir except mkpath also creates implied directory structure as needed.

    For example, suppose the directory "C:\\temp" is empty. Build the hierarchy "C:\\temp\\subdir0\\subdir1\\subdir2" with single call:
    >>> newdir = r'C:\\temp\\subdir0\\subdir1\\subdir2'
    >>> mkpath(newdir)

    """
    u = list(path2tuple(path))
    pth = u[0]

    for i, j in enumerate(u, 1):
        if i < len(u):
            pth = os.path.join(pth, u[i])
            if not any([os.path.isdir(pth), os.path.isfile(pth)]):
                os.mkdir(pth)


def create_temporary_directory():
    temp_dir = os.path.join(
        os.getcwd(), f'TMP{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
    )
    if not os.path.isdir(temp_dir):
        mkpath(temp_dir)

    return temp_dir


def clear_info():
    del st.session_state.message
    del st.session_state.target_info


def zip_dir(dir_path, zip_filename=None, keep_abs_paths=False):
    """
    create zip file containing all files in dir_path.
    directory structure is not preserved unless keep_abs_paths is True

    """

    if zip_filename is None:
        zip_filename = (
            f'archive_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        )

    with zipfile.ZipFile(zip_filename, "w") as zip_file:
        if keep_abs_paths:
            count = len(
                [
                    zip_file.write(os.path.join(dir_path, f))
                    for f in stqdm(os.listdir(dir_path))
                ]
            )
        else:
            count = len(
                [
                    zip_file.write(os.path.join(dir_path, f), os.path.basename(f))
                    for f in stqdm(os.listdir(dir_path))
                ]
            )

    return zip_filename, count


def zip_files(temp_dir):
    st.session_state.zip_filename, _ = zip_dir(temp_dir)


def abbreviate_url(url):
    # Parse the URL to get the query
    parsed_url = parse.urlparse(url.replace('%20','-'))
    if all([r"www.google.com" == parsed_url.netloc, r"/search" == parsed_url.path]):
        # Extract the search query from the query string
        query = parsed_url.query
        search_query = parse.parse_qs(query).get("q", [""])[0]

        # Replace '=' with '~'
        search_query = search_query.replace("=", "~")

        # Capitalize Google search operators
        abbr_url = re.sub(
            r"(?i)\b(site|inurl|intitle|intext|filetype|ext):",
            lambda m: m.group().upper(),
            search_query,
        )
    else:
        abbr_url = parsed_url.netloc + "_" + parsed_url.path

    # Replace all remaining non-alphanumeric characters with '-'
    abbr_url = re.sub(r"[^a-zA-Z0-9-=:/]+", "-", abbr_url)
    abbr_url = re.sub(r"[:]+", "--", abbr_url)
    abbr_url = re.sub(r"[/]", "_", abbr_url)
    return abbr_url


# @st.cache_data#(show_spinner=False)
def download_by_urlretrieve(filenames, fileurls, dName, status_placeholder, delay_lo, delay_hi, delay=False):
    target_count = len(fileurls)
    not_downloaded_files = []
    not_downloaded_urls = []
    successful_files = []
    successful_urls = []

    for i, (filename, fileurl) in stqdm(enumerate(zip(filenames, fileurls))):
        print(f"[{timestamp()}] Downloading (file {i+1} of {target_count} ): {fileurl}  ...")
        status_placeholder.text(
            f"Downloading (file {i+1} of {target_count} ): {fileurl}  ..."
        )
        fPath = os.path.join(dName, filename)
        fPath = fPath.replace(" ", "_")
        try:
            request.urlretrieve(fileurl, filename=fPath)
            successful_files.append(filename)
            successful_urls.append(fileurl)
        except:
            print(f"[{timestamp()}]   ╚═► Download failed: {fileurl}")
            fileurl_ = fileurl.replace(" ", "%20")  # replace single whitespaces with hex code %20
            if fileurl_ == fileurl:                
                not_downloaded_files.append(filename)
                not_downloaded_urls.append(fileurl)  # if no whitespaces to replace, note then no further attempts with urlretrieve
                continue
            else:
                print(f"[{timestamp()}] Downloading (file {i+1} of {target_count} ): {fileurl_}  ...")  # retry download with ' ' -> '%20'
                try:
                    request.urlretrieve(fileurl_, filename=fPath)
                    successful_files.append(filename)
                    successful_urls.append(fileurl_)
                except:
                    print(f"[{timestamp()}]   ╚═► Download failed: {fileurl_}")
                    not_downloaded_files.append(filename)
                    not_downloaded_urls.append(fileurl_)              # add filename (version with %20 instead of whitespaces) to list to be retried by alternative method
                    continue

        if delay:
            delta = random.randint(delay_lo, delay_hi)
            time = timeit.timeit("time.sleep(0.01)", number=delta)
            print(f"[{timestamp()}] [{delta}] sleeping for {time} seconds...")

    source_info_file_path = os.path.join(dName, "source_info.psv")
    with open(source_info_file_path, "w") as source_info_file:
        for j, (fname, furl) in enumerate(zip(successful_files, successful_urls)):
            source_info_file.write("|".join([str(j), fname, furl]) + NEWLINE)

    print(os.lstat(source_info_file_path))
    # if len(not_downloaded_files):
    #     not_downloaded_file_path = os.path.join(dName, "not_downloaded.psv")
    #     with open(not_downloaded_file_path, "w") as not_downloaded_info_file:
    #         for j, (fname, furl) in enumerate(zip(not_downloaded_files, not_downloaded_urls)):
    #             not_downloaded_info_file.write("|".join([str(j), fname, furl]) + NEWLINE)
    num_not_downloaded = len(not_downloaded_urls)
    if num_not_downloaded > 0:
        not_downloaded_urls_filename = os.path.join(dName, "missed_urls.txt")
        with open(not_downloaded_urls_filename, "w") as fout:
            for not_downloaded_url in not_downloaded_urls:
                fout.write(not_downloaded_url + NEWLINE)

        print(f"[{timestamp()}] {num_not_downloaded} filenames written to {not_downloaded_urls_filename}")
        return num_not_downloaded, not_downloaded_urls_filename

    print(f"[{timestamp()}] All files downloaded")
    return 0, None


def download_by_curl(urls_file, dName):        # if this function fails, check if newline chars being written to source_info.psv and missed_urls.txt are consistent with posix/nt
    
    # Determine OS type (Linux or Windows)  
    if os.name == "posix":                           # 
        command = r"xargs -n 1 curl --insecure -O --output-dir "
        command += f"{dName}"
        command += " < "
        command += f"{urls_file}"
    elif os.name == "nt":                            # C:\GIT_REPOS\HREF_DOWNLOADER_LOCAL\TMP20230606_020900>for /f "tokens=*" %i in (missed_urls.txt) do curl --insecure -O "%i" -J -L
        command = r'for /f "tokens=*" %i in '
        command += f"({urls_file})"
        command += r' do curl --insecure -O "%i"'
    else:
        print(f"[{timestamp()}] Unrecognized OS.  Skipping alternative download method.")
        return False
    try:
        # run command in subprocess
        print(f"[{timestamp()}] RUNNING subprocess command: {command}")
        check_output(command)
        print(f"[{timestamp()}] Done")

    except CalledProcessError as e:
        st.session_state.called_process_error = f"exited with error{NEWLINE}returncode: {e.returncode}{NEWLINE}cmd: {e.cmd}{NEWLINE}output: {e.output}{NEWLINE}stderr: {e.stderr}"
        print(f"[{timestamp()}] {st.session_state.called_process_error}")  
        st.session_state.curl_failed = True
        st.session_state.message = f"Download was denied"
 #       return False
#    shutil.move("urls.txt", os.path.join(dName, "urls.txt"))
#    return True

# @st.cache_data#(show_spinner=False)
def download_by_wget(urls_file, dName):
    
    command = f"wget --no-check-certificate -i {urls_file} --random-wait -P {dName}"

    try:
        # run command in subprocess
        print(f"[{timestamp()}] RUNNING subprocess command: {command}")
        check_output(command)
        print(f"[{timestamp()}] Done")    

    except CalledProcessError as e:
        st.session_state.called_process_error = f"exited with error{NEWLINE}returncode: {e.returncode}{NEWLINE}cmd: {e.cmd}{NEWLINE}output: {e.output}{NEWLINE}stderr: {e.stderr}"
        print(f"[{timestamp()}] {st.session_state.called_process_error}")  
        st.session_state.wget_failed = True
        st.session_state.message = f"Download was denied"
    #    return False
#        shutil.move("urls.txt", os.path.join(dName, "urls.txt"))
   # return True



def download_to_archive(filenames, fileurls, status_placeholder, delay_lo=30, delay_hi=120, delay=False, allow_curl=False, allow_wget=False):
    temp_dir = create_temporary_directory()

    # Download files to server
    num_missed, missed_urls_filename = download_by_urlretrieve(
        st.session_state.filenames,
        st.session_state.fileurls,
        temp_dir,
        status_placeholder,
        delay_lo,
        delay_hi,
        delay,
    )

    # Try to get any files missed in 1st download attempt
    if all([num_missed > 0, os.path.isfile(str(missed_urls_filename))]):
        print(f"{NEWLINE}[{timestamp()}]  ►►► {num_missed} files were not downloaded.")
        
        if all([allow_curl, shutil.which("curl") is not None]):
            print(f"{NEWLINE}[{timestamp()}] Retrying with curl ...{NEWLINE}")
            download_by_curl(missed_urls_filename, temp_dir)
        elif all([allow_wget, shutil.which("wget") is not None]):
            print(f"{NEWLINE}[{timestamp()}] Retrying with wget ...{NEWLINE}")
            download_by_wget(missed_urls_filename, temp_dir)
        else:
            print(f"[{timestamp()}] WARNING: Skipping alternate download method. ")
            print(f"[{timestamp()}] Undownloaded files are listed in {missed_urls_filename}")

    # Copy downloaded files into compressed archive file
    zip_filename = abbreviate_url(st.session_state.target_url) + ".zip"
    st.session_state.zip_filename, st.session_state.count_downloaded = zip_dir(
        temp_dir, zip_filename=zip_filename
    )

    # remove temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)

    # st.session_state.message = f'{st.session_state.count_downloaded} files were downloaded to temporary archive {st.session_state.zip_filename}'

    return st.session_state.zip_filename, st.session_state.count_downloaded
