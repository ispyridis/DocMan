import re
from fpdf import FPDF
import os
from docx import Document
import pdfkit
import streamlit as st
from langdetect import detect
from collections import OrderedDict
from io import StringIO
import markdown
from datetime import datetime
from file_operations import list_templates, save_filled_template, parse_template
from ui_components import template_selection, format_selection, filename_input

# Added for ODT support
from odf.opendocument import OpenDocumentText
from odf.text import P

# Update this path to where your templates are stored
template_directory = os.path.join(os.path.dirname(__file__), 'Templates')

export_directory = os.path.join(os.path.dirname(__file__), 'exported_docs')

def filename_input(default_value="filled_document"):
    """
    Collect a filename from the user for saving the document.
    The default filename can be dynamically set based on the context.
    """
    return st.text_input("Enter filename for the saved document", value=default_value, key="filename")


def merge_templates(template_directory, selected_templates):
    """Merges the content of selected templates into a single string."""
    merged_content = ""
    for template_name in selected_templates:
        template_path = os.path.join(template_directory, template_name)
        with open(template_path, 'r', encoding='utf-8') as file:
            merged_content += file.read() + "\n\n"  # Add space between templates
    return merged_content

def convert_markdown_to_html(markdown_text):
    return markdown.markdown(markdown_text)

def convert_markdown_to_html_with_page_breaks(editable_template_content):
    # Replace horizontal rules in Markdown with HTML page break
    markdown_text_with_page_breaks = editable_template_content.replace('---', '<div style="page-break-after: always;"></div>')
    # Convert the modified Markdown text to HTML
    html_content_pb = markdown.markdown(markdown_text_with_page_breaks)
    return html_content_pb

def generate_html_with_utf8(content):
    # Basic HTML structure with UTF-8 encoding specified
    html_template = f"""
    <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body>
            {content}
        </body>
    </html>
    """
    return html_template

def convert_html_to_pdf_with_pdfkit(html_content_pbr, output_path):
    pdfkit.from_string(html_content_pbr, output_path)

def generate_download_link(output_path, format_selected):
    # Read the file into memory, depending on the format
    if format_selected in ['pdf', 'docx', 'odt']:
        with open(output_path, "rb") as file:
            btn = st.download_button(
                label="Download document",
                data=file,
                file_name=os.path.basename(output_path),
                mime="application/octet-stream"
            )
    elif format_selected == 'html' or format_selected == 'txt':
        with open(output_path, "r", encoding="utf-8") as file:
            btn = st.download_button(
                label="Download document",
                data=file.read(),
                file_name=os.path.basename(output_path),
                mime="text/html" if format_selected == 'html' else "text/plain"
            )


def run_app():
    st.title("Template Filler App")

    templates = list_templates(template_directory)
    selected_templates = template_selection(templates)

    if not selected_templates:
        st.error("Please select at least one template.")
        return

 # Determine the default filename based on the selected templates
    current_time_str = datetime.now().strftime("%y%m%d%H%M%S")
    if len(selected_templates) == 1:
        # If there's only one template, use its name in the proposed filename
        template_name = selected_templates[0].split('.')[0]  # Assuming the template name is the filename without the extension
        default_filename = f"{template_name}_{current_time_str}"
    else:
        # For multiple templates, suggest "Project_Name_Binder" as the filename
        default_filename = f"Project_Name_Binder_{current_time_str}"



    # Merge selected templates into a single document
    merged_template_content = merge_templates(template_directory, selected_templates)

    # Parse the merged content as if it were a single template
    fields, template_content = parse_template(merged_template_content)  # This will need adjustments to accept content directly

    for field in fields:
        if field not in st.session_state:
            st.session_state[field] = ""

    if not fields:
        st.write("No placeholders found in the template.")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        for field in fields:
            st.session_state[field] = st.text_input(label=field, value=st.session_state[field])

        current_date = datetime.now().strftime("%d/%m/%Y")
        if "[Today's Date]" in template_content:
            st.session_state["Today's Date"] = current_date

    with col2:
        st.write("Template Preview and Editor:")

        def generate_preview(template_content, fields):
            for field in fields:
                placeholder = f"[{field}]"
                template_content = template_content.replace(placeholder, st.session_state[field])
            return template_content

        updated_preview = generate_preview(template_content, fields)
        editable_template_content = st.text_area("Edit the template using Markdown (optional):", value=updated_preview, height=300)
    html_content_pbr=convert_markdown_to_html_with_page_breaks(editable_template_content)
    format_selected = format_selection()


    filename = filename_input(default_value=default_filename)

    if st.button("Save Document"):
        output_path = os.path.join(export_directory, f'{filename}.{format_selected}')
        if format_selected == 'pdf':
            html_content_pb_pdf = generate_html_with_utf8(convert_markdown_to_html(html_content_pbr))
            convert_html_to_pdf_with_pdfkit(html_content_pb_pdf, output_path)
            st.success('PDF generated and saved successfully!')
            # Function call to generate and display the download link
            generate_download_link(output_path, format_selected)            
        elif format_selected == 'docx':
            save_filled_template(editable_template_content, filename, format_selected, export_directory)
            st.success('DOCX document generated and saved successfully!')
            # Function call to generate and display the download link
            generate_download_link(output_path, format_selected)            
        elif format_selected == 'html':
            # Logic to save as HTML
            html_content = markdown.markdown(editable_template_content)
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(html_content)
            st.success('HTML document saved successfully!')
            # Function call to generate and display the download link
            generate_download_link(output_path, format_selected)            
        elif format_selected == 'odt':
            # Logic to save as ODT
            doc = OpenDocumentText()
            for paragraph in editable_template_content.split('\n'):
                para = P(text=paragraph)
                doc.text.addElement(para)
            doc.save(output_path)
            st.success('ODT document generated and saved successfully!')
            # Function call to generate and display the download link
            generate_download_link(output_path, format_selected)            
        else:
            save_filled_template(editable_template_content, filename, format_selected, export_directory)
            st.success("Document saved successfully.")
            # Function call to generate and display the download link
            generate_download_link(output_path, format_selected)
if __name__ == "__main__":
    run_app()
