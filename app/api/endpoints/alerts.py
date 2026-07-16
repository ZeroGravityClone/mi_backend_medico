from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List

from app.db.database import get_db
from app.models.patient import Loan, Patient
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/summary")
def get_system_alerts_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Genera en tiempo real el centro de alertas de préstamos, vencimientos e insolvencia documental."""
    today_date = date.today()
    alerta_48h = today_date + timedelta(days=2)
    cinco_anos_atras = today_date - timedelta(days=1825)

    # 1. PRÉSTAMOS VENCIDOS (Fecha límite expiró y estatus es ACTIVO)
    overdue_loans = db.query(Loan).filter(
        Loan.status == "ACTIVO",
        Loan.expected_return_date < today_date
    ).all()

    vencidos = []
    for ol in overdue_loans:
        vencidos.append({
            "id": ol.id,
            "borrower": ol.borrower_name,
            "patient_id": ol.patient_id,
            "due_date": str(ol.expected_return_date),
            "days_overdue": (today_date - ol.expected_return_date).days
        })

    # 2. PRÉSTAMOS POR VENCER (Vencen entre hoy y las próximas 48h)
    due_soon_loans = db.query(Loan).filter(
        Loan.status == "ACTIVO",
        Loan.expected_return_date >= today_date,
        Loan.expected_return_date <= alerta_48h
    ).all()

    por_vencer = []
    for psl in due_soon_loans:
        por_vencer.append({
            "id": psl.id,
            "borrower": psl.borrower_name,
            "patient_id": psl.patient_id,
            "due_date": str(psl.expected_return_date),
            "hours_remaining": (psl.expected_return_date - today_date).days * 24 or 24
        })

    # 3. EXPURGOS / RETENCIONES (Expedientes con fecha de ingreso > 5 años)
    expired_patients = db.query(Patient).filter(
        Patient.birth_date <= cinco_anos_atras
    ).all()

    expurgos = []
    for p in expired_patients:
        # CORRECCIÓN PYLANCE: Evitamos la evaluación booleana directa de la columna
        history_text = str(p.medical_history) if p.medical_history is not None else ""
        status = "ACTIVO"
        if "[ESTADO: EGRESADO]" in history_text:
            status = "EGRESADO"
        elif "[ESTADO: JUBILADO]" in history_text:
            status = "JUBILADO"

        action = "Archivar en Depósito Permanente"
        if status in ("EGRESADO", "FALLECIDO"):
            action = "Destrucción / Expurgo Documental Autorizado"

        expurgos.append({
            "id": p.id,
            "name": f"{p.last_name}, {p.first_name}",
            "cedula": p.cedula,
            "entry_date": str(p.birth_date),
            "status": status,
            "suggested_action": action
        })

    return {
        "overdue": vencidos,
        "due_soon": por_vencer,
        "purges": expurgos,
        "total_alerts": len(vencidos) + len(por_vencer) + len(expurgos)
    }