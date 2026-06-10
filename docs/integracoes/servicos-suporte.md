# Integrações de suporte

**Fonte:** `projeto/docs-externos/integracoes.md:55-103`

## Receita Federal (consulta CNPJ)
- **Uso:** situação cadastral de loja (RN-011) e MEI do entregador (RN-010 — CNAEs: 4930-2/01, 4930-2/02, 5320-2/02, 5229-0/99)
- **Provedor:** minhareceita.org self-hosted primário `[ASSUMIDO]`, BrasilAPI fallback
- **Falha:** indisponível → cadastro segue `pending_validation`, retry em job 6/6/12/24h, funcionalidade limitada (F-01 E4)

## SMS — Zenvia (primário) / Twilio (fallback)
- **Uso:** OTP de verificação de telefone no cadastro + notificação "a caminho" com link de tracking (RN-018). Quota por plano; excedente na fatura
- **Falha:** primário falha → fallback automático; ambos → degrada para e-mail + push, custo zero, evento logado

## E-mail — AWS SES
- **Uso:** confirmação de e-mail, ciclo (fatura fechada/vencendo, KYC, recurso respondido), fallback de SMS
- **Falha:** bounce/complaint → supressão do endereço; SES fora → fila com retry

## Web Push (VAPID)
- **Uso:** canal principal — entregador (nova oferta, lembretes) e loja (aceitou, concluiu). Gratuito
- **Falha:** permissão negada → degrade silencioso para e-mail; tokens expirados limpos por job

## Backblaze B2 + Cloudflare
- **Buckets:** `jaxego-kyc-prod` (privado), `jaxego-proofs-prod` (privado), `jaxego-public-prod` (assets)
- Upload por URL pré-assinada direto do cliente; compressão server-side (máx 1920px, WebP); SHA-256 registrado
- **Falha:** retry com backoff; B2 fora → comprovação **offline-tolerante** (foto no device, flag `pending_upload`, transição só conclui com upload OK)

## Rotas/ETA — OSRM self-hosted `[ASSUMIDO]`
- **Uso:** distância em rota e ETA (ranking de despacho, estimativas). Tiles OSM/MapLibre
- **Falha:** OSRM fora → haversine × 1,4 com flag `eta_degraded`; Google Distance Matrix como fallback pago opcional

## LLMs — Claude (primário) / OpenAI (fallback) — pós-M1, infra desde o M1
- **M1:** apenas router simples + `ai_usage_log` (provedor, modelo, tokens, custo, latência). Nenhuma feature
- **Pós-M1:** triagem de disputas, análise de foto de comprovação, antifraude
- **Falha:** indisponível → fila manual; **nunca bloqueia fluxo operacional**
