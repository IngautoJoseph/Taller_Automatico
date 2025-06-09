import streamlit as st
from fpdf import FPDF
import smtplib
from email.message import EmailMessage
import os
import sqlite3

# Mostrar logo desde URL (más grande)
st.image("https://www.ingauto.com.ec/wp-content/uploads/2019/06/logo-Ingauto-T.png", width=400)

# Estilos personalizados
st.markdown("""
    <style>
    /* Fondo general */
    .stApp {
        background-color: #eeeeee;
    }

    /* Fondo del contenido */
    .block-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
    }

    /* Títulos */
    h1, h2, h3 {
        color: #ff7300 !important;
    }

    label {
        color: #003865 !important;
        font-weight: 600 !important;
    }

    /* Botones */
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

# Título y enlace
st.title("Sistema de Citas - Ingauto Catamayo")
st.markdown("[📬 Accede a tu correo Ingauto aquí](https://www.ingauto.com.ec:2096/cpsess9732837900/3rdparty/roundcube/?_task=mail&_mbox=INBOX.Sent)")

# Crear base de datos y tabla
conn = sqlite3.connect("citas.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS citas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        telefono TEXT,
        cedula TEXT,
        correo TEXT,
        marca TEXT,
        modelo TEXT,
        anio TEXT,
        placa TEXT,
        kilometraje TEXT,
        combustible TEXT,
        motor TEXT,
        chasis TEXT,
        servicio TEXT,
        servicio_extra TEXT,
        fecha TEXT,
        hora TEXT
    )
""")
conn.commit()

# Función PDF
def generar_pdf(datos, nombre_archivo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for clave, valor in datos.items():
        pdf.cell(200, 10, txt=f"{clave}: {valor}", ln=True)
    pdf.output(nombre_archivo)

# Función email
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
    
    servicios_disponibles = [
        "Mantenimiento de 5000 km",
        "Mantenimiento de 10000 km",
        "Mantenimiento de 15000 km",
        "Mantenimiento de 20000 km",
        "Mantenimiento de 25000 km",
        "Mantenimiento de 30000 km",
        "Mantenimiento de 40000 km",
        "Mantenimiento de 50000 km",
        "Cambio de aceite",
        "Revisión de frenos",
        "Diagnóstico general",
        "Alineación y balanceo",
        "Otros"
    ]
    
    servicio = st.selectbox("Servicio solicitado", servicios_disponibles)

    servicio = st.selectbox("Servicio solicitado", servicios_disponibles)

# Mostrar campo adicional solo si es "Otros"
servicio_extra = ""
if servicio == "Otros":
    servicio_extra = st.text_area("📝 Descripción del servicio solicitado")
)

    fecha = st.date_input("Fecha de cita")
    hora = st.time_input("Hora")
    enviar = st.form_submit_button("Registrar y generar PDF")

# Guardar datos y generar PDF
if enviar:
    if not all([nombre, telefono, cedula, correo_cliente, marca, modelo, anio, placa]):
        st.warning("Por favor completa todos los campos obligatorios.")
    else:
        datos = {
            "Nombre": nombre,
            "Teléfono": telefono,
            "Cédula / RUC": cedula,
            "Correo": correo_cliente,
            "Marca": marca,
            "Modelo": modelo,
            "Año": anio,
            "Placa": placa,
            "Kilometraje": kilometraje,
            "Combustible": combustible,
            "Motor": motor,
            "Chasis": chasis,
            "Servicio solicitado": servicio,
            "Detalle adicional": servicio_extra if servicio == "Otros" else "",
            "Fecha de cita": str(fecha),
            "Hora": str(hora),
        }

        # Guardar en BD
        try:
            cursor.execute("""
                INSERT INTO citas (nombre, telefono, cedula, correo, marca, modelo, anio, placa, kilometraje, combustible, motor, chasis, servicio, servicio_extra, fecha, hora)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nombre, telefono, cedula, correo_cliente, marca, modelo, anio, placa,
                kilometraje, combustible, motor, chasis, servicio, servicio_extra, str(fecha), str(hora)
            ))
            conn.commit()
        except Exception as e:
            st.error(f"Error al guardar en base de datos: {e}")

        # Generar PDF
        nombre_pdf = f"cita_{placa}_{fecha}.pdf"
        ruta_pdf = os.path.join("/tmp", nombre_pdf)
        generar_pdf(datos, ruta_pdf)

        st.success("✅ Cita registrada correctamente.")
        with open(ruta_pdf, "rb") as f:
            st.download_button("⬇️ Descargar PDF", data=f, file_name=nombre_pdf, mime="application/pdf")

        # Enviar por correo
        try:
            remitente = "accesoriossd@ingauto.com.ec"
            clave_app = "51TBdC375q"  # ⚠️ Reemplaza por tu clave real
            enviar_pdf_por_correo(remitente, clave_app, correo_cliente, ruta_pdf, "Tu cita en Ingauto")
            enviar_pdf_por_correo(remitente, clave_app, "accesoriossd@ingauto.com.ec", ruta_pdf, "Nueva cita registrada")
            st.info("📧 PDF enviado correctamente a ambos correos.")
        except Exception as e:
            st.error(f"Error al enviar correo: {e}")

# Mostrar citas guardadas
st.subheader("📋 Citas registradas")
if st.checkbox("Mostrar todas las citas registradas"):
    cursor.execute("SELECT * FROM citas ORDER BY id DESC")
    filas = cursor.fetchall()
    for fila in filas:
        st.markdown(f"""
        **ID:** {fila[0]}  
        **Nombre:** {fila[1]}  
        **Teléfono:** {fila[2]}  
        **Cédula:** {fila[3]}  
        **Correo:** {fila[4]}  
        **Vehículo:** {fila[5]} {fila[6]} ({fila[7]})  
        **Placa:** {fila[8]}  
        **Kilometraje:** {fila[9]}  
        **Combustible:** {fila[10]}  
        **Motor:** {fila[11]}  
        **Chasis:** {fila[12]}  
        **Servicio:** {fila[13]}  
        **Detalle adicional:** {fila[14]}  
        **Fecha:** {fila[15]}  
        **Hora:** {fila[16]}  
        ---
        """)
