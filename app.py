# app.py

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import plotly.express as px
import math

# ---------------------- Configuration ---------------------- #

# Replace with your FastAPI backend URL
API_BASE_URL = 'https://api.demopython.in/'  # Update this if your backend is hosted elsewhere

# Set Streamlit page configuration
st.set_page_config(
    page_title="Excel Comparison Tool",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------- Apply Dark Theme ---------------------- #
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import plotly.express as px
import math

# ---------------------- Apply Dark Theme and Custom Background ---------------------- #
st.markdown(
    """
    <style>
    /* Background */
    .css-18e3th9, .css-1d391kg, .css-1dp5vir {
        background-color: #0e1117;
        color: #c9d1d9;
    }
    /* Text */
    .css-1d391kg p, .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3,
    .css-1d391kg h4, .css-1d391kg h5, .css-1d391kg h6, .css-1d391kg label {
        color: #c9d1d9;
    }
    /* Input Fields */
    .css-1cpxqw2, .css-1d1r5lo {
        background-color: #161b22;
        color: #c9d1d9;
    }
    /* Buttons */
    .stButton>button {
        background-color: #21262d;
        color: #c9d1d9;
        border-color: #30363d;
    }
    .stButton>button:hover {
        background-color: #30363d;
        border-color: #8b949e;
    }
    /* Metrics */
    .css-1aumxhk {
        background-color: #161b22;
        border-color: #30363d;
    }
    /* DataFrame */
    .ag-header-cell-text, .ag-cell {
        color: #c9d1d9 !important;
    }
    .ag-row {
        background-color: #0e1117 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------- Initialize Session State ---------------------- #
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = None
if 'date_ranges' not in st.session_state:
    st.session_state['date_ranges'] = None
if 'data_processed' not in st.session_state:
    st.session_state['data_processed'] = False
# Initialize pagination states for API, Dashboard, Amount Differences, and Status Differences
if 'api_pagination' not in st.session_state:
    st.session_state['api_pagination'] = {'page': 1, 'page_size': 10}
if 'dashboard_pagination' not in st.session_state:
    st.session_state['dashboard_pagination'] = {'page': 1, 'page_size': 10}
if 'amount_diff_pagination' not in st.session_state:
    st.session_state['amount_diff_pagination'] = {'page': 1, 'page_size': 10}
if 'status_diff_pagination' not in st.session_state:
    st.session_state['status_diff_pagination'] = {'page': 1, 'page_size': 10}

# ---------------------- Sidebar ---------------------- #
if st.session_state['session_id']:
    st.sidebar.success(f"Session ID: {st.session_state['session_id']}")

# ---------------------- Step 1: Upload Files ---------------------- #
st.header("Upload Excel/CSV Files")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload API Excel/CSV")
    api_file = st.file_uploader("Upload API File", type=['csv', 'xls', 'xlsx', 'xlsb'], key='api_file')

with col2:
    st.subheader("Upload Dashboard Excel/CSV")
    dashboard_file = st.file_uploader("Upload Dashboard File", type=['csv', 'xls', 'xlsx', 'xlsb'],
                                      key='dashboard_file')

# Upload Files Button
if st.button("Upload Files"):
    if api_file and dashboard_file:
        with st.spinner('Uploading files...'):
            files = {
                'api_file': (api_file.name, api_file.getvalue()),
                'dashboard_file': (dashboard_file.name, dashboard_file.getvalue())
            }
            try:
                response = requests.post(f"{API_BASE_URL}/upload", files=files)
                if response.status_code == 200:
                    data = response.json()
                    session_id = data['session_id']
                    st.session_state['session_id'] = session_id
                    st.success("Files uploaded successfully!")
                else:
                    st.error(f"File upload failed: {response.json().get('detail', '')}")
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload both files.")

# ---------------------- Step 2: Get Date Range ---------------------- #
st.header("Get Date Range")

if st.button("Get Date Range"):
    session_id = st.session_state.get('session_id')
    if session_id:
        with st.spinner('Getting date ranges...'):
            try:
                # Assuming the backend provides a /summary endpoint that includes date ranges
                date_range_response = requests.get(f"{API_BASE_URL}/get_date_range", params={'session_id': session_id})
                if date_range_response.status_code == 200:
                    date_ranges = date_range_response.json()
                    st.session_state['date_ranges'] = date_ranges
                    st.success("Date ranges retrieved successfully!")
                else:
                    st.error(f"Failed to get date ranges: {date_range_response.json().get('detail', '')}")
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload files first.")

# Display Date Ranges
if st.session_state['date_ranges']:
    date_ranges = st.session_state['date_ranges']
    st.subheader("Date Ranges in Uploaded Files")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**API File Date Range**")
        st.write(
            f"From **{date_ranges.get('date_range_api', {}).get('min_date', 'N/A')}** to **{date_ranges.get('date_range_api', {}).get('max_date', 'N/A')}**")
    with col2:
        st.markdown("**Dashboard File Date Range**")
        st.write(
            f"From **{date_ranges.get('date_range_dashboard', {}).get('min_date', 'N/A')}** to **{date_ranges.get('date_range_dashboard', {}).get('max_date', 'N/A')}**")

# ---------------------- Step 3: Process Data ---------------------- #
st.header("Process Data")

# Date Range Selector beside Process Button
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    start_date = st.date_input("Start Date", value=None, key='start_date')
with col2:
    end_date = st.date_input("End Date", value=None, key='end_date')
with col3:
    if st.button("Process Data"):
        session_id = st.session_state.get('session_id')
        if session_id:
            with st.spinner('Processing data...'):
                process_data = {
                    'session_id': session_id,
                    'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                    'end_date': end_date.strftime('%Y-%m-%d') if end_date else None
                }
                try:
                    response = requests.post(f"{API_BASE_URL}/process", json=process_data)
                    if response.status_code == 200:
                        st.session_state['data_processed'] = True
                        st.success("Data processed successfully!")
                        # Reset pagination when data is processed
                        st.session_state['api_pagination'] = {'page': 1, 'page_size': 10}
                        st.session_state['dashboard_pagination'] = {'page': 1, 'page_size': 10}
                        st.session_state['amount_diff_pagination'] = {'page': 1, 'page_size': 10}
                        st.session_state['status_diff_pagination'] = {'page': 1, 'page_size': 10}
                    else:
                        st.error(f"Data processing failed: {response.json().get('detail', '')}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.warning("Please upload files and get date ranges first.")

# ---------------------- Display Summary, Data, and Visualizations ---------------------- #
if st.session_state['data_processed']:
    session_id = st.session_state['session_id']

    # ---------------------- Fetch and Display Summary ---------------------- #
    st.header("Summary")

    with st.spinner('Fetching summary...'):
        try:
            # Fetch the summary from /summary endpoint
            summary_response = requests.get(f"{API_BASE_URL}/summary", params={'session_id': session_id})
            if summary_response.status_code == 200:
                summary = summary_response.json()

                # Fetch the status counts from /status_counts endpoint
                status_counts_response = requests.get(f"{API_BASE_URL}/status_counts",
                                                      params={'session_id': session_id})
                if status_counts_response.status_code == 200:
                    status_counts = status_counts_response.json()
                    status_counts_api = status_counts.get('status_counts_api', {})
                    status_counts_dashboard = status_counts.get('status_counts_dashboard', {})
                else:
                    st.error(f"Failed to fetch status counts: {status_counts_response.json().get('detail', '')}")
                    status_counts_api = {}
                    status_counts_dashboard = {}

                # Display Key Metrics
                st.markdown("### Key Metrics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="Total Amount (API)", value=f"₹{summary.get('total_amount_api', 0):,.2f}")
                with col2:
                    st.metric(label="Total Amount (Dashboard)",
                              value=f"₹{summary.get('total_amount_dashboard', 0):,.2f}")
                with col3:
                    amount_diff = summary.get('total_amount_difference', 0)
                    delta_color = "normal" if amount_diff >= 0 else "inverse"
                    st.metric(label="Amount Difference", value=f"₹{amount_diff:,.2f}", delta="",
                              delta_color=delta_color)

                col4, col5, col6 = st.columns(3)
                with col4:
                    st.metric(label="Transactions (API)", value=f"{summary.get('num_transactions_api', 0):,}")
                with col5:
                    st.metric(label="Transactions (Dashboard)",
                              value=f"{summary.get('num_transactions_dashboard', 0):,}")
                with col6:
                    transaction_diff = summary.get('num_transactions_api', 0) - summary.get(
                        'num_transactions_dashboard', 0)
                    delta_color = "normal" if transaction_diff >= 0 else "inverse"
                    st.metric(label="Transaction Difference", value=f"{transaction_diff:,}", delta="",
                              delta_color=delta_color)

                col7, col8 = st.columns(2)
                with col7:
                    st.metric(label="Common OrderIDs", value=f"{summary.get('num_common_orderids', 0):,}")
                with col8:
                    st.metric(label="Uncommon OrderIDs", value=f"{summary.get('num_uncommon_orderids', 0):,}")

                # Display Status Counts
                st.markdown("### Status Counts")
                col9, col10 = st.columns(2)
                with col9:
                    st.markdown("**API Status Counts**")
                    if status_counts_api:
                        status_counts_api_df = pd.DataFrame(list(status_counts_api.items()),
                                                            columns=['Status', 'Count'])
                        st.table(status_counts_api_df)
                    else:
                        st.write("No status counts available for API data.")
                with col10:
                    st.markdown("**Dashboard Status Counts**")
                    if status_counts_dashboard:
                        status_counts_dashboard_df = pd.DataFrame(list(status_counts_dashboard.items()),
                                                                  columns=['Status', 'Count'])
                        st.table(status_counts_dashboard_df)
                    else:
                        st.write("No status counts available for Dashboard data.")

                
                # Visual Separator
                st.markdown("---")

                # Date Ranges (Already displayed in Step 2)
            else:
                st.error(f"Failed to fetch summary: {summary_response.json().get('detail', '')}")
        except Exception as e:
            st.error(f"An error occurred while fetching summary: {e}")

    # ---------------------- Fetch and Display Dataframes with Custom Pagination ---------------------- #
    st.header("Processed Data Comparison")


    def fetch_dataframe(session_id, endpoint, page, page_size):
        try:
            response = requests.get(
                f"{API_BASE_URL}/{endpoint}",
                params={'session_id': session_id, 'page': page, 'page_size': page_size}
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch data from {endpoint}: {response.json().get('detail', '')}")
                return None
        except Exception as e:
            st.error(f"An error occurred while fetching data from {endpoint}: {e}")
            return None


    def display_data_with_aggrid(session_id, endpoint, title, pagination_key):
        st.subheader(title)

        # Get current pagination state
        current_page = st.session_state[pagination_key]['page']
        page_size = st.session_state[pagination_key]['page_size']

        # Fetch data for current page
        data_response = fetch_dataframe(session_id, endpoint, current_page, page_size)
        if data_response:
            data = data_response['data']
            total_records = data_response.get('total_records', 0)
            total_pages = math.ceil(total_records / page_size) if page_size else 1
            # Convert to DataFrame
            df = pd.DataFrame(data)

            if df.empty:
                st.warning("No data available on this page.")
            else:
                # Configure AgGrid options
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(resizable=True, filterable=True, sortable=True)
                grid_options = gb.build()

                # Display AgGrid
                AgGrid(
                    df,
                    gridOptions=grid_options,
                    height=400,  # Adjust height as needed
                    width='100%',
                    # fit_columns_on_grid_load=True,
                    theme='balham',
                    enable_enterprise_modules=True,
                    update_mode=GridUpdateMode.NO_UPDATE,
                    allow_unsafe_jscode=True,
                )

                # Display pagination controls
                col_prev, col_page, col_next = st.columns([1, 2, 1])
                with col_prev:
                    if st.button("Previous", key=f"{endpoint}_prev"):
                        if current_page > 1:
                            st.session_state[pagination_key]['page'] -= 1
                with col_page:
                    st.write(f"Page {current_page} of {total_pages}")
                with col_next:
                    if st.button("Next", key=f"{endpoint}_next"):
                        if current_page < total_pages:
                            st.session_state[pagination_key]['page'] += 1


    # Display API Data
    col1, col2 = st.columns(2)
    with col1:
        # Page Size Selector
        api_page_size = st.selectbox(
            "API Data - Rows per page",
            options=[10, 20, 50, 100],
            index=0,
            key='api_page_size'
        )
        st.session_state['api_pagination']['page_size'] = api_page_size
        display_data_with_aggrid(session_id, "get_dataframe_api", "API Data", 'api_pagination')
    with col2:
        # Page Size Selector
        dashboard_page_size = st.selectbox(
            "Dashboard Data - Rows per page",
            options=[10, 20, 50, 100],
            index=0,
            key='dashboard_page_size'
        )
        st.session_state['dashboard_pagination']['page_size'] = dashboard_page_size
        display_data_with_aggrid(session_id, "get_dataframe_dashboard", "Dashboard Data", 'dashboard_pagination')

    # ---------------------- Amount Differences ---------------------- #
    # ---------------------- Amount and Status Differences Side by Side ---------------------- #
    st.header("Differences")

    # Create two columns: one for Amount Differences and one for Status Differences
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Amount Differences")


        def display_amount_differences(session_id, pagination_key):
            st.subheader("Amount Differences")

            # Get current pagination state
            current_page = st.session_state[pagination_key]['page']
            page_size = st.session_state[pagination_key]['page_size']

            # Fetch data for current page
            data_response = fetch_dataframe(session_id, "get_amount_differences", current_page, page_size)
            if data_response:
                data = data_response['data']
                total_records = data_response.get('total_records', 0)
                total_pages = math.ceil(total_records / page_size) if page_size else 1
                # Convert to DataFrame
                df = pd.DataFrame(data)

                if df.empty:
                    st.warning("No data available on this page.")
                else:
                    # Configure AgGrid options
                    gb = GridOptionsBuilder.from_dataframe(df)
                    gb.configure_default_column(resizable=True, filterable=True, sortable=True)
                    grid_options = gb.build()

                    # Display AgGrid
                    AgGrid(
                        df,
                        gridOptions=grid_options,
                        height=400,
                        width='100%',
                        theme='balham',
                        enable_enterprise_modules=True,
                        update_mode=GridUpdateMode.NO_UPDATE,
                        allow_unsafe_jscode=True,
                    )

                    # Display pagination controls
                    col_prev, col_page, col_next = st.columns([1, 2, 1])
                    with col_prev:
                        if st.button("Previous", key=f"{pagination_key}_prev"):
                            if current_page > 1:
                                st.session_state[pagination_key]['page'] -= 1
                    with col_page:
                        st.write(f"Page {current_page} of {total_pages}")
                    with col_next:
                        if st.button("Next", key=f"{pagination_key}_next"):
                            if current_page < total_pages:
                                st.session_state[pagination_key]['page'] += 1


        # Page Size Selector for Amount Differences
        amount_diff_page_size = st.selectbox(
            "Amount Differences - Rows per page",
            options=[10, 20, 50, 100],
            index=0,
            key='amount_diff_page_size'
        )
        st.session_state['amount_diff_pagination']['page_size'] = amount_diff_page_size
        display_amount_differences(session_id, 'amount_diff_pagination')

    with col2:
        st.subheader("Status Differences")


        def display_status_differences(session_id, pagination_key):
            st.subheader("Status Differences")

            # Get current pagination state
            current_page = st.session_state[pagination_key]['page']
            page_size = st.session_state[pagination_key]['page_size']

            # Fetch data for current page
            data_response = fetch_dataframe(session_id, "get_status_differences", current_page, page_size)
            if data_response:
                data = data_response['data']
                total_records = data_response.get('total_records', 0)
                total_pages = math.ceil(total_records / page_size) if page_size else 1
                # Convert to DataFrame
                df = pd.DataFrame(data)

                if df.empty:
                    st.warning("No data available on this page.")
                else:
                    # Configure AgGrid options
                    gb = GridOptionsBuilder.from_dataframe(df)
                    gb.configure_default_column(resizable=True, filterable=True, sortable=True)
                    grid_options = gb.build()

                    # Display AgGrid
                    AgGrid(
                        df,
                        gridOptions=grid_options,
                        height=400,
                        width='100%',
                        theme='balham',
                        enable_enterprise_modules=True,
                        update_mode=GridUpdateMode.NO_UPDATE,
                        allow_unsafe_jscode=True,
                    )

                    # Display pagination controls
                    col_prev, col_page, col_next = st.columns([1, 2, 1])
                    with col_prev:
                        if st.button("Previous", key=f"{pagination_key}_prev"):
                            if current_page > 1:
                                st.session_state[pagination_key]['page'] -= 1
                    with col_page:
                        st.write(f"Page {current_page} of {total_pages}")
                    with col_next:
                        if st.button("Next", key=f"{pagination_key}_next"):
                            if current_page < total_pages:
                                st.session_state[pagination_key]['page'] += 1


        # Page Size Selector for Status Differences
        status_diff_page_size = st.selectbox(
            "Status Differences - Rows per page",
            options=[10, 20, 50, 100],
            index=0,
            key='status_diff_page_size'
        )
        st.session_state['status_diff_pagination']['page_size'] = status_diff_page_size
        display_status_differences(session_id, 'status_diff_pagination')
    # ---------------------- Fetch and Display Visualizations ---------------------- #
    st.header("Visualizations")

    # Fetch status counts
    with st.spinner('Fetching status counts...'):
        try:
            status_counts_response = requests.get(f"{API_BASE_URL}/status_counts", params={'session_id': session_id})
            if status_counts_response.status_code == 200:
                status_counts = status_counts_response.json()
                status_counts_api = status_counts.get('status_counts_api', {})
                status_counts_dashboard = status_counts.get('status_counts_dashboard', {})

                # Convert to DataFrame for Plotly
                status_counts_api_df = pd.DataFrame(list(status_counts_api.items()), columns=['Status', 'Count'])
                status_counts_dashboard_df = pd.DataFrame(list(status_counts_dashboard.items()),
                                                          columns=['Status', 'Count'])

                # Plot Pie Charts
                st.subheader("Status Distribution")

                col1, col2 = st.columns(2)
                with col1:
                    fig_api_pie = px.pie(
                        status_counts_api_df,
                        names='Status',
                        values='Count',
                        title='API Status Distribution',
                        color_discrete_sequence=px.colors.sequential.RdBu
                    )
                    st.plotly_chart(fig_api_pie, use_container_width=True)
                with col2:
                    fig_dashboard_pie = px.pie(
                        status_counts_dashboard_df,
                        names='Status',
                        values='Count',
                        title='Dashboard Status Distribution',
                        color_discrete_sequence=px.colors.sequential.RdBu
                    )
                    st.plotly_chart(fig_dashboard_pie, use_container_width=True)
            else:
                st.error(f"Failed to fetch status counts: {status_counts_response.json().get('detail', '')}")
        except Exception as e:
            st.error(f"An error occurred while fetching status counts: {e}")

    # Fetch total amount per status
    with st.spinner('Fetching total amount per status...'):
        try:
            amount_per_status_response = requests.get(f"{API_BASE_URL}/total_amount_per_status",
                                                      params={'session_id': session_id})
            if amount_per_status_response.status_code == 200:
                amount_per_status = amount_per_status_response.json()
                amount_per_status_api = amount_per_status.get('total_amount_per_status_api', [])
                amount_per_status_dashboard = amount_per_status.get('total_amount_per_status_dashboard', [])

                # Convert to DataFrame for Plotly
                amount_per_status_api_df = pd.DataFrame(amount_per_status_api)
                amount_per_status_dashboard_df = pd.DataFrame(amount_per_status_dashboard)

                # Plot Bar Charts
                st.subheader("Total Amount per Status")

                col1, col2 = st.columns(2)
                with col1:
                    fig_api_bar = px.bar(
                        amount_per_status_api_df,
                        x='Status',
                        y='Amount',
                        title='API Amount per Status',
                        color='Amount',
                        color_continuous_scale=px.colors.sequential.RdBu
                    )
                    st.plotly_chart(fig_api_bar, use_container_width=True)
                with col2:
                    fig_dashboard_bar = px.bar(
                        amount_per_status_dashboard_df,
                        x='Status',
                        y='Amount',
                        title='Dashboard Amount per Status',
                        color='Amount',
                        color_continuous_scale=px.colors.sequential.RdBu
                    )
                    st.plotly_chart(fig_dashboard_bar, use_container_width=True)
            else:
                st.error(
                    f"Failed to fetch total amount per status: {amount_per_status_response.json().get('detail', '')}")
        except Exception as e:
            st.error(f"An error occurred while fetching total amount per status: {e}")

    # ---------------------- Download Reports ---------------------- #
    st.header("Download Reports")

    st.write("Download the difference reports below:")

    amount_diff_url = f"{API_BASE_URL}/download/amount_differences?session_id={session_id}"
    status_diff_url = f"{API_BASE_URL}/download/status_differences?session_id={session_id}"
    uncommon_orderids_url = f"{API_BASE_URL}/download/uncommon_orderids?session_id={session_id}"

    st.markdown(f"[Download Amount Differences CSV]({amount_diff_url})")
    st.markdown(f"[Download Status Differences CSV]({status_diff_url})")
    st.markdown(f"[Download Uncommon OrderIDs CSV]({uncommon_orderids_url})")

    # ---------------------- Search Functionality ---------------------- #
    st.header("Search for OrderID")

    orderid_to_search = st.text_input("Enter OrderID to search")

    if st.button("Search") and orderid_to_search:
        with st.spinner("Searching..."):
            try:
                search_response = requests.get(
                    f"{API_BASE_URL}/search",
                    params={'session_id': session_id, 'orderid': orderid_to_search}
                )
                if search_response.status_code == 200:
                    search_results = search_response.json()
                    st.subheader("API File Matches")
                    if search_results.get('api_matches'):
                        api_matches_df = pd.DataFrame(search_results['api_matches'])
                        gb = GridOptionsBuilder.from_dataframe(api_matches_df)
                        gb.configure_pagination(paginationAutoPageSize=True)
                        gb.configure_side_bar()
                        gb.configure_default_column(resizable=True, min_width=100, wrapText=True, autoHeight=True)
                        grid_options = gb.build()
                        AgGrid(
                            api_matches_df,
                            gridOptions=grid_options,
                            height=150,  # Increased height
                            # fit_columns_on_grid_load=True,
                            theme='balham'  # Use 'balham' to match dark theme
                        )
                    else:
                        st.write("No matches found in API File.")

                    st.subheader("Dashboard File Matches")
                    if search_results.get('dashboard_matches'):
                        dashboard_matches_df = pd.DataFrame(search_results['dashboard_matches'])
                        gb = GridOptionsBuilder.from_dataframe(dashboard_matches_df)
                        gb.configure_pagination(paginationAutoPageSize=True)
                        gb.configure_side_bar()
                        gb.configure_default_column(resizable=True, min_width=100, wrapText=True, autoHeight=True)
                        grid_options = gb.build()
                        AgGrid(
                            dashboard_matches_df,
                            gridOptions=grid_options,
                            height=150,  # Increased height
                            # fit_columns_on_grid_load=True,
                            theme='balham'  # Use 'balham' to match dark theme
                        )
                    else:
                        st.write("No matches found in Dashboard File.")
                else:
                    st.error(f"Search failed: {search_response.json().get('detail', '')}")
            except Exception as e:
                st.error(f"An error occurred during search: {e}")

    # ---------------------- End Session ---------------------- #
    st.header("End Session")

    if st.button("End Session"):
        if session_id:
            with st.spinner("Ending session..."):
                try:
                    delete_response = requests.delete(f"{API_BASE_URL}/session/{session_id}")
                    if delete_response.status_code == 200:
                        st.success("Session ended successfully.")
                        st.session_state.clear()
                        # Removed st.experimental_rerun()
                    else:
                        st.error(f"Failed to end session: {delete_response.json().get('detail', '')}")
                except Exception as e:
                    st.error(f"An error occurred while ending session: {e}")
        else:
            st.warning("No active session to end.")

    # ---------------------- Footer ---------------------- #
    st.markdown("---")
    st.markdown("Developed with ❤️ using Streamlit and FastAPI")
