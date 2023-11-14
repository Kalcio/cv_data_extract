import os
import re
import csv
import pandas as pd
import streamlit as st
from paddleocr import PaddleOCR
from unicodedata import normalize
from pdfminer.high_level import extract_text
from dotenv import load_dotenv
from openai import OpenAI
import json

# Load environment variables from .env file
load_dotenv()

# Ruta a la carpeta que contiene los archivos PDF
folder_path = './Data'
output_folder = './Data_extract'

os.makedirs(output_folder, exist_ok=True)

# Función para guardar texto en un archivo de texto
def save_text_to_file(text, output_directory, base_filename):
    output_filename = os.path.join(output_directory, base_filename + '.txt')
    with open(output_filename, 'w', encoding='utf-8') as output_file:
        output_file.write(text)

def image_to_text(folder_path, output_folder):
    ocr = PaddleOCR(use_angle_cls=True, use_gpu=True, lang='es')

    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            # Ruta completa de la imagen de entrada
            image_path = os.path.join(folder_path, filename)

            # Obtener el texto de la imagen
            result = ocr.ocr(image_path, cls=False)
        
            output_filename = os.path.splitext(filename)[0] + '.txt'
            output_path = os.path.join(output_folder, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for line in result:
                    f.write(line[1][0] + ' ')

def pdf_to_text(folder_path, output_folder):
    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            # Ruta completa de la imagen de entrada
            pdf_path = os.path.join(folder_path, filename)

            result = extract_text(pdf_path)
            
            output_filename = os.path.splitext(filename)[0] + '.txt'
            output_path = os.path.join(output_folder, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result)

def normalize_text(folder_data):
  for filename in os.listdir(folder_data):
    if filename.endswith('.txt'):
      # Ruta completa de la imagen de entrada
      file_path = os.path.join(folder_data, filename)
      
      with open(file_path, 'r', encoding='utf-8') as input_file:
        text = input_file.read()
        text = re.sub(
            r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+", r"\1",
            normalize("NFD", text), 0, re.I
        )
      
      with open(file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(text)
            
# Función para extraer los datos de los currículums
def extraer_datos_cv(client, cv_text):
  response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "user", "content": f"Necesito que extraigas del texto los siguientes datos y me los entregues en formato diccionario python: nombres, telefono, email, direccion, titulo actual o al egresar, universidad o instituto, año de termino de estudios, habilidades técnicas, habilidades blandas, cargo experiencia laboral, empresa en la que trabajo, certificados, idiomas que habla, nivel de idioma, URL. Si no tiene alguno de estos dejarlo vacío, si hay más de un dato separarlo por coma. Texto: {cv_text}"}
    ],
    temperature=0.2,
    max_tokens=800
  )
  # datos = {}
  # st.write(response.choices[0].message.content)

  datos = json.loads(response.choices[0].message.content)

  return datos

def procesar_cv(folder_data):
  client = OpenAI()

  st.write("Procesando CV")
  resultados = []

  for filename in os.listdir(folder_data):
    if filename.endswith(".txt"):
      file_path = os.path.join(folder_data, filename)
      with open(file_path, "r", encoding="utf-8") as file:
        cv_text = file.read()
        datos = extraer_datos_cv(client, cv_text)
        resultados.append(datos)
    
  st.write("CV Procesados")

  df = pd.DataFrame(resultados)

  st.dataframe(df)
  df.to_excel('cv_datas.xlsx', index=False)
  df.to_csv('cv_datas.csv', index=False)
  df.to_json('cv_datas.json', orient='records')
  st.write("Proceso finalizado!!!")