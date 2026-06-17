# Spike A3 — Capacitor Camera/Geolocation EXIF GPS (Phase 9, T-01)

> **Status:** decidido. Contrato da foto definido. Consumido por T-03 (backend pipeline) e T-12 (UI de captura).
> **Decisão:** a foto é validada por geofence server-side sobre **GPS explícito `{lat,lng}` enviado pelo cliente** como caminho PRINCIPAL; o EXIF GPS do RAW é **reforço** quando presente. EXIF OU lat/lng = evidência, **nunca autoridade** (RN-017 / ADR-008).

## Pergunta do spike

O `@capacitor/camera` preserva o EXIF GPS no arquivo capturado em Android real? E o navegador (PWA/M1) entrega EXIF na captura via `<input capture>`?

## Achado

| Plataforma | EXIF GPS no arquivo capturado? | Observação |
|------------|-------------------------------|------------|
| Navegador desktop/mobile (`<input type="file" capture="environment">`) | **Não confiável.** Maioria dos browsers **remove** EXIF da captura via `getUserMedia`/canvas; mesmo o file picker da câmera nativa frequentemente não preenche GPS sem permissão de localização explícita. | No M1 (web/PWA) **não dá para depender de EXIF**. |
| Capacitor Camera (Android, `resultType: Uri`) | **Parcial / dependente do device.** Alguns OEMs preservam o EXIF GPS do arquivo original; outros (e o pipeline `DataUrl`/`Base64`) re-encodam e **descartam** o EXIF. Requer permissão de localização concedida ao app de câmera, não só ao nosso app. | Inconsistente entre fabricantes — **não pode ser o caminho único**. |

Conclusão: o EXIF GPS **não é uma fonte confiável o suficiente para ser o caminho principal** no M1 (web/PWA). Confiar só nele faria toda comprovação cair em `low_confidence` (Pitfall 1 do RESEARCH — taxa anormal de low_confidence é o warning sign).

## Contrato da foto (consumido por T-03 e T-12) — DEFINIDO

O cliente, no momento da captura, **SEMPRE** chama `Geolocation.getCurrentPosition()` (Capacitor Geolocation no app; `navigator.geolocation` no PWA) e envia `{lat, lng}` explícito no corpo do `POST proof`, junto da `storage_key` da foto já enviada ao B2.

O servidor (T-03), na ordem **obrigatória** (Pitfall 1):

1. `fetch(raw)` do B2 (a foto que o cliente subiu via presign PUT).
2. magic bytes + tamanho (reuso `media/validation.py`).
3. `extract_gps_from_raw(raw)` — lê o EXIF GPS do RAW **se existir** (reforço).
4. Decide o ponto a validar: **se o cliente enviou `{lat,lng}` → usa esse** (caminho principal); senão, usa o GPS do EXIF; se nenhum → `gps_missing` (rejeita, orienta).
5. `within_radius` (geofence server-side, `ST_Distance_Sphere`) vs o POINT de coleta/destino + `geofence_m` da área.
6. ≤ raio? OK : reject. 3 falhas → `low_confidence` + CTA destrava (revisão admin).
7. **SÓ DEPOIS** `reprocess_to_webp` (strip) → B2 derivativo.
8. `transition()` gravando `gps=(lat,lng)` na transição (RN-012, auditoria).

### Invariante de segurança

- Tanto o `{lat,lng}` client quanto o EXIF são **client-supplied** e trivialmente forjáveis. A barreira é o **geofence server-side**, não a origem do dado.
- A defesa de M1 é: geofence + `low_confidence` após 3 falhas + revisão humana (sem contra-prova de IA — TD-008, risco residual aceito em TH-1).
- O GPS usado fica gravado na `delivery_state_transition` para auditoria (RN-012).

### Por que `{lat,lng}` client como principal (e não EXIF)

- Funciona no M1 web/PWA (onde EXIF some), que é o alvo do piloto.
- Permissão de localização do **nosso** app é mais simples de obter do que permissão de GPS embutido no EXIF do app de câmera do OEM.
- O EXIF entra como reforço sem custo: quando presente e o `{lat,lng}` client ausente, ainda valida.

## Fallback de background (A5 → TD-020)

O polling de posição (T-08) pausa em background (Page Visibility). Rastreamento contínuo em background é pós-M1 (TD-020). Isto é independente da captura da foto — a foto é uma operação em foreground (o entregador está com a tela aberta tirando a foto).

## Permissões necessárias (UI — T-12)

- Localização (`Geolocation`): pedida **contextualmente** ao abrir a tela de comprovação (não no primeiro load do app).
- Câmera: pedida no momento de "Tirar foto".
- Se a localização for negada: a UI explica que sem localização não dá para comprovar no raio e oferece reabrir as permissões; sem `{lat,lng}` e sem EXIF, o server rejeita com `gps_missing` (acionável, não trava para sempre — 3 falhas → low_confidence).
