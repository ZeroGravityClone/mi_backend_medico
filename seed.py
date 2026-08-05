import random
from datetime import date, timedelta
import unicodedata
from app.db.database import SessionLocal
from app.models.patient import Patient

first_names = [
    "Carlos", "María", "Pedro", "Ana", "Juan", "José", "Carmen", "Luis", 
    "Francisco", "Miguel", "Isabel", "Rafael", "Elena", "Jorge", "Lucía", 
    "Manuel", "Gabriela", "Andrés", "Patricia", "Alejandro", "Sofía"
]
last_names = [
    "Gómez", "Rodríguez", "Mendoza", "Silva", "Hernández", "Pérez", 
    "González", "Martínez", "Torres", "Ramírez", "Sánchez", "Díaz", 
    "Álvarez", "Castillo", "Morales", "Vargas", "Rojas", "Herrera"
]
statuses = ["ACTIVO", "EGRESADO", "SEGURO SOCIAL", "JUBILADO", "VACACIONES"]
doc_statuses = ["COMPLETO", "PENDIENTE", "CRITICO"]
addresses = [
    "Av. Principal Sabana Grande, Edif. El Sol, Apto 4B",
    "Sector Centro, Calle Libertad, Casa Nro. 45",
    "Urb. Las Acacias, Vereda 12, Casa 3",
    "Av. Francisco de Miranda, Res. Avila, Piso 10",
    "Urb. El Marqués, Calle El Limón, Quinta Mi Refugio",
    "La Candelaria, Esquina El Ancla, Edif. Parque Centro",
    "Sector El Paraíso, Av. Páez, Res. Galaxia, Apto 1A",
    "Casco Central, Calle Sucre, Nro. 12-B",
    "Urb. San Bernardino, Av. Patria, Res. Los Pinos"
]
notes_pool = [
    "Expediente físico completo en caja de archivo A-12, carpeta marrón.",
    "Falta firma de recepción en planilla de ingreso de RRHH.",
    "Carpeta digitalizada parcialmente. Folios del 1 al 15 validados.",
    "Registro de nómina histórica física en buen estado.",
    "Se requiere actualizar comprobante de Seguro Social (IVSS).",
    "Carpeta deteriorada por antigüedad, se sugiere re-archivar físicamente.",
    "Expediente auditado por la dirección general sin observaciones."
]

def generate_random_date(start_year=2015, end_year=2026):
    """Genera una fecha de ingreso aleatoria."""
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def clean_string(txt):
    """Limpia tildes y caracteres especiales para generar correos limpios."""
    return "".join(
        c for c in unicodedata.normalize('NFD', txt)
        if unicodedata.category(c) != 'Mn'
    ).lower().replace(" ", "")

def seed_data():
    db = SessionLocal()
    print("🚀 Iniciando la inserción de 100 expedientes de prueba de forma segura...")
    
    try:
        current_count = db.query(Patient).count()
        needed = 100 - current_count

        if needed <= 0:
            print(f"La base de datos ya tiene {current_count} registros. No es necesario agregar más.")
            return

        print(f"Actualmente hay {current_count} registros. Generando {needed} nuevos registros...")
        
        inserted_count = 0
        
        while inserted_count < needed:
            fn_raw = random.choice(first_names)
            ln_raw = random.choice(last_names)
            
            fn_clean = clean_string(fn_raw)
            ln_clean = clean_string(ln_raw)
            
            cedula_num = random.randint(5000000, 30000000)
            cedula = f"V-{cedula_num}"
            
            existing_cedula = db.query(Patient).filter(Patient.cedula == cedula).first()
            if existing_cedula:
                continue
                
            email_addr = f"{fn_clean}.{ln_clean}{random.randint(10, 999)}@hospital.com"
            existing_email = db.query(Patient).filter(Patient.email == email_addr).first()
            if existing_email:
                continue
            
            status = random.choice(statuses)
            doc_status = random.choice(doc_statuses)
            notes = random.choice(notes_pool)
            
            formatted_notes = f"[ESTADO: {status}] [DOCS: {doc_status}] - {notes}"
            
            patient = Patient(
                first_name=fn_raw,
                last_name=ln_raw,
                cedula=cedula,
                address=random.choice(addresses),
                birth_date=generate_random_date(), 
                phone=f"0412-{random.randint(1000000, 9999999)}",
                email=email_addr,
                medical_history=formatted_notes
            )
            db.add(patient)
            inserted_count += 1
        
        db.commit()
        print(f"✅ ¡Éxito! Se han insertado {needed} nuevos registros sin colisiones de unicidad.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error al sembrar datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()