import streamlit as st
from fpdf import FPDF
import smtplib
from email.message import EmailMessage
import os
import psycopg2
import pandas as pd
import io

# Mostrar logo
direccion_logo = "https://www.ingauto.com.ec/wp-content/uploads/2019/06/logo-Ingauto-T.png"
st.image(direccion_logo, width=400)

# Estilos
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

# Título
st.title("Sistema de Citas - Ingauto Catamayo")
st.markdown("[&#128236; Accede a tu correo Ingauto aquí](https://www.ingauto.com.ec:2096/cpsess9732837900/3rdparty/roundcube/?_task=mail&_mbox=INBOX.Sent)")

# Conexión a Supabase

def conectar_supabase():
    return psycopg2.connect(
        host="db.dzmiihvsgwbemftjlpsj.supabase.co",
        port=5432,
        database="postgres",
        user="postgres",
        password="TU_PASSWORD_AQUI"  # ← Cambia por tu contraseña real
    )

def guardar_en_supabase(datos):
    try:
        conn = conectar_supabase()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citas (
                id SERIAL PRIMARY KEY,
                nombre TEXT, telefono TEXT, cedula TEXT, correo TEXT,
                marca TEXT, modelo TEXT, anio TEXT, placa TEXT, kilometraje TEXT,
                combustible TEXT, motor TEXT, chasis TEXT,
                servicio TEXT, servicio_extra TEXT, fecha TEXT, hora TEXT
            )
        """)
        conn.commit()

        cursor.execute("""
            INSERT INTO citas (
                nombre, telefono, cedula, correo, marca, modelo, anio, placa,
                kilometraje, combustible, motor, chasis, servicio, servicio_extra, fecha, hora
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, tuple(datos.values()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error al guardar en Supabase: {e}")
        return False

def exportar_citas_csv():
    try:
        conn = conectar_supabase()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM citas ORDER BY id DESC")
        filas = cursor.fetchall()
        columnas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(filas, columns=columnas)
        conn.close()
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue()
    except Exception as e:
        st.error(f"Error al exportar citas: {e}")
        return None

def generar_pdf(datos, nombre_archivo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.image(direccion_logo, x=10, y=8, w=50)
    pdf.ln(30)
    pdf.cell(200, 10, txt="Cita Registrada - Ingauto Catamayo", ln=True, align="C")
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

def enviar_pdf_por_correo(remitente, clave, destinatario, archivo, asunto):
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = remitente
    msg["To"] = destinatario
    msg.set_content("Adjunto encontrarás la cita generada en PDF.")
    with open(archivo, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(archivo))
    with smtplib.SMTP_SSL("mail.ingauto.com.ec", 465) as smtp:
        smtp.login(remitente, clave)
        smtp.send_message(msg)

# Formulario de cita
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
        "Mantenimiento de 5000 km", "Mantenimiento de 10000 km",
        "Mantenimiento de 15000 km", "Mantenimiento de 20000 km",
        "Mantenimiento de 25000 km", "Mantenimiento de 30000 km",
        "Mantenimiento de 40000 km", "Mantenimiento de 50000 km",
        "Cambio de aceite", "Revisión de frenos", "Diagnóstico general",
        "Alineación y balanceo", "Otros"])
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

        if guardar_en_supabase(datos):
            st.success("✅ Cita guardada en Supabase.")
            try:
                remitente = "accesoriossd@ingauto.com.ec"
                clave_app = "51TBdC375q"  # ⚠️ Reemplaza por la clave real
                enviar_pdf_por_correo(remitente, clave_app, correo_cliente, ruta_pdf, "Tu cita en Ingauto")
                enviar_pdf_por_correo(remitente, clave_app, "accesoriossd@ingauto.com.ec", ruta_pdf, "Nueva cita registrada")
                st.info("📧 PDF enviado correctamente a ambos correos.")
            except Exception as e:
                st.error(f"Error al enviar correo: {e}")
        else:
            st.error("❌ Error al guardar en Supabase.")

# Exportar citas
st.subheader("⬇️ Exportar citas registradas")
if st.button("Generar y descargar CSV"):
    csv = exportar_citas_csv()
    if csv:
        st.download_button(
            label="📄 Descargar archivo CSV",
            data=csv,
            file_name="citas_ingauto.csv",
            mime="text/csv"
        )
