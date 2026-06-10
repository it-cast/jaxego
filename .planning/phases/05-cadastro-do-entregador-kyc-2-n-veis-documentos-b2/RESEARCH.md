# Phase 5: Cadastro do entregador + KYC 2 níveis + documentos B2 — Research

**Researched:** 2026-06-10
**Domain:** KYC onboarding (PII sensível) + upload de documentos para object storage privado S3-compatible (Backblaze B2) + máquina de estados + validação MEI (Receita)
**Confidence:** HIGH (padrões da Phase 4 reusados, verificados em código; libs verificadas no PyPI; OWASP/LGPD citados de skill)

## Summary

A Phase 5 estende o backend FastAPI existente com duas entidades novas (`couriers`, `courier_documents`) e o fluxo F-02 (wizard de cadastro + KYC 2 níveis com aprovação item-a-item do admin de área). O grosso da infraestrutura JÁ EXISTE e DEVE ser reusado: o padrão de adapter `Protocol + httpx impl + Stub` (`apps/api/app/integrations/base.py`/`factory.py`), o SSRF guard `assert_safe_url` (`integrations/http.py`), o adapter Receita com fallback (`integrations/receita.py`) — usado tal-e-qual para validar o MEI —, as máscaras de PII (`core/logging.py`: `mask_document`/`mask_email`/`mask_phone`), a máquina de estados explícita (`merchants/state_machine.py`), o padrão de OTP aware-UTC (`merchants/otp.py`), os mixins de schema (`db/mixins.py`: `AreaScopedMixin`, `UTC_DATETIME`, `ensure_aware_utc`) e o job de revalidação backoff aware-UTC (`workers/revalidate.py`). A novidade real é o **storage adapter para B2** (presigned URL) e o **pipeline de validação/reprocessamento de imagem** (magic bytes, compressão WebP, strip EXIF, hash SHA-256).

A abordagem central é **upload direto cliente→B2 por presigned URL** (o byte do documento NUNCA passa pelo backend), com o backend atuando em três momentos: (1) emite a presigned URL escopada (método PUT, key, content-type, expiração curta); (2) após o cliente reportar upload OK, o backend **baixa o objeto do B2** (via presigned GET interno), **valida magic bytes + content-type + tamanho**, **reprocessa a imagem com Pillow** (resize máx 1920px, re-encode WebP, strip de TODO EXIF), **confirma o SHA-256** declarado pelo cliente, e **regrava** o derivado limpo; (3) expõe o documento ao admin de área SÓ por presigned GET de expiração curta, com autorização por papel+área. B2 é S3-compatible: `boto3` contra o endpoint S3 da B2 com `signature_version='s3v4'` é o caminho recomendado (não `b2sdk` — ver LOW confidence). Testes não tocam B2: o `StorageStubAdapter` devolve URLs fake e simula upload em filesystem temporário.

**Primary recommendation:** Reusar TODO o padrão de adapter/SSRF/PII/state-machine/aware-UTC da Phase 4; adicionar `StoragePort` (boto3 S3v4 contra endpoint B2 + Stub); fazer **validação + reprocessamento de imagem server-side obrigatório pós-upload** (magic bytes, Pillow re-encode WebP, strip EXIF, confirmação SHA-256); bucket B2 100% privado, acesso só por presigned GET curto autorizado por ownership+área; reusar o adapter Receita para MEI/CNAEs com flag `mei_pending` (RN-024).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Wizard F-02 (passos 1-6) | Mobile (Ionic) + Frontend | API | UI multi-step com salvamento parcial; API valida e persiste cada etapa |
| Upload do byte do documento | Browser/Device → B2 (CDN/Storage) | API (emite presigned) | Byte vai direto cliente→B2; backend nunca recebe o arquivo bruto no request (resiliência + custo) |
| Emissão de presigned URL | API/Backend | — | Segredo da conta B2 só no backend; URL escopada e curta |
| Validação/reprocessamento de imagem | API/Backend (worker) | — | Magic bytes, Pillow re-encode, strip EXIF, SHA-256 — server é autoridade |
| KYC item-a-item (aprovar/reprovar) | API/Backend | Frontend admin (tela 19) | Decisão de negócio + audit_log no backend; UI só dispara |
| Máquina de estados courier/documento | API/Backend | Database (status persistido) | Transições explícitas validadas no servidor (RN-002/RN-012) |
| Validação MEI (situação+CNAEs) | API/Backend (adapter Receita) | Worker (revalidação) | Reuso do adapter Phase 4; degradação E4 → job |
| Job de expiração de documentos | Worker (arq) | Database | CNH/CRLV/MEI vencem; aware-UTC; transita documento para re-upload |
| Armazenamento dos documentos | Database (metadados) + B2 (bytes) | — | DB guarda key/hash/status/expiração; B2 guarda só o byte privado |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| boto3 | 1.43.27 `[VERIFIED: pip index versions]` | Cliente S3-compatible p/ gerar presigned PUT/GET contra o endpoint S3 da Backblaze B2 | B2 expõe API S3-compatible; boto3 é a referência S3, `generate_presigned_url` é a operação canônica `[CITED: github.com/boto/boto3 docs/source/guide/s3-presigned-urls.rst]` |
| Pillow | 12.2.0 `[VERIFIED: pip index versions; pip show = 12.2.0 instalado]` | Validar/reprocessar imagem: resize, re-encode WebP, strip EXIF, anti decompression-bomb | Fork canônico do PIL; `Image.thumbnail`/`save(format="WEBP")`/`MAX_IMAGE_PIXELS` `[CITED: pillow.readthedocs.io]` |
| httpx | >=0.28.1 (já no projeto) `[VERIFIED: pyproject.toml]` | Cliente do backend para baixar o objeto do B2 pós-upload (validação) via presigned GET interno | Já é o cliente do projeto; passa pelo `assert_safe_url` (allowlist B2) |
| arq | >=0.26,<0.27 (já no projeto) `[VERIFIED: pyproject.toml]` | Worker do job de expiração de documentos + reprocessamento assíncrono | Já é o worker do projeto (`workers/revalidate.py`) |
| structlog | >=24.1,<26 (já no projeto) `[VERIFIED: pyproject.toml]` | Logging JSON sem PII (máscaras já existentes) | Padrão estabelecido (`core/logging.py`) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| botocore (transitivo de boto3) | acompanha boto3 1.43.x | `Config(signature_version='s3v4', s3={'addressing_style':'path'})` p/ B2 | Sempre — B2 endpoint exige S3v4; ver pitfall de addressing style |
| aioboto3 | 15.5.0 `[VERIFIED: pip index versions]` | Alternativa async se quiser gerar presigned sem `run_in_executor` | OPCIONAL — boto3 síncrono é suficiente p/ presigned (operação local, sem rede) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| boto3 (S3v4 → endpoint B2) | b2sdk 2.12.0 (SDK nativo B2) | `[LOW confidence — virar task]` b2sdk é nativo B2 (auth por application keys, `get_download_authorization`), mas QUEBRA o padrão "tudo é S3-compatible atrás de um StoragePort". boto3 mantém um único contrato; a Phase 9 (`jaxego-proofs-prod`) e assets públicos reusam o mesmo adapter. **Recomendação: boto3.** |
| presigned PUT (`generate_presigned_url('put_object')`) | presigned POST (`generate_presigned_post`, com policy + conditions) | POST permite impor `content-length-range` e `Content-Type` na POLICY (servidor força limite de tamanho ANTES do upload chegar); PUT é mais simples mas o limite de tamanho fica só na validação pós-upload. **Recomendação: avaliar presigned POST p/ impor `content-length-range` — ver Security Baseline TH-upload.** `[CITED: boto3 generate_presigned_post Conditions]` |
| Reprocessar com Pillow | Aceitar o upload original sem re-encode | Re-encode é a defesa central contra polyglot/EXIF malicioso/decompression-bomb. **Nunca** servir o byte original. |

**Installation:**
```bash
# no apps/api/pyproject.toml, adicionar:
#   "boto3>=1.43,<2",
#   "Pillow>=12.2,<13",
uv add "boto3>=1.43,<2" "Pillow>=12.2,<13"
```

**Version verification (executado nesta sessão):**
- `boto3` → 1.43.27 mais recente; 1.43.6 instalado (transitivo via supabase libs). Fixar `>=1.43,<2`. `[VERIFIED]`
- `Pillow` → 12.2.0 mais recente E instalado. `[VERIFIED]`
- `aioboto3` → 15.5.0; `b2sdk` → 2.12.0 (não recomendado, ver acima). `[VERIFIED]`
- Python do projeto: `==3.13.*` `[VERIFIED: pyproject.toml]`. boto3/Pillow suportam 3.13.

## Architecture Patterns

### System Architecture Diagram

```
[App Ionic / Web]                          [FastAPI /v1]                    [Backblaze B2]
       │                                          │                          (jaxego-kyc-prod
       │  1. POST /couriers/signup (etapa N)      │                            PRIVADO)
       │─────────────────────────────────────────▶│                               │
       │     (dados PII; body NUNCA logado)        │ persiste courier/etapa        │
       │                                          │ valida CPF, SMS-OTP, e-mail   │
       │                                          │                               │
       │  2. POST /couriers/{id}/documents        │                               │
       │     {kind, sha256_client, content_type}  │                               │
       │─────────────────────────────────────────▶│ cria courier_document         │
       │                                          │  status=pending_upload        │
       │                                          │ assert_safe_url(B2 allowlist) │
       │                                          │ presign PUT (key, ct, 5min)   │
       │   ◀──────────────── presigned PUT URL ────│                               │
       │                                          │                               │
       │  3. PUT byte direto no B2 ───────────────────────────────────────────────▶│ (objeto cru)
       │                                          │                               │
       │  4. POST /couriers/{id}/documents/{d}/complete                            │
       │─────────────────────────────────────────▶│  [worker assíncrono]          │
       │                                          │  presign GET interno ─────────▶│ baixa cru
       │                                          │  ◀─────────────────────────────│
       │                                          │  validate magic bytes+ct+size │
       │                                          │  Pillow: resize 1920 + WebP   │
       │                                          │          + strip TODO EXIF    │
       │                                          │  confirma SHA-256 do derivado │
       │                                          │  regrava derivado ────────────▶│ (objeto limpo)
       │                                          │  status=pending (p/ revisão)  │
       │                                          │                               │
[Admin de área]                                   │                               │
       │  GET /admin/.../documents/{d}/view-url   │                               │
       │─────────────────────────────────────────▶│ authz: ownership + área       │
       │                                          │ presign GET (60-300s) ────────▶│
       │   ◀──────────────── presigned GET URL ────│                               │
       │  PATCH .../documents/{d} {approve|reject} │ máquina estados + audit_log   │
       │─────────────────────────────────────────▶│ se todos approved → courier   │
       │                                          │   active (nível atingido)     │
                                                  │                               │
[Worker arq: expiração]  ──── varre CNH/CRLV/MEI vencidos (aware-UTC) ───▶ status→expired/re-upload
[Worker arq: MEI]        ──── reusa ReceitaPort (situação + CNAEs) ──────▶ mei_pending (RN-024)
```

### Recommended Project Structure
```
apps/api/app/
├── couriers/
│   ├── models.py          # Courier (AreaScoped), CourierDocument
│   ├── schemas.py         # Pydantic v2, extra="forbid", enums estreitos
│   ├── router.py          # /v1/couriers (signup público + etapas auth)
│   ├── service.py         # orquestra wizard, KYC, transições + audit
│   ├── state_machine.py   # COURIER_TRANSITIONS + DOCUMENT_TRANSITIONS
│   ├── kyc.py             # regras de nível simple/complete (RN-002)
│   └── documents.py       # presign + validação + reprocess pipeline
├── integrations/
│   ├── base.py            # + StoragePort (Protocol) + PresignResult
│   ├── storage.py         # StorageB2Adapter (boto3 S3v4 + assert_safe_url)
│   ├── storage_stub.py    # StorageStubAdapter (FS temp, URLs fake)
│   └── factory.py         # + get_storage_adapter()
├── media/
│   ├── validation.py      # magic bytes (allowlist), content-type, tamanho
│   └── reprocess.py       # Pillow: resize 1920 + WebP + strip EXIF + sha256
└── workers/
    ├── document_reprocess.py   # job pós-upload (download→validate→reprocess→regrava)
    └── document_expiry.py      # job de expiração CNH/CRLV/MEI (aware-UTC)
```

### Pattern 1: StoragePort (Protocol + boto3 impl + Stub)
**What:** Mesmo padrão de `ReceitaPort`/`SmsPort`. Service depende do Protocol; factory injeta Stub em dev/test, boto3-B2 em staging/prod.
**When to use:** Toda interação com B2.
**Example:**
```python
# integrations/base.py — adicionar
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class PresignResult:
    url: str
    method: str          # "PUT" | "GET"
    expires_in: int      # segundos
    headers: dict[str, str]  # ex.: {"Content-Type": "image/jpeg"} a impor no PUT

class StoragePort(Protocol):
    """Object storage privado (B2 S3-compatible). Bytes NUNCA passam pelo backend no upload."""
    async def presign_put(self, key: str, *, content_type: str, max_bytes: int, expires_in: int) -> PresignResult: ...
    async def presign_get(self, key: str, *, expires_in: int) -> PresignResult: ...
    async def fetch(self, key: str) -> bytes: ...           # download interno p/ validação
    async def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None: ...  # regrava derivado

# integrations/storage.py — impl boto3 (presigned é operação LOCAL, sem rede → seguro chamar síncrono)
import boto3
from botocore.config import Config
from app.integrations.http import assert_safe_url

class StorageB2Adapter:
    def __init__(self, *, endpoint_url: str, region: str, key_id: str, app_key: str,
                 bucket: str, allowlist: set[str]) -> None:
        self._bucket = bucket
        self._allowlist = allowlist  # host do endpoint B2 (TH-ssrf)
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,        # ex.: https://s3.us-west-004.backblazeb2.com
            region_name=region,
            aws_access_key_id=key_id,         # B2 keyID  [segredo — só env, nunca repo]
            aws_secret_access_key=app_key,    # B2 applicationKey
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    async def presign_put(self, key, *, content_type, max_bytes, expires_in):
        url = self._client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )
        assert_safe_url(url, allowlist=self._allowlist)  # A10 — host B2 público
        return PresignResult(url=url, method="PUT", expires_in=expires_in,
                             headers={"Content-Type": content_type})
# Source: boto3 generate_presigned_url put_object  [CITED: github.com/boto/boto3 s3-presigned-urls.rst]
```

### Pattern 2: Validação + reprocessamento de imagem (Pillow) — server é autoridade
**What:** Após o cliente reportar upload OK, o backend baixa o cru, valida e regrava um derivado limpo. NUNCA serve o byte original.
**Example:**
```python
# media/reprocess.py
import hashlib, io
from PIL import Image

Image.MAX_IMAGE_PIXELS = 40_000_000  # anti decompression-bomb (DoS)  [CITED: pillow.readthedocs.io]
MAX_DIM = 1920
ALLOWED_MAGIC = {b"\xff\xd8\xff": "image/jpeg", b"\x89PNG\r\n\x1a\n": "image/png",
                 b"RIFF": "image/webp"}  # WEBP: RIFF....WEBP

def sniff_content_type(data: bytes) -> str | None:
    for magic, ct in ALLOWED_MAGIC.items():
        if data.startswith(magic):
            return ct
    return None  # extensão/content-type declarados são IGNORADOS — só magic bytes valem (A03/upload)

def reprocess_to_webp(data: bytes) -> tuple[bytes, str]:
    """Valida, resize<=1920, re-encode WebP SEM exif (strip total), devolve (bytes, sha256)."""
    if sniff_content_type(data) is None:
        raise UnsupportedMediaError()
    with Image.open(io.BytesIO(data)) as im:
        im = im.convert("RGB")          # descarta canais/metadados estranhos
        im.thumbnail((MAX_DIM, MAX_DIM))  # mantém aspecto
        out = io.BytesIO()
        im.save(out, format="WEBP", quality=80)  # NÃO passa exif= → derivado sem EXIF
    derived = out.getvalue()
    return derived, hashlib.sha256(derived).hexdigest()
# Pillow re-encode sem `exif=` produz arquivo sem EXIF — strip de GPS/serial da câmera (LGPD/TH-exif).
# Source: Pillow WebP encoder só grava exif se passado em encoderinfo  [CITED: pillow.readthedocs.io WebPImagePlugin]
```

### Pattern 3: Máquina de estados dupla (courier + documento) — espelha `merchants/state_machine.py`
```python
# couriers/state_machine.py
COURIER_TRANSITIONS = {
    "pending_kyc": {"active", "banned"},
    "active": {"suspended", "banned"},
    "suspended": {"active", "banned"},
    "banned": set(),
}
DOCUMENT_TRANSITIONS = {
    "pending_upload": {"pending"},          # upload + reprocess OK → entra na fila
    "pending": {"approved", "rejected"},    # decisão item-a-item do admin
    "approved": {"expired", "rejected"},    # expiração (job) ou revogação
    "rejected": {"pending_upload"},         # reenvio SÓ daquele item (E4) — não refaz o resto
    "expired": {"pending_upload"},
}
# assert_transition idêntico ao merchants (422 InvalidTransitionError).
```

### Pattern 4: Hash SHA-256 (cliente declara, servidor confirma)
**What:** Cliente computa sha256 do arquivo e envia em `POST /documents`. Após reprocess, o servidor registra o sha256 do **derivado** (não do cru) como fonte de verdade anti-tamper. O sha256 do cliente serve para detectar corrupção de transporte; o do derivado é o registro legal.

### Anti-Patterns to Avoid
- **Servir o byte original do B2:** sempre serve o derivado reprocessado (sem EXIF, re-encoded).
- **Confiar em extensão/content-type declarado:** validar por magic bytes; content-type do request é hint, não autoridade (A03).
- **Bucket público / URL permanente:** B2 KYC é 100% privado, só presigned GET curto (invariante de dados, ADR-004).
- **Filtro de ownership em `if` pós-fetch:** WHERE `courier_id`/`area_id` na query (A01 ownership).
- **`datetime.utcnow()` em expiração/presigned:** sempre `datetime.now(UTC)` + `ensure_aware_utc` (TD-010).
- **Logar body de signup / key+CPF:** body NUNCA logado; CPF mascarado (`mask_document`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Assinatura de URL S3/B2 | HMAC/canonical request manual | `boto3.generate_presigned_url` (S3v4) | Canonical request S3v4 é sutil; erro = URL inválida ou vazamento de escopo |
| Validar/redimensionar imagem | Parser de header próprio | Pillow (`Image.open`, `thumbnail`, `save`) | Formatos têm milhares de edge cases; bombs, polyglots |
| Strip de EXIF | Editar bytes do JPEG | Re-encode Pillow sem `exif=` | Remoção parcial deixa metadados em outros segmentos |
| SSRF guard (download do B2) | Checar IP na mão | `assert_safe_url` (já existe, `integrations/http.py`) | Já cobre IP privado/link-local/redirect (A10) |
| Máscara de PII em log | `replace` ad-hoc | `mask_document/mask_email/mask_phone` (já existe) | Denylist central testada (A09/LGPD) |
| Validação MEI/CNAEs | Cliente HTTP novo p/ Receita | `ReceitaPort`/`get_receita_adapter()` (já existe) | Fallback minhareceita→BrasilAPI + SSRF + degradação E4 prontos |
| OTP de telefone | Gerar código novo | `merchants/otp.py` (aware-UTC, lockout, compare_digest) | TD-010 + A07 já resolvidos |
| Máquina de estados | `if/elif` espalhado | `assert_transition` (padrão `merchants/state_machine.py`) | Transição inválida → 422 explícito + audit |
| Hash de arquivo | — | `hashlib.sha256` (stdlib) | Trivial, mas computar sobre o DERIVADO, não o cru |

**Key insight:** ~80% desta phase é montagem de peças que a Phase 4 já entregou. O código novo de verdade é: o `StoragePort`/B2 adapter, o pipeline `media/` (validação+reprocess), as duas máquinas de estado e o job de expiração. Tudo o mais é reuso.

## Runtime State Inventory

> Phase greenfield em termos de dados (entidades novas, sem rename). Não há estado legado a migrar. Itens de infra externa a provisionar:

| Categoria | Itens | Ação |
|-----------|-------|------|
| Live service config | Bucket `jaxego-kyc-prod` (B2, PRIVADO) + application key escopada (só este bucket, capability `readFiles`+`writeFiles`) | Provisionar no painel B2; **não** versionar a key (env/secret) |
| Secrets/env vars | `B2_KEY_ID`, `B2_APP_KEY`, `B2_ENDPOINT_URL`, `B2_REGION`, `B2_KYC_BUCKET`, `B2_ALLOWLIST_HOSTS` | Adicionar a `core/config.py` (Field default None p/ os secrets) + `.env.example` com placeholders |
| Build artifacts | Novas deps boto3/Pillow no lockfile | `uv add` + commitar lockfile |
| Stored data | Nenhum dado pré-existente | None — entidades novas |
| OS-registered state | Job de expiração entra no scheduler arq existente | Registrar cron no `workers/settings.py` |

## Common Pitfalls

### Pitfall 1: B2 endpoint rejeita presigned por addressing style / region errada
**What goes wrong:** boto3 default usa virtual-hosted addressing; o endpoint S3 da B2 funciona melhor com `path` style e a região derivada do endpoint (ex.: `us-west-004`).
**Why:** B2 é S3-compatible mas não idêntico à AWS.
**How to avoid:** `Config(signature_version="s3v4", s3={"addressing_style":"path"})`, `endpoint_url` explícito, `region_name` casando com o endpoint. `[LOW confidence — validar contra a conta B2 real no integration check]`
**Warning signs:** `SignatureDoesNotMatch`, `403` no PUT do cliente.

### Pitfall 2: presigned PUT não limita tamanho do arquivo
**What goes wrong:** presigned PUT só fixa key+content-type; um cliente malicioso sobe 5 GB.
**How to avoid:** preferir **presigned POST** com `Conditions=[["content-length-range", 1, MAX_BYTES], {"Content-Type": ct}]`; OU validar tamanho no pós-upload (worker rejeita >limite e apaga). `[CITED: boto3 generate_presigned_post Conditions]`
**Warning signs:** objeto gigante no bucket; custo B2.

### Pitfall 3: EXIF GPS vaza localização do entregador (LGPD)
**What goes wrong:** foto de selfie/documento carrega GPS+modelo da câmera no EXIF; se o byte original for servido, vaza PII de localização.
**How to avoid:** re-encode Pillow sem `exif=` (strip total). **Nota:** diferente da Phase 9 (comprovação), aqui KYC **não precisa** de GPS — então removemos 100% do EXIF.
**Warning signs:** `Image.getexif()` não-vazio no derivado em teste.

### Pitfall 4: decompression bomb (DoS)
**What goes wrong:** PNG de 64 KB que descomprime para 1 GB derruba o worker.
**How to avoid:** `Image.MAX_IMAGE_PIXELS` (Pillow alerta/erra acima do limite) + limite de bytes no upload + timeout no worker. `[CITED: pillow.readthedocs.io]`

### Pitfall 5: naive datetime em expiração de documento/presigned/OTP (TD-010)
**What goes wrong:** comparar `next_expiry_at` naive com `now()` aware → `TypeError` ou janela errada.
**How to avoid:** `UTC_DATETIME` nas colunas, `datetime.now(UTC)` sempre, `ensure_aware_utc` na leitura (padrão `db/mixins.py`/`merchants/otp.py`/`workers/revalidate.py`).

### Pitfall 6: IDOR no documento entre áreas
**What goes wrong:** admin da área A acessa presigned GET de documento de entregador da área B.
**How to avoid:** query com `WHERE area_id = scope AND courier_id = ...`; `area_scope` dependency já resolve o escopo; 404 (não 403) para fora do escopo (A01).

## Code Examples

### Gerar presigned GET para o admin revisar (autorização por área+ownership)
```python
# couriers/router.py
@router.get("/{courier_id}/documents/{doc_id}/view-url")
async def view_document(courier_id: int, doc_id: int,
                        admin = Depends(require_role("admin_area")),
                        scope: AreaScopeDep, session: SessionDep,
                        storage: StoragePort = Depends(get_storage_adapter)):
    # ownership + área NA QUERY (A01) — 404 se fora do escopo
    doc = await repo.get_document_for_area(session, doc_id, courier_id=courier_id, area_id=scope)
    if doc is None:
        raise NotFoundError()
    pres = await storage.presign_get(doc.storage_key, expires_in=180)  # 3 min (TH-presign)
    await write_audit(session, actor_id=admin.id, action="kyc.document_viewed",
                      area_id=scope, after={"doc_id": doc_id})  # acesso a PII sensível é logado (A09)
    return {"url": pres.url, "expires_in": pres.expires_in}
# Source: padrão A01 ownership-na-query + presign curto  [CITED: owasp-security A01/A10]
```

### Validação MEI reusando o adapter Receita (RN-024 / mei_pending)
```python
# couriers/service.py
COMPATIBLE_CNAES = {"4930-2/01", "4930-2/02", "5320-2/02", "5229-0/99"}  # D-07

async def validate_mei(session, courier, receita: ReceitaPort) -> None:
    result = await receita.consultar_cnpj(courier.mei_cnpj)  # reuso Phase 4 (fallback+SSRF+E4)
    active = result is not None and result.situacao == "ativa" and (
        set(result.cnaes) & COMPATIBLE_CNAES)
    courier.mei_pending = not active   # RN-024: sem MEI → só pagamento DIRETO; banner permanente
    # se result is None (Receita fora) → agenda revalidação (job, igual workers/revalidate.py)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Upload via backend (multipart → servidor → storage) | Presigned URL direto cliente→storage | padrão consolidado | Backend não vira gargalo/limite de RAM; byte não trafega 2x |
| Servir arquivo original | Re-encode + strip EXIF antes de servir | — | Defesa contra polyglot/EXIF; padronização WebP |
| `datetime.utcnow()` | aware UTC (`datetime.now(UTC)`) | deprecado no Python 3.12+ | TD-010 do projeto já adota |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | B2 funciona com boto3 S3v4 + `addressing_style="path"` + endpoint `s3.<region>.backblazeb2.com` | Pitfall 1 / Stack | Médio — presigned inválido; resolvido no integration check com conta real |
| A2 | presigned PUT é suficiente (limite de tamanho no pós-upload); ou migra p/ presigned POST | Pitfall 2 | Baixo — POST é fallback documentado; decisão de implementação |
| A3 | KYC não precisa de GPS no EXIF (diferente da comprovação Phase 9) → strip total | Security Baseline TH-exif | Baixo — confirmado pelo CONTEXT (selfie/documento, não prova de entrega) |
| A4 | Limite de tamanho por documento (ex.: 10 MB) e dimensão (1920px) | Stack / LOW | Baixo — número a fixar no PLAN com derivação |
| A5 | Antivírus/scan de malware é DEFERIDO (Pillow re-encode é a mitigação primária no piloto) | Security Baseline TH-malware / LOW | Médio — virar TD com urgency_class se não couber na phase |
| A6 | Política de retenção de documentos KYC alinha a RN-021 (anonimização 12m, exclusão conta 30d) | Security Baseline TH-lgpd | Médio — base legal/retenção precisa de confirmação jurídica (DPO) |

## Open Questions

1. **SDK B2: boto3 (S3v4) vs b2sdk nativo?**
   - Sabe-se: B2 é S3-compatible; boto3 mantém um único `StoragePort` p/ KYC, proofs (Phase 9) e assets.
   - Incerto: latência/quirks de presigned do endpoint S3 da B2 com a conta real.
   - Recomendação: **boto3**; validar no integration check (Gate 5) com a conta contratada. → vira **task de spike** no PLAN.

2. **Antivírus/scan de upload malicioso.**
   - Sabe-se: re-encode Pillow neutraliza a maioria dos vetores de imagem.
   - Incerto: se o piloto exige ClamAV/scan externo para documentos não-imagem (antecedentes pode vir PDF?).
   - Recomendação: se antecedentes for PDF, decidir pipeline próprio OU restringir a imagem; senão DEFERIR scan → **TD com urgency_class `post_launch_30d`** (Regra 12).

3. **Limites numéricos (tamanho máx, expiração presigned, dimensão).**
   - Recomendação: fixar no PLAN com derivação documentada (A04): presign PUT 5 min, presign GET admin 3 min, máx 10 MB, máx 1920px.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| boto3 | presigned B2 | a instalar | 1.43.27 disponível PyPI | — |
| Pillow | reprocess imagem | ✓ instalado | 12.2.0 | — |
| httpx | download interno B2 | ✓ (projeto) | >=0.28.1 | — |
| arq | jobs expiração/reprocess | ✓ (projeto) | >=0.26 | — |
| Backblaze B2 (conta+bucket) | storage prod/staging | ✗ a provisionar | — | **Stub em dev/test (sem rede)** — `StorageStubAdapter` |
| Receita (minhareceita/BrasilAPI) | MEI | ✓ adapter Phase 4 | — | Stub / E4 degradação |

**Missing com fallback:** B2 — coberto pelo Stub; testes/dev nunca tocam B2. Integration check (Gate 5) valida contra a conta real ou um endpoint S3 mock.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (já configurado; `pythonpath=["."]`) `[VERIFIED: pyproject.toml]` |
| Config file | `apps/api/pyproject.toml` (`[tool.pytest...]`) |
| Quick run command | `cd apps/api && uv run pytest tests/couriers -x` |
| Full suite command | `cd apps/api && uv run pytest && uv run ruff check .` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-013 | Wizard F-02 etapas + retomada 30d (E1) | integration | `pytest tests/couriers/test_wizard.py -x` | ❌ Wave 0 |
| REQ-013 | CPF mesma área bloqueia / outra área permite (E2) | unit | `pytest tests/couriers/test_signup.py::test_cpf_same_area_blocks -x` | ❌ Wave 0 |
| REQ-014 | KYC simples/completa item-a-item; reenvio só do item (E4) | unit | `pytest tests/couriers/test_kyc.py -x` | ❌ Wave 0 |
| REQ-014 | Escalação 48h sem revisão (E5) | unit (clock fake) | `pytest tests/couriers/test_escalation.py -x` | ❌ Wave 0 |
| REQ-015 | Bucket inacessível sem presigned; presign curto | integration (Stub) | `pytest tests/couriers/test_documents.py::test_no_public_access -x` | ❌ Wave 0 |
| REQ-015 | magic bytes + strip EXIF + sha256 do derivado | unit | `pytest tests/media/test_reprocess.py -x` | ❌ Wave 0 |
| REQ-019 | `mei_pending` quando MEI inativo/CNAE incompatível (E3) | unit | `pytest tests/couriers/test_mei.py -x` | ❌ Wave 0 |
| — | Transições inválidas courier/documento → 422 | unit | `pytest tests/couriers/test_state_machine.py -x` | ❌ Wave 0 |
| — | IDOR cross-área no documento → 404 | integration | `pytest tests/couriers/test_authz.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/couriers tests/media -x`
- **Per wave merge:** `uv run pytest && uv run ruff check .`
- **Phase gate:** suíte completa verde + integration check B2/Receita (Gate 5) antes de `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tests/integrations/test_storage_stub.py` — contrato do `StoragePort` (presign fake, upload simulado em FS temp)
- [ ] `tests/media/test_reprocess.py` — magic bytes, resize, EXIF stripped, sha256, bomb guard
- [ ] `tests/couriers/conftest.py` — fixtures de courier/documento + Stub injetado
- [ ] Deps: `uv add boto3 Pillow` antes de implementar

## Security Baseline (Gate 4 — OBRIGATÓRIA)

> Fonte: `.claude/skills/owasp-security/SKILL.md` (OWASP Top 10:2025 / ASVS 5.0) + `.claude/skills/br/lgpd-compliance/SKILL.md`. Feature toca PII sensível (selfie, CPF, CNH, CRLV, MEI, antecedentes) + upload + acesso admin → threat model de 15 min obrigatório (A04). O threat_model do PLAN herda desta seção (Regra 7).

### Threat model curto (A04)
- **Quem pode abusar?** entregador malicioso (sobe arquivo hostil / força documento de terceiro), admin de outra área (curiosidade/IDOR), atacante externo (presigned vazada, SSRF), insider (PII em log).
- **O que ganha?** acesso a documentos de identidade de terceiros (selfie+CPF = kit de fraude), DoS, exfiltração de PII.
- **Pior caso:** vazamento em massa de selfies+CPFs de entregadores (incidente LGPD reportável à ANPD).

### Ameaças → mitigações

| # | Ameaça | STRIDE | Mitigação | Citação owasp-security / LGPD |
|---|--------|--------|-----------|-------------------------------|
| TH-01 | Acesso não-autorizado a documento KYC | Information Disclosure | Bucket B2 **privado** (sem ACL pública); acesso SÓ por presigned GET de expiração curta (180s); autorização por papel (`require_role("admin_area")`) **e** escopo de área (`area_scope`); só dono (entregador) e admin da área. Nunca URL permanente. | A01 (auth explícita por rota; ownership na query) + A02 (HTTPS/HSTS) |
| TH-02 | Upload malicioso (polyglot, malware, EXIF hostil, formato falso) | Tampering / Elevation | **Magic bytes** (allowlist jpeg/png/webp) — content-type/extensão declarados são ignorados; **re-encode obrigatório** com Pillow (descarta payload embutido); **strip TOTAL de EXIF** (KYC não usa GPS); limite de tamanho + `MAX_IMAGE_PIXELS` (anti decompression-bomb). Servir SEMPRE o derivado, nunca o cru. | A03 (validação de entrada; path traversal no key) + A04 (insecure design) |
| TH-03 | IDOR em documento (ler doc de outro entregador/área) | Information Disclosure | `WHERE area_id = :scope AND courier_id = :cid` na query do repositório (não `if` pós-fetch); **404** (não 403) para fora do escopo (não vazar existência); key do objeto = ULID não-sequencial. | A01 (tenant_id no WHERE; 404; IDs não-sequenciais) |
| TH-04 | SSRF na geração/fetch de URL do B2 (download interno pós-upload) | Spoofing / Information Disclosure | `assert_safe_url(url, allowlist=B2_hosts)` ANTES de conectar e após redirect; cliente httpx com `follow_redirects=False`; allowlist só o host do endpoint B2; rejeita IP privado/link-local/metadata (169.254.169.254). **Reuso de `integrations/http.py`.** | A10 (allowlist host + rejeita IP interno + revalida pós-redirect) |
| TH-05 | PII em log (CPF, documentos, telefone, e-mail) | Information Disclosure | Body de signup/documento **NUNCA** logado; máscara central `mask_document`/`mask_email`/`mask_phone` (denylist em `config.json`); key do objeto não contém CPF; acesso a documento é logado SEM o conteúdo (só `doc_id`+`actor`). | A09 (PII em log = FAIL-BLOCK; redação estrutural) + LGPD (logs sem PII) |
| TH-06 | Presigned URL vazada (compartilhada/interceptada) | Information Disclosure | Expiração curta (PUT 5 min, GET 3 min); escopo de **método** (PUT só grava aquela key; GET só lê) e de **key** específica; HTTPS only; URL não logada. Vazamento expira sozinho. | A01/A02 (escopo mínimo, TLS) + A04 |
| TH-07 | Tampering do documento pós-upload | Tampering | **SHA-256** do derivado registrado em `courier_documents` (fonte de verdade); cliente declara sha256 do cru (detecta corrupção de transporte); qualquer regravação muda o hash → detectável. | A08 (integridade; `compare_digest` em comparações) |
| TH-08 | Abuso da consulta MEI/Receita (enumeração de CNPJ / DoS no provedor) | DoS | Rate limit no endpoint de signup/etapa (reuso `signup_rate_limit`, derivação documentada); adapter Receita já tem timeout curto + fallback + degradação E4; CNPJ nunca logado. | A04 (rate limit derivado) + A10 (allowlist Receita) + A09 |
| TH-09 | Escalonamento cross-área no painel admin (admin vê fila de outra área) | Elevation of Privilege | Fila de KYC filtrada por `area_id = scope` na query; `area_scope` retorna o escopo do token; admin de plataforma cross-área é AUDITADO (nunca silencioso); 48h-escalação dá visibilidade ao admin plataforma sem dar a outro admin de área. | A01 (rotas admin com dependency separada; multi-tenant WHERE) |
| TH-10 | Brute force / lockout no OTP de telefone | Spoofing | Reuso `merchants/otp.py`: 6 dígitos, TTL 10 min aware-UTC, máx 5 tentativas, `secrets.compare_digest`, resend 3/15 min por conta+IP. | A07 (lockout progressivo, duas dimensões de rate limit) + A04 |
| TH-11 | Path traversal via key do objeto | Tampering | Key gerada server-side (`couriers/{courier_id}/{ulid}.webp`), nunca derivada de input do usuário; validação de prefixo. | A03 (path traversal: resolve + verifica prefixo) |
| TH-12 | Segredo B2 no repo | — | `B2_KEY_ID`/`B2_APP_KEY` só via env/secret (Field default None em `config.py`); `.env` no `.gitignore` desde o 1º commit; `.env.example` com placeholders. Segredo commitado = rotacionar. | Gestão de Segredos (FAIL-BLOCK) + A02 |

### LGPD (TH-lgpd — `br/lgpd-compliance`)
- **Base legal:** dados do entregador (CPF, selfie, CNH, CRLV, MEI, antecedentes) = **execução de contrato** + **obrigação legal/regulatória** (KYC do entregador, PLP de plataformas). Antecedentes só quando a área exigir (minimização — coletar só o necessário por nível).
- **Minimização:** KYC SIMPLES não pede CNH/CRLV/MEI; COMPLETA só os itens que a área configura. Documento removido após decisão se não exigido por retenção.
- **Finalidade explícita:** cada campo do wizard com hint ("por que pedimos"); link visível à política de privacidade.
- **Retenção / anonimização (RN-021):** documentos KYC seguem a retenção do projeto — anonimização de PII em registros com >12 meses; exclusão de conta anonimiza em 30 dias; dado fiscal (MEI) preservado sem PII. Job de expiração (CNH/CRLV/MEI) transita o documento; job de anonimização (RN-021) é da Phase 14 mas o schema deve já marcar `anonymized_at` nullable.
- **Compartilhamento (operador):** B2 (storage) e Receita (consulta) são operadores → DPA + lista pública na política.
- **Direitos do titular:** o entregador é titular — endpoints de acesso/exclusão (Phase 14) devem alcançar `couriers`/`courier_documents`; já desenhar com `deleted_at`/`anonymized_at`.

### Checklist Security Baseline para o PLAN
- [ ] Toda rota nova: dependency de auth explícita OU `# público:` justificado (signup público + rate-limited, igual merchants)
- [ ] Ownership+área no WHERE de todo acesso a `courier_documents`; 404 fora do escopo
- [ ] Bucket B2 privado; presigned GET ≤ 300s; PUT ≤ 300s; URLs não logadas
- [ ] Magic bytes + re-encode Pillow + strip EXIF + `MAX_IMAGE_PIXELS` + limite de tamanho
- [ ] SHA-256 do derivado registrado; `compare_digest` em comparações sensíveis
- [ ] `assert_safe_url` (allowlist B2) no download interno; `follow_redirects=False`
- [ ] CPF/documento/telefone/e-mail mascarados; body nunca logado; acesso a doc auditado sem conteúdo
- [ ] Segredos B2 só via env; `.env.example` com placeholders
- [ ] Rate limit do signup/etapa com derivação documentada
- [ ] Base legal + retenção (RN-021) declaradas por categoria; minimização por nível KYC
- [ ] aware-UTC (TD-010) em expiração de documento, presigned, OTP

## Sources

### Primary (HIGH confidence)
- `.claude/skills/owasp-security/SKILL.md` — A01, A03, A04, A07, A08, A09, A10, Gestão de Segredos (lido integralmente)
- `.claude/skills/br/lgpd-compliance/SKILL.md` — base legal, minimização, retenção, logs sem PII (lido integralmente)
- Código Phase 4 (lido): `integrations/base.py`, `http.py`, `factory.py`, `receita.py`, `core/logging.py`, `merchants/state_machine.py`, `merchants/otp.py`, `merchants/models.py`, `db/mixins.py`, `workers/revalidate.py`, `auth/dependencies.py` — padrões reusados
- boto3 docs (Context7/ctx7 `/boto/boto3`): `generate_presigned_url` put/get_object, `generate_presigned_post` Conditions — `s3-presigned-urls.rst`
- Pillow docs (Context7/ctx7 `/websites/pillow_readthedocs_io_en_stable`): WebP encoder (`exif` opcional), `getexif`, `MAX_IMAGE_PIXELS`
- PyPI (`pip index versions`): boto3 1.43.27, Pillow 12.2.0, aioboto3 15.5.0, b2sdk 2.12.0

### Secondary (MEDIUM confidence)
- `projeto/docs-externos/integracoes.md` §7 (B2: bucket privado, presigned, compressão 1920/WebP, SHA-256), §3 (Receita/MEI/CNAEs), §4 (SMS)
- `projeto/regras-negocio/fluxos.md` §F-02 (E1-E5), `regras.md` (RN-002/010/016/021/024), `entidades.md` §Lado da oferta
- `.planning/phases/05.../05-CONTEXT.md` (D-01..D-08), `.planning/ROADMAP.md` Phase 5

### Tertiary (LOW confidence — virar task/TD, Regra 12)
- B2 quirks de presigned (addressing style/region/endpoint) — validar com conta real no Gate 5
- Política de antivírus/scan (sobretudo se antecedentes for PDF) — DEFERIR como TD ou restringir a imagem
- Limites numéricos exatos (tamanho/dimensão/expiração) — fixar no PLAN com derivação

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versões verificadas no PyPI; boto3/Pillow são referência; padrão de adapter já em uso
- Architecture: HIGH — reuso direto de 11 módulos lidos da Phase 4
- Security baseline: HIGH — 12 ameaças mapeadas a seções concretas da owasp-security + LGPD
- B2 specifics (endpoint/addressing): MEDIUM-LOW — S3-compatibility é boa, mas quirks exigem validação na conta real

**Research date:** 2026-06-10
**Valid until:** 2026-07-10 (stack estável; boto3/Pillow movem-se devagar)
