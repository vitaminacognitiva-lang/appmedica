import streamlit as st
from google import genai
from google.genai import types
from docx import Document
from io import BytesIO
from streamlit_mic_recorder import speech_to_text  # Nueva librería agregada


        file_name="ficha_clinica.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
