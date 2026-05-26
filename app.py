import streamlit as st
from google import genai
from google.genai import types
from docx import Document
from io import BytesIO
from streamlit_mic_recorder import speech_to_text  # Nueva librería agregada

# Función para convertir el texto de la IA en un archivo Word (.docx)
def crear_archivo_word(texto_ficha):
    doc = Document()
    doc.add_heading("Ficha Clínica Estructurada", level=1)
    
    # Separar el texto por líneas para mantener los párrafos en Word
    lineas = texto_ficha.split("\n")
    for linea in lineas:
        if linea.strip():
            # Si es un título importante, darle un formato limpio
            if linea.startswith(("1.", "2.", "3.", "4.", "5.")):
                doc.add_heading(linea, level=2)
            else:
                doc.add_paragraph(linea)
                
    # Guardar en memoria para que Streamlit pueda descargarlo directamente
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# 1. Configuración de la página web
st.set_page_config(page_title="Asistente de Anamnesis Chile", page_icon="🩺")
st.title("🩺 Formateador de Anamnesis Clínica")
st.subheader("Ingrese los datos desordenados del paciente:")

# Inicializar la memoria del texto para que no se borre al interactuar
if "notas_paciente" not in st.session_state:
    st.session_state["notas_paciente"] = ""

# --- SECCIÓN DEL MICRÓFONO ---
st.write("🎙️ **Dictar notas por voz (Opcional):**")
texto_dictado = speech_to_text(
    start_prompt="🎤 Haz clic para hablar",
    stop_prompt="🛑 Detener y procesar",
    language="es",
    use_container_width=True,
    key="microfono_anamnesis"
)

# Si el usuario dictó algo, se acumula en la memoria de la sesión
if texto_dictado:
    if st.session_state["notas_paciente"]:
        st.session_state["notas_paciente"] += " " + texto_dictado
    else:
        st.session_state["notas_paciente"] = texto_dictado

# Entrada de texto del usuario (se autorellena si usó el micrófono)
datos_sucios = st.text_area(
    "Notas del paciente (puedes escribir aquí o editar lo que dictaste):", 
    value=st.session_state["notas_paciente"],
    height=150, 
    placeholder="Ej: paciente Juan 45 años dolor de cabeza..."
)

# Sincronizar el área de texto con la memoria de la sesión por si el usuario escribe a mano
st.session_state["notas_paciente"] = datos_sucios
# ------------------------------

# 2. Conexión con Gemini al presionar el botón
if st.button("Ordenar Ficha Clínica"):
    if not datos_sucios.strip():
        st.warning("Por favor, ingrese datos antes de continuar.")
    else:
        with st.spinner("Gemini está estructurando la información médica..."):
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            
            mi_prompt_medico = (
                "Actúa como un experto en medicina y gestión de fichas clínicas en Chile. "
                "Tu tarea es tomar un bloque de texto desordenado proveniente de una anamnesis / entrevista clínica "
                "y transformarlo en una Ficha Clínica estructurada, profesional y limpia.\n\n"
                "Utiliza la siguiente estructura:\n"
                "1. IDENTIFICACIÓN DEL PACIENTE\n"
                "2. ANAMNESIS ANTECEDENTES (Médicos, quirúrgicos, fármacos, lesiones previas)\n"
                "3. ANAMNESIS PRÓXIMA (Motivo de consulta principal, descripción del dolor: tipo, factores que agravan o mitigan)\n"
                "4. EVALUACIÓN GENERAL DE SÍNTOMAS (Resumen técnico de la molestia reportada)\n"
                "5. OBJETIVOS TERAPÉUTICOS PROPUESTOS (Genera 3 objetivos basados en el texto: a corto, mediano y largo plazo)\n\n"
                "Reglas:\n"
                "- Traduce el lenguaje coloquial del paciente a terminología médica.\n"
                "- Mantén un tono formal, técnico y conciso.\n"
                "- Si falta información crítica, añade una sección final de 'Notas: Sugerencia de datos a evaluar en la sesión presencial'."
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=datos_sucios,
                config=types.GenerateContentConfig(system_instruction=mi_prompt_medico),
            )
            
            # Guardar el resultado en la sesión para que el botón de descarga funcione correctamente
            st.session_state["ficha_texto"] = response.text
            st.success("¡Ficha generada con éxito!")

# 3. Mostrar el resultado y el botón de descarga si la ficha ya existe
if "ficha_texto" in st.session_state:
    st.markdown("---")
    st.markdown("### 📋 Ficha Clínica Estructurada")
    st.write(st.session_state["ficha_texto"])
    
    # Crear el archivo Word a partir del texto generado
    archivo_word = crear_archivo_word(st.session_state["ficha_texto"])
    
    # Botón nativo de descarga de Streamlit
    st.download_button(
        label="📥 Descargar Ficha en Word (.docx)",
        data=archivo_word,
        file_name="ficha_clinica.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
