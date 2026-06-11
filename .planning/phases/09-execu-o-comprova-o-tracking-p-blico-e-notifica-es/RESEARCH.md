# Phase 9: Execução, comprovação, tracking público e notificações - Research

**Researched:** 2026-06-10
**Domain:** Comprovação foto+EXIF/GPS antifraude · tracking público sem auth · GPS polling/mapa ao vivo · notificações multicanal · jobs de ciclo de vida da entrega
**Confidence:** HIGH (stack e padrões reusam código verificado das Phases 5/7/8; libs verificadas no PyPI/npm em 2026-06-10)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (D-01..D-10 — copiar verbatim)
- **D-01:** ACEITA → rota até coleta + ligar/mensagem (janela telefones RN-022). "Cheguei na coleta" → confere itens → **foto da coleta** com **GPS validado no raio da coleta** (geofence 80m default da área, Phase 6) → `COLETADA`. **Endereço completo do destino revelado AGORA** (RN-013).
- **D-02:** Rota até destino. Geofence de aproximação dispara "está chegando" ao destinatário. No destino: **foto da entrega**; se método = número de referência → digita o nº; valida contra `reference_number`. → `ENTREGUE`.
- **D-03:** Toda transição COLETADA/ENTREGUE exige **foto com EXIF/GPS dentro do raio** (server-side: extrair EXIF GPS, validar geofence; sem GPS válido → bloqueia e orienta; 3 falhas → flag `low_confidence` + revisão do admin de área). Foto no B2 (reuso StoragePort Phase 5). **OTP de comprovação fora do M1** (TD-003).
- **D-04:** Upload offline-tolerante: foto fica no device e sobe quando reconectar (flag `pending_upload`); transição só conclui com upload OK.
- **D-05:** Pagamento = direto → "Recebeu o pagamento?" → confirma "Recebi R$ X em dinheiro/PIX" (`direct_payment_confirmations`). "Não recebi" → entrega conclui (ENTREGUE) mas abre `payment_dispute` (registro; mediação Phase 11/13).
- **D-06:** Após 24h sem disputa → `FINALIZADA` (job arq). No M1 (só direto) não há liberação de saldo.
- **D-07:** E2 ausente → "ausente" → notifica + telefone → 10min sem resposta → "retornar" → `RECUSADA_NO_DESTINO` (reason `absent`). E3 RECUSA → foto + motivo → RECUSADA_NO_DESTINO (reason `refused`). E1 foto sem GPS/fora do raio → rejeição na hora; 3 falhas → low_confidence. E4 número de referência não bate (3x) → orientar ligar à loja.
- **D-08:** Cancelamentos RN-004: antes do aceite custo zero (Phase 8); após aceite antes da coleta → 50%; após coleta → 100% + retorno (% da área). No M1 (direto) isso é registrado na entrega; cobrança efetiva é fatura (Phase 11).
- **D-09:** Tracking público (tela 26, SEM login, via public_token Phase 7): timeline + ETA + **mapa em tempo real** (DEC-002/ADR-101): app do entregador faz **polling de localização HTTP 60-120s** (filtro de movimento 50m, Page Visibility pausa em background), grava em `delivery_locations` (retenção 24h pós-entrega); tiles OSM/MapLibre. **NUNCA expõe PII do entregador além do permitido** (RN-013/RN-022); endereço completo do destino só após COLETADA.
- **D-10:** Notificações proativas ao destinatário em 3 momentos (aceite, a caminho/aproximação, entregue). Canal: **push/e-mail**; **SMS somente no "a caminho"** com link de tracking (quota — RN-018). Multicanal com fallback (push→email; SMS provider primário→fallback→email). Telefones acessíveis às partes só na janela ACEITA→FINALIZADA (RN-022). `notifications` + `push_subscriptions`.

### Claude's Discretion
- Lib de extração de EXIF GPS (Pillow/exifread) server-side.
- Mecânica do polling de localização (endpoint de ingestão + tabela + retenção via job).
- Componente de mapa Angular (MapLibre GL JS) e fonte de tiles.
- Estrutura de notifications (adapter multicanal reusando push da Phase 8 + SMS/SES adapters da Phase 4).

### Deferred Ideas (OUT OF SCOPE)
- Cobrança online cartão/PIX + escrow + liberação de saldo — Phase 10.
- Fatura mensal de taxas + disputas (mediação completa) + saques — Phase 11.
- OTP de comprovação — pós-M1 (TD-003, RN-007).
- Score com peso — Phase 13.
- Antifraude de foto por IA — pós-M1 (TD-008).
- "Aceitou e sumiu" (2× ETA) — registrado; automação fina pós-M1.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-026 | F-06 com 6 exceções | Máquina de estados Phase 7 (já cobre COLETADA/ENTREGUE/RECUSADA/FINALIZADA); E1-E6 mapeadas em "Pattern: F-06 driver" |
| REQ-027 | foto+EXIF/GPS geofence | Pillow `getexif().get_ifd(GPSInfo)` no RAW antes do reprocess; `ST_Distance_Sphere`/haversine vs ponto da área (geofence_m da AreaConfig Phase 6) |
| REQ-028 | número de referência | Compara `reference_number` da delivery (já existe no model); 3 falhas → orientação |
| REQ-029 | cancelamentos RN-004 | `transition()` Phase 7 já registra reason/actor; % por estado calculado server-side, cobrança em Phase 11 |
| REQ-030 | tracking público + mapa ao vivo (DEC-002) | Endpoint `# público:` por public_token (ULID-like Crockford 26ch já em service.py); MapLibre + raster OSM |
| REQ-031 | notificações 3 momentos | Adapter multicanal reusando PushPort (Phase 8) + SmsPort/EmailPort (Phase 4) |
| REQ-032 | janela de telefones | Filtro por estado ACEITA→FINALIZADA no serializer (RN-022) |
| REQ-035 (parcial) | confirmação pagamento direto | `direct_payment_confirmations`; "não recebi" → registro de disputa |
| REQ-049 | multicanal com fallback | Cadeia push→email; SMS Zenvia→Twilio→email |
| REQ-055 | estados de UI | empty/error/loading nas telas 06/07/13/26 |
</phase_requirements>

---

## Summary

A Phase 9 fecha o ciclo operacional (F-06). Tecnicamente ela é **reuso pesado** de código já validado: a máquina de estados completa (`transition()` com `FOR UPDATE`, append-only) já existe na Phase 7; o `StoragePort` (B2 presigned + reprocess) na Phase 5; o `PushPort`/`SmsPort`/`EmailPort` nas Phases 4/8; a `AreaConfig.geofence_m` (30–300m, default 80) na Phase 6; o `public_token` (Crockford base32, 26 chars ≈ 130 bits, opaco/não-sequencial) já é gerado em `deliveries/service.py`. As peças **novas** são: (1) o pipeline de comprovação foto+GPS — que é o **oposto** do KYC; (2) o endpoint de ingestão de localização + tabela `delivery_locations` + jobs de retenção (DEC-002); (3) o endpoint público de tracking; (4) o componente de mapa MapLibre no front; (5) o adapter multicanal de notificações; (6) os jobs arq de ciclo (FINALIZADA 24h, retenção 24h, ausente 10min). Migration **0008**.

A descoberta crítica de research: o pipeline de imagem atual (`media/reprocess.py`) **destrói o EXIF** — faz `convert("RGB")` + `save(WEBP)` sem `exif=`, produzindo derivativo sem nenhum metadado (correto para KYC/privacidade). Para comprovação isso é **antagônico**: o GPS do EXIF é a prova antifraude. Logo, a comprovação precisa **ler o EXIF do byte RAW ANTES de reprocessar**, e só depois descartar o EXIF no derivativo armazenado. Não reusar `reprocess_to_webp` cegamente — extrair GPS primeiro com `Image.getexif().get_ifd(IFD.GPSInfo)` sobre o original.

A segunda decisão de research é confiança: GPS de EXIF é **fornecido pelo cliente** e trivialmente forjável. A defesa não é "confiar no EXIF" e sim **validar geofence server-side** (distância ≤ `geofence_m` do POINT de coleta/destino) e degradar para `low_confidence` + revisão humana após 3 falhas — exatamente como ADR-008/RN-005 já preveem. EXIF é evidência, não autoridade.

**Primary recommendation:** Pipeline de comprovação dedicado (lê GPS do RAW → valida geofence com `ST_Distance_Sphere` no MySQL → reprocessa+strip para armazenar) + `delivery_locations` com retenção 24h por job arq cron + endpoint público read-only por `public_token` que minimiza PII por estado. Stack: Pillow 12 (GPS IFD), MapLibre GL JS 5 + raster OSM, pywebpush 2 (já em uso). Tudo aware-UTC (TD-010).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Extração EXIF GPS | API / Backend | — | Cliente é hostil; EXIF lido e validado server-side (RN-017, A01/A04) |
| Validação de geofence | Database (MySQL spatial) | API | `ST_Distance_Sphere(POINT, POINT)` no banco; haversine fallback em app |
| Foto: validação magic bytes + reprocess | API / Backend | Storage (B2) | Bytes nunca confiados; derivativo no bucket privado |
| Captura de foto / câmera | Browser/Capacitor | — | `getUserMedia`/plugin de câmera; offline-tolerante no device |
| Ingestão de posição GPS | API / Backend | Database | Endpoint autenticado por entrega; grava em `delivery_locations` |
| Polling de localização (60-120s, Page Visibility) | Browser/Capacitor | — | App do entregador; pausa em background; filtro 50m client-side |
| Tracking público (timeline+mapa) | Frontend Server / Browser | API (read-only) | Tela 26 sem login; consome endpoint público por token |
| Renderização do mapa + tiles | Browser | CDN (tiles OSM) | MapLibre GL JS; tiles servidos por host OSM/self-host |
| Notificações multicanal | API / Backend (arq) | Push/SMS/SES | Orquestração + fallback fora do request (enqueued) |
| Jobs de ciclo (FINALIZADA, retenção, ausente) | API / Backend (arq cron) | Database | Cron jobs idempotentes |
| Confirmação de pagamento direto | API / Backend | — | Autorização: só o entregador da entrega |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pillow | 12.2.0 | Extrair EXIF GPS do RAW (`getexif().get_ifd(IFD.GPSInfo)`) + reprocess | Já é dependência da Phase 5 (`media/reprocess.py`); API de GPS IFD nativa `[VERIFIED: PyPI 2026-06-10]` |
| MapLibre GL JS | 5.24.0 (npm) | Mapa do tracking público + app entregador; raster OSM tiles | Open-source, GPU vector/raster, sem chave de API; padrão pós-Mapbox fechar licença `[VERIFIED: npm 2026-06-10]` `[CITED: github.com/maplibre/maplibre-gl-js]` |
| pywebpush | 2.3.0 | Web Push VAPID (aes128gcm) — canal push das notificações | Já em uso (`integrations/push.py`); `content_encoding="aes128gcm"` `[VERIFIED: PyPI 2026-06-10]` `[CITED: github.com/web-push-libs/pywebpush]` |
| MySQL 8 spatial | — | `ST_Distance_Sphere(p1, p2)` para geofence em metros | Já há POINT/POLYGON e `ST_Contains` na Phase 6; `ST_Distance_Sphere` retorna metros direto `[ASSUMED]` (verificar em task) |
| arq | (lockfile) | Jobs cron: FINALIZADA 24h, retenção 24h, ausente 10min | Worker já configurado (`workers/settings.py`); usar `cron_jobs` `[VERIFIED: codebase apps/api/app/workers]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| boto3 (StorageB2Adapter) | (lockfile) | Presigned PUT/GET das fotos de comprovação | Reuso direto do `StoragePort` (Phase 5) `[VERIFIED: codebase integrations/storage.py]` |
| Capacitor Geolocation | (front lockfile) | `getCurrentPosition`/`watchPosition` para o polling | App do entregador (Ionic/Capacitor — ADR-003) `[ASSUMED]` (validar plugin) |
| Capacitor Camera | (front lockfile) | Captura de foto de comprovação | Tela 07; gera arquivo com EXIF GPS `[ASSUMED]` (ver LOW-3) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pillow GPS IFD | `exifread` 3.5.1 / `piexif` 1.1.3 (Python) | exifread é read-only mais explícito p/ GPS; piexif lê+escreve. Pillow **já é dep** — adicionar lib só se Pillow falhar em algum formato (LOW-1) |
| `ST_Distance_Sphere` no banco | haversine em Python | Banco é fonte de verdade do POINT da área; haversine como **fallback** se a query spatial não compor. Documentar a derivação |
| MapLibre raster OSM | Leaflet | Leaflet é mais leve mas DEC-002 já fixou MapLibre/OSM; MapLibre dá dark mode por style JSON (DEC-001) |
| HTTP polling 60-120s | WebSocket | **Rejeitado por DEC-002** (custo). Não reabrir |

**Installation:**
```bash
# Backend: Pillow já instalado (Phase 5). Confirmar nada novo no requirements para EXIF.
# Frontend:
npm install maplibre-gl@^5.24.0
# Capacitor (se ainda não): @capacitor/geolocation @capacitor/camera
```

**Version verification (executado 2026-06-10):**
- `piexif` 1.1.3 · `exifread` 3.5.1 · `pillow` 12.2.0 · `pywebpush` 2.3.0 (PyPI) · `maplibre-gl` 5.24.0 (npm) — todos `[VERIFIED]`.

---

## Architecture Patterns

### System Architecture Diagram

```
ENTREGADOR (Ionic/Capacitor)                          DESTINATÁRIO / PÚBLICO (tela 26, sem login)
  │                                                         │
  │ 1. câmera → foto c/ EXIF GPS                            │ GET /v1/public/tracking/{public_token}
  │ 2. watchPosition (60-120s, filtro 50m,                  │   (# público: token opaco)
  │    Page Visibility pausa)                               ▼
  ▼                                                    ┌─────────────────────────────┐
┌──────────────────────────────┐                      │ Public Tracking Serializer  │
│ POST proof (multipart/presign)│                     │  - timeline (estados)       │
│ POST location {lat,lng}       │                     │  - ETA                       │
└──────────────┬───────────────┘                      │  - posição aproximada (últ. │
               │                                       │    delivery_location)        │
               ▼  (auth: courier == delivery.courier;  │  - MINIMIZA PII por estado: │
               │   estado ∈ janela)                    │    endereço destino só após │
  ┌────────────────────────────────────┐              │    COLETADA (RN-013); sem   │
  │ COMPROVAÇÃO (novo pipeline)         │              │    telefone/nome do courier │
  │  a. fetch RAW bytes                 │              └──────────────┬──────────────┘
  │  b. magic bytes + size (reuso)      │                             │
  │  c. EXIF GPS do RAW (Pillow IFD) ◄──┼── DIFERE DO KYC             ▼
  │  d. ST_Distance_Sphere vs POINT     │              MapLibre GL JS + raster OSM tiles
  │     coleta/destino (geofence_m)     │              (posição aproximada do courier)
  │  e. ≤raio? → OK : reject;           │
  │     3 falhas → low_confidence       │              JOBS arq (cron)
  │  f. reprocess+STRIP → B2 (deriv.)   │              ┌────────────────────────────┐
  │  g. transition() COLETADA/ENTREGUE  │─────────────►│ finalize_deliveries (24h)  │
  └────────────────┬───────────────────┘              │ purge_locations (>24h)     │
                   │                                   │ absent_timeout (10min)     │
                   ▼                                   └────────────────────────────┘
        NOTIFICATION DISPATCHER (enqueued, arq)
          aceite     → push → email
          a caminho  → push + SMS(quota) + email  (link tracking)
          entregue   → push → email
```

### Recommended Project Structure
```
apps/api/app/
├── proofs/                  # NOVO — comprovação foto+GPS
│   ├── exif.py              # extract_gps_from_raw(bytes) -> (lat,lng)|None  [NÃO reusa reprocess cego]
│   ├── geofence.py          # within_radius(point, target, radius_m) via ST_Distance_Sphere
│   ├── service.py           # orquestra: fetch→exif→geofence→low_confidence→strip→B2→transition
│   ├── models.py            # DeliveryProof
│   ├── router.py            # POST proof (auth courier-of-delivery)
│   └── schemas.py
├── tracking/                # NOVO — público + localização
│   ├── public.py            # GET /v1/public/tracking/{token}  (# público:)
│   ├── locations.py         # POST location (ingestão autenticada por entrega)
│   ├── serializer.py        # minimização de PII por estado (RN-013/RN-022)
│   └── models.py            # DeliveryLocation (retenção 24h)
├── notifications/           # NOVO — multicanal
│   ├── dispatcher.py        # 3 momentos + cadeia de fallback
│   ├── models.py            # Notification, PushSubscription
│   └── router.py            # registrar/remover push_subscription
├── payments_direct/         # NOVO — confirmação direta
│   ├── service.py           # confirm / não-recebi → payment_dispute (registro)
│   └── models.py            # DirectPaymentConfirmation
└── workers/
    ├── lifecycle.py         # NOVO — finalize_deliveries, purge_locations, absent_timeout (cron)
    └── settings.py          # registrar os novos cron_jobs

apps/web/src/app/
├── shared/map/              # NOVO — wrapper MapLibre (raster OSM + dark style DEC-001)
├── courier/active-delivery/ # tela 06: rota + comprovação + polling
├── courier/proof/           # tela 07: câmera + envio
└── public/tracking/         # tela 26: timeline + mapa (lazy, sem auth guard)
```

### Pattern 1: Extração de GPS do EXIF (RAW, antes de reprocessar) — O OPOSTO DO KYC
**What:** Ler GPS do byte original; só depois descartar EXIF no derivativo armazenado.
**When to use:** Toda foto de comprovação (COLETADA/ENTREGUE/recusa).
```python
# apps/api/app/proofs/exif.py
# Source: [CITED: pillow.readthedocs.io/en/stable/reference/ExifTags.html]
from PIL import Image
from PIL.ExifTags import IFD, GPS
import io

def _dms_to_deg(dms, ref: str) -> float:
    deg, minutes, sec = (float(x) for x in dms)
    val = deg + minutes / 60 + sec / 3600
    return -val if ref in ("S", "W") else val

def extract_gps_from_raw(raw: bytes) -> tuple[float, float] | None:
    """Lê GPS do EXIF do byte ORIGINAL (antes de qualquer reprocess que faz strip).
    Retorna (lat, lng) ou None se ausente/ilegível. NUNCA confiar como verdade —
    é evidência que o geofence valida (RN-017 / ADR-008)."""
    with Image.open(io.BytesIO(raw)) as im:
        gps = im.getexif().get_ifd(IFD.GPSInfo)
        if not gps:
            return None
        lat = gps.get(GPS.GPSLatitude); lat_ref = gps.get(GPS.GPSLatitudeRef)
        lng = gps.get(GPS.GPSLongitude); lng_ref = gps.get(GPS.GPSLongitudeRef)
        if not (lat and lat_ref and lng and lng_ref):
            return None
        return _dms_to_deg(lat, lat_ref), _dms_to_deg(lng, lng_ref)
```
> **CRÍTICO:** `media/reprocess.py` (Phase 5) faz `convert("RGB")` + `save(WEBP)` sem `exif=` → derivativo SEM EXIF. Se a comprovação chamar `reprocess_to_webp` antes de `extract_gps_from_raw`, **o GPS já se perdeu**. Ordem obrigatória: (1) `extract_gps_from_raw(raw)` → (2) validar geofence → (3) `reprocess_to_webp(raw)` para armazenar o derivativo limpo.

### Pattern 2: Validação de geofence server-side (autoridade ≠ cliente)
```python
# apps/api/app/proofs/geofence.py
from sqlalchemy import text

async def within_radius(session, *, lat: float, lng: float,
                        target_lat: float, target_lng: float, radius_m: int) -> bool:
    # ST_Distance_Sphere(POINT(lng,lat), POINT(lng,lat)) -> metros (SRID 4326 long,lat)
    row = await session.execute(
        text("SELECT ST_Distance_Sphere(POINT(:plng,:plat), POINT(:tlng,:tlat)) AS d"),
        {"plng": lng, "plat": lat, "tlng": target_lng, "tlat": target_lat},
    )
    return float(row.scalar_one()) <= radius_m
# radius_m = AreaConfig.geofence_m (30..300, default 80) — Phase 6.
# Fallback haversine em Python se a query spatial não estiver disponível (LOW-2).
```

### Pattern 3: Endpoint público com minimização de PII por estado
```python
# apps/api/app/tracking/public.py
@router.get("/public/tracking/{public_token}")
async def public_tracking(public_token: str, session: ...):
    # público: tracking sem login via token opaco (ULID-like, RN-030).
    # Rate limit por IP (anti-enumeração). 404 genérico se token inválido.
    d = await get_by_public_token(session, public_token)  # WHERE public_token = :t
    if d is None:
        raise NotFoundError("Acompanhamento não encontrado.")
    return serialize_public(d)  # ver serializer

def serialize_public(d) -> dict:
    out = {"state": d.state, "timeline": d.timeline, "eta_seconds": d.eta_seconds}
    # RN-013: endereço completo do destino só após COLETADA.
    out["dropoff"] = (d.dropoff_full if d.state in ("COLETADA","ENTREGUE","FINALIZADA")
                      else d.dropoff_neighborhood_only)
    # Posição aproximada do courier (último delivery_location), SEM nome/telefone.
    if d.state in ("ACEITA","COLETADA"):
        loc = d.last_location
        out["courier_position"] = {"lat": loc.lat, "lng": loc.lng} if loc else None
    # NUNCA: nome/telefone/CPF do courier; telefone do destinatário no payload público.
    return out
```

### Pattern 4: Ingestão de localização autenticada por entrega (anti-IDOR)
```python
# apps/api/app/tracking/locations.py
@router.post("/deliveries/{delivery_id}/locations")
async def ingest_location(delivery_id: int, body: LocationIn, courier: CurrentCourier, session):
    d = await get_delivery_for_courier(session, delivery_id=delivery_id, courier_id=courier.id)
    if d is None:
        raise NotFoundError()                      # 404 — não vaza existência (A01)
    if d.state not in ("ACEITA","COLETADA"):       # janela ACEITA→FINALIZADA, só fase móvel
        raise ConflictError("Entrega fora da janela de rastreamento.")
    session.add(DeliveryLocation(delivery_id=d.id, area_id=d.area_id,
                                 lat=body.lat, lng=body.lng,
                                 recorded_at=datetime.now(UTC)))   # AWARE UTC — TD-010
```

### Pattern 5: Job cron de retenção e finalização (arq)
```python
# apps/api/app/workers/lifecycle.py — registrar em workers/settings.py cron_jobs
from arq import cron
async def finalize_deliveries(ctx):
    # ENTREGUE há >24h sem disputa aberta → FINALIZADA via transition() (D-06).
    ...
async def purge_locations(ctx):
    # DELETE delivery_locations de entregas FINALIZADA/terminais há >24h (D-09 / LGPD).
    ...
async def absent_timeout(ctx):
    # "ausente" há >10min sem resposta → habilita "retornar" (D-07 E2). Idempotente.
    ...
# WorkerSettings.cron_jobs = [cron(finalize_deliveries, minute=set(range(0,60,5))), ...]
```

### Anti-Patterns to Avoid
- **Reusar `reprocess_to_webp` antes de ler o GPS** → strip destrói a prova (a armadilha central desta phase).
- **Confiar no lat/lng do EXIF sem geofence** → spoofing trivial; sempre validar server-side.
- **Expor PII do courier no payload público** → tracking é anônimo do lado do entregador.
- **public_token sequencial/curto** → enumeração; manter Crockford 26ch (já implementado).
- **Polling sem Page Visibility / sem filtro 50m** → drena bateria e enche `delivery_locations`.
- **Notificação síncrona no request** → enfileirar no arq (já é o padrão Phase 8).
- **Telefone no payload fora da janela ACEITA→FINALIZADA** → viola RN-022.
- **`datetime.now()` naive** em proof/location/job → TD-010; sempre `datetime.now(UTC)`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parse de EXIF/GPS | Parser binário de IFD próprio | `Pillow getexif().get_ifd(IFD.GPSInfo)` | DMS→decimal, refs N/S/E/W, formatos diversos — borda cheia de casos |
| Distância geográfica | Fórmula manual sem SRID | `ST_Distance_Sphere` (MySQL) | Banco é fonte do POINT; haversine só como fallback documentado |
| Token opaco | UUID4 ou random ad-hoc | `_new_public_token()` (Crockford, já existe) | Já implementado, 130 bits, não-sequencial |
| Web Push encryption | aes128gcm na mão | `pywebpush` (já em uso) | Cripto + VAPID corretos; reinventar = falha de segurança |
| Mapa/tiles | Canvas próprio | MapLibre GL JS + raster OSM | GPU, dark style por JSON, zero chave de API |
| Máquina de estados | Novos if/else de transição | `transition()` + `assert_delivery_transition` (Phase 7) | FOR UPDATE + append-only + 422 já corretos |
| Upload de bytes | Aceitar byte do cliente direto | `StoragePort` presign + magic bytes + reprocess (Phase 5) | Anti-polyglot, anti-bomb, SSRF guard já prontos |

**Key insight:** ~70% desta phase é orquestração de adapters/serviços já construídos e testados (242 testes backend na Phase 7). O risco real está nas 2 peças novas e sensíveis: o **pipeline de comprovação** (ordem EXIF-antes-de-strip) e o **endpoint público** (minimização de PII). Concentrar revisão de segurança ali.

---

## Runtime State Inventory

> Phase greenfield em termos de dados (não há rename/migração de string). Itens abaixo são para completude.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Nova migration 0008: `delivery_proofs`, `delivery_locations`, `notifications`, `push_subscriptions`, `direct_payment_confirmations`. POINTs de coleta/destino devem existir em `deliveries` (verificar 0006) | Migration 0008 + confirmar colunas POINT |
| Live service config | `AreaConfig.geofence_m` (Phase 6) já em produção como JSON tipado | Nenhuma — reusar |
| OS-registered state | Novos cron_jobs arq (finalize/purge/absent) — registrados em `WorkerSettings.cron_jobs` | Adicionar e fazer deploy do worker |
| Secrets/env vars | VAPID keys (já em uso Phase 8), B2 keys (Phase 5), SMS/SES (Phase 4) — nenhum novo segredo | Nenhuma — reusar |
| Build artifacts | `maplibre-gl` adicionado ao bundle do front | Reinstalar deps front; monitorar bundle (perf budget) |

**Verificado:** os POINTs de coleta/destino precisam estar em `deliveries` para o geofence — **task obrigatória confirmar em 0006** (se ausentes, 0008 adiciona colunas + backfill via geocoding). `[ASSUMED]` — não confirmado nesta sessão.

---

## Common Pitfalls

### Pitfall 1: EXIF perdido por reprocess prematuro
**What goes wrong:** Comprovação chama o pipeline de imagem da Phase 5, que faz strip; GPS some; geofence sempre falha → toda comprovação vira `low_confidence`.
**Why it happens:** `media/reprocess.py` foi desenhado para KYC (privacidade). Reuso cego.
**How to avoid:** `extract_gps_from_raw(raw)` PRIMEIRO; reprocess só para armazenar.
**Warning signs:** Taxa anormal de `low_confidence`; testes de geofence verdes só com mocks.

### Pitfall 2: GPS spoofado aceito como verdade
**What goes wrong:** App malicioso injeta lat/lng dentro do raio sem estar lá.
**Why it happens:** EXIF é client-supplied.
**How to avoid:** Geofence server-side é a barreira; em M1 não há contra-prova forte (IA é pós-M1, TD-008). Registrar GPS na transição (RN-012) para auditoria. Aceitar o risco residual documentado.
**Warning signs:** Comprovações com coordenadas idênticas repetidas.

### Pitfall 3: `delivery_locations` cresce sem limite / vaza PII
**What goes wrong:** Sem job de purga, tabela explode e retém rastro de movimento > 24h (viola minimização LGPD).
**How to avoid:** `purge_locations` cron + índice por `recorded_at`; filtro de movimento 50m no cliente reduz volume.
**Warning signs:** Tabela grande; queries de mapa lentas.

### Pitfall 4: SRID/ordem de coordenadas trocada no `ST_Distance_Sphere`
**What goes wrong:** `POINT(lat,lng)` vs `POINT(lng,lat)` invertido → distância absurda → geofence sempre falha ou sempre passa.
**How to avoid:** MySQL `POINT(x,y)` = `POINT(longitude, latitude)`. Teste com par conhecido (coleta ↔ 100m).
**Warning signs:** Distâncias de milhares de km para pontos próximos.

### Pitfall 5: Polling não pausa em background → bateria/quota
**What goes wrong:** `watchPosition` continua com app em background; drena bateria, polui dados.
**How to avoid:** Page Visibility API pausa; intervalo 60-120s; filtro 50m.
**Warning signs:** Reclamação de bateria; muitos pontos quase idênticos.

---

## Code Examples

### Mapa MapLibre com raster OSM + posição do courier
```javascript
// Source: [CITED: github.com/maplibre/maplibre-gl-js — add-a-raster-tile-source]
import maplibregl from 'maplibre-gl';
const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    sources: { 'osm': { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                        tileSize: 256, attribution: '© OpenStreetMap contributors' } },
    layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
  },
  center: [courierLng, courierLat], zoom: 14,
});
new maplibregl.Marker().setLngLat([courierLng, courierLat]).addTo(map);
// Dark mode (DEC-001): trocar style JSON / filtro CSS no container conforme tema (LOW-4).
```
> **Atenção tiles:** `tile.openstreetmap.org` tem **política de uso restritiva** (não para alto volume comercial). Confirmar fonte para produção: self-host (Phase 8 já cogita OSRM self-host) ou provider de tiles (MapTiler/Protomaps). Ver LOW-5.

### Notificação multicanal com fallback (3 momentos)
```python
# apps/api/app/notifications/dispatcher.py (enqueued no arq)
async def notify(moment: str, delivery, *, push: PushPort, sms: SmsPort, email: EmailPort):
    if moment in ("accepted", "delivered"):
        if not await try_push(push, delivery):
            await email.send(...)                    # push → email
    elif moment == "on_the_way":
        await try_push(push, delivery)
        if within_sms_quota(delivery):               # RN-018: SMS só aqui
            if not await sms.send(tracking_link(delivery)):   # Zenvia→Twilio interno
                await email.send(...)                # SMS falha total → email
    # registrar cada tentativa em `notifications` (canal, status, custo)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Mapbox GL JS (licença) | MapLibre GL JS (fork BSD) | Mapbox v2 fechou (2020) | Sem chave de API, dark style por JSON |
| `aesgcm` Web Push | `aes128gcm` (RFC 8188) | GCM legado depreciado (~2024) | Já usado em `push.py` |
| `Image._getexif()` (privado) | `Image.getexif().get_ifd(IFD.GPSInfo)` | Pillow ≥6 | API pública estável; usar a nova |

**Deprecated/outdated:**
- `Image._getexif()` (sublinhado, privado): usar `getexif()` + `get_ifd`.
- WebSocket para tracking: **rejeitado por DEC-002** (não reabrir).

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `ST_Distance_Sphere` retorna metros e está disponível no MySQL 8 contratado | Stack/Pattern 2 | Geofence precisa de fallback haversine; pequena task extra |
| A2 | `deliveries` (migration 0006) já tem POINTs de coleta E destino | Runtime Inventory | Sem POINT, 0008 adiciona colunas + backfill por geocoding (task maior) |
| A3 | Capacitor Camera entrega arquivo COM EXIF GPS no Android | Supporting / Pitfall 1 | Se o plugin strippar EXIF, capturar GPS via Geolocation e anexar como metadado próprio (não EXIF) → muda contrato da foto |
| A4 | `tile.openstreetmap.org` é aceitável no piloto Pádua (baixo volume) | Code Examples | Bloqueio/rate-limit de tiles → mapa quebra; precisa self-host/provider |
| A5 | Plugin Capacitor Geolocation suporta `watchPosition` em background suficiente | Polling | Se background for cortado pelo SO, polling só com app aberto (degradação aceitável M1) |

**Estes A1–A5 viram tasks de verificação ou TD no PLAN.md (Regra 12).**

---

## Open Questions

1. **Fonte de tiles em produção (A4/LOW-5)**
   - What we know: DEC-002 fixou OSM/MapLibre; OSRM já é self-host.
   - What's unclear: usar `tile.openstreetmap.org` direto (proibido p/ volume) vs self-host vs provider pago.
   - Recommendation: piloto Pádua (baixo volume) pode começar com OSM público + atribuição; **task** para avaliar self-host antes de escalar. Vira TD se adiada.

2. **EXIF GPS via Capacitor Camera (A3/LOW-3)**
   - What we know: comprovação exige GPS na foto.
   - What's unclear: o plugin preserva EXIF GPS no arquivo capturado?
   - Recommendation: **spike obrigatório** em device real; fallback = ler GPS via Geolocation no momento da captura e enviar `{lat,lng}` assinado junto da foto (server valida geofence igual). Vira task no PLAN.

3. **POINT de coleta/destino existe em `deliveries`? (A2)**
   - Recommendation: **task** de verificação na 0006 antes de escrever a 0008.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Pillow | EXIF GPS + reprocess | ✓ (Phase 5) | 12.2.0 | — |
| MySQL 8 spatial (`ST_Distance_Sphere`) | geofence | ✓ (Phase 6 usa ST_Contains) | 8 | haversine em Python |
| arq worker | jobs de ciclo | ✓ | (lockfile) | — |
| pywebpush + VAPID keys | push | ✓ (Phase 8) | 2.3.0 | email |
| B2 (StoragePort) | fotos | ✓ (Phase 5) | — | offline pending_upload |
| SMS Zenvia/Twilio | "a caminho" | ✓ (Phase 4) | — | email |
| SES | email | ✓ (Phase 4) | — | push |
| maplibre-gl (npm) | mapa | ✗ (a instalar) | 5.24.0 | timeline sem mapa (degradação) |
| Tiles OSM produção | mapa | ⚠ (política de uso) | — | self-host / provider (LOW-5) |

**Missing com fallback:** maplibre-gl (instalar); tiles produção (avaliar self-host).
**Missing blocking:** nenhum.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend, marca `not-mysql` p/ unit; mysql p/ spatial) + Jasmine/Karma (Angular) |
| Config file | `apps/api/pyproject.toml` (pytest) |
| Quick run command | `uv run pytest -m "not mysql" -x` |
| Full suite command | `uv run pytest && uv run ruff check . && (cd apps/web && npm test -- --watch=false)` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-027 | foto sem GPS → reject; fora do raio → reject; 3 falhas → low_confidence | unit | `pytest tests/proofs/test_exif.py tests/proofs/test_geofence.py -x` | ❌ Wave 0 |
| REQ-027 | EXIF lido do RAW antes do strip (ordem) | unit | `pytest tests/proofs/test_pipeline_order.py -x` | ❌ Wave 0 |
| REQ-027 | `ST_Distance_Sphere` par conhecido (SRID/ordem) | integration (mysql) | `pytest -m mysql tests/proofs/test_geofence_db.py` | ❌ Wave 0 |
| REQ-030 | tracking público responde sem auth; token inválido → 404; rate limit | unit | `pytest tests/tracking/test_public.py -x` | ❌ Wave 0 |
| REQ-030 | endereço destino só após COLETADA; sem PII do courier | unit | `pytest tests/tracking/test_serializer_pii.py -x` | ❌ Wave 0 |
| REQ-030 | ingestão de localização: só courier da entrega, só na janela (IDOR) | unit | `pytest tests/tracking/test_locations_authz.py -x` | ❌ Wave 0 |
| REQ-032 | telefone inacessível fora de ACEITA→FINALIZADA | unit | `pytest tests/tracking/test_phone_window.py -x` | ❌ Wave 0 |
| DEC-002 | job purga `delivery_locations` >24h | unit | `pytest tests/workers/test_purge_locations.py -x` | ❌ Wave 0 |
| D-06 | job FINALIZADA 24h sem disputa | unit | `pytest tests/workers/test_finalize.py -x` | ❌ Wave 0 |
| REQ-031/049 | fallback push→email; SMS só "a caminho" | unit | `pytest tests/notifications/test_dispatcher.py -x` | ❌ Wave 0 |
| REQ-035 | "não recebi" → ENTREGUE + payment_dispute | unit | `pytest tests/payments_direct/test_confirm.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest -m "not mysql" -x`
- **Per wave merge:** `uv run pytest && uv run ruff check .`
- **Phase gate:** suíte completa (incl. mysql spatial) verde antes de `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/proofs/conftest.py` — fixtures de imagens com/sem EXIF GPS (gerar com piexif para teste)
- [ ] `tests/tracking/conftest.py` — entregas em vários estados + delivery_locations
- [ ] Framework de imagem de teste: gerar JPEG com GPS conhecido (piexif útil **só nos testes**)

---

## Security Baseline (OBRIGATÓRIA — Gate 4)

> Threat model curto (A04): quem abusa? o que ganha? pior caso? — para foto-prova, link público, localização.
> 9 ameaças mapeadas, cada uma → mitigação citando owasp-security/lgpd-compliance.

### Applicable ASVS / OWASP Categories
| Categoria | Aplica | Controle padrão |
|-----------|--------|-----------------|
| A01 Broken Access Control | sim | IDOR fechado por `(courier_id/delivery)` na query; 404 não 403; endpoint público com `# público:` justificado |
| A03 Injection / Input validation | sim | Pydantic v2 `extra="forbid"`; magic bytes na foto; `ST_Distance_Sphere` parametrizado (`:lat/:lng`) |
| A04 Insecure Design | sim | Geofence server-side; invariante "EXIF é evidência, não autoridade"; rate limit derivado |
| A09 Logging | sim | Zero PII em log/push payload; filtro central (observability) |
| LGPD | sim | Minimização no tracking; retenção 24h de localização; janela RN-022; base legal execução de contrato |

### Threat Model — 9 ameaças

| # | Ameaça | STRIDE | Mitigação (cita skill) |
|---|--------|--------|------------------------|
| TH-1 | **EXIF/GPS spoofing** — app injeta coordenada falsa dentro do raio | Spoofing/Tampering | Geofence validado **server-side** (`ST_Distance_Sphere` vs POINT da área, `geofence_m`); EXIF nunca é autoridade; `low_confidence` após 3 falhas + revisão humana; GPS gravado na transição p/ auditoria (RN-012). `[owasp A04 — invariante de negócio no backend; A01 — não confiar no cliente]` |
| TH-2 | **Upload malicioso de foto** (polyglot, bomba de descompressão, não-imagem) | Tampering/DoS | Magic bytes (`sniff_content_type`, ignora content-type declarado) + `MAX_UPLOAD_BYTES` + `MAX_IMAGE_PIXELS` (anti-bomb) — reuso `media/validation.py`. **MAS:** ler GPS do RAW ANTES do reprocess; o strip só ocorre no derivativo armazenado. `[owasp A03 upload]` |
| TH-3 | **Tracking público sem auth** vaza dados | Info Disclosure | Endpoint `# público:` por `public_token` opaco (Crockford 26ch ≈130 bits, não-sequencial); expõe MÍNIMO: estado, timeline, ETA, posição aproximada; **sem nome/telefone/CPF do courier**; endereço destino só após COLETADA (RN-013). 404 genérico para token inválido. `[owasp A01 — rota pública justificada + minimização]` |
| TH-4 | **PII no tracking/localização** (LGPD) | Info Disclosure | Retenção 24h de `delivery_locations` (job `purge_locations`); minimização (só lat/lng, sem rastro permanente); telefones só na janela ACEITA→FINALIZADA (RN-022); base legal = execução de contrato. `[lgpd-compliance — minimização + retenção declarada]` |
| TH-5 | **IDOR na ingestão de localização** — courier B posta posição na entrega de A | Elevation/Tampering | `get_delivery_for_courier(delivery_id, courier_id=courier.id)` no WHERE → 404; estado deve estar na janela móvel (ACEITA/COLETADA). `[owasp A01 — ownership na query, 404 não 403]` |
| TH-6 | **Enumeração de public_token** — varrer tokens p/ raspar entregas | Info Disclosure | Token 130 bits não-sequencial (já gerado por `secrets.choice`) + **rate limit por IP** no endpoint público (derivar: ex. 60/min/IP); 404 uniforme. `[owasp A01/A04 — IDs não-sequenciais + rate limit derivado]` |
| TH-7 | **Confirmação de pagamento direto por ator errado** | Elevation | `direct_payment_confirmations` só aceita do courier dono da entrega (auth + ownership na query); "não recebi" gera `payment_dispute` (registro, mediação Phase 11). `[owasp A01]` |
| TH-8 | **PII em log / payload de push** | Info Disclosure | Push payload = `delivery_id` + deep link + título (PADRÃO JÁ EM `PushMessage`, zero PII); filtro central de log mascara `phone/cpf/email/token` (config.json `pii_fields_forbidden_in_logs`). `[owasp A09 + lgpd]` |
| TH-9 | **Link de tracking em SMS vaza** (reencaminhamento, histórico do device) | Info Disclosure | O link contém só o token opaco (não PII); o conteúdo atrás dele já é minimizado (TH-3). SMS só no "a caminho" (RN-018) reduz superfície. `[owasp A01 — o token não é credencial de PII; lgpd minimização]` |

### Diferença EXIF: KYC (Phase 5) vs Comprovação (Phase 9)
| Aspecto | KYC (Phase 5) | Comprovação (Phase 9) |
|---------|---------------|------------------------|
| Objetivo do EXIF | **Privacidade** — remover rastro | **Antifraude** — provar local |
| Ação no GPS | **STRIP** (descarta) | **EXTRAIR + VALIDAR** (lê, valida geofence) |
| Pipeline | `reprocess_to_webp` direto (sem `exif=`) | `extract_gps_from_raw(raw)` PRIMEIRO → geofence → só então reprocess/strip p/ armazenar |
| Onde o GPS termina | Em lugar nenhum | Na `delivery_state_transition` (RN-012, auditoria) + flag geofence em `delivery_proofs` |
| Risco se confundir | (n/a) | **Toda comprovação vira low_confidence** — o GPS é destruído antes de ler |

**Base legal LGPD (declarar):** dados de localização e foto = **execução de contrato** (RN-022/RN-021) + **legítimo interesse** (antifraude). Retenção: localização 24h; foto de comprovação segue retenção da entrega (anonimização 12 meses — RN-021). Endpoints de direitos do titular (Phase 14) devem incluir `delivery_locations` e `delivery_proofs`.

---

## Project Constraints (from CLAUDE.md)
- Aware UTC no banco (TD-010); naive datetime é proibido — auditar `datetime.now(UTC)` em proof/location/job.
- PII nunca em log (filtro central; `pii_fields_forbidden_in_logs`).
- `/v1` prefix, RFC-7807, AreaScoped, idempotência por header em escrita relevante.
- Máquina de estados server-side append-only; novo estado exige ADR (RN-019 — não criar estado novo).
- Segurança desenhada no researcher (Gate 4/Regra 7) — esta seção herda para o threat_model do PLAN.
- LOW confidence vira task ou TD (Regra 12) — ver Assumptions Log A1–A5.
- Soft delete em domínio EXCETO append-only (transitions); `delivery_locations` é hard-delete por retenção (LGPD).

## Sources

### Primary (HIGH confidence)
- Codebase verificado: `apps/api/app/media/{reprocess,validation}.py` (strip EXIF KYC), `deliveries/{service,state_machine,models}.py` (transition FOR UPDATE, public_token), `integrations/{base,storage,push}.py` (StoragePort/PushPort), `areas/config_schema.py` (geofence_m), `workers/settings.py` (arq).
- `[CITED: pillow.readthedocs.io/en/stable/reference/ExifTags.html]` — `getexif().get_ifd(IFD.GPSInfo)` + GPS sub-tags.
- `[CITED: github.com/maplibre/maplibre-gl-js]` — raster OSM tile source (Context7).
- `[CITED: github.com/web-push-libs/pywebpush]` — webpush aes128gcm (Context7).
- `.claude/skills/owasp-security/SKILL.md` (A01/A03/A04/A09), `.claude/skills/br/lgpd-compliance/SKILL.md`, `.claude/skills/mobile/offline-first/SKILL.md`.

### Secondary (MEDIUM confidence)
- Versões PyPI/npm verificadas 2026-06-10: piexif 1.1.3, exifread 3.5.1, pillow 12.2.0, pywebpush 2.3.0, maplibre-gl 5.24.0.

### Tertiary (LOW confidence)
- `ST_Distance_Sphere` semantics no MySQL contratado (A1) — verificar em task.
- Capacitor Camera/Geolocation EXIF GPS em background (A3/A5) — spike obrigatório.
- Política de tiles OSM em produção (A4) — avaliar self-host.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — libs verificadas; reuso de código testado.
- Architecture: HIGH — máquina de estados, StoragePort, push, geofence já existem.
- Pitfalls: HIGH — a armadilha central (EXIF strip) confirmada lendo `reprocess.py`.
- Comprovação foto+GPS: MEDIUM — depende de A3 (EXIF via Capacitor em device real).
- Tiles produção: LOW — A4 em aberto.

**Research date:** 2026-06-10
**Valid until:** 2026-07-10 (stack estável; reverificar tiles/Capacitor se atrasar)
