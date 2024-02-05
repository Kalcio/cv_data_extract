# Trabajo de Titulo
Sistema que extrae datos de los currículums adjuntados, para generar y visualizar métricas que entreguen un resumen de la información de los postulantes.

Para la instalación de las dependencias, es necesario tener [Anaconda](https://www.anaconda.com/products/individual) instalado.

## Instalación

1. Crear un entorno con las dependencias necesarias mediante el siguiente comando:

    ```conda env create --name <nombre_del_entorno> --file environment.yml```

2. Activar el entorno de desarrollo:

    ```conda activate <nombre_del_entorno>```

3. Añadir la clave de la API de OpenAI en el archivo .env

4. Para ejecutar el programa, se utiliza el siguiente comando en la carpeta raíz del proyecto:

    ```streamlit run main.py```

    Esto desplegará una interfaz de usuario en una ventana del navegador.
