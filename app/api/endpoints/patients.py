from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form # <-- Agregados File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List
import shutil # <-- Requerido para escribir archivos en disco
import os     # <-- Requerido para crear directorios de almacenamiento
from datetime import datetime

from app.core.vision_helper import convert_pdf_to_base64_images, encode_image_to_base64
from app.core.validation_helper import normalize_date, verify_document_consistency
from app.services.ai_service import AIService
from app.core.pdf_helper import extract_text_from_pdf
from app.services.ai_service import AIService
from app.db.database import get_db
# Agregado "DocumentResponse" para la validación de salida de metadatos
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate, DocumentResponse
from app.repositories.patient_repository import PatientRepository
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.patient import PatientDocument # <-- Requerido para insertar en la tabla de documentos

router = APIRouter(prefix="/patients", tags=["patients"])

@router.get("/", response_model=List[PatientResponse])
def read_patients(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requiere Token válido
):
    """Lista todos los pacientes."""
    repo = PatientRepository(db)
    patients = repo.get_all(skip=skip, limit=limit)
    return patients

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Registra un nuevo expediente de trabajador (Solo Administradores)."""
    repo = PatientRepository(db)
    
    # 1. Validar duplicado de cédula
    if patient_in.cedula:
        existing_cedula = repo.get_by_cedula(patient_in.cedula)
        if existing_cedula:
            raise HTTPException(
                status_code=400,
                detail="Ya existe un expediente registrado con esa Cédula de Identidad."
            )
            
    # 2. Validar duplicado de email
    if patient_in.email:
        existing_email = repo.get_by_email(patient_in.email)
        if existing_email:
            raise HTTPException(
                status_code=400, 
                detail="Ya existe un expediente con este correo electrónico."
            )
            
    return repo.create(patient_in)

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_in: PatientUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)  # Protegido para ADMIN
):
    """Actualiza la información de un paciente (Solo Administradores)."""
    repo = PatientRepository(db)
    db_patient = repo.get_by_id(patient_id)
    
    if not db_patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
        
    return repo.update(db_patient=db_patient, patient_in=patient_in)

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)  # Protegido para ADMIN
):
    """Elimina un paciente del sistema (Solo Administradores)."""
    repo = PatientRepository(db)
    db_patient = repo.get_by_id(patient_id)
    
    if not db_patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
        
    repo.delete(db_patient=db_patient)


# ===========================================================================
#             NUEVOS ENDPOINTS: NÚCLEO DE GESTIÓN DOCUMENTAL (DMS)
# ===========================================================================

# 1. SUBIR, INDEXAR Y REGISTRAR METADATA DE DOCUMENTO (Solo visible/ejecutable si el token es válido)
@router.post("/{patient_id}/documents", status_code=status.HTTP_201_CREATED)
def upload_patient_document(
    patient_id: int,
    file: UploadFile = File(...),
    description: str = Form(...),
    category: str = Form(...),
    folder_number: str = Form(...),
    qr_code: str = Form(None),
    document_status: str = Form("digitalizado"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recibe un archivo físico digitalizado, lo almacena en disco y registra su metadata y auditoría."""
    repo = PatientRepository(db)
    patient = repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Expediente de personal no encontrado.")

    # Asegurar que exista el directorio físico en el servidor
    os.makedirs("uploads", exist_ok=True)

    # Generar nomenclatura de archivo única para auditoría
    timestamp = int(datetime.utcnow().timestamp())
    safe_filename = f"{patient_id}_{timestamp}_{file.filename}"
    file_path = f"uploads/{safe_filename}"

    # Escribir el archivo físico en disco duro
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Registrar metadata limpia en base de datos MySQL/PostgreSQL
    new_doc = PatientDocument(
        patient_id=patient_id,
        file_name=description,
        file_path=file_path,
        category=category,
        folder_number=folder_number,
        qr_code=qr_code,
        document_status=document_status,
        uploaded_by=current_user.id  # Auditoría automática del transcriptor
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    return {"message": "Documento indexado con éxito en la bóveda", "file_path": file_path}


# 2. OBTENER EXPEDIENTE DOCUMENTAL COMPLETO (Metadata y Auditoría)
@router.get("/{patient_id}/documents", response_model=List[DocumentResponse])
def get_patient_documents(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna todo el expediente documental digitalizado de un trabajador."""
    documents = db.query(PatientDocument).filter(PatientDocument.patient_id == patient_id).all()
    return documents

@router.get("/documents/all", response_model=List[DocumentResponse])
def get_all_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el listado global de TODOS los documentos indexados en el hospital."""
    documents = db.query(PatientDocument).order_by(PatientDocument.id.desc()).all()
    return documents

# 3. ESCANEAR, CONVERTIR, EVALUAR VISUALMENTE CON IA Y VALIDAR INTEGRIDAD (NUEVO PIPELINE DMS)
@router.post("/{patient_id}/documents/auto", status_code=status.HTTP_201_CREATED)
async def upload_document_auto(
    patient_id: int,
    file: UploadFile = File(...),
    mode: str = "fast",  # "fast" (primera pág.) o "full" (todo el documento)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pipeline DMS Inteligente: Recibe PDF/Imagen, procesa con IA de OpenAI en Groq, valida metadata y guarda."""
    repo = PatientRepository(db)
    patient = repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Expediente de personal no encontrado.")

    # 1. Leer archivo en memoria
    file_bytes = await file.read()
    content_type = str(file.content_type)
    
    # 2. Generar lista de imágenes en Base64 según el tipo de archivo recibido
    base64_images = []
    if "pdf" in content_type:
        base64_images = convert_pdf_to_base64_images(file_bytes, mode=mode)
    elif "image" in content_type:
        base64_images = [encode_image_to_base64(file_bytes)]
    else:
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado. Debe ser PDF o Imagen.")

    if not base64_images:
        raise HTTPException(status_code=400, detail="No se pudo procesar la imagen del documento para análisis de IA.")

    # 3. Llamar al modelo de Visión de Groq para análisis visual
    ai_service = AIService()
    ai_data = ai_service.classify_document_vision(base64_images, mode=mode)

    # Extraer variables devueltas por la IA
    ai_category = ai_data.get("category", "Otros")
    ai_name = ai_data.get("extracted_name", "")
    ai_cedula = ai_data.get("extracted_cedula", "")
    ai_date_raw = ai_data.get("extracted_date", "")
    has_signatures = ai_data.get("has_signatures_and_stamps", False)
    ai_title = ai_data.get("suggested_title", "Digitalización")

    # 4. CAPA DE VALIDACIÓN Y NORMALIZACIÓN DEL BACKEND
    # Normalizar Fecha
    normalized_date_str = normalize_date(ai_date_raw)
    
    # Verificar consistencia de la metadata contra la Base de Datos
    is_consistent, validation_message = verify_document_consistency(
        ocr_name=ai_name,
        ocr_cedula=ai_cedula,
        worker_first=str(patient.first_name),
        worker_last=str(patient.last_name),
        worker_cedula=str(patient.cedula)
    )

    # El estatus documental reflejará si la IA detectó firmas y sellos reales
    doc_status = "validado" if has_signatures and is_consistent else "digitalizado"
    if not is_consistent:
        doc_status = "incompleto"

    # 5. Guardar físicamente el archivo original en disco
    os.makedirs("uploads", exist_ok=True)
    timestamp = int(datetime.utcnow().timestamp())
    safe_filename = f"{patient_id}_{timestamp}_{file.filename}"
    file_path = f"uploads/{safe_filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    # 6. Registrar los metadatos limpios, normalizados y validados en la base de datos
    new_doc = PatientDocument(
        patient_id=patient_id,
        file_name=ai_title,
        file_path=file_path,
        category=ai_category,
        folder_number="S/N", # Se puede indexar después
        qr_code="",
        document_status=doc_status,
        uploaded_by=current_user.id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return {
        "message": "Expediente digitalizado, verificado por la IA y auditado por el backend con éxito.",
        "category": ai_category,
        "suggested_title": ai_title,
        "file_path": file_path,
        "validation": {
            "is_consistent": is_consistent,
            "message": validation_message,
            "date_detected_normalized": normalized_date_str,
            "has_signatures_and_stamps": has_signatures
        }
    }

# 4. AUDITAR EXPEDIENTE AUTOMÁTICAMENTE CON IA (CORREGIDO Y OPTIMIZADO PARA PYLANCE)
@router.post("/{patient_id}/audit", response_model=PatientResponse)
def audit_worker_expediente(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analiza la base de datos de documentos de un trabajador, llama a la IA para verificar faltantes y actualiza su estatus."""
    import re  # Importamos la librería de expresiones regulares de Python
    
    repo = PatientRepository(db)
    patient = repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Expediente de personal no encontrado.")

    # 1. Obtener todos los documentos del paciente en la base de datos
    documents = db.query(PatientDocument).filter(PatientDocument.patient_id == patient_id).all()
    
    # 2. Extraer una lista limpia con las categorías de los documentos ya digitalizados
    existing_categories = [doc.category for doc in documents]

    # 3. Convertimos explícitamente a tipos nativos para que Pylance esté contento
    raw_history = patient.medical_history
    history_text = ""
    
    # Evaluamos usando comparación explícita contra None (evita el error de __bool__)
    if raw_history is not None:
        history_text = str(raw_history)

    # 4. Desempaquetar el estatus laboral de forma segura usando el texto casteado
    work_status = "ACTIVO"
    if history_text:
        full_match = re.match(r"^\[ESTADO: (.*?)\] \[DOCS: (.*?)\] - (.*)$", history_text)
        partial_match = re.match(r"^\[ESTADO: (.*?)\] - (.*)$", history_text)
        
        if full_match:
            work_status = full_match.group(1)
        elif partial_match:
            work_status = partial_match.group(1)

    # 5. Ejecutar la Auditoría Inteligente con Groq
    ai_service = AIService()
    audit_results = ai_service.audit_expediente(
        estatus_laboral=work_status, 
        documentos_existentes=existing_categories
    )
    
    ai_doc_status = audit_results.get("document_status", "PENDIENTE")
    ai_remarks = audit_results.get("remarks", "Auditoría realizada.")

    # 6. Empaquetar el nuevo resultado y guardarlo en la base de datos
    new_formatted_notes = f"[ESTADO: {work_status}] [DOCS: {ai_doc_status}] - {ai_remarks}"
    
    # Actualizar el registro del paciente usando setattr
    setattr(patient, "medical_history", new_formatted_notes)
    db.commit()
    db.refresh(patient)

    return patient