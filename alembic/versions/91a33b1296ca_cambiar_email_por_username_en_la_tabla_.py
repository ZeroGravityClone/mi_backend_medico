"""Cambiar email por username en la tabla de usuarios

Revision ID: 91a33b1296ca
Revises: d36fc140ee6e
Create Date: 2026-07-08 20:47:41.934698

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91a33b1296ca'
down_revision: Union[str, Sequence[str], None] = 'd36fc140ee6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agregar la columna permitiendo nulos temporalmente
    op.add_column('users', sa.Column('username', sa.String(length=100), nullable=True))
    
    # 2. Copiar los datos de email a username, extrayendo la parte previa al '@'
    # Usamos split_part nativo de PostgreSQL para limpiar el correo (ej: 'jose@gmail.com' -> 'jose')
    op.execute("UPDATE users SET username = split_part(email, '@', 1)")
    
    # 3. Si por alguna razón algún registro quedó vacío, le asignamos un valor por defecto
    op.execute("UPDATE users SET username = 'usuario_migrado' WHERE username IS NULL OR username = ''")

    # 4. Ahora que todos tienen datos, aplicamos la restricción NOT NULL de forma segura
    op.alter_column('users', 'username', nullable=False)
    
    # 5. Crear el índice único para el nuevo username
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # 6. Eliminar el índice y la columna vieja de email
    op.drop_index('ix_users_email', table_name='users')
    op.drop_column('users', 'email')


def downgrade() -> None:
    # Lógica inversa en caso de querer revertir la migración
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.execute("UPDATE users SET email = username || '@hospital.com'")
    op.alter_column('users', 'email', nullable=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'username')
