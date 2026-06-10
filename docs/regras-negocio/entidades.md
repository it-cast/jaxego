# Jaxegô — Entidades e dados

> Substantivos do domínio com atributos-chave, relações e marcação [LGPD] de PII. Schema técnico completo (27 tabelas tipadas) já existe e acompanha o projeto; este arquivo é o mapa conceitual que o framework consome.

## Núcleo multi-área

**Área** (`areas`) — cidade ou região de cidade. Unidade de regras locais.
Chave: `codename` único (ex.: `padua`). Atributos: nome, cidade, UF, status, nível de KYC exigido (`simple`|`complete`), exige antecedentes (bool), piso de frete (por km e por entrega), raio de geofence (m), timeouts de despacho (oferta, janela de favoritos), política de retorno (% sobre a corrida), revenue share do admin (%), branding. Não deletável com entregas existentes (arquivamento).

**Admin de área** (`area_admins`) — vínculo user↔área com papel (owner/manager/viewer).

**Usuário** (`users`) — autenticação base de TODOS os papéis.
[LGPD] e-mail, telefone, CPF, nome completo. Senha argon2id. TOTP opcional (obrigatório admin plataforma). Exclusão → anonimização em 30 dias (RN-021).

## Lado da demanda

**Loja** (`merchants`) — estabelecimento vinculado a UMA área.
[LGPD] CNPJ/CPF, endereço, telefone. Atributos: nome fantasia, categoria, localização (POINT), plano ativo, status (`pending_payment`, `pending_validation`, `active`, `suspended`), `menu_certo_external_id` (nullable), modalidade direta habilitada (bool — RN-027). Único por CNPJ na plataforma.

**Operador de loja** (`merchant_users`) — vínculo user↔loja com papel (owner/operator).

**Plano** (`subscription_plans`) — Free / Início / Profissional / Sem Limite (+ planos custom por área).
Atributos: mensalidade, limite de entregas/mês, taxa de plataforma por entrega, quota de SMS, acesso API (bool), prioridade de despacho (bool). Plano Free é seed imutável.

**Assinatura** (`merchant_subscriptions`) — loja↔plano com ciclo corrente, uso do mês (contador de entregas), status (`active`, `past_due`, `cancelled`), id da recorrência Safe2Pay.

**Fatura de taxas** (`platform_invoices`) — mensal por loja: soma das taxas de entregas com pagamento direto + excedentes. Fecha dia 1º, vence dia 8 (RN-025). Status: `open`, `closed`, `paid`, `overdue`.

## Lado da oferta

**Entregador** (`couriers`) — vínculo user↔área (mesmo user pode ser entregador em várias áreas).
[LGPD] documentos, selfie, placa. Atributos: nível de validação atingido (`simple`|`complete`), status (`pending_kyc`, `active`, `suspended`, `banned`), MEI (cnpj, situação, CNAEs) nullable, veículo, online/offline/busy, máx. entregas simultâneas, score (valor + nível: probation/bronze/prata/ouro/diamante), chave PIX de saque [LGPD].

**Documento do entregador** (`courier_documents`) — selfie, CNH, CRLV, MEI, antecedentes. [LGPD] arquivos no Backblaze B2 (bucket privado, URL assinada). Status por item: `pending`, `approved`, `rejected` (+ motivo). Hash SHA-256 do arquivo. Expiração (CNH/CRLV/MEI) monitorada por job.

**Cobertura** (`courier_coverage_areas`) — bairros do catálogo onde atende (e exclusões). Vale para coleta E entrega (RN-003).

**Tabela de frete** (`courier_pricing_tables`) — linhas por bairro OU faixas por km, com % de retorno. Respeita piso da área (RN-015).

**Catálogo de bairros** (`neighborhoods_catalog`) — por área, curado pelo admin local. Nome + polígono opcional. Inclui bairros informais.

## Transacional

**Entrega** (`deliveries`) — coração do sistema.
[LGPD] endereços, telefone do destinatário. Atributos: área, loja, entregador (nullable até aceite), estado (7 — RN-019), modo de despacho, endereços + POINTs, bairro destino, distância, corrida (R$), taxa de plataforma (R$), **forma de pagamento** (`card`|`pix`|`direct`), método de comprovação, `reference_number`, origem (`manual`|`menu_certo`|`api`), timestamps por transição, motivo/ator de cancelamento. Nunca deletada — anonimizada após 12 meses (RN-021).

**Transição de estado** (`delivery_state_transitions`) — append-only, imutável (RN-012). [LGPD] GPS, IP.

**Comprovação** (`delivery_proofs`) — fotos de coleta/entrega/recusa com EXIF GPS extraído, flag geofence, motivo de baixa confiança. [LGPD] imagens.

**Confirmação de pagamento direto** (`direct_payment_confirmations`) — entrega, valor declarado, meio (dinheiro/PIX), confirmado pelo entregador (bool), timestamp. "Não recebi" → gera disputa.

**Disputa** (`disputes`) — tipo (`payment_direct`, `proof`, `damage`, `other`), partes, status, mediador (admin de área), resolução + texto. SLA monitorado.

**Destinatário** (`recipients`) — identidade separada do endereço. [LGPD] nome, telefone, e-mail opcional. Hash de CPF para antifraude (nunca CPF puro). Contadores de entregas/recusas.

**Avaliação** (`ratings`) — multidirecional (loja→entregador, destinatário→entregador, entregador→loja). Estrelas + dimensões JSON + comentário. Única por entrega+avaliador.

**Snapshot de score** (`courier_score_snapshots`) — diário, com componentes e pesos (explicabilidade do score — exigência PLP 152/2025).

**Favoritos / Bloqueados** (`merchant_courier_favorites` / `_blocks`) — pares loja↔entregador. Bloqueio privado (RN-014).

## Financeiro

**Cobrança** (`platform_charges`) — por loja: assinatura, corrida+taxa (cartão/PIX), item de fatura, excedente SMS. Id de transação Safe2Pay, status, idempotency key.

**Saque** (`payouts`) — por entregador: valor, status, transação Safe2Pay, motivo de falha. Semanal automático ou manual ≥ R$ 20 [ASSUMIDO].

## Integração e governança

**API key** (`api_keys`) — por área (opcional por loja). Hash SHA-256, prefixo `jx_live_`/`jx_test_`, escopos, rate limit, último uso, revogação (RN-020).

**Webhook endpoint** (`webhook_endpoints`) + **tentativas** (`webhook_deliveries`) — alvo, eventos, segredo HMAC, saúde, retries.

**Notificação** (`notifications`) — canal (push/e-mail/SMS), template, custo (centavos), status do provedor. Quota de SMS debitada do plano.

**Log de IA** (`ai_usage_log`) — feature, provedor, modelo, tokens, custo, latência.

**Audit log** (`audit_log`) — ações administrativas com before/after. Append-only.

**Recurso de suspensão** (`suspension_appeals`) — texto, SLA (5 dias úteis), resolução. SLA estourado → reversão automática (RN-016).

## Relações essenciais

- Área 1:N {lojas, entregadores, entregas, bairros, API keys}
- User 1:N vínculos (pode ser dono de loja numa área e entregador em outra)
- Loja 1:N entregas; 1:1 assinatura ativa; 1:N faturas
- Entregador 1:N {documentos, coberturas, linhas de frete, entregas, saques}
- Entrega 1:N {transições, comprovações}; 0..1 confirmação de pagamento direto; 0..N disputas
- Loja N:N entregador via favoritos e via bloqueados (separados)

## Invariantes de dados

- Nada de domínio sem `area_id` (RN-001).
- `delivery_state_transitions` e `audit_log`: INSERT-only por trigger.
- PII nunca em log de aplicação; mascarar CPF em qualquer tela que não exija o dado completo.
- Arquivos sensíveis (KYC) só em bucket privado com URL assinada de expiração curta.
- Timestamps UTC no banco; timezone só na apresentação.
