import pandas as pd
import streamlit as st
from unidecode import unidecode
from ast import literal_eval
from collections import Counter
from wordcloud import WordCloud
from io import BytesIO
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
import plotly.express as px
import matplotlib.pyplot as plt
import spacy
import re
import os
import nltk

result_file_path = "export/cv_datas.csv"
nltk.download('stopwords')
nltk.download('wordnet')

def procesar_formato_datos(df):
    # Convertir todas los datos a minúsculas
    df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
    # Formatear datos nombres a mayúsculas
    df['nombres'] = df['nombres'].apply(lambda x: x.title())

    # Quitar tildes de la columna 'idiomas_que_habla'
    df['idiomas_que_habla'] = df['idiomas_que_habla'].apply(lambda x: unidecode(x) if isinstance(x, str) else x)
    
    # Aplicar title() a la columna 'empresa_en_la_que_trabajo' y manejar valores nulos
    df['universidad_o_instituto'] = df['universidad_o_instituto'].apply(lambda x: x.title() if pd.notna(x) else x)

    df['titulo_actual_o_al_egresar'] = df['titulo_actual_o_al_egresar'].apply(lambda x: x.title() if pd.notna(x) else x)

    # Aplicar title() a la columna 'empresa_en_la_que_trabajo' y manejar valores nulos
    df['empresa_en_la_que_trabajo'] = df['empresa_en_la_que_trabajo'].apply(lambda x: x.title() if pd.notna(x) else x)

    return df

def extraer_habilidades_certificados(certificaciones):
    # Cargar el modelo de lenguaje de SpaCy con el entity_ruler
    nlp = spacy.load("model_skills")

    habilidades_certificados = []
    for certificacion in certificaciones:
        doc = nlp(certificacion)
        for ent in doc.ents:
            if ent.label_ == 'SKILLS':
                habilidades_certificados.append(ent.text)
    return habilidades_certificados

def normalizar_palabras(lista_frases):
    lemmatizer = WordNetLemmatizer()
    
    # Aplicar lematización y filtrar palabras con menos de 4 caracteres
    palabras = [palabra.lower() for frase in lista_frases for palabra in frase.split() if len(palabra) >= 6 and palabra.lower() not in stopwords.words('spanish')]
    lemas = [lemmatizer.lemmatize(palabra) for palabra in palabras]
    
    return ' '.join(lemas)

def extraer_habilidades_blandas(df):
    # Aplicar la función a la columna 'Texto'
    df['habilidades_blandas_lematizadas'] = df['habilidades_blandas'].apply(normalizar_palabras)

    # Concatenar todas las habilidades blandas lematizadas en un solo texto
    text = ' '.join(df['habilidades_blandas_lematizadas'])

    # Crear la nube de palabras
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

    # Mostrar la nube de palabras
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Nube de Palabras de Habilidades Blandas')
    st.pyplot(plt)

def procesar_columnas(df):
    # Columnas a enlistar
    columns_to_process = ['telefono', 'email', 'idiomas_que_habla', 'certificados', 'habilidades_blandas', 'titulo_actual_o_al_egresar', 'universidad_o_instituto', 'anno_de_termino_de_estudios', 'cargo_experiencia_laboral', 'empresa_en_la_que_trabajo', 'nivel_de_idioma', 'URL']
    # Función para manejar NaN y enlistar
    for column in columns_to_process:
        df[column] = df[column].apply(lambda x: [] if pd.isna(x) else [data.strip() for data in x.split(',')] if isinstance(x, str) else [])

    df['habilidades_certificados'] = df['certificados'].apply(extraer_habilidades_certificados)
    return df

def procesar_habilidades_tecnicas(df):
    # Convertir la cadena de lista a una lista de Python
    df['habilidades_tecnicas'] = df['habilidades_tecnicas'].apply(lambda x: literal_eval(x) if isinstance(x, str) else x)
    return df

def calcular_frecuencia(df):
    # Explode y calcular para las columnas relevantes
    columns_to_explode = ['idiomas_que_habla', 'certificados', 'habilidades_blandas', 'habilidades_tecnicas']
    for column in columns_to_explode:
        df_exploded = df.explode(column).dropna(subset=[column])
        count_column = df_exploded.groupby('nombres').size()
        df = df.join(count_column.rename(f'cantidad_{column}'), on='nombres').fillna({f'cantidad_{column}': 0})
    
    return df

def quitar_datos_no_deseado(lista_idiomas):
    idiomas_a_ignorar = ['sin informacion', 'espanol', 'chileno']
    return [idioma for idioma in lista_idiomas if idioma.lower() not in idiomas_a_ignorar]

def filtrar_idiomas(df):
    # Filtrar datos no deseados y NaN
    df['idiomas_que_habla'] = df['idiomas_que_habla'].apply(quitar_datos_no_deseado)

    # Obtener todos los idiomas únicos después de la limpieza
    todos_idiomas = sorted(set(idioma for sublist in df['idiomas_que_habla'] for idioma in sublist))

    return todos_idiomas

def obtener_filtros_postulante(df):
    idiomas_seleccionados = filtrar_idiomas(df)

    # Establecer el ancho deseado para la barra lateral
    st.markdown(
        """
        <style>
            .sidebar .sidebar-content {
                width: 250px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.title('Filtrado de candidatos')
    
    unique_skills = df['habilidades_tecnicas'].explode().unique()
    non_nan_skills = [skill for skill in unique_skills if pd.notna(skill)]
    sorted_skills = sorted(non_nan_skills)

    # Sidebar con el menú de habilidades
    selected_skills = st.sidebar.multiselect('Selecciona habilidades técnicas', sorted_skills)
    # Sidebar con el menú de idiomas
    selected_languages = st.sidebar.multiselect('Selecciona idiomas', idiomas_seleccionados)

    return selected_skills, selected_languages

def aplicar_filtrado(df, selected_skills, selected_languages):
    # Lógica de filtrado
    if selected_skills or selected_languages:
        # Filtrar el DataFrame según habilidades o idiomas seleccionados
        filtered_df = df[
            ((df['habilidades_tecnicas'].apply(lambda skills: any(skill in selected_skills for skill in skills)) if selected_skills else False)
            | (df['idiomas_que_habla'].apply(lambda languages: any(language in selected_languages for language in languages)) if selected_languages else False))
        ]
    else:
        # Si no se selecciona ningún filtro, mostrar todos los datos
        filtered_df = df

    return filtered_df

def reorganizar_dataframe(filtered_df, selected_skills, df):
    # Crear una columna con las habilidades únicas
    filtered_df['habilidades_tecnicas_unicas'] = df['habilidades_tecnicas'].apply(lambda x: list(set(x)))
    df['habilidades_tecnicas_unicas'] = df['habilidades_tecnicas'].apply(lambda x: list(set(x)))

    # Cuenta la frecuencia de cada habilidad para cada postulante
    for habilidad in selected_skills:
        filtered_df[habilidad] = df['habilidades_tecnicas'].apply(lambda x: Counter(x)[habilidad] if isinstance(x, list) else 0)

    # Reorganiza el DataFrame para tener un formato largo
    df_long = pd.melt(filtered_df, id_vars=['nombres'], value_vars=selected_skills,
                      var_name='Habilidad', value_name='Frecuencia')

    # Filtrar los nombres que tienen relación con los filtros seleccionados
    df_long = df_long[df_long['nombres'].isin(filtered_df['nombres'].unique())]

    return df_long

def extraer_anno_egreso(texto):
    anos = re.findall(r'\b\d{4}\b', str(texto))
    anos = [int(ano) for ano in anos]  # Convertir a enteros
    return max(anos, default=None)

# Función para contar la cantidad de elementos en una lista
def contar_elementos(lista):
    return len(lista)

def grafico_idiomas(df_filtrado):
    df_exploded = df_filtrado.explode('idiomas_que_habla')
    df_exploded = df_exploded[~df_exploded['idiomas_que_habla'].isna()]
    idiomas_seleccionados = sorted(df_exploded['idiomas_que_habla'].unique())
    
    # Filtrar el DataFrame según los idiomas seleccionados
    df_idioma = df_exploded[df_exploded['idiomas_que_habla'].isin(idiomas_seleccionados)]

    # Crear el gráfico interactivo
    fig_idiomas = px.bar(df_idioma, x='idiomas_que_habla', color='nombres',
                        labels={'idiomas_que_habla': 'Idioma', 'nombres': 'Candidato', 'count': 'Cantidad'},
                        title='Distribución de Idiomas',
                        hover_data={'nombres': True, 'idiomas_que_habla': False},
                        # category_orders={'idiomas_que_habla': sorted(df_exploded['idiomas_que_habla'].unique())},
                        color_discrete_sequence=px.colors.qualitative.Set1)

    # Configurar diseño
    fig_idiomas.update_layout(barmode='stack', width=600)
    # Mostrar el gráfico interactivo en Streamlit
    st.plotly_chart(fig_idiomas)

def generar_nube_palabras(df_filtrado):
    all_skills = [skill.lower() for sublist in df_filtrado['habilidades_tecnicas_unicas'] for skill in sublist]
    text = ' '.join(all_skills)
    wordcloud = WordCloud(width=600, height=400, background_color='white').generate(text)
    img_bytes = BytesIO()
    wordcloud.to_image().save(img_bytes, format='PNG')
    st.image(img_bytes, caption='Nube de palabras de habilidades técnicas de los postulantes')

def grafico_certificados(df_filtrado, habilidades_seleccionadas):
    df_exploded = df_filtrado.explode('habilidades_certificados')
    df_exploded = df_exploded[~df_exploded['habilidades_certificados'].isna()]
    df_exploded = df_exploded[df_exploded['habilidades_certificados'] != 'certificate']    # Filtrar el DataFrame según las habilidades seleccionadas
    
    if habilidades_seleccionadas:
        df_certificados = df_exploded[df_exploded['habilidades_certificados'].isin(habilidades_seleccionadas)]
    else:
        df_certificados = df_exploded
    # Crear el gráfico interactivo solo si hay datos después de aplicar el filtro
    if not df_certificados.empty:
        # Obtener la frecuencia de cada valor único
        frecuencia_valores_grupo = df_exploded.groupby(['nombres', 'habilidades_certificados']).size().reset_index(name='Cantidad')

        # Crear el gráfico interactivo
        fig_certificados = px.bar(frecuencia_valores_grupo, x='habilidades_certificados', y='Cantidad', color='nombres',
                                  labels={'habilidades_certificados': 'Habilidades', 'nombres': 'Candidato', 'count': 'Cantidad'},
                                  title=f'Distribución de certificaciones para las habilidades técnicas',
                                  hover_data={'nombres': True, 'habilidades_certificados': False},
                                  color_discrete_sequence=px.colors.qualitative.Set1)

        # Configurar diseño
        fig_certificados.update_layout(barmode='stack', width=600,yaxis=dict(tickmode='linear', tickformat='d'))
        # Mostrar el gráfico interactivo en Streamlit
        st.plotly_chart(fig_certificados)
    else:
        st.warning("No hay certificaciones para las habilidades seleccionadas")

def grafico_radar_skills(df_long):
    # Crea el gráfico interactivo de radar con Plotly Express y asigna un color a cada postulante
    fig = px.line_polar(df_long, r='Frecuencia', theta='Habilidad', line_close=True,
                        range_r=[0, df_long['Frecuencia'].max()],
                        labels={'Frecuencia': 'Frecuencia de Habilidad'},
                        title='Frecuencia de Habilidades Técnicas por Postulante')

    # Añadir puntos al gráfico de radar
    scatter_trace = px.scatter_polar(df_long, r='Frecuencia', theta='Habilidad',
                                        color='nombres', symbol='nombres',
                                        range_r=[0, df_long['Frecuencia'].max()])
    
    for trace in scatter_trace.data:
        fig.add_trace(trace)
        
    fig.update_traces(fill='toself')

    # Configura el formato del eje radial como enteros
    fig.update_layout(polar=dict(radialaxis=dict(tickmode='linear', tickformat='d', visible=True)), showlegend=True)

    # Muestra el gráfico
    st.plotly_chart(fig)

def grafico_experiencia(df):
    # Ordenar el DataFrame por la cantidad de experiencia en orden descendente
    df = df.sort_values(by='cantidad_experiencia', ascending=False)

    fig = px.bar(df, x='cantidad_experiencia', y='nombres', orientation='h', text='cantidad_experiencia',
                color='nombres',width=800, height=600, # Especificar la columna para determinar el color
                labels={'cantidad_experiencia': 'Cantidad de Experiencia Laboral', 'nombres': 'Candidatos'},
                title='Experiencia Laboral de Empleados')
    # Configurar diseño
    fig.update_layout(barmode='stack', width=600)
    # Mostrar el gráfico
    st.plotly_chart(fig)

def mostrar_tabla_resultados(df_filtrado):
    columnas_mostrar = ['nombres','universidad_o_instituto','habilidades_tecnicas_unicas','habilidades_blandas','idiomas_que_habla','certificados','URL']
    # Mostrar la tabla con los resultados
    # print_df = df_filtrado[columnas_mostrar].rename(columns={'nombres': 'Nombres', 'telefono': 'Teléfono', 'email': 'Email', 'titulo_actual_o_al_egresar': 'Título','universidad_o_instituto': 'Universidad o Instituto', 'habilidades_tecnicas_unicas': 'Habilidades Técnicas', 'habilidades_blandas': 'Habilidades blandas', 'idiomas_que_habla': 'Idiomas','certificados': 'Certificados','URL':'URL'})
    print_df = df_filtrado[columnas_mostrar].rename(columns={'nombres': 'Nombres', 'titulo_actual_o_al_egresar': 'Título','universidad_o_instituto': 'Universidad o Instituto', 'habilidades_tecnicas_unicas': 'Habilidades Técnicas', 'habilidades_blandas': 'Habilidades blandas', 'idiomas_que_habla': 'Idiomas','certificados': 'Certificados','URL':'URL'})

    st.write("Candidatos con habilidades seleccionadas:")
    st.write(print_df)

def borrar_resultados():
    if os.path.exists(result_file_path):
        try:
            os.remove(result_file_path)
            st.experimental_rerun()
        except Exception as e:
            st.error(f"No se pudo borrar el archivo {result_file_path}. Error {e}")

# Desglosar la lista de idiomas
def procesar_df(df):
    df = procesar_formato_datos(df)
    df = procesar_columnas(df)
    df = procesar_habilidades_tecnicas(df)
    # Aplicar la función a la columna del DataFrame
    df['solo_annos'] = df['anno_de_termino_de_estudios'].apply(extraer_anno_egreso)
    annos = ['nombres','anno_de_termino_de_estudios','solo_annos']
    # Reemplazar valores vacíos con NaN
    df['solo_annos'].replace('', pd.NA, inplace=True)
    # Aplicar la función a la columna 'experiencia_laboral'
    df['cantidad_experiencia'] = df['cargo_experiencia_laboral'].apply(contar_elementos)
    
    df = calcular_frecuencia(df)
    # st.dataframe(df)
    col1, col2 = st.columns(2)

    selected_skills, selected_languages = obtener_filtros_postulante(df)
    filtered_df = aplicar_filtrado(df, selected_skills, selected_languages)

    df_long = reorganizar_dataframe(filtered_df,selected_skills,df)

    with col1:
        with st.container():
            grafico_idiomas(filtered_df)
        with st.container():
            grafico_certificados(filtered_df,selected_skills)
        with st.container():
            grafico_experiencia(filtered_df)

    with col2:
        with st.container():
            # Agrega una condición para mostrar el gráfico de radar solo cuando se seleccionan 3 habilidades
            generar_nube_palabras(filtered_df)
        with st.container():
            if len(selected_skills) >= 3:
                grafico_radar_skills(df_long)
            else:
                st.warning("Selecciona más 3 habilidades técnicas para mostrar el gráfico de radar.")
        with st.container():
            extraer_habilidades_blandas(df)

    mostrar_tabla_resultados(filtered_df)

    st.sidebar.markdown(
        f'<style>div.stButton button[data-baseweb="button"] {{background-color: red; color: white;}}</style>',
        unsafe_allow_html=True
    )
    if st.sidebar.button("Borrar Resultados"):
        borrar_resultados()