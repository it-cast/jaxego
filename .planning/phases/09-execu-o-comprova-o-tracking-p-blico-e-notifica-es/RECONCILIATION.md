# RECONCILIATION — Phase 9: Execução, comprovação, tracking público e notificações

**Data:** 2026-06-10
**Método:** PLAN/UI-SPEC/RESEARCH (prometido) × código real + verificação ao vivo contra MySQL 8 + Redis

---

## Prometido vs. Entregue

| Área | Prometido | Real | Status |
|---|---|---|---|
| Entidades (migration 0008) | delivery_proofs, delivery_locations, notifications, push_subscriptions, direct_payment_confirmations | `0008_proofs_tracking_notif` | ✅ **aplica + reversível (após fix revision id)** |
| Comprovação foto+GPS (RN-005/017) | extrair EXIF GPS do RAW ANTES de reprocess + validar geofence + low_confidence 3 falhas (OPOSTO do KYC) | pipeline dedicado, ordem testada | ✅ |
| Geofence (ST_Distance_Sphere) | ponto dentro/fora do raio decide validade | spatial + haversine fallback | ✅ **verificado ao vivo (5 mysql tests)** |
| Máquina F-06 | ACEITA→COLETADA (revela destino RN-013)→ENTREGUE→FINALIZADA + RECUSADA_NO_DESTINO | transition() Phase 7 | ✅ |
| delivery_locations + polling (DEC-002) | ingestão autenticada por entrega na janela, retenção 24h, filtro 50m | endpoint + job | ✅ |
| Tracking público (sem auth) | public_token opaco, serializer minimiza PII por estado (RN-013), rate limit | implementado | ✅ |
| Mapa ao vivo (DEC-002) | MapLibre LAZY (LCP=timeline), dark mode | jx-live-map chunk lazy 231KB | ✅ (main 163KB, mapa fora do crítico) |
| Notificações multicanal (RN-018) | push+SMS(só "a caminho")+email, fallback, 3 momentos | adapter orquestrado | ✅ |
| Janela de telefones (RN-022) | acessível só ACEITA→FINALIZADA | phone_window_open por estado | ✅ |
| Pagamento direto (RN-026) | confirma "recebi"; "não recebi"→disputa | direct_payment_confirmations | ✅ |
| Cancelamentos (RN-004) | 50%/100%+retorno registrados | cancel_cost_cents | ✅ |
| Jobs | FINALIZADA 24h, retenção localização, ausente 10min | arq jobs aware UTC | ✅ |
| Frontend | telas 06/07/13/26 + 8 componentes novos (jx-proof-capture/live-map/tracking-timeline) | implementado | ✅ |

---

## Verificação ao vivo (MySQL 8 + Redis real)
| Check | Resultado |
|---|---|
| `alembic upgrade head` (0001→0008) | ✅ aplica (após fix revision id) |
| Reversibilidade 0008 (downgrade→upgrade) | ✅ limpo (sem bug 1553) |
| Geofence ST_Distance_Sphere (dentro/fora) | ✅ 5 mysql tests passed |
| `pytest -m "not mysql"` | ✅ 326 passed |
| Frontend (ng build/lint/test) | ✅ main 162.88 kB + maplibre lazy 231KB; lint limpo; 121 testes; zero hardcode |

---

## Bug pego no smoke ao vivo (deploy-safety)
- **Migration 0008 não aplicava:** revision id `0008_proofs_tracking_notifications` (34 chars) estourava `alembic_version.version_num` VARCHAR(32) → erro 1406 no stamp final; todo o DDL aplicava mas a revisão nunca completava (DB ficava em 0007 com schema parcial → "duplicate column" em re-runs). → Corrigido (`0c67b5a`): id encurtado para `0008_proofs_tracking_notif` (26 chars) + arquivo renomeado. Outro bug de deploy que mock não pega. **Lição:** revision ids ≤32 chars.

## Critérios de aceite do ROADMAP
| Critério | Resultado |
|---|---|
| Foto sem GPS/fora do raio → rejeição; 3 falhas → low_confidence | ✅ |
| Telefone inacessível fora de ACEITA→FINALIZADA (RN-022) | ✅ |
| Tracking público sem auth; link inválido → erro; sem PII além do permitido (RN-013) | ✅ |
| Job FINALIZADA 24h pós-ENTREGUE sem disputa | ✅ |
| Localização ao vivo: posição só na janela; expira 24h; pausa background; mapa sem PII | ✅ |
| Wireframe-contract 06, 07, 13, 26 | ✅ |

## Desvios
1. Rule 2: `deliveries.cancel_cost_cents` (RN-004 exige registro do custo).
2. Rule 3: estrutura real do front (`src/{features,shared,core}`); piexif dev-dep (gera EXIF GPS nos testes).
3. Rule 1: endpoints 204 com Response explícito; attributionControl removido (typing MapLibre v5).

## Gates
| Gate | Status |
|---|---|
| Gate 2 (UI-SPEC) | ✅ zero token novo, mapa lazy |
| Gate 3 (Skills) | ✅ PASS (25/25, 1ª iteração) |
| Gate 4 (Security Baseline) | ✅ 9 ameaças → threat model |
| Gate 5 (Integration) | ✅ B2/push/SMS/SES/tiles validados por Stub |
| Gate 6 (Reconciliation) | ✅ este documento |
| Gate 7 (tests+lint) | ✅ 326+5 backend, 121 frontend, ruff/pyright/ng lint limpos |
| Gate 8 (senior-quality-bar) | ✅ EXIF evidência não autoridade, tracking público sem PII, IDOR localização, sem segredo no repo |

## Pendências / follow-up (não-bloqueantes)
- TD-019 (tiles OSM produção — self-host/provider, tile.openstreetmap.org proibido p/ volume) — post_launch_30d.
- TD-020 (watchPosition background no Capacitor — M1 só app aberto) — post_launch_30d.
- A3 (Capacitor Camera EXIF em device real) — spike documentado; M1 usa GPS explícito do cliente validado server-side + EXIF como reforço.
- OTP de comprovação (RN-007) — pós-M1 (TD-003).
- Disputa de pagamento direto: registro aberto; mediação completa é Phase 11.
