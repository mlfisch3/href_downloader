# '''
# href_downloader retrieves a list of urls to any downloadable files referenced by an href tag found at target_url
# the number of each type of file found is listed in a table
# user removes any unwanted filetypes prior to actual download (info for remaining files is shown in "Selected Files" tab")
# clicking "Download Files" initiates download of files from target_url to temporary directory on the server
# all downloaded files are compressed into a single .zip archive file
# a new "Download Archive" button appears, indicating .zip file is ready
# clicking initiates download of the .zip archive file from the server to the user's local file system
# the temporary directory on the server is removed

#  Secondary behavior: urls for remote files not successfully downloaded by request.urlretrieve() are saved to local server file "not_downloaded.txt"
#  and an additional download attempt is made for these urls via system call to curl:
#  import subprocess; command='xargs -n 1 curl --insecure -O --output-dir dOut < not_downloaded.txt'; subprocess.check_output(command, shell=True, text=True)
#  or wget -i:
#  import subprocess; command='wget -i not_downloaded.txt'; subprocess.check_output(command, shell=True, text=True)


# '''


import streamlit as st
import os
import requests
from urllib import request
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from utils.io_tools import download_to_archive, clear_info, NEWLINE
from utils import session
from utils.logging import timestamp
import subprocess
import re

title = "href downloader (local)"
st.set_page_config(page_title=title, layout="wide", initial_sidebar_state="expanded")

hide_streamlit_style = """
<style>
#MainMenu {visibility: visible;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

pd.options.display.width = 1000
pd.options.display.max_colwidth = 9999


def extract_url_re(href):
    rgx = r"(url\?q\=)(\S+)(&sa\=)"
    return re.search(rgx, href)


@st.cache_data
def get_target_info(target_url):
    try:
        r = requests.get(target_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        hrefs = soup.find_all("a", href=lambda x: x and "." in os.path.basename(x))
        #files = list(map(lambda x: x["href"], hrefs))
        # get all links to (static) files
        files = [x for x in list(map(lambda x: x["href"], hrefs)) if '?' not in x]
        # check if the target url is a google search response
        if target_url[:30] == "https://www.google.com/search?":
            fileurls = [
                y.group(2) for y in (extract_url_re(x) for x in files) if y is not None
            ]
            fileurls = [x for x in fileurls if 0 < len(x.split(".")[-1]) < 5]
            filenames = list(map(lambda x: x.split("/")[-1], fileurls))
            filenames = list(
                map(lambda x: x.replace(r"%20", "_").replace("__", "_-_"), filenames)
            )
        else:

            filenames = list(map(lambda x: x.split("/")[-1], files))
            filenames = list(
                map(lambda x: x.replace(r"%20", "_").replace("__", "_-_"), filenames)
            )
            fileurls = list(map(lambda x: request.urljoin(target_url, x), files))

        filetypes = list(map(lambda x: x.split(".")[-1], filenames))

        return pd.DataFrame({"File": filenames, "URL": fileurls, "Type": filetypes})
    except requests.exceptions.InvalidSchema as e:
        return pd.DataFrame({"File": [], "URL": [], "Type": []})


def run_command():
    print(f"[{timestamp()}] st.session_state.console_in: {st.session_state.console_in}")
    try:
        st.session_state.console_out = str(
            subprocess.check_output(st.session_state.console_in, shell=True, text=True)
        )
        st.session_state.console_out_timestamp = f"{timestamp()}"
    except subprocess.CalledProcessError as e:
        st.session_state.console_out = f"exited with error\nreturncode: {e.returncode}\ncmd: {e.cmd}\noutput: {e.output}\nstderr: {e.stderr}"
        st.session_state.console_out_timestamp = f"{timestamp()}"

    print(
        f"[{timestamp()}] st.session_state.console_out: {st.session_state.console_out}"
    )


def run():
    container = st.sidebar.container()
    with container:
        pid = os.getpid()
        placeholder = st.empty()
        if st.session_state.show_console:
            with placeholder.container():
                with st.expander("console", expanded=True):
                    with st.form("console"):
                        command = st.text_input(
                            f"[{pid}] {timestamp()}",
                            str(st.session_state.console_in),
                            key="console_in",
                        )
                        submitted = st.form_submit_button(
                            "run", help="coming soon", on_click=run_command
                        )

                        st.write(f"IN: {command}")
                        st.text(f"OUT:\n{st.session_state.console_out}")
                    file_name = st.text_input("File Name", "")
                    if os.path.isfile(file_name):
                        button = st.download_button(
                            label="Download File",
                            data=Path(file_name).read_bytes(),
                            file_name=file_name,
                            key="console_download",
                        )
        else:
            placeholder.empty()

        if st.session_state.low_resources:
            clear_cache()
            st.session_state.low_resources = False

        if st.session_state.show_resource_usage:
            with st.expander(
                f"{Process(pid).memory_info()[0]/float(2**20):.2f}", expanded=True
            ):
                pass
                # with st.form("Clear"):
                #     st.session_state.cache_checked = st.checkbox("Clear Cache", help="coming soon", value=False)
                #     st.session_state.data_checked = st.checkbox("Clear Data", help="coming soon", value=False)
                #     st.form_submit_button("Clear", on_click=clear, args=([st.session_state.cache_checked, st.session_state.data_checked]), help="coming soon")

    st.session_state.target_url = st.text_input(
        "Target URL:",
        "http://erewhon.superkuh.com/library/Math",
        on_change=clear_info,
        help="Type exact url (then Enter $\hookleftarrow$) to scan for downloadable files (e.g., http://erewhon.superkuh.com/library/Math)",
    )

    if st.session_state.target_url != "":
        if st.session_state.target_url[-1] != "/":
            st.session_state.target_url = f"{st.session_state.target_url}/"

        if st.session_state.target_info is None:
            st.session_state.target_info = get_target_info(st.session_state.target_url)

        st.session_state.count_all = len(st.session_state.target_info)

        st.sidebar.write("Number of Files Found")
        st.sidebar.dataframe(
            pd.DataFrame(
                st.session_state.target_info.groupby(by="Type").size(),
                columns=["Count"],
            )
        )

        filetypes = st.session_state.target_info.Type.unique().tolist()
        filetype_selection = st.sidebar.multiselect(
            "Add/Remove File Types To Include in Download:",
            filetypes,
            default=filetypes,
        )
        st.session_state.selected_targets_info = st.session_state.target_info[
            st.session_state.target_info.Type.isin(filetype_selection)
        ].reset_index(drop=True)

        st.session_state.count_selected = len(st.session_state.selected_targets_info)

        st.session_state.filenames = (
            st.session_state.selected_targets_info.File.tolist()
        )
        st.session_state.fileurls = st.session_state.selected_targets_info.URL.tolist()

        selected_tab, full_tab = st.tabs(
            [
                f"• Selected Files ({st.session_state.count_selected})",
                f"• All Files ({st.session_state.count_all})",
            ]
        )

        with selected_tab:
            st.table(st.session_state.selected_targets_info)

        with full_tab:
            st.table(st.session_state.target_info)

        with st.sidebar:
            button = st.button("Create Downloadable .ZIP File")
            status_placeholder = st.empty()
            if button:
                ######################################
                # Download Files to Streamlit Server
                (
                    st.session_state.zip_filename,
                    st.session_state.count_downloaded,
                ) = download_to_archive(
                    st.session_state.filenames,
                    st.session_state.fileurls,
                    status_placeholder,
                )

                if all(
                    [
                        not st.session_state.wget_failed,
                        os.path.exists(st.session_state.zip_filename),
                    ]
                ):
                    st.session_state.message = f"{st.session_state.count_downloaded-1} files were downloaded to temporary archive:{NEWLINE} {st.session_state.zip_filename}"
                    status_placeholder.text(st.session_state.message)
                    ###################################
                    # Download Archive from Streamlit Server to User's Filesystem
                    st.download_button(
                        label=f"Download .ZIP File",
                        data=Path(st.session_state.zip_filename).read_bytes(),
                        file_name=st.session_state.zip_filename,
                        key="download",
                        help="Downloads the compressed .zip archive containing all selected files",
                    )
                else:
                    status_placeholder.text(st.session_state.called_process_error)

        if all(
            [st.session_state.download, os.path.exists(st.session_state.zip_filename)]
        ):
            print(
                f"User has downloaded temporary archive file.  It will now be deleted."
            )
            os.remove(st.session_state.zip_filename)
            st.session_state.download = False


if __name__ == "__main__":
    session.initialize_session()

    query_params = st.experimental_get_query_params()
    for k, v in query_params.items():
        st.session_state.query_params[k] = v[0]
        st.session_state.query_params.setdefault(k, v[0])

    if "cache" in query_params:
        st.session_state.cache_clearance = query_params["cache"][0]
    else:
        st.session_state.cache_clearance = False

    if "resources" in query_params:
        st.session_state.show_resource_usage = query_params["resources"][0]
    else:
        st.session_state.show_resource_usage = False

    if "console" in query_params:
        st.session_state.show_console = query_params["console"][0]
    else:
        st.session_state.show_console = False

    if "debug" in query_params:
        st.session_state.debug = query_params["debug"][0]
    else:
        st.session_state.debug = False

    run()
