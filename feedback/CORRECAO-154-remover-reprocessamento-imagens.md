# CORRECAO-154 — Remover reprocessamento de imagens (upload direto)

## O que mudou

### Backend (apps/api)
- **couriers/documents.py**: `complete_upload` simplificado — apenas muda status para `pending`, sem baixar, reprocessar ou re-upload. A imagem fica no B2 no formato original.
- **proofs/service.py**: Removido download da imagem para extrair GPS do EXIF. Usa apenas o GPS do cliente (lat/lng enviados no request). Removido reprocessamento WebP — a prova fica no formato original no B2.

## Impacto
- Upload de documentos KYC: instantâneo (antes: download + Pillow + re-upload)
- Comprovação de entrega: instantâneo (antes: download + EXIF + Pillow + re-upload)
- Imagens de produto: já eram sem reprocessamento

## Trade-offs
- Imagens ficam no formato original (JPEG/PNG) em vez de WebP otimizado
- EXIF (GPS, serial) não é mais removido automaticamente
- Sem validação de magic bytes no servidor (confia no content-type do upload)

## Arquivos alterados
- apps/api/app/couriers/documents.py
- apps/api/app/proofs/service.py
