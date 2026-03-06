import streamlit as st
import pandas as pd
import easyocr
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os

# CONFIGURACIÓN DE PÁGINA Y ESTILO JP (NEGRO Y DORADO)
st.set_page_config(page_title="JP Registro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    h1, h2, h3 { color: #D4AF37 !important; }
    .stButton>button { 
        background-color: #D4AF37; color: black; font-weight: bold; border-radius: 10px; border: none;
    }
    div[data-testid="column"]:nth-of-type(2) .stButton>button { background-color: #8B0000; color: white; }
    .css-12w0qpk { border: 1px solid #D4AF37; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# SISTEMA DE ARCHIVOS PARA QUE NO SE PIERDAN LOS DATOS
DB_FILE = "base_datos.csv"
LOG_FILE = "registro_entradas.csv"

def cargar_datos():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=['Placa', 'Conductor', 'Licencia', 'Area'])

def cargar_log():
    if os.path.exists(LOG_FILE): return pd.read_csv(LOG_FILE)
    return pd.DataFrame(columns=['Placa', 'Conductor', 'Area', 'Ingreso', 'Salida'])

# INICIALIZACIÓN
if 'db' not in st.session_state: st.session_state.db = cargar_datos()
if 'log' not in st.session_state: st.session_state.log = cargar_log()

@st.cache_resource
def get_reader(): return easyocr.Reader(['en'])

# --- DISEÑO DE 3 COLUMNAS ---
st.title("🔱 JP REGISTRO VEHICULAR PROFESIONAL")
col1, col2, col3 = st.columns(3)

# COLUMNA 1: BASE DE DATOS
with col1:
    st.header("🗂️ Base de Datos")
    with st.container():
        placa = st.text_input("Placa (ID)").upper()
        nombre = st.text_input("Nombre del Conductor")
        area_opt = ["Administración", "Logística", "Operaciones", "Ventas", "Otro"]
        area_sel = st.selectbox("Área", area_opt)
        area_final = st.text_input("Especifique Área") if area_sel == "Otro" else area_sel
        
        if st.button("Registrar en Sistema"):
            nueva_fila = pd.DataFrame([[placa, nombre, "DNI/LIC", area_final]], columns=st.session_state.db.columns)
            st.session_state.db = pd.concat([st.session_state.db, nueva_fila], ignore_index=True)
            st.session_state.db.to_csv(DB_FILE, index=False)
            st.success("Guardado correctamente")

# COLUMNA 2: REGISTRO MANUAL
with col2:
    st.header("⌨️ Registro Manual")
    buscar_p = st.text_input("Buscar Placa para Marcar").upper()
    match = st.session_state.db[st.session_state.db['Placa'] == buscar_p]
    
    if not match.empty:
        persona = match.iloc[0]
        st.info(f"Conductor: {persona['Conductor']}\n\nÁrea: {persona['Area']}")
        if st.button("🔔 MARCAR INGRESO"):
            nuevo_log = pd.DataFrame([[buscar_p, persona['Conductor'], persona['Area'], datetime.now().strftime("%H:%M:%S %d/%m/%Y"), "-"]], columns=st.session_state.log.columns)
            st.session_state.log = pd.concat([st.session_state.log, nuevo_log], ignore_index=True)
            st.session_state.log.to_csv(LOG_FILE, index=False)
            st.success("Ingreso Marcado")
        
        if st.button("🛑 MARCAR SALIDA"):
            idx = st.session_state.log[st.session_state.log['Placa'] == buscar_p].index
            if not idx.empty:
                st.session_state.log.loc[idx[-1], 'Salida'] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
                st.session_state.log.to_csv(LOG_FILE, index=False)
                st.warning("Salida Marcada")

# COLUMNA 3: REGISTRO AUTOMÁTICO (CÁMARA IA)
with col3:
    st.header("📸 Registro con IA")
    foto = st.camera_input("Tomar foto a la placa")
    if foto:
        img = Image.open(foto)
        with st.spinner("IA Identificando..."):
            res = get_reader().readtext(np.array(img))
            texto_detectado = res[0][1].upper().replace(" ", "") if res else "No detectada"
            st.write(f"Placa detectada: **{texto_detectado}**")
            # Aquí se puede repetir la lógica de buscar_p automáticamente

# --- EXPORTACIÓN A EXCEL PROFESIONAL ---
st.divider()
st.subheader("📊 Reporte de Movimientos")
st.dataframe(st.session_state.log, use_container_width=True)

output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    st.session_state.log.to_excel(writer, index=False, sheet_name='Reporte')
    workbook = writer.book
    worksheet = writer.sheets['Reporte']
    formato_oro = workbook.add_format({'bold': True, 'bg_color': '#D4AF37', 'border': 1})
    for col_num, value in enumerate(st.session_state.log.columns.values):
        worksheet.write(0, col_num, value, formato_oro)

st.download_button("📥 Descargar Reporte Excel", data=output.getvalue(), file_name="JP_Registro.xlsx")
