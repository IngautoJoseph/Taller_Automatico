
import streamlit as st
from fpdf import FPDF
import pandas as pd
import os
import datetime
import io
import uuid

from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials

# Mostrar logo más grande
direccion_logo = "https://www.ingauto.com.ec/wp-content/uploads/2019/06/logo-Ingauto-T.png"
st.image(direccion_logo, width=600)

# Estilos visuales
st.markdown("""
    <style>
    .stApp {
        background-color: #eeeeee;
    }
    .block-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
    }
    h1, h2, h3 {
        color: #ff7300 !important;
    }
    label {
        color: #003865 !important;
        font-weight: 600 !important;
    }
    .stButton>button {
        background-color: #ff7300;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        padding: 0.4rem 1.2rem;
    }
    .stDownloadButton>button {
        background-color: #003865;
        color: white;
        font-weight: bold;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Sistema de Citas - Firebase")

# Inicializar Firebase con dict de secrets (no archivo)
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Guardar cita
def guardar_cita(datos):
    try:
        doc_id = str(uuid.uuid4())
        db.collection("citas").document(doc_id).set(datos)
        return True
    except Exception as e:
        st.error(f"Error al guardar cita: {e}")
        return False

# Exportar citas a CSV
def exportar_citas_csv():
    try:
        docs = db.collection("citas").stream()
        datos = [doc.to_dict() for doc in docs]
        df = pd.DataFrame(datos)
        df.insert(0, "#", range(1, 1 + len(df)))
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue()
    except Exception as e:
        st.error(f"Error al exportar citas: {e}")
        return None

# Generar PDF
def generar_pdf(datos, nombre_archivo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.image(direccion_logo, x=10, y=8, w=80)
    pdf.ln(30)
    pdf.cell(200, 10, txt="Cita Registrada - Firebase", ln=True, align="C")
    pdf.ln(10)
    pdf.set_fill_color(255, 115, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, "Campo", 1, 0, 'C', fill=True)
    pdf.cell(130, 10, "Valor", 1, 1, 'C', fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=12)
    for clave, valor in datos.items():
        pdf.cell(60, 10, clave, 1)
        pdf.cell(130, 10, str(valor), 1)
        pdf.ln()
    pdf.output(nombre_archivo)

# Formulario
with st.form("formulario_cita"):
    nombre = st.text_input("Nombre completo")
    telefono = st.text_input("Teléfono")
    cedula = st.text_input("Cédula / RUC")
    correo_cliente = st.text_input("Correo del cliente")
    marca = st.text_input("Marca del vehículo")
    modelo = st.text_input("Modelo")
    anio = st.text_input("Año")
    placa = st.text_input("Placa")
    kilometraje = st.text_input("Kilometraje")
    combustible = st.selectbox("Combustible", ["Gasolina", "Diésel"])
    motor = st.text_input("Motor")
    chasis = st.text_input("Chasis")
    servicio = st.selectbox("Servicio solicitado", [
        "Mantenimiento 5000 km", "Mantenimiento 10000 km",
        "Cambio de aceite", "Revisión de frenos",
        "Diagnóstico general", "Otros"
    ])
    servicio_extra = st.text_area("📝 Descripción del servicio solicitado (si aplica)")
    fecha = st.date_input("Fecha de cita")
    hora = st.time_input("Hora")
    enviar = st.form_submit_button("Registrar y generar PDF")

if enviar:
    if not all([nombre, telefono, cedula, correo_cliente, marca, modelo, anio, placa]):
        st.warning("Por favor completa todos los campos obligatorios.")
    else:
        datos = {
            "nombre": nombre,
            "telefono": telefono,
            "cedula": cedula,
            "correo": correo_cliente,
            "marca": marca,
            "modelo": modelo,
            "anio": anio,
            "placa": placa,
            "kilometraje": kilometraje,
            "combustible": combustible,
            "motor": motor,
            "chasis": chasis,
            "servicio": servicio,
            "servicio_extra": servicio_extra,
            "fecha": str(fecha),
            "hora": str(hora),
        }
        nombre_pdf = f"cita_{placa}_{fecha}.pdf"
        ruta_pdf = os.path.join("/tmp", nombre_pdf)
        generar_pdf(datos, ruta_pdf)
        st.success("✅ Cita registrada correctamente.")
        with open(ruta_pdf, "rb") as f:
            st.download_button("⬇️ Descargar PDF", data=f, file_name=nombre_pdf, mime="application/pdf")
        if guardar_cita(datos):
            st.success("✅ Cita guardada en Firebase.")

# Mostrar citas
st.subheader("📋 Citas registradas")
try:
    docs = db.collection("citas").stream()
    datos = [doc.to_dict() for doc in docs]
    if datos:
        df = pd.DataFrame(datos)
        df.insert(0, "#", range(1, 1 + len(df)))
        st.dataframe(df)
    else:
        st.info("No hay citas registradas.")
except Exception as e:
    st.error(f"Error al mostrar citas: {e}")

# Exportar CSV
st.subheader("⬇️ Exportar citas")
if st.button("Generar y descargar CSV"):
    csv = exportar_citas_csv()
    if csv:
        st.download_button(
            label="📄 Descargar archivo CSV",
            data=csv,
            file_name="citas_firebase.csv",
            mime="text/csv"
        )
