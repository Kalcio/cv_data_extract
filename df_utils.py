import pandas as pd
import streamlit as st
from unidecode import unidecode
from ast import literal_eval
from collections import Counter
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO

# Desglosar la lista de idiomas
def procesar_df(df):
    # Convertir todas las cadenas a minúsculas
    df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)

    # Quitar tildes de la columna 'idiomas_que_habla'
    df['idiomas_que_habla'] = df['idiomas_que_habla'].apply(lambda x: unidecode(x) if isinstance(x, str) else x)

    df['nombres'] = df['nombres'].apply(lambda x: x.title())

    # Función para manejar NaN y dividir por coma
    def process_column(column):
        return df[column].apply(lambda x: [] if pd.isna(x) else [data.strip() for data in x.split(',')])

    # Aplicar la función a las columnas relevantes
    columns_to_process = ['telefono', 'email', 'idiomas_que_habla', 'certificados', 'habilidades_blandas', 'titulo_actual_o_al_egresar', 'universidad_o_instituto', 'anno_de_termino_de_estudios', 'cargo_experiencia_laboral', 'empresa_en_la_que_trabajo', 'nivel_de_idioma', 'url']
    for column in columns_to_process:
        df[column] = process_column(column)

    # Convertir la cadena de lista a una lista de Python
    df['habilidades_tecnicas'] = df['habilidades_tecnicas'].apply(lambda x: literal_eval(x) if isinstance(x, str) else x)

    # Explode y calcular para las columnas relevantes
    columns_to_explode = ['idiomas_que_habla', 'certificados', 'habilidades_blandas', 'habilidades_tecnicas']
    for column in columns_to_explode:
        df_exploded = df.explode(column).dropna(subset=[column])
        count_column = df_exploded.groupby('nombres').size()
        df = df.join(count_column.rename(f'cantidad_{column}'), on='nombres').fillna({f'cantidad_{column}': 0})

    st.dataframe(df)

    # Explotar el DataFrame para cada idioma
    df_exploded = df.explode('idiomas_que_habla')

    

    # Filtrar datos no deseados y NaN
    df_exploded = df_exploded[
        (df_exploded['idiomas_que_habla'].astype(str) != 'sin informacion') &
        (df_exploded['idiomas_que_habla'].astype(str) != 'espanol') &
        (df_exploded['idiomas_que_habla'].astype(str) != 'chileno') &
        ~df_exploded['idiomas_que_habla'].isna()
    ]

    # Convertir todos los valores a cadenas (str)
    df_exploded['idiomas_que_habla'] = df_exploded['idiomas_que_habla'].astype(str)

    todos_idiomas = sorted(df_exploded['idiomas_que_habla'].unique())

    # Crear un filtro por idioma usando multiselect
    idiomas_seleccionados = st.multiselect('Selecciona idiomas', todos_idiomas, default=todos_idiomas)

    # Filtrar el DataFrame según los idiomas seleccionados
    df_filtrado = df_exploded[df_exploded['idiomas_que_habla'].isin(idiomas_seleccionados)]

    # Crear el gráfico interactivo
    fig_idiomas = px.bar(df_filtrado, x='idiomas_que_habla', color='nombres',
                        labels={'idiomas_que_habla': 'Idioma', 'nombres': 'Candidato'},
                        title='Distribución de Idiomas (Interactivo)',
                        hover_data={'nombres': True, 'idiomas_que_habla': False},
                        # category_orders={'idiomas_que_habla': sorted(df_exploded['idiomas_que_habla'].unique())},
                        color_discrete_sequence=px.colors.qualitative.Set1)

    # Configurar diseño
    fig_idiomas.update_layout(barmode='stack')

    # Mostrar el gráfico interactivo en Streamlit
    st.plotly_chart(fig_idiomas)

    # Obtener una lista plana de todas las habilidades técnicas
    all_skills = [skill.lower() for sublist in df['habilidades_tecnicas'] for skill in sublist]

    # Crear una cadena con todas las habilidades separadas por espacio
    text = ' '.join(all_skills)

    # Configurar el objeto WordCloud
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

    # Obtener la imagen como BytesIO
    img_bytes = BytesIO()
    wordcloud.to_image().save(img_bytes, format='PNG')

    # Mostrar el gráfico de la nube de palabras en Streamlit
    st.image(img_bytes, caption='Nube de Palabras de Habilidades Técnicas', use_column_width=True)

    # Crear un nuevo DataFrame con el nombre del usuario y la lista de habilidades
    df_habilidades_usuario = pd.DataFrame({
        'usuario': df['nombres'],
        'habilidades_tecnicas': df['habilidades_tecnicas']
    })

    # Apilar las listas de habilidades y contar la frecuencia por usuario
    df_habilidades_usuario = df_habilidades_usuario.explode('habilidades_tecnicas')

    df['habilidades_tecnicas_unicas'] = df['habilidades_tecnicas'].apply(lambda x: list(set(x)))

    # Sidebar con el menú de habilidades
    selected_skills = st.sidebar.multiselect('Selecciona habilidades', df['habilidades_tecnicas_unicas'].explode().unique())

    # Sidebar con el menú de idiomas
    selected_languages = st.sidebar.multiselect('Selecciona idiomas', df['idiomas_que_habla'].explode().unique())

    # Lógica de filtrado
    if selected_skills or selected_languages:
        # Filtrar el DataFrame según habilidades o idiomas seleccionados
        filtered_df = df[
            ((df['habilidades_tecnicas_unicas'].apply(lambda skills: any(skill in selected_skills for skill in skills)) if selected_skills else False)
            | (df['idiomas_que_habla'].apply(lambda languages: any(language in selected_languages for language in languages)) if selected_languages else False))
        ]
    else:
        # Si no se selecciona ningún filtro, mostrar todos los datos
        filtered_df = df

    # Seleccionar las columnas deseadas
    selected_columns = ['nombres', 'telefono', 'email', 'titulo_actual_o_al_egresar', 'universidad_o_instituto','habilidades_tecnicas_unicas','habilidades_blandas','idiomas_que_habla','url']

    # Filtrar y seleccionar solo las columnas deseadas
    filtered_df = filtered_df[selected_columns]

    # Mostrar la tabla con los resultados
    st.write("Candidatos con habilidades seleccionadas:")
    st.write(filtered_df)