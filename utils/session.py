import streamlit as st
from utils.logging import timestamp

def initialize_session():
    if "status" not in st.session_state:
        st.session_state.status = ""

    if "query_param_values" not in st.session_state:
        st.session_state.query_param_values = {}
        st.session_state.query_param_values["console"] = False
        st.session_state.query_param_values["resources"] = False
        st.session_state.query_param_values["cache"] = False

    if "show_resource_usage" not in st.session_state:
        st.session_state.show_resource_usage = False
    else:
        st.session_state.show_resource_usage = False

    if "show_console" not in st.session_state:
        st.session_state.show_console = False

    if "console_out" not in st.session_state:
        st.session_state.console_out = ""

    if "console_in" not in st.session_state:
        st.session_state.console_in = ""

    if "cache_checked" not in st.session_state:
        st.session_state.cache_checked = False

    if "data_checked" not in st.session_state:
        st.session_state.data_checked = False

    if "low_resources" not in st.session_state:
        st.session_state.low_resources = False

    if "allow_curl" not in st.session_state:
        st.session_state.allow_curl = False

    if "curl_failed" not in st.session_state:
        st.session_state.curl_failed = False

    if "allow_wget" not in st.session_state:
        st.session_state.allow_wget = False

    if "wget_failed" not in st.session_state:
        st.session_state.wget_failed = False

    if "target_url" not in st.session_state:
        st.session_state.target_url = ""

    if "zip_filename" not in st.session_state:
        st.session_state.zip_filename = ""

    if "fileurls" not in st.session_state:
        st.session_state.fileurls = []

    if "selected_targets_info" not in st.session_state:
        st.session_state.selected_targets_info = []

    if "filenames" not in st.session_state:
        st.session_state.filenames = []

    if "target_info" not in st.session_state:
        st.session_state.target_info = None

    if "message" not in st.session_state:
        st.session_state.message = ""

    if "download" not in st.session_state:
        st.session_state.download = False

    if "count_downloaded" not in st.session_state:
        st.session_state.count_downloaded = 0

    if "called_process_error" not in st.session_state:
        st.session_state.called_process_error = None