# Jaxegô — Regras de negócio

> Formato: condição → ação → exceção. Origem: "decidido" (conversas de produto) ou [ASSUMIDO] (proposto pelo gerador, aguardando validação). Renumeração das R-001..R-022 originais + novas regras desta rodada.

| # | Regra | Origem |
|---|---|---|
| RN-001 | Toda entidade de domínio carrega `area_id`; toda query filtra pelo escopo da área do token/chave. Admin plataforma bypassa com flag auditada. **Exceção:** tabelas globais (`users`, `audit_log`, `ai_usage_log`). | decidido |
| RN-002 | Entregador só fica `active` com validação SIMPLES completa (CPF validado + selfie + telefone + e-mail confirmados). Área pode exigir COMPLETA (+ CNH EAR + CRLV + MEI + antecedentes se configurado). Nunca menos que simples. | decidido (2 níveis) |
| RN-003 | Entregador só recebe oferta se a cobertura dele inclui o bairro/polígono da coleta E da entrega. Áreas de exclusão vetam nos dois pontos. | decidido |
| RN-004 | Cancelamento pela loja: antes do aceite → custo zero; após aceite e antes da coleta → 50% da corrida; após coleta → 100% da corrida + retorno (% configurado pela área). Cancelamento por culpa do entregador → loja não paga e o evento entra no histórico do entregador. | decidido |
| RN-005 | Transição para ENTREGUE exige foto com EXIF/GPS dentro do raio do destino (default 80 m, configurável por área). Sem GPS válido → bloqueia e orienta; 3 falhas → `low_confidence` + revisão do admin. | decidido |
| RN-006 | Corrida paga via plataforma fica em escrow e só entra no saldo sacável 24h após FINALIZADA, sem disputa aberta. | decidido |
| RN-007 | Em comprovação por código OTP (pós-M1), o código NUNCA é exposto ao entregador por nenhuma API/tela; só digitação com validação server-side. | decidido |
| RN-008 | Score do entregador usa janela móvel de 90 dias: 70–80% dados objetivos (SLA, aceite, cancelamento-pós-aceite, comprovação correta) + 20–30% avaliação humana. Probation para novatos (primeiras 30 entregas). **No M1 o score é coletado e exibido, sem consequência financeira automática.** | decidido |
| RN-009 | Despacho default é cascata sequencial (favoritos → auto). Broadcast aberto é opt-in explícito por entrega (pós-M1). Nunca broadcast como padrão. | decidido |
| RN-010 | Receber repasse VIA PLATAFORMA (cartão/PIX split) exige MEI ativo com CNAE compatível e chave PIX/conta do MEI. Sem MEI → saldo acumula, saque bloqueado. | decidido |
| RN-011 | Anti-duplicidade de cadastro: CNPJ/CPF + telefone + e-mail únicos por tipo de conta. CNPJ validado na Receita (situação ativa) antes de ativar loja. | decidido |
| RN-012 | Toda transição de estado de entrega e toda ação administrativa sensível geram registro imutável (append-only) com timestamp, ator, motivo, GPS quando houver, IP. Trigger nega UPDATE/DELETE nessas tabelas. | decidido |
| RN-013 | Endereço completo do destino só é revelado ao entregador APÓS a coleta confirmada. Antes: bairro + distância estimada. | decidido |
| RN-014 | Lista de bloqueados da loja é privada, vale só para aquela loja e não afeta o score do entregador. | decidido |
| RN-015 | O entregador define a própria tabela de frete (por bairro ou por km). A plataforma impõe apenas PISO mínimo por área e calcula sugestão. A plataforma nunca fixa o preço. | decidido |
| RN-016 | Toda suspensão automática ou manual carrega motivo verificável (enum + texto) e abre canal de recurso com SLA de 5 dias úteis. SLA estourado → suspensão é automaticamente revertida até decisão + alerta ao admin plataforma. | decidido + [ASSUMIDO] reversão automática |
| RN-017 | Foto de comprovação deve enquadrar referência do local; EXIF + GPS extraídos e validados server-side; reprovação na hora com motivo acionável. | decidido |
| RN-018 | Notificação proativa ao destinatário em 3 momentos (aceite, a caminho/aproximação, entregue). Canal: push/e-mail; SMS somente no momento "a caminho" com link de tracking, limitado pela quota do plano. | decidido + [ASSUMIDO] economia de SMS |
| RN-019 | Estados da entrega no M1 são exatamente 7: CRIADA, ACEITA, COLETADA, ENTREGUE, RECUSADA_NO_DESTINO, CANCELADA, FINALIZADA. Novo estado exige ADR. | decidido |
| RN-020 | API keys: escopo por área (opcional por loja), hash SHA-256 no banco, prefixo identificável (`jx_live_`/`jx_test_`), exibida apenas uma vez, rate limit por chave, revogação propaga em <1 min. | decidido |
| RN-021 | LGPD: anonimização de PII em entregas com mais de 12 meses; exclusão de conta anonimiza histórico em 30 dias; dado fiscal preservado sem PII. | decidido |
| RN-022 | Telefones de entregador/destinatário/loja acessíveis às partes apenas durante a janela ativa da entrega (ACEITA→FINALIZADA). | decidido |
| RN-023 | A loja escolhe a forma de pagamento da corrida POR ENTREGA: cartão (Safe2Pay), PIX (Safe2Pay) ou DIRETO ao entregador (dinheiro/PIX pessoal). A taxa de plataforma incide nas três modalidades. | decidido (nova) |
| RN-024 | Entregador SEM MEI ativo pode trabalhar normalmente em entregas com pagamento DIRETO. O bloqueio por MEI (RN-010) vale apenas para repasse via plataforma. | decidido (nova) — destrava onboarding no interior |
| RN-025 | Taxas de plataforma de entregas com pagamento direto acumulam em fatura mensal da loja (fecha dia 1º, vence dia 8, Safe2Pay PIX/cartão/boleto). Fatura vencida >7 dias → bloqueio de criação de novas entregas até quitação. | [ASSUMIDO] |
| RN-026 | Em pagamento direto, o entregador confirma o recebimento ("recebi R$ X em dinheiro/PIX") na conclusão. "Não recebi" → entrega conclui, mas abre `payment_dispute` para mediação do admin de área. | decidido (nova) |
| RN-027 | Loja com 2+ disputas de pagamento direto PROCEDENTES em 30 dias perde a modalidade direta por 90 dias (só cartão/PIX). | [ASSUMIDO] — proteção do entregador |
| RN-028 | Plano Free: máximo 2 entregas/mês por loja. Contador zera no dia 1º. Tentativa de 3ª entrega → oferta de upgrade, sem cobrança automática. | decidido |
| RN-029 | Mudança de plano: upgrade imediato com cobrança pro-rata; downgrade agendado para o próximo ciclo. Limites do novo plano valem na virada. | [ASSUMIDO] |
| RN-030 | Estimativa de frete mostrada à loja antes de confirmar = mediana das tabelas dos entregadores online elegíveis para o trecho; valor final = tabela do entregador que aceitou (nunca acima do teto exibido + 10%, senão re-confirma com a loja). | [ASSUMIDO] — evita surpresa de preço |

## Convenções transversais

- API: versionamento por prefixo de URL (`/v1/`), erros RFC 7807, paginação por cursor, idempotência via header em toda escrita relevante.
- Banco: soft delete (`deleted_at`) em tabelas de domínio; FKs RESTRICT em transacionais; `utf8mb4`; timestamps UTC (conversão para America/Sao_Paulo só na borda); índices espaciais em POINT/POLYGON; cuidado com naive datetime (`grace_boundary.replace(tzinfo=None)` auditado — lição da v1.0).
- Frontend: Angular signals, reactive forms, OnPush, standalone components, lazy por rota.
