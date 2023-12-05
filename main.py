import streamlit as st
import os
import shutil
import pandas as pd
from utils import image_to_text, document_to_text, normalize_text ,procesar_cv
from df_utils import main_utils

def create_directories():
    # Crear un directorio temporal para almacenar los archivos subidos
    if not os.path.exists("temp"):
        os.makedirs("temp")

    # Crea un directorio para almacener los documentos extraidos
    if not os.path.exists("output"):
        os.makedirs("output")

def process_uploaded_files(uploaded_files):
    for uploaded_file in uploaded_files:
        with open(os.path.join("temp", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.read())
        print('Transformación a texto del archivo: ', uploaded_file.name)
        if uploaded_file.name.endswith(('.jpg', '.jpeg', '.png')):
            # Extrae texto de las imagenes
            image_to_text("temp", "output")
            # image_to_text("temp", "output")
        elif uploaded_file.name.endswith(('.pdf', '.doc', '.docx', '.txt')):
            # Extrae texto de los documentos
            document_to_text("temp", "output")
        else:
            # Muestra mensaje de error
            st.warning(f"El archivo {uploaded_file.name} no es archivo compatible")

def main():
    # Titulo página
    st.set_page_config(page_title="Extract Data!!!", page_icon=":page_facing_up:", layout="wide")
    # Titulo principal
    st.title(" :page_facing_up: Extracción de métricas CV")
    st.markdown('<style>div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)
    # Campo para cargar archivos
    uploaded_files = st.file_uploader("Cargar archivos", accept_multiple_files=True)

    # # Verifica si se han subido archivos
    # if uploaded_files is not None and len(uploaded_files)>0:
    #     if st.button("Procesar CV"):
    #         st.write("Procesando archivos...")
    #         process_uploaded_files(uploaded_files)
    #         shutil.rmtree("temp")

    #         # Mostrar mensaje de éxito
    #         st.success(f"Archivos transformados con éxito!")
    #         normalize_text("output")

    #         # Procesa los currículum
    #         procesar_cv("output")
    #         # Elimina archivos temporales
    #         # shutil.rmtree("output")

    # else:
    #     st.warning("Por favor, carga al menos un archivo.")
    #     st.button("Procesar CV",disabled=True)
    # open a dataframe in csv with pandas
    df = pd.read_csv('./cv_data.csv')
    main_utils(df)
    # procesar_df(df)


if __name__ == "__main__":
    create_directories()
    main()