# Evaluador de tono de piel (escala Fitzpatrick)

App gratuita en Streamlit para que varias personas evalúen el tono de piel
(escala Fitzpatrick I–VI) de un set de fotos. Guarda cada evaluación en
Google Sheets con: nombre del evaluador, nombre de la foto, resultado
Fitzpatrick, tiempo de respuesta y fecha/hora.

## Estructura del proyecto

```
fitzpatrick-app/
├── app.py
├── requirements.txt
├── images/                      <- se llena desde el panel admin (Paso 1)
└── .streamlit/
    └── secrets.toml.example     <- plantilla de configuración
```

## Paso 1 — Sube tus fotos — sin ZIP, directo desde el navegador

Ya descomprimiste tus fotos, así que no necesitas ningún zip. La app tiene
un **panel de administrador** con un selector de archivos donde eliges
todas tus fotos de una vez (arrastrando o seleccionando la carpeta
completa) y se suben directo, una por una, sin pasar por ningún proceso
de compresión/descompresión que pueda fallar.

Este paso lo haces **después de desplegar la app** (Paso 6), entrando a:

```
https://tu-app.streamlit.app/?admin=1
```

con tu `admin_password`, y usando ahí el selector "Choose image files"
(puedes seleccionar varios cientos de archivos de una sola vez) y el botón
"Add to gallery".

⚠️ **Importante**: las fotos subidas así quedan en el disco temporal de la
app (Streamlit Cloud gratis no tiene almacenamiento permanente). Se
mantienen disponibles mientras la app siga corriendo, pero podrían
perderse si la app se reinicia (por ejemplo, si Streamlit Cloud la pone a
"dormir" tras varios días sin uso, o si haces un nuevo despliegue desde
GitHub). Si eso pasa, solo repites este paso — toma un minuto.

## Paso 2 — Crea la Google Sheet donde se guardarán los resultados

1. Ve a https://sheets.google.com y crea una hoja nueva, por ejemplo
   "Evaluaciones Fitzpatrick".
2. Copia el ID de la hoja: es la parte de la URL entre `/d/` y `/edit`.
   Ejemplo: `https://docs.google.com/spreadsheets/d/AQUI_ESTA_EL_ID/edit`

## Paso 3 — Crea credenciales de Google (cuenta de servicio)

Esto le da permiso a la app para escribir en tu Google Sheet sin pedirte
usuario/contraseña cada vez.

1. Ve a https://console.cloud.google.com/ e inicia sesión con tu cuenta
   de Google (puedes crear un proyecto nuevo, es gratis).
2. En el buscador escribe "Google Sheets API" y actívala para tu proyecto.
3. Ve a "APIs y servicios" > "Credenciales" > "Crear credenciales" >
   "Cuenta de servicio".
4. Ponle un nombre (ej. "fitzpatrick-app") y termina el asistente.
5. Entra a la cuenta de servicio creada, pestaña "Claves" > "Agregar clave"
   > "Crear clave nueva" > tipo **JSON**. Se descargará un archivo `.json`.
6. Abre ese archivo JSON: ahí están todos los datos que necesitas
   (`client_email`, `private_key`, etc.).
7. **Muy importante:** vuelve a tu Google Sheet, dale clic en "Compartir" y
   agrega como editor el correo que aparece en `client_email` del JSON
   (algo como `fitzpatrick-app@tu-proyecto.iam.gserviceaccount.com`).

## Paso 4 — Configura los "secrets" (credenciales) de la app

`secrets.toml` es simplemente un archivo con tus **claves privadas**
(las de Google, y la contraseña de admin) para que la app pueda escribir
en tu Google Sheet sin que nadie más vea esas claves. Nunca se sube a
GitHub ni se comparte con los evaluadores — solo tú lo configuras.

Tienes que ponerlo en **dos lugares distintos** (no es el mismo archivo
físico, es la misma información en cada entorno donde corra la app):

1. **En tu computadora (opcional, solo si vas a probar en local, Paso 5):**
   copia `.streamlit/secrets.toml.example`, renómbralo a
   `.streamlit/secrets.toml`, y rellena los valores reales (los datos del
   JSON que descargaste en el Paso 3, tu `sheet_id` y tu `admin_password`).
   Este archivo se queda solo en tu disco — el `.gitignore` ya está
   configurado para que nunca se suba a GitHub por accidente.

2. **En Streamlit Cloud (obligatorio para que la app publicada funcione):**
   Streamlit Cloud no lee tu archivo local. Tienes que pegar ese mismo
   contenido dentro de la web de Streamlit Cloud, en
   **"Settings" > "Secrets"** de tu app (lo haces en el Paso 6, punto 4).
   Ahí no es un archivo que subes, es un cuadro de texto donde pegas el
   contenido completo tipo TOML.

En resumen: el archivo `.streamlit/secrets.toml.example` es solo la
**plantilla/guía** de qué información necesitas — la rellenas con tus
datos reales y la usas en local y/o la pegas en Streamlit Cloud, pero
nunca la subes a GitHub tal cual.

## Paso 5 — Prueba en tu computadora (opcional)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abrirá en `http://localhost:8501`.

## Paso 6 — Publica gratis en Streamlit Cloud

1. Sube esta carpeta a un repositorio de GitHub (puede ser privado).
   - Asegúrate de que `.streamlit/secrets.toml` **no** esté incluido
     (agrégalo a un `.gitignore`), solo sube `secrets.toml.example`.
2. Ve a https://share.streamlit.io/ e inicia sesión con GitHub (gratis).
3. Clic en "New app", selecciona tu repositorio, la rama y `app.py` como
   archivo principal.
4. Antes de desplegar (o después, en "Settings > Secrets"), pega el
   contenido completo de tu `secrets.toml` real ahí.
5. Despliega. Streamlit te dará un link público, por ejemplo:
   `https://tu-app.streamlit.app`

Ese es el link que compartes con los evaluadores.

## Cómo lo usan los evaluadores

1. Abren el link (interfaz en inglés).
2. Escriben su nombre.
3. Ven las fotos una por una (en orden aleatorio distinto para cada
   persona) y eligen el tipo Fitzpatrick presionando el **botón 1-6 en
   pantalla o directamente la tecla numérica 1-6 del teclado** — esto
   hace el flujo mucho más rápido para evaluar muchas fotos seguidas.
4. Al terminar todas las fotos ven un mensaje de agradecimiento.

Cada clic guarda automáticamente una fila en tu Google Sheet con:
`timestamp, evaluador, foto, fitzpatrick, tiempo_segundos`.

## Cómo ves y descargas los resultados finales

Abre tu link agregando `?admin=1` al final, por ejemplo:

```
https://tu-app.streamlit.app/?admin=1
```

Ingresa la contraseña que definiste en `admin_password` y podrás ver la
tabla completa y descargarla en **CSV** o **Excel**.

También puedes simplemente abrir la Google Sheet directamente en cualquier
momento — los datos se van guardando ahí en tiempo real.

## Notas

- El tiempo de respuesta se mide desde que la foto aparece en pantalla
  hasta que el evaluador presiona un botón.
- El orden de las fotos es aleatorio y distinto para cada evaluador
  (para reducir sesgos de orden).
- Si quieres agregar más fotos después, solo súbelas a `images/` en
  GitHub; Streamlit Cloud redepliega solo.
