
import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
import base64
import smtplib
from email.message import EmailMessage

car_data = {
    "Toyota": ["Corolla", "Hilux", "RAV4", "Yaris", "Fortuner", "Prado"],
    "Nissan": ["Sentra", "Frontier", "X-Trail", "Versa", "Kicks", "Navara"],
    "Hyundai": ["Elantra", "Tucson", "Santa Fe", "Accent", "Creta", "Kona"],
    "Chevrolet": ["Aveo", "Tracker", "Captiva", "Onix", "Spark", "Cruze"],
    "Ford": ["Ranger", "Focus", "EcoSport", "Escape", "Explorer", "F-150"],
    "Kia": ["Rio", "Sportage", "Sorento", "Picanto", "Cerato", "Seltos"],
    "Great Wall": ["Wingle 5", "Wingle 7", "Poer", "Haval H6", "Haval Jolion"],
    "Chery": ["Tiggo 2", "Tiggo 3", "Tiggo 7", "Arrizo 5", "Tiggo 8 Pro"],
    "JAC": ["J2", "JS2", "JS3", "T6", "T8", "Sunray"],
    "BYD": ["Dolphin", "Yuan Plus", "Han EV", "Tang", "Song Plus"],
    "Geely": ["Coolray", "Azkarra", "Okavango", "GC6", "Emgrand"],
    "Mazda": ["Mazda 2", "Mazda 3", "CX-5", "CX-30", "BT-50"],
    "Volkswagen": ["Gol", "Jetta", "Amarok", "Tiguan", "Virtus", "T-Cross"],
    "Honda": ["Civic", "CR-V", "Fit", "HR-V", "City"],
    "Mitsubishi": ["L200", "Montero Sport", "Outlander", "Mirage"],
    "Renault": ["Logan", "Duster", "Kwid", "Sandero", "Oroch"]
}

servicios = [
    "MANTENIMIENTO 700 KM", "MANTENIMIENTO 5,000 KM", "MANTENIMIENTO 10,000 KM",
    "MANTENIMIENTO 15,000 KM", "MANTENIMIENTO 20,000 KM", "MANTENIMIENTO 25,000 KM",
    "MANTENIMIENTO 30,000 KM", "MANTENIMIENTO 35,000 KM", "MANTENIMIENTO 40,000 KM",
    "MANTENIMIENTO 45,000 KM", "MANTENIMIENTO 50,000 KM", "CAMBIO DE ACEITE",
    "DIAGNÓSTICO", "REVISIÓN GENERAL", "ALINEACIÓN Y BALANCEO"
]

if "citas" not in st.session_state:
    st.session_state.citas = []
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

st.title("📅 Sistema de Citas - Taller Automotriz")

with st.form("form_cita"):
    nombre = st.text_input("Nombre del cliente")
    correo = st.text_input("Correo del cliente")
    telefono = st.text_input("Teléfono")
    marca = st.selectbox("Marca del vehículo", list(car_data.keys()))
    modelo = st.selectbox("Modelo", car_data[marca])
    placa = st.text_input("Placa del vehículo")
    servicio = st.selectbox("Servicio", servicios)
    combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Gas", "Eléctrico"])
    fecha = st.date_input("Fecha de la cita")
    hora = st.time_input("Hora de la cita")

    submitted = st.form_submit_button("Guardar / Actualizar Cita")

    if submitted:
        if not all([nombre, correo, telefono, marca, modelo, placa, servicio, combustible, fecha, hora]):
            st.error("Por favor completa todos los campos.")
        else:
            nueva_cita = {
                "nombre": nombre, "correo": correo, "telefono": telefono,
                "marca": marca, "modelo": modelo, "placa": placa,
                "servicio": servicio, "combustible": combustible,
                "fecha": str(fecha), "hora": str(hora)
            }

            if st.session_state.edit_index is not None:
                st.session_state.citas[st.session_state.edit_index] = nueva_cita
                cita_id = st.session_state.edit_index + 1
                st.session_state.edit_index = None
                st.success(f"Cita N.º {str(cita_id).zfill(3)} actualizada correctamente.")
            else:
                st.session_state.citas.append(nueva_cita)
                cita_id = len(st.session_state.citas)
                st.success(f"Cita N.º {str(cita_id).zfill(3)} guardada exitosamente.")

            # Crear PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"CITA N.º {str(cita_id).zfill(3)}", ln=True, align="C")
            pdf.set_font("Arial", size=12)
            pdf.ln(5)
            for k, v in nueva_cita.items():
                pdf.cell(0, 10, f"{k.upper()}: {v}", ln=True)
            pdf_output = f"cita_{str(cita_id).zfill(3)}.pdf"
            pdf.output(pdf_output)

            # Enviar por correo
            try:
                msg = EmailMessage()
                msg["Subject"] = f"CITA N.º {str(cita_id).zfill(3)} - Confirmación"
                msg["From"] = "accesoriossd@ingauto.com.ec"
                msg["To"] = [correo, "accesoriossd@ingauto.com.ec"]
                msg.set_content(f"Estimado/a {nombre}, adjunto encontrará el comprobante de su cita.")

                with open(pdf_output, "rb") as f:
                    msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=pdf_output)

                with smtplib.SMTP("mail.ingauto.com.ec", 587) as smtp:
                    smtp.starttls()
                    smtp.login("accesoriossd@ingauto.com.ec", "51TBdC375q")
                    smtp.send_message(msg)

                st.success("📧 Correo enviado correctamente.")
            except Exception as e:
                st.warning(f"⚠️ Error al enviar correo: {e}")

            # Descargar PDF
            with open(pdf_output, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{pdf_output}">📥 Descargar PDF</a>'
                st.markdown(href, unsafe_allow_html=True)

if st.session_state.citas:
    st.subheader("📋 Lista de Citas")
    for i, cita in enumerate(st.session_state.citas):
        st.write(f"**CITA N.º {str(i+1).zfill(3)}** - {cita['nombre']} ({cita['placa']}) - {cita['fecha']} {cita['hora']}")
        if st.button(f"✏️ Editar cita {i+1}", key=f"editar_{i}"):
            st.session_state.edit_index = i
            for key, value in cita.items():
                st.session_state[key] = value
            st.experimental_rerun()
