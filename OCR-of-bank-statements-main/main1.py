import streamlit as st
import os
import io
import tempfile
import fitz
from PIL import Image
import pandas as pd
import base64
import requests
from dotenv import load_dotenv
import random
import zipfile
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from document_processor import DocumentProcessor
from visualizations import visualize_comparative_data, process_comparative_data, create_interactive_pie_chart

# Initialize session state
if 'processed_dfs' not in st.session_state:
    st.session_state.processed_dfs = []
if 'temp_image_paths' not in st.session_state:
    st.session_state.temp_image_paths = []
if 'processing_errors' not in st.session_state:
    st.session_state.processing_errors = []
if 'cloudinary_images' not in st.session_state:
    st.session_state.cloudinary_images = []

# Load environment variables and configure Cloudinary
load_dotenv()




def create_requests_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def download_image(url, session=None):
    if session is None:
        session = requests.Session()
    try:
        response = session.get(url, timeout=(10, 30))
        return response.content if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None





def create_zip_file(images):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for idx, image in enumerate(images):
            zip_file.writestr(image['name'], image['content'])
    return zip_buffer.getvalue()


def process_uploaded_files(uploaded_files, processor, selected_doc_type):
    if not st.session_state.processed_dfs:  # Only process if not already processed
        for uploaded_file in uploaded_files:
            try:
                with tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                    temp_file.write(uploaded_file.getvalue())
                    temp_path = temp_file.name

                if os.path.splitext(uploaded_file.name)[1].lower() == ".pdf":
                    with fitz.open(stream=uploaded_file.getvalue(), filetype="pdf") as doc:
                        page = doc[0]
                        pix = page.get_pixmap()
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        temp_image_path = f"{temp_path}_page_0.png"
                        img.save(temp_image_path)
                        st.session_state.temp_image_paths.append(temp_image_path)
                else:
                    st.session_state.temp_image_paths.append(temp_path)

                df, _ = processor.extract_parameters(st.session_state.temp_image_paths[-1], selected_doc_type)

                if df is not None and all(col in df.columns for col in ["Parameter", "Value"]):
                    df["Document"] = uploaded_file.name if len(uploaded_files) > 1 else "Default Document"
                    st.session_state.processed_dfs.append(df)
                else:
                    st.session_state.processing_errors.append(f"Invalid DataFrame format for {uploaded_file.name}")

            except Exception as e:
                st.session_state.processing_errors.append(f"Error processing {uploaded_file.name}: {str(e)}")


def main():
    st.set_page_config(page_title="Financial Document Analyzer", layout="wide")

    with st.sidebar:
        st.title("Financial Document Analyzer")
        document_types = {
            "Bank Statement": "bank_statements",
            "Cheques": "cheques",
            "Profit and Loss Statement": "profit_loss_statements",
            "Salary Slip": "salary_slips",
            "Transaction History": "transaction_history",
        }
        selected_doc_type = st.selectbox("Select Document Type", list(document_types.keys()))

        graph_types = ["Bar Chart", "Pie Chart"]
        data_source = st.radio("Select Data Source", ["Upload Files"])
        selected_graph_type = st.selectbox("Select Graph Type", graph_types)

        if st.button("Clear All Data"):
            st.session_state.processed_dfs = []
            st.session_state.temp_image_paths = []
            st.session_state.processing_errors = []
            st.rerun()

    st.header(f"{selected_doc_type} Analysis")
    processor = DocumentProcessor()

    # Manual Upload Section
    uploaded_files = st.file_uploader(
        f"Upload {selected_doc_type}",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        process_uploaded_files(uploaded_files, processor, selected_doc_type)

    # Display errors if any
    for error in st.session_state.processing_errors:
        st.error(error)

    # Process and visualize data
    if st.session_state.processed_dfs:
        combined_df = pd.concat(st.session_state.processed_dfs, ignore_index=True)

        st.subheader("Extracted Parameters")
        st.dataframe(combined_df)

        if selected_graph_type == "Bar Chart":
            figs = visualize_comparative_data(combined_df)
            if figs:
                for fig in figs:
                    st.plotly_chart(fig, use_container_width=True)

        elif selected_graph_type == "Pie Chart":
            if len(st.session_state.processed_dfs) > 1:
                _, common_params = process_comparative_data(combined_df)
                selected_param = st.selectbox("Choose a parameter to visualize", common_params, key='pie_param')
                pie_fig = create_interactive_pie_chart(combined_df, selected_param)
            else:
                pie_fig = create_interactive_pie_chart(combined_df)

            if pie_fig:
                st.plotly_chart(pie_fig, use_container_width=True)

        # Download CSV option
        csv_buffer = io.StringIO()
        combined_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download Parameters CSV",
            data=csv_buffer.getvalue(),
            file_name=f"{selected_doc_type.lower().replace(' ', '_')}_parameters.csv",
            mime="text/csv",
        )

        # Image Query Section
        st.divider()
        st.subheader("Ask a Question About the Document")

        if st.session_state.temp_image_paths:
            if len(st.session_state.temp_image_paths) > 1:
                selected_image = st.selectbox(
                    "Select Image to Query",
                    [f"Document {i + 1}" for i in range(len(st.session_state.temp_image_paths))],
                    key='query_image'
                )
                image_index = [f"Document {i + 1}" for i in range(len(st.session_state.temp_image_paths))].index(
                    selected_image)
                current_image_path = st.session_state.temp_image_paths[image_index]
            else:
                current_image_path = st.session_state.temp_image_paths[0]

            user_query = st.text_input("Enter your question about the document:", key='user_query')

            if user_query:
                try:
                    with open(current_image_path, "rb") as img_file:
                        encoded_image = base64.b64encode(img_file.read()).decode("utf-8")

                    response = processor.client.chat.completions.create(
                        model=processor.model,
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_query},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                            ]
                        }],
                        max_tokens=500,
                        temperature=0.3
                    )

                    st.write(response.choices[0].message.content)

                except Exception as e:
                    st.error(f"Error processing query: {e}")


if __name__ == "__main__":
    main()
