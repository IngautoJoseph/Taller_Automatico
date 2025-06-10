from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import openpyxl
from openpyxl.styles import Font, Alignment
from fpdf import FPDF
import os

app = FastAPI()

# Configuración del CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos en memoria
db = []
counter = 1

# Base de datos de marcas y modelos
# Base de datos de marcas y modelos
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

# Servicios predefinidos
servicios = [
    "MANTENIMIENTO 700 KM", "MANTENIMIENTO 5,000 KM", "MANTENIMIENTO 10,000 KM",
    "MANTENIMIENTO 15,000 KM", "MANTENIMIENTO 20,000 KM", "MANTENIMIENTO 25,000 KM",
    "MANTENIMIENTO 30,000 KM", "MANTENIMIENTO 35,000 KM", "MANTENIMIENTO 40,000 KM",
    "MANTENIMIENTO 45,000 KM", "MANTENIMIENTO 50,000 KM", "CAMBIO DE ACEITE",
    "ALINEACIÓN Y BALANCEO", "REVISIÓN DE FRENOS", "DIAGNÓSTICO COMPLETO"
]

# Configuración del correo
conf = ConnectionConfig(
    MAIL_USERNAME="tucorreo@gmail.com",
    MAIL_PASSWORD="tupasswordgenerada",
    MAIL_FROM="tucorreo@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True
)

class Cita(BaseModel):
    cliente: str
    correo: str
    telefono: str
    marca: str
    modelo: str
    servicio: str
    fecha: str
    hora: str
    combustible: str

@app.get("/marcas")
async def obtener_marcas():
    return list(car_data.keys())

@app.get("/modelos/{marca}")
async def obtener_modelos(marca: str):
    return car_data.get(marca, [])

@app.get("/servicios")
async def obtener_servicios():
    return servicios

@app.get("/citas")
async def obtener_citas():
    return db

@app.post("/crear-cita")
async def crear_cita(cita: Cita):
    global counter
    if not all([cita.cliente, cita.correo, cita.telefono, cita.marca, cita.modelo, cita.servicio, cita.fecha, cita.hora, cita.combustible]):
        return JSONResponse(status_code=400, content={"error": "Todos los campos son obligatorios."})

    numero = f"CITA N.º {counter:03d}"
    nueva_cita = cita.dict()
    nueva_cita["numero"] = numero
    db.append(nueva_cita)
    counter += 1

    # Crear PDF
    pdf_file = f"cita_{numero}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "TALLER - ORDEN DE CITA", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.ln(10)

    for key, value in nueva_cita.items():
        pdf.cell(0, 10, f"{key.upper()}: {value}", ln=True)

    pdf.output(pdf_file)

    # Enviar correo
    message = MessageSchema(
        subject="Confirmación de Cita",
        recipients=[cita.correo, conf.MAIL_FROM],
        body="Adjunto encontrará el comprobante de su cita.",
        attachments=[pdf_file],
        subtype="plain"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

    return {"mensaje": "Cita creada y correo enviado exitosamente."}

@app.get("/descargar-pdf/{numero}")
async def descargar_pdf(numero: str):
    filename = f"cita_{numero}.pdf"
    if os.path.exists(filename):
        return FileResponse(filename, media_type='application/pdf', filename=filename)
    return JSONResponse(status_code=404, content={"error": "PDF no encontrado."})
