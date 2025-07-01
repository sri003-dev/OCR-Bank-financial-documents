Financial Document Analyzer
A Streamlit-based web application that leverages LLMs to extract and visualize key financial metrics from documents like Bank Statements, Salary Slips, Cheques, Profit & Loss Statements, and Transaction Histories using multimodal AI capabilities.

🚀 Features
📄 Document Upload: Upload multiple image or PDF documents.

🧠 LLM-Powered Extraction: Uses Meta LLaMA 3.2 Vision model (via Together API) to extract numeric parameters.

📊 Data Visualization: View comparative Bar Charts and Pie Charts of extracted financial values.

🔍 Ask Questions: Query the document using natural language and get visual context-aware answers.

💾 Export: Download extracted data as a CSV file.

🧠 Multimodal AI: Supports image + text prompt completion.

🧱 Tech Stack
Frontend: Streamlit

Visualization: Plotly

OCR & PDF Processing: PyMuPDF (fitz), Pillow

Backend Model: Meta-LLaMA Vision via Together.ai

Cloud Image Retrieval (Optional): Cloudinary

Environment Management: python-dotenv

