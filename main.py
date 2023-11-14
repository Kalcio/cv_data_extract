#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import os
import re
import csv
import pandas as pd
from utils import image_to_text, pdf_to_text, normalize_text ,procesar_cv, extraer_datos_cv
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Titulo página
st.set_page_config(page_title="Extract Data!!!", page_icon=":page_facing_up:", layout="wide")

st.title(" :page_facing_up: Extracción de métricas CV")
st.markdown('<style>div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)

# df = pd.read_csv('./cv_datas.csv')
# st.dataframe(df)

# languages = ['Español', 'Ingles', 'Aleman', 'Frances', 'Chino']

# Crear un directorio temporal para almacenar los archivos
if not os.path.exists("temp"):
    os.makedirs("temp")

if not os.path.exists("output"):
    os.makedirs("output")

# Cargar archivos CV
uploaded_files = st.file_uploader("Cargar archivos", accept_multiple_files=True)

if uploaded_files is not None:
  if st.button("Procesar CV"):
    for uploaded_file in uploaded_files:
      with open(os.path.join("temp", uploaded_file.name), "wb") as f:
        f.write(uploaded_file.read())

      if uploaded_file.name.endswith(('.jpg', '.jpeg', '.png')):
        # Procesar las imagenes
        image_to_text("temp", "output")
      elif uploaded_file.name.endswith('.pdf'):
        # Procesar PDF
        pdf_to_text("temp", "output")
      else:
        st.warning(f"El archivo {uploaded_file.name} no es archivo compatible")
      # Eliminar archivo temporal
      os.remove(os.path.join("temp", uploaded_file.name))

    # Mostrar mensaje de éxito
    st.write(f"Archivos procesados con éxito!")
    
    normalize_text("output")
    st.write("Textos normalizados con éxito!")

    # DESCOMENTAAAAR
    procesar_cv("output")