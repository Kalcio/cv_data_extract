import os
import re
import textract
import streamlit as st
import json
import pandas as pd
from paddleocr import PaddleOCR
from unicodedata import normalize
from pdfminer.high_level import extract_text
from dotenv import load_dotenv
from openai import OpenAI
import spacy

# Cargar el modelo de lenguaje de SpaCy con el entity_ruler
nlp = spacy.load("model_skills")

# Load environment variables from .env file
load_dotenv()

# Extrae texto de las imagenes
def image_to_text(folder_path, output_folder):
    ocr = PaddleOCR(use_angle_cls=True, use_gpu=False, lang='es')

    for filename in os.listdir(folder_path):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            # Ruta completa de la imagen de entrada
            image_path = os.path.join(folder_path, filename)

            # Obtener el texto de la imagen
            result = ocr.ocr(image_path, cls=False)
        
            output_filename = os.path.splitext(filename)[0] + '.txt'
            output_path = os.path.join(output_folder, output_filename)
            
            # Se crea el archivo de texto
            with open(output_path, 'w', encoding='utf-8') as f:
                for line in result:
                    f.write(line[1][0] + ' ')

# Extrae textos de los documentos 
def document_to_text(folder_path, output_folder):
    for filename in os.listdir(folder_path):
        if filename.endswith(('.pdf', '.doc', '.docx')):
            # Ruta completa de la imagen de entrada
            document_path = os.path.join(folder_path, filename)
            try:
                if filename.endswith('.pdf'):
                    # Se extrae el texto
                    result = extract_text(document_path)
                else:
                    # Se extrae el texto
                    result = textract.process(document_path)
            except Exception as e:
                st.error(f"Error al procesar el archivo {filename}: {e}")
                continue
                
            # Genera el nombre del archivo de salida con extensión .txt
            output_filename = os.path.splitext(filename)[0] + '.txt'
            output_path = os.path.join(output_folder, output_filename)
            
            # Se crea el archivo de texto
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result if filename.endswith('.pdf') else result.decode('utf-8'))
            
# Normaliza el texto (elimina tildes)
def normalize_text(folder_data):
    for filename in os.listdir(folder_data):
        if filename.endswith('.txt'):
            # Ruta completa de la imagen de entrada
            file_path = os.path.join(folder_data, filename)
            
            # Se lee el archivo de texto
            with open(file_path, 'r', encoding='utf-8') as input_file:
                text = input_file.read()
                # Se transforman las letras con tildes a su equivalente
                text = re.sub(
                    r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+", r"\1",
                    normalize("NFD", text), 0, re.I
                )
              
            with open(file_path, 'w', encoding='utf-8') as output_file:
                output_file.write(text)
            
# Función para extraer los datos de los currículums
def extraer_datos_cv(client, cv_text):
    # Se envía el texto a OpenAI para extraer los datos
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
          {"role": "user", "content": f"Necesito que extraigas del texto los siguientes datos y me los entregues en formato diccionario python: nombres, telefono, email, direccion, titulo_actual_o_al_egresar, universidad_o_instituto, anno_de_termino_de_estudios, habilidades_tecnicas, habilidades_blandas, cargo_experiencia_laboral, empresa_en_la_que_trabajo, certificados, idiomas_que_habla, nivel_de_idioma, URL. Si no tiene alguno de estos dejarlo vacío, si hay más de un dato separarlo por coma. Texto: {cv_text}"}
        ],
        temperature=0.2,
        max_tokens=800
    )
    # Se transforma el texto de respuesta a un diccionario
    datos = json.loads(response.choices[0].message.content)

    doc = nlp(cv_text)

    datos['habilidades_tecnicas'] = [ent.text for ent in doc.ents if ent.label_ == 'SKILLS']

    return datos

def guardar_resultados(df):
    # Crear un directorio temporal para almacenar los archivos subidos
    if not os.path.exists("export"):
        os.makedirs("export")

    df.to_excel('export/cv_datas.xlsx', index=False)
    df.to_csv('export/cv_datas.csv', index=False)
    df.to_json('export/cv_datas.json', orient='records')
    print("Exportación finalizada")

# Función para procesar los currículums
def procesar_cv(folder_data):
    client = OpenAI()

    print("Inicio procesamiento CV")
    st.write("Procesando CV...")
    resultados = []

    for filename in os.listdir(folder_data):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_data, filename)
            print(f"Procesando archivo {filename}")
            # Se lee el archivo de texto
            with open(file_path, "r", encoding="utf-8") as file:
                cv_text = file.read()
                datos = extraer_datos_cv(client, cv_text)
                resultados.append(datos)

    print("Fin procesamiento CV")
    st.write("CV Procesados")

    df = pd.DataFrame(resultados)
    guardar_resultados(df)

    st.dataframe(df)