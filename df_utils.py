import pandas as pd
import streamlit as st
from unidecode import unidecode
from ast import literal_eval
from collections import Counter
from wordcloud import WordCloud
from io import BytesIO
import plotly.express as px
# import matplotlib.pyplot as plt

def procesar_formato_datos(df):
    # Convertir todas los datos a minúsculas
    df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
    # Formatear datos nombres a mayúsculas
    df['nombres'] = df['nombres'].apply(lambda x: x.title())

    return df

def procesar_idiomas(df):
    # Quitar tildes de la columna 'idiomas_que_habla'
    df['idiomas_que_habla'] = df['idiomas_que_habla'].apply(lambda x: unidecode(x) if isinstance(x, str) else x)
    return df

def procesar_columnas(df):
    # Columnas a enlistar
    columns_to_process = ['telefono', 'email', 'idiomas_que_habla', 'certificados', 'habilidades_blandas', 'titulo_actual_o_al_egresar', 'universidad_o_instituto', 'anno_de_termino_de_estudios', 'cargo_experiencia_laboral', 'empresa_en_la_que_trabajo', 'nivel_de_idioma', 'url']
    # Función para manejar NaN y enlistar
    for column in columns_to_process:
        df[column] = df[column].apply(lambda x: [] if pd.isna(x) else [data.strip() for data in x.split(',')])

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

    # Crear un filtro por idioma usando multiselect
    idiomas_seleccionados = st.multiselect('Selecciona idiomas', todos_idiomas, default=todos_idiomas)

    # Filtrar el DataFrame según los idiomas seleccionados
    df_filtrado = df[df['idiomas_que_habla'].apply(lambda x: any(idioma in x for idioma in idiomas_seleccionados))]

    return df_filtrado

def grafico_idiomas(df_filtrado):
    # Crear el gráfico interactivo
    fig_idiomas = px.bar(df_filtrado, x='idiomas_que_habla', color='nombres',
                        labels={'idiomas_que_habla': 'Idioma', 'nombres': 'Candidato'},
                        title='Distribución de Idiomas (Interactivo)',
                        hover_data={'nombres': True, 'idiomas_que_habla': False},
                        color_discrete_sequence=px.colors.qualitative.Set1)
    
    # Configurar diseño
    fig_idiomas.update_layout(barmode='stack')
    # Mostrar el gráfico interactivo en Streamlit
    st.plotly_chart(fig_idiomas)


def generar_nube_palabras(df):
    all_skills = [skill.lower() for sublist in df['habilidades_tecnicas'] for skill in sublist]
    text = ' '.join(all_skills)
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    img_bytes = BytesIO()
    wordcloud.to_image().save(img_bytes, format='PNG')
    st.image(img_bytes, caption='Nube de Palabras de Habilidades Técnicas', use_column_width=True)

def obtener_filtros_postulante(df):
    # Sidebar con el menú de habilidades
    selected_skills = st.sidebar.multiselect('Selecciona habilidades', df['habilidades_tecnicas'].explode().unique())
    # Sidebar con el menú de idiomas
    selected_languages = st.sidebar.multiselect('Selecciona idiomas', df['idiomas_que_habla'].explode().unique())

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

    # selected_columns = ['nombres', 'telefono', 'email', 'titulo_actual_o_al_egresar', 'universidad_o_instituto','habilidades_tecnicas','habilidades_tecnicas_unicas','habilidades_blandas','idiomas_que_habla','url']

    # Filtrar y seleccionar solo las columnas deseadas
    # filtered_df = filtered_df[selected_columns]

    # Cuenta la frecuencia de cada habilidad para cada postulante
    for habilidad in selected_skills:
        filtered_df[habilidad] = df['habilidades_tecnicas'].apply(lambda x: Counter(x)[habilidad] if isinstance(x, list) else 0)

    # Reorganiza el DataFrame para tener un formato largo
    df_long = pd.melt(filtered_df, id_vars=['nombres'], value_vars=selected_skills,
                      var_name='Habilidad', value_name='Frecuencia')

    # Filtrar los nombres que tienen relación con los filtros seleccionados
    df_long = df_long[df_long['nombres'].isin(filtered_df['nombres'].unique())]

    return df_long

def crear_grafico_radar(df_long):
    # Crea el gráfico interactivo de radar con Plotly Express y asigna un color a cada postulante
    fig = px.line_polar(df_long, r='Frecuencia', theta='Habilidad', line_close=True,
                        color='nombres', # Asigna colores según los nombres de los postulantes
                        range_r=[0, df_long['Frecuencia'].max()],
                        labels={'Frecuencia': 'Frecuencia de Habilidad'},
                        title='Frecuencia de Habilidades Técnicas por Postulante en Gráfico Radar')

    fig.update_traces(fill='toself')

    # Muestra el gráfico
    st.plotly_chart(fig)

def mostrar_tabla_resultados(filtered_df):
    # Mostrar la tabla con los resultados
    st.write("Candidatos con habilidades seleccionadas:")
    st.write(filtered_df)

# Desglosar la lista de idiomas
def main_utils(df):
    df = procesar_formato_datos(df)
    df = procesar_idiomas(df)
    df = procesar_columnas(df)
    df = procesar_habilidades_tecnicas(df)
    
    df = calcular_frecuencia(df)
    st.dataframe(df)

    df_filtrado = filtrar_idiomas(df)
    grafico_idiomas(df_filtrado)
    generar_nube_palabras(df_filtrado)

    selected_skills, selected_languages = obtener_filtros_postulante(df_filtrado)
    filtered_df = aplicar_filtrado(df_filtrado, selected_skills, selected_languages)

    df_long = reorganizar_dataframe(df_filtrado,selected_skills,df)
    crear_grafico_radar(df_long)

    mostrar_tabla_resultados(filtered_df)


    