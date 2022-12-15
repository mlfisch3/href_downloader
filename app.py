# '''
 # href_downloader retrieves a list of urls to any downloadable files referenced by an href tag found at target_url
 # the number of each type of file found is listed in a table
 # user removes any unwanted filetypes prior to actual download (info for remaining files is shown in "Selected Files" tab")
 # clicking "Download Files" initiates download of files from target_url to temporary directory on the server
 # all downloaded files are compressed into a single .zip archive file
 # the .zip archive file is downloaded from the server to the user's local file system
 # the temporary directory on the server is removed

#  The new behavior: urls for remote files not successfully downloaded by request.urlretrieve() are saved to local server file "not_downloaded.txt"
#  and an additional download attempt is made for these urls via system call to wget -i:
#  import subprocess; command='wget -i not_downloaded.txt'; subprocess.check_output(command, shell=True, text=True)



# '''


import streamlit as st
import os
import requests
from urllib import request
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from utils.io_tools import download_to_archive, clear_info

title = 'href downloader'
st.set_page_config(page_title=title, layout="wide")

hide_streamlit_style = """
<style>
#MainMenu {visibility: visible;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

pd.options.display.width = 1000
pd.options.display.max_colwidth = 9999

@st.experimental_memo(show_spinner=False)
def get_target_info(target_url):

    r=requests.get(target_url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(r.text, 'html.parser')
    hrefs = soup.find_all("a", href=lambda x: x and "." in os.path.basename(x))
    files = list(map(lambda x: x["href"], hrefs))
    filenames = list(map(lambda x: x.replace(r'%20','_').replace('__','_-_'), files))
    urls = list(map(lambda x: request.urljoin(target_url, x) , files))
    filetypes = list(map(lambda x: x.split('.')[-1] , filenames))

    return pd.DataFrame({'File':filenames, 'URL': urls, 'Type':filetypes})
        
def run():

    if "target_url" not in st.session_state:
        st.session_state.target_url = ""

    if "zip_filename" not in st.session_state:
        st.session_state.zip_filename = ""

    if "urls" not in st.session_state:
        st.session_state.urls = []    

    if "selected_targets_info" not in st.session_state:
        st.session_state.selected_targets_info = [] 

    if "filenames" not in st.session_state:
        st.session_state.filenames = []  

    if "target_info" not in st.session_state:
        st.session_state.target_info = None

    if "message" not in st.session_state:
        st.session_state.message = ""

    if "count_downloaded" not in st.session_state:
        st.session_state.count_downloaded = 0

    st.session_state.target_url = st.text_input("Target URL:", "", on_change=clear_info, help="Type exact url (then Enter $\hookleftarrow$) to scan for downloadable files (e.g., https://web.stanford.edu/class/ee398a/handouts/lectures/)")
    

    if st.session_state.target_url != "":
        if st.session_state.target_url[-1] != "/":
            st.session_state.target_url = f'{st.session_state.target_url}/'

        if st.session_state.target_info is None:
            st.session_state.target_info = get_target_info(st.session_state.target_url)

        st.session_state.count_all = len(st.session_state.target_info)

        st.sidebar.write("Number of Files Found")
        st.sidebar.dataframe(pd.DataFrame(st.session_state.target_info.groupby(by='Type').size(), columns=['Count']))

        filetypes = st.session_state.target_info.Type.unique().tolist()
        filetype_selection = st.sidebar.multiselect('Add/Remove File Types To Include in Download:', filetypes, default=filetypes)
        st.session_state.selected_targets_info = st.session_state.target_info[st.session_state.target_info.Type.isin(filetype_selection)].reset_index(drop=True)

        st.session_state.count_selected = len(st.session_state.selected_targets_info)

        st.session_state.filenames = st.session_state.selected_targets_info.File.tolist()
        st.session_state.urls = st.session_state.selected_targets_info.URL.tolist()

        selected_tab, full_tab = st.tabs([f"• Selected Files ({st.session_state.count_selected})", f"• All Files ({st.session_state.count_all})"])

        with selected_tab:
            st.table(st.session_state.selected_targets_info)

        with full_tab:
            st.table(st.session_state.target_info)            
        
        with st.sidebar:
            button = st.button("Create Downloadable .ZIP File")
            if button:
                st.session_state.zip_filename, st.session_state.count_downloaded = download_to_archive(st.session_state.filenames, st.session_state.urls)

                st.session_state.message = f'{st.session_state.count_downloaded} files were downloaded to temporary archive {st.session_state.zip_filename}'

                st.download_button(label = f'Download {st.session_state.zip_filename}',  
                                                data=Path(st.session_state.zip_filename).read_bytes(),
                                                file_name = st.session_state.zip_filename, 
                                                key='download',
                                                help="Downloads the compressed .zip archive containing all selected files"
                                           )  

                #st.write(st.session_state.message)


if __name__ == '__main__':

    run()
