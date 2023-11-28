import pandas as pd
import streamlit as st
from unidecode import unidecode
from collections import Counter
import plotly.express as px

# Desglosar la lista de idiomas

def procesar_idiomas(df):
    idiomas_desglosados = df['idiomas_que_habla'].explode()
    # Crear un DataFrame con información para el gráfico interactivo
    df_interactivo = pd.DataFrame({
        'Nombre': df['nombres'].repeat(df['idiomas_que_habla'].apply(len)),
        'Idioma': idiomas_desglosados
    })

    # Filtrar datos "sin información"
    df_interactivo = df_interactivo[(df_interactivo['Idioma'] != 'sin informacion') & (df_interactivo['Idioma'] != 'espanol') & (df_interactivo['Idioma'] != 'chileno')]

    # Crear el gráfico interactivo
    fig = px.bar(df_interactivo, x='Idioma', color='Nombre',
                labels={'Nombre': 'Candidato'},
                title='Distribución de Idiomas (Interactivo)',
                hover_data={'Nombre': True, 'Idioma': False})

    # Configurar diseño
    fig.update_layout(barmode='stack')

    # Mostrar el gráfico interactivo
    st.plotly_chart(fig)

def procesar_df(df):
    df = df.fillna("sin informacion")

    columns_to_fill = ['universidad_o_instituto','anno_de_termino_de_estudios','habilidades_tecnicas','habilidades_blandas','cargo_experiencia_laboral','empresa_en_la_que_trabajo','certificados','idiomas_que_habla','nivel_de_idioma','url']
    df[columns_to_fill] = df[columns_to_fill].apply(lambda x: x.str.split(', '))

    # Calcular la cantidad de elementos en cada celda
    df['cantidad_certificados'] = df['certificados'].apply(lambda x: len(x) if isinstance(x, list) and x != ['sin informacion'] else 0)
    df['cantidad_idiomas'] = df['idiomas_que_habla'].apply(lambda x: len(x) if isinstance(x, list) and x != ['sin informacion'] else 0)
    df['cantidad_experiencia_laboral'] = df['cargo_experiencia_laboral'].apply(lambda x: len(x) if isinstance(x, list) and x != ['sin informacion'] else 0)
    df['cantidad_empresas'] = df['empresa_en_la_que_trabajo'].apply(lambda x: len(x) if isinstance(x, list) and x != ['sin informacion'] else 0)

    columnas_en_lista = ['universidad_o_instituto','habilidades_tecnicas','habilidades_blandas','cargo_experiencia_laboral','empresa_en_la_que_trabajo','certificados','idiomas_que_habla','nivel_de_idioma','url']
    df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
    df = df.applymap(lambda x: [elem.lower() if isinstance(elem, str) else elem for elem in x] if isinstance(x, list) else x)

    df['nombres'] = df['nombres'].apply(lambda x: x.title())

    # Elimina las tildes de la columna "idiomas"
    df['idiomas_que_habla'] = df['idiomas_que_habla'].apply(lambda x: [unidecode(i) for i in x])
    st.dataframe(df)
    procesar_idiomas(df)

