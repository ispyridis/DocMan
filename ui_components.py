import streamlit as st
import os

def template_selection(templates):
    selected_templates = st.multiselect("Select templates:", options=templates, key="template_selection_key")
    return selected_templates

def collect_user_inputs(fields):
    """
    Dynamically generate text input fields for each placeholder field found in the template.
    Collects and returns the user inputs in a dictionary.
    """
    user_inputs = {}
    for field in fields:
        # Use the field as the key and the user input as the value
        user_inputs[field] = st.text_input(f"Enter value for {field}", key=field)
    return user_inputs

def format_selection():
    format_options = ['pdf', 'docx', 'html', 'odt', 'txt']  # Ensure 'txt' is included alongside the new formats
    format_selected = st.selectbox("Select the format to save the document:", format_options)
    return format_selected

def filename_input(default_value="filled_document"):
    """
    Collect a filename from the user for saving the document.
    Provides a default filename which can be overridden by the user.
    """
    return st.text_input("Enter filename for the saved document", value=default_value, key="filename")