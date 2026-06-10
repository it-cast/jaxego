# RECONCILIATION — Phase 5: Cadastro do entregador + KYC 2 níveis + documentos B2

**Data:** 2026-06-10
**Método:** PLAN/UI-SPEC/RESEARCH (prometido) × código real + verificação ao vivo contra MySQL 8

---

## Prometido vs. Entregue

| Área | Prometido | Real | Status |
|---|---|---|---|
| Entidades | couriers, courier_documents (migration 0004, AreaScoped, unique area_id+cpf) | migration `0004_couriers_kyc` | ✅ **verificada ao vivo (aplica + reversível)** |
| KYC 2 níveis (ADR-011) | simples/completa, nível mínimo por área, RN-002 | implementado | ✅ |
| Aprovação item-a-item | admin aprova/reprova com motivo; reprovar item não invalida aprovados; reenvio só do item | PATCH review por item | ✅ (E4) |
| Upload B2 | StoragePort (Protocol+B2 boto3 S3v4+Stub), presigned PUT/GET, bucket privado | implementado | ✅ (Stub testado; B2 real → Gate 5) |
| Reprocess server-side | magic bytes + Pillow WebP + strip EXIF + SHA-256 + anti-bomb | pipeline de mídia | ✅ |
| MEI (RN-024) | consulta Receita, CNAEs, mei_pending se inativo | adapter reuso Phase 4 | ✅ (E3) |
| Máquinas de estado | courier (pending_kyc/active/suspended/banned) + documento (pending_upload/pending/approved/rejected/expired), transição inválida → 422 | implementado | ✅ |
| Jobs arq | expiração de documentos + escalação 48h, aware UTC | implementado | ✅ (E5) |
| F-02 exceções | E1 retomada 30d, E2 CPF mesma/outra área, E3 mei_pending, E4 reenvio, E5 escalação | testes | ✅ |
| Frontend | wizard Ionic tela 03 (stepper 3/4, câmera, upload presign background), painel admin tela 19, 4 componentes novos | implementado | ✅ |
| LGPD/segurança | documentos nunca públicos, presigned curto authz por ownership+área, PII fora de log, CPF mascarado | implementado | ✅ |

---

## Verificação ao vivo (MySQL 8 real)
| Check | Resultado |
|---|---|
| `alembic upgrade head` (0001→0004) | ✅ aplica limpo |
| Reversibilidade (downgrade 0004→0003 → upgrade) | ✅ reversível |
| 12 tabelas (couriers, courier_documents) | ✅ |
| `pytest -m mysql` | ✅ 4 passed, 1 skipped (skip = integration check B2, precisa conta real) |
| `pytest -m "not mysql"` (backend) | ✅ 179 passed |
| Frontend (ng build/lint/test) | ✅ 160.26 kB, lint limpo, 46 testes, zero hardcode |

---

## Critérios de aceite do ROADMAP
| Critério | Resultado |
|---|---|
| Bucket KYC inacessível sem URL assinada | ✅ (presigned + authz; teste contra Stub) |
| Testes F-02 E1-E5 | ✅ |
| Wireframe-contract 03 + 19 no UI-SPEC | ✅ |
| Aprovação item-a-item (reprovar CNH não invalida selfie) | ✅ |
| Upload valida magic bytes + strip EXIF + SHA-256 | ✅ |

---

## Desvios (auto-fixados)
1. Rule 3: import lazy do storage_stub no conftest.
2. Rule 1: anotação `list[str]` (basedpyright); `readonly idleHint` (ng lint).

## Gates
| Gate | Status |
|---|---|
| Gate 2 (UI-SPEC) | ✅ zero token novo, 4 componentes |
| Gate 3 (Skills) | ✅ PASS (21/21, 1ª iteração) |
| Gate 4 (Security Baseline) | ✅ 12 ameaças → threat model → tasks |
| Gate 5 (Integration check) | ⚠ contratos B2/Receita/SMS validados por Stub; presigned real contra B2 precisa conta (1 teste skipped) — Gate 5 parcial, completado em /gsd:verify-work com conta B2 |
| Gate 6 (Reconciliation) | ✅ este documento |
| Gate 7 (tests+lint) | ✅ 179+4 backend, 46 frontend, ruff/pyright/ng lint limpos |
| Gate 8 (senior-quality-bar) | ✅ segredo B2 só env, PII fora de log, sem N+1 na fila, authz explícita |

## Pendências / follow-up (não-bloqueantes)
- **Integration check B2 real (Gate 5):** presigned PUT/GET contra `jaxego-kyc-prod` exige conta Backblaze B2 — 1 teste skipped. Validar em /gsd:verify-work quando houver credencial. LOW-1 (SDK B2 quirks) resolvido com spike + Stub; falta o round-trip real.
- **TD-016:** antivírus/scan de upload diferido (post_launch_30d); M1 restringe antecedentes a imagem (mitiga vetor de PDF malicioso).
- Smoke E2E do fluxo KYC servindo API+frontend (signup→upload→admin aprova→active) não rodado; coberto por 179 testes + 4 mysql. Opcional em /gsd:verify-work 5.
