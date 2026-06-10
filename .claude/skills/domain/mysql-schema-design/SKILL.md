# Skill: mysql-schema-design

> Convenções de schema MySQL 8 para o {PROJETO}: CHAR(36) UUID, DECIMAL(10,2), DATETIME(6), naming, indexes, FULLTEXT, SQLAlchemy 2.0 async, Alembic.
> Categoria: `domain` · 2026-04-18

## Propósito

Manter o schema do {PROJETO} consistente. As 20 tabelas atuais (16 MVP + 4 Fase 2) seguem convenções específicas — este documento é a referência para toda nova tabela, coluna, índice ou migration.

## Quando usar (triggers)

- Nova tabela
- Nova coluna em tabela existente
- Novo índice
- Nova migration Alembic
- Alterar tipo de coluna
- Adicionar FULLTEXT
- Code review de migration

---

## 1. Tipos padrão {PROJETO}

| Conceito | Tipo MySQL | SQLAlchemy |
|---|---|---|
| Identificador primário | `CHAR(36)` | `Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid4()))` |
| Foreign key | `CHAR(36)` | `Mapped[str] = mapped_column(CHAR(36), ForeignKey('users.id', ondelete='CASCADE'))` |
| String curta (nome, título) | `VARCHAR(255)` | `Mapped[str] = mapped_column(String(255))` |
| String longa (descrição, bio) | `TEXT` | `Mapped[str] = mapped_column(Text)` |
| String muito longa (conteúdo, histórico) | `MEDIUMTEXT` | `Mapped[str] = mapped_column(MEDIUMTEXT)` |
| Email | `VARCHAR(320)` | `Mapped[str] = mapped_column(String(320), unique=True)` |
| Dinheiro | `DECIMAL(10,2)` | `Mapped[Decimal] = mapped_column(Numeric(10, 2))` |
| Boolean | `TINYINT(1)` | `Mapped[bool] = mapped_column(Boolean)` |
| Timestamp | `DATETIME(6)` | `Mapped[datetime] = mapped_column(DateTime(6))` |
| Status / enum | `VARCHAR(20)` com CHECK constraint | `Mapped[str] = mapped_column(String(20))` — **não usar ENUM nativo** |
| JSON (raro) | `JSON` | `Mapped[dict] = mapped_column(JSON)` |
| Coordenada geográfica | `DECIMAL(10,7)` lat, `DECIMAL(10,7)` lng | — (Fase 3) |

**Por que `CHAR(36)` e não `BINARY(16)` ou `UUID` nativo?**
- MySQL 8 ainda não tem tipo `UUID` nativo robusto
- `CHAR(36)` é debugável (você lê o valor direto no `SELECT`)
- Geramos em Python, não no MySQL → compatibilidade com SQLAlchemy async

**Por que `DATETIME(6)` e não `DATETIME`?**
- `(6)` armazena microssegundos — obrigatório para ordering preciso de eventos (mensagens, timeline)
- Sem isso, duas mensagens no mesmo segundo ficam desordenadas

---

## 2. Charset e collation

```python
# apps/api/app/models/base.py
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

metadata = MetaData(
    naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s',
    },
)

class Base(DeclarativeBase):
    metadata = metadata

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci',
    }
```

**Nunca** `utf8` (alias do `utf8mb3`, não suporta emoji). Sempre `utf8mb4`.

---

## 3. Colunas obrigatórias em toda tabela

```python
from datetime import datetime
from sqlalchemy import text

class User(Base):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True, default=lambda: str(uuid4()))
    # ... colunas do domínio ...

    # Obrigatórias:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(6),
        server_default=text('CURRENT_TIMESTAMP(6)'),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(6),
        server_default=text('CURRENT_TIMESTAMP(6)'),
        onupdate=text('CURRENT_TIMESTAMP(6)'),
        nullable=False,
    )

    # Soft delete (recomendado para dados importantes):
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(6), nullable=True)
```

**Detalhe crítico:** `server_default=text('CURRENT_TIMESTAMP(6)')` (não `func.current_timestamp(6)`) — a forma `text()` é compatível com SQLite (testes) + MySQL (produção). Decisão registrada no `.planning/STATE.md`.

---

## 4. Foreign keys e cascade

```python
# Regra: dados que "pertencem" ao pai → CASCADE
# Dados históricos/fiscais → RESTRICT ou SET NULL

portfolio_images = relationship(
    'PortfolioImage',
    cascade='all, delete-orphan',  # deletar profissional apaga portfolio
    back_populates='professional',
)

payments = relationship(
    'Payment',
    # NÃO cascade — pagamentos são históricos fiscais
    back_populates='client',
)
```

```sql
-- migration
ALTER TABLE portfolio_images
  ADD CONSTRAINT fk_portfolio_images_professional
  FOREIGN KEY (professional_id) REFERENCES professionals(id)
  ON DELETE CASCADE;

ALTER TABLE payments
  ADD CONSTRAINT fk_payments_client
  FOREIGN KEY (client_id) REFERENCES users(id)
  ON DELETE RESTRICT;
```

---

## 5. Indexes

### Regra: crie índice em toda coluna que entra em `WHERE`, `ORDER BY`, `JOIN`

```python
class ServiceRequest(Base):
    __tablename__ = 'service_requests'

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    client_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey('users.id'), index=True)
    professional_id: Mapped[str] = mapped_column(CHAR(36), ForeignKey('professionals.id'), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(6))

    __table_args__ = (
        # Índice composto para queries comuns
        Index('ix_service_requests_client_status', 'client_id', 'status'),
        Index('ix_service_requests_created_at', 'created_at'),
    )
```

### FULLTEXT (busca por texto)

```python
# Alembic migration
def upgrade():
    op.create_table('services', ...)

    # ⚠️ FULLTEXT via op.execute, não create_index
    # (decisão registrada em STATE.md — mais confiável no MySQL 8)
    op.execute(
        "CREATE FULLTEXT INDEX ix_services_fulltext ON services (name, description)"
    )

def downgrade():
    op.execute("DROP INDEX ix_services_fulltext ON services")
    op.drop_table('services')
```

**Uso em query:**

```python
# Atenção: aiosqlite (testes) não suporta MATCH AGAINST
# Usar .ilike() como fallback nos testes (registrado no STATE.md)

async def search_services(db: AsyncSession, q: str) -> list[Service]:
    if settings.ENV == 'test':
        stmt = select(Service).where(Service.name.ilike(f'%{q}%'))
    else:
        stmt = text("""
            SELECT * FROM services
            WHERE MATCH(name, description) AGAINST (:q IN NATURAL LANGUAGE MODE)
            ORDER BY MATCH(name, description) AGAINST (:q IN NATURAL LANGUAGE MODE) DESC
            LIMIT 20
        """).bindparams(q=q)
    return list(await db.scalars(stmt))
```

---

## 6. Naming conventions

| Regra | Exemplo |
|---|---|
| Tabela no plural | `users`, `professionals`, `service_requests` |
| Join table | `professional_categories` (ordem alfabética) |
| FK column | `<tabela_singular>_id` → `user_id`, `professional_id` |
| Boolean | `is_<adj>` ou `has_<noun>` → `is_active`, `has_verified_docs` |
| Timestamp | `<verb>_at` → `created_at`, `deleted_at`, `approved_at` |
| Enum string | singular → `status`, `type`, `role` |
| Monetário | `price`, `amount`, `fee`, `total` (sempre DECIMAL(10,2)) |

---

## 7. Check constraints

MySQL 8 suporta CHECK constraints. Use para enums:

```python
class Payment(Base):
    status: Mapped[str] = mapped_column(String(20))

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'held', 'released', 'refunded', 'failed')",
            name='valid_status',
        ),
    )
```

---

## 8. Migrations Alembic (padrão {PROJETO})

```python
# alembic/versions/2026_04_15_0001_create_service_requests.py
"""Create service_requests table.

Revision ID: abc123
Revises: def456
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR

revision = 'abc123'
down_revision = 'def456'

def upgrade() -> None:
    op.create_table(
        'service_requests',
        sa.Column('id', CHAR(36), primary_key=True),
        sa.Column('client_id', CHAR(36), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('professional_id', CHAR(36), sa.ForeignKey('professionals.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), onupdate=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'active', 'completed', 'cancelled')", name='ck_service_requests_valid_status'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index('ix_service_requests_client_id', 'service_requests', ['client_id'])
    op.create_index('ix_service_requests_status', 'service_requests', ['status'])

def downgrade() -> None:
    op.drop_index('ix_service_requests_status', 'service_requests')
    op.drop_index('ix_service_requests_client_id', 'service_requests')
    op.drop_table('service_requests')
```

**Migration sempre tem downgrade funcional.** Teste rodando `alembic downgrade -1` e `upgrade head`.

---

## Anti-patterns

1. ❌ **Usar ENUM nativo** — inflexível, mudar valor exige ALTER TABLE caro; use VARCHAR + CHECK
2. ❌ **UUID gerado no MySQL** (`DEFAULT (UUID())`) — inconsistente entre ambientes, quebra testes
3. ❌ **`DATETIME` sem `(6)`** — ordenação de eventos com colisão no mesmo segundo
4. ❌ **`float` para dinheiro** — perde precisão; sempre `DECIMAL(10,2)`
5. ❌ **`utf8`** em vez de `utf8mb4` — quebra com emoji
6. ❌ **`created_at` com `DEFAULT NULL`** — valores NULL em análise temporal
7. ❌ **FK `ON DELETE CASCADE` em dados fiscais** (pagamentos, logs) — apaga histórico ao deletar usuário
8. ❌ **Falta de `ix_` no prefix** do índice — viola naming convention do projeto
9. ❌ **Índice em coluna boolean isolada** — seletividade baixa, MySQL ignora
10. ❌ **FULLTEXT via `create_index`** Alembic — gera SQL errado no MySQL 8; use `op.execute`
11. ❌ **Migration sem `downgrade`** real — impossível reverter em produção
12. ❌ **Chave primária composta** em tabelas transacionais — complica FK e ORM; prefira surrogate `id`

---

## Checklist de review de migration

- [ ] Naming convention respeitada (`ix_`, `uq_`, `fk_`, `ck_`, `pk_`)
- [ ] Charset `utf8mb4` + collation `utf8mb4_unicode_ci`
- [ ] Engine `InnoDB`
- [ ] `created_at` + `updated_at` em `DATETIME(6)` com `server_default=text('CURRENT_TIMESTAMP(6)')`
- [ ] UUIDs `CHAR(36)` gerados no Python
- [ ] Money em `Numeric(10, 2)` / `DECIMAL(10,2)`
- [ ] FKs com `ondelete` explícito (CASCADE ou RESTRICT, nunca default)
- [ ] Índices em colunas de `WHERE`/`ORDER BY`/`JOIN`
- [ ] FULLTEXT via `op.execute`, não `create_index`
- [ ] CHECK constraint para enums
- [ ] `downgrade()` funcional e testado
- [ ] Migration atômica (uma feature = uma migration)

<!-- Skill aplicada: alembic/versions/*, apps/api/app/models/* -->
