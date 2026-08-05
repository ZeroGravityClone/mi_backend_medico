from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
from datetime import datetime, date

from app.db.database import get_db
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate, DocumentResponse, DocumentUpdate
from app.repositories.patient_repository import PatientRepository
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.patient import PatientDocument

from app.core.vision_helper import convert_pdf_to_base64_images, encode_image_to_base64
from app.core.validation_helper import normalize_date, verify_document_consistency
from app.services.ai_service import AIService

router = APIRouter(prefix="/patients", tags=["patients"])

@router.get("/", response_model=List[PatientResponse])
def read_patients(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    
    if patient_in.cedula:
        existing_cedula = repo.get_by_cedula(patient_in.cedula)
        if existing_cedula:
            raise HTTPException(
                status_code=400,
                detail="Ya existe un expediente registrado con esa Cédula de Identidad."
            )
            
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
    current_admin: User = Depends(get_current_admin)
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
    current_admin: User = Depends(get_current_admin)
):
    """Elimina un paciente del sistema (Solo Administradores)."""
    repo = PatientRepository(db)
    db_patient = repo.get_by_id(patient_id)
    
    if not db_patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
        
    repo.delete(db_patient=db_patient)


# ===========================================================================
#             ENDPOINTS PARA LA GESTIÓN DE DOCUMENTOS
# ===========================================================================

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

    os.makedirs("uploads", exist_ok=True)

    timestamp = int(datetime.utcnow().timestamp())
    safe_filename = f"{patient_id}_{timestamp}_{file.filename}"
    file_path = f"uploads/{safe_filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_doc = PatientDocument(
        patient_id=patient_id,
        file_name=description,
        file_path=file_path,
        category=category,
        folder_number=folder_number,
        qr_code=qr_code,
        document_status=document_status,
        uploaded_by=current_user.id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    return {"message": "Documento indexado con éxito en la bóveda", "file_path": file_path}

@router.get("/{patient_id}/documents", response_model=List[DocumentResponse])
def get_patient_documents(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna todo el expediente documental digitalizado de un trabajador."""
    documents = db.query(PatientDocument).filter(PatientDocument.patient_id == patient_id).all()
    return documents

@router.post("/{patient_id}/documents/auto", status_code=status.HTTP_201_CREATED)
async def upload_document_auto(
    patient_id: int,
    file: UploadFile = File(...),
    mode: str = "fast",  # "fast" o "full"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pipeline DMS Premium: Recibe el escaneo de una carpeta, extrae la metadata con Llama 4, valida y guarda."""
    repo = PatientRepository(db)
    patient = repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Expediente de personal no encontrado.")

    file_bytes = await file.read()
    content_type = str(file.content_type)
    
    base64_images = []
    if "pdf" in content_type:
        base64_images = convert_pdf_to_base64_images(file_bytes, mode=mode)
    elif "image" in content_type:
        base64_images = [encode_image_to_base64(file_bytes)]
    else:
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado.")

    if not base64_images:
        raise HTTPException(status_code=400, detail="No se pudo procesar el documento visual.")

    ai_service = AIService()
    ai_data = ai_service.classify_document_vision(base64_images, mode=mode)

    ai_category = ai_data.get("category", "Otros")
    ai_name = ai_data.get("extracted_name", "")
    ai_cedula = ai_data.get("extracted_cedula", "")
    ai_date_raw = ai_data.get("extracted_date", "")
    has_signatures = ai_data.get("has_signatures_and_stamps", False)
    ai_title = ai_data.get("suggested_title", "Digitalización")

    normalized_date_str = normalize_date(ai_date_raw)
    
    is_consistent, validation_message = verify_document_consistency(
        ocr_name=ai_name,
        ocr_cedula=ai_cedula,
        worker_first=str(patient.first_name),
        worker_last=str(patient.last_name),
        worker_cedula=str(patient.cedula)
    )

    doc_status = "validado" if has_signatures and is_consistent else "digitalizado"
    if not is_consistent:
        doc_status = "incompleto"

    os.makedirs("uploads", exist_ok=True)
    timestamp = int(datetime.utcnow().timestamp())
    safe_filename = f"{patient_id}_{timestamp}_{file.filename}"
    file_path = f"uploads/{safe_filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    new_doc = PatientDocument(
        patient_id=patient_id,
        file_name=ai_title,
        file_path=file_path,
        category=ai_category,
        folder_number="S/N",
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

@router.post("/auto-register", status_code=status.HTTP_201_CREATED)
async def auto_register_worker_and_doc(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pipeline DMS Premium: Recibe el escaneo de una carpeta, extrae la ficha del trabajador, crea el expediente y guarda el documento."""
    file_bytes = await file.read()
    content_type = str(file.content_type)
    
    base64_images = []
    if "pdf" in content_type:
        base64_images = convert_pdf_to_base64_images(file_bytes, mode="fast")
    elif "image" in content_type:
        base64_images = [encode_image_to_base64(file_bytes)]
    else:
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado.")

    if not base64_images:
        raise HTTPException(status_code=400, detail="No se pudo procesar el documento visual.")

    ai_service = AIService()
    ai_data = ai_service.auto_register_worker_vision(base64_images)
    
    if not ai_data:
        raise HTTPException(status_code=500, detail="La IA no logró extraer los datos del documento.")

    first_name = ai_data.get("first_name", "")
    last_name = ai_data.get("last_name", "")
    cedula = ai_data.get("cedula", "")
    address = ai_data.get("address", "")
    raw_cargo = ai_data.get("cargo")
    cargo = str(raw_cargo).strip() if raw_cargo else "No especificado"
    if cargo.lower() in ("null", "none", "", "no especificado"):
        cargo = "No especificado"
    entry_date_raw = ai_data.get("birth_date", "")
    phone = ai_data.get("phone", "")
    email = ai_data.get("email", "")
    category = ai_data.get("category", "Otros")
    doc_title = ai_data.get("suggested_title", "Documento de Ingreso")
    remarks = ai_data.get("remarks", "Expediente digitalizado automáticamente.")

    if not first_name or not last_name or not cedula:
        raise HTTPException(status_code=422, detail="La IA no pudo detectar los campos mínimos obligatorios.")

    repo = PatientRepository(db)
    existing_worker = repo.get_by_cedula(cedula)
    if existing_worker:
         raise HTTPException(status_code=400, detail=f"El trabajador con la C.I. {cedula} ya se encuentra registrado.")

    normalized_date_str = normalize_date(entry_date_raw)
    parsed_date = date.today()
    if normalized_date_str:
        try:
            parsed_date = date.fromisoformat(normalized_date_str)
        except ValueError:
            pass

    formatted_notes = f"[ESTADO: ACTIVO] [DOCS: PENDIENTE] - {remarks}"
    
    db_patient = repo.create(PatientCreate(
        first_name=first_name,
        last_name=last_name,
        cedula=cedula,
        address=address,
        cargo=cargo,
        birth_date=parsed_date,
        phone=phone,
        email=email,
        medical_history=formatted_notes
    ))

    os.makedirs("uploads", exist_ok=True)
    timestamp = int(datetime.utcnow().timestamp())
    safe_filename = f"{db_patient.id}_{timestamp}_{file.filename}"
    file_path = f"uploads/{safe_filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    new_doc = PatientDocument(
        patient_id=db_patient.id,
        file_name=doc_title,
        file_path=file_path,
        category=category,
        folder_number="S/N",
        qr_code="",
        document_status="digitalizado",
        uploaded_by=current_user.id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return {
        "message": "Expediente de trabajador creado y primer documento archivado de forma 100% automática con IA.",
        "worker": db_patient,
        "document": {
            "title": doc_title,
            "category": category,
            "file_path": file_path
        }
    }

@router.put("/documents/{document_id}", response_model=DocumentResponse)
def update_document_metadata(
    document_id: int,
    doc_in: DocumentUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Modifica la metadata de indexación de un documento de la bóveda."""
    doc = db.query(PatientDocument).filter(PatientDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    
    for field, value in doc_in.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
        
    db.commit()
    db.refresh(doc)
    return doc



@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Elimina el registro de la base de datos y borra el archivo físico del disco del servidor."""
    doc = db.query(PatientDocument).filter(PatientDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado en la bóveda.")
        
    file_path_str = str(doc.file_path) if doc.file_path is not None else ""
    if file_path_str and os.path.exists(file_path_str):
        try:
            os.remove(file_path_str)
        except Exception as e:
            print(f"No se pudo borrar el archivo físico: {e}")
            
    db.delete(doc)
    db.commit()

@router.get("/documents/all", response_model=List[DocumentResponse])
def get_all_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el listado global de TODOS los documentos indexados en el hospital."""
    documents = db.query(PatientDocument).order_by(PatientDocument.id.desc()).all()
    return documents

@router.post("/{patient_id}/audit", response_model=PatientResponse)
def audit_worker_expediente(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analiza la base de datos de documentos de un trabajador, llama a la IA para verificar faltantes y actualiza su estatus."""
    import re
    
    repo = PatientRepository(db)
    patient = repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Expediente de personal no encontrado.")

    documents = db.query(PatientDocument).filter(PatientDocument.patient_id == patient_id).all()
    
    existing_categories = [doc.category for doc in documents]

    raw_history = patient.medical_history
    history_text = ""
    
    if raw_history is not None:
        history_text = str(raw_history)

    work_status = "ACTIVO"
    if history_text:
        full_match = re.match(r"^\[ESTADO: (.*?)\] \[DOCS: (.*?)\] - (.*)$", history_text)
        partial_match = re.match(r"^\[ESTADO: (.*?)\] - (.*)$", history_text)
        
        if full_match:
            work_status = full_match.group(1)
        elif partial_match:
            work_status = partial_match.group(1)

    ai_service = AIService()
    audit_results = ai_service.audit_expediente(
        estatus_laboral=work_status, 
        documentos_existentes=existing_categories
    )
    
    ai_doc_status = audit_results.get("document_status", "PENDIENTE")
    ai_remarks = audit_results.get("remarks", "Auditoría realizada.")

    new_formatted_notes = f"[ESTADO: {work_status}] [DOCS: {ai_doc_status}] - {ai_remarks}"
    
    setattr(patient, "medical_history", new_formatted_notes)
    db.commit()
    db.refresh(patient)

    return patient