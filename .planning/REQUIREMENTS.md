# REQUIREMENTS — Jaxegô

> Gerado por `gsd-project-ingestor` em 2026-06-10 a partir de `projeto/`. Cada REQ cita a fonte.
> Prioridade MoSCoW. Itens `[ASSUMIDO]` aguardam validação humana; itens `[DECIDIR]` são Open Questions (ver DISCOVERY-REPORT.md).
> Status de implementação: Phase 1 (infra) + Phase 2 (auth/multi-área/RBAC) executadas.
> REQ-001/002/004/005/006/007 implementados na Phase 2 (ver `phases/02-.../EXECUTION-LOG.md`).
> Ressalvas: REQ-004 critério "trigger nega UPDATE/DELETE" verificado por `@pytest.mark.mysql` (pendente run ao vivo contra MySQL 8); `delivery_state_transitions` é de phase futura. REQ-002 "config sem deploy" e REQ-006 "CPF por área (entregador)" parcialmente diferidos para as phases de cadastro de loja/entregador (4/5) — nesta phase: CRUD de área (admin plataforma), email/CPF únicos em `users`, mensagem de colisão genérica.

---

## A. Núcleo multi-área e plataforma

### REQ-001: Multi-área shared-DB com `area_id` em tudo
**Categoria:** functional · **Prioridade:** must · **Origem:** `projeto/decisoes-existentes/adrs.md:7-11` (ADR-001), `projeto/regras-negocio/regras.md` RN-001
Aplicação única; toda entidade de domínio carrega `area_id`; middleware injeta escopo do token/chave em toda query. Admin plataforma bypassa com flag auditada. Tabelas globais: `users`, `audit_log`, `ai_usage_log`.
**Critérios de aceite:**
- [ ] Toda tabela de domínio tem `area_id` NOT NULL com índice
- [ ] Middleware de escopo aplicado a 100% das queries de domínio; tentativa cross-área → 403
- [ ] Testes de isolamento com 2+ áreas em todo módulo (exigência ADR-001)
- [ ] Bypass de admin plataforma gera registro em `audit_log`
**Bloqueia:** todos os demais REQs de domínio

### REQ-002: Entidade Área com regras locais configuráveis
**Categoria:** functional · **Prioridade:** must · **Origem:** `projeto/regras-negocio/entidades.md:7-8`
Área = cidade/região. Atributos: `codename` único, nível de KYC exigido (`simple|complete`), exige antecedentes, piso de frete (km e entrega), raio de geofence, timeouts de despacho, política de retorno (%), revenue share (%), branding. Não deletável com entregas (arquivamento).
**Critérios de aceite:**
- [ ] CRUD de área restrito ao admin plataforma
- [ ] Tentativa de deletar área com entregas → erro orientando arquivamento
- [ ] Configurações editáveis pelo admin de área refletem sem deploy

### REQ-003: Catálogo de bairros por área, curado pelo admin local
**Categoria:** functional · **Prioridade:** must · **Origem:** ADR-006 (`adrs.md:33-36`), `entidades.md:40`
Catálogo oficial inclui bairros informais; nome + polígono opcional; internamente tudo vira polígono espacial (índices spatial MySQL 8).
**Critérios de aceite:**
- [ ] CRUD de bairros pelo admin de área (tela 21)
- [ ] Bairro com polígono usado em matching espacial de cobertura
- [ ] Cobertura exigida na coleta E na entrega (RN-003)

### REQ-004: Audit log e transições append-only
**Categoria:** non-functional/regulatory · **Prioridade:** must · **Origem:** RN-012 (`regras.md:18`), `entidades.md:79,95`
`delivery_state_transitions` e `audit_log` são INSERT-only por trigger; registram timestamp, ator, motivo, GPS quando houver, IP, before/after em ações administrativas.
**Critérios de aceite:**
- [ ] Trigger MySQL nega UPDATE/DELETE nas duas tabelas (teste automatizado)
- [ ] Toda transição de estado de entrega gera registro
- [ ] Toda ação administrativa sensível (suspensão, mudança de piso) gera registro com before/after

---

## B. Autenticação, contas e permissões

### REQ-005: Autenticação JWT + refresh + argon2id + TOTP
**Categoria:** functional/security · **Prioridade:** must · **Origem:** ADR-005 (`adrs.md:28-31`)
Access token 15 min em memória; refresh opaco em DB (httpOnly cookie web / Secure Storage app); argon2id; TOTP obrigatório admin plataforma, opcional demais; lockout 5 tentativas/15 min.
**Critérios de aceite:**
- [ ] Login/refresh/logout funcionais nas 3 superfícies (tela 01)
- [ ] Admin plataforma sem TOTP configurado é forçado a configurar no primeiro login
- [ ] 6ª tentativa em 15 min → lockout com mensagem de tempo restante

### REQ-006: Anti-duplicidade de cadastro
**Categoria:** functional · **Prioridade:** must · **Origem:** RN-011 (`regras.md:17`), F-01 E2 (`fluxos.md:21`)
CNPJ/CPF + telefone + e-mail únicos por tipo de conta. Mensagem de colisão nunca revela QUAL dado colide além do informado (antifraude). CPF de entregador único por área; permitido em outra área (novo vínculo).
**Critérios de aceite:**
- [x] Colisão → "Já existe conta com esse dado. Recuperar acesso?" (Phase 4: mensagem única + `verify_dummy`, `test_colisao_anti_enumeracao`)
- [ ] CPF já entregador na área A pode se cadastrar na área B reaproveitando o user (Phase 5 — entregador)

### REQ-007: Papéis e permissões (6 papéis)
**Categoria:** functional/security · **Prioridade:** must · **Origem:** `visao-geral.md:25-34`
Admin plataforma, admin de área (owner/manager/viewer), loja dono, loja operador, entregador, destinatário (sem login). Operador não vê financeiro nem gere plano. Admin de área não vê outras áreas (403 — F-08 E1).
**Critérios de aceite:**
- [ ] Matriz de permissões testada por papel (testes de autorização por endpoint)
- [ ] Operador tentando acessar plano/faturas → 403 + UI esconde seções
- [ ] User pode acumular vínculos (dono de loja numa área, entregador em outra)

---

## C. Loja: cadastro, planos, assinatura

### REQ-008: Cadastro e ativação de loja (F-01)
**Categoria:** functional · **Prioridade:** must · **Origem:** `fluxos.md:7-24`, wireframe 02
CNPJ (ou CPF autônomo) validado na Receita Federal (situação ativa); confirmação de e-mail (link) e telefone (SMS); geocodificação do endereço vincula à área. Exceções E1–E4 obrigatórias (CNPJ inativo bloqueia; Receita fora do ar → `pending_validation` com retry 6/6/12/24h e Free limitado; pagamento falha → `pending_payment` usando Free).
**Critérios de aceite:**
- [x] Fluxo completo em wizard com as 4 exceções tratadas conforme F-01 (Phase 4: `test_signup` E1–E4 + wizard tela 02)
- [x] Endereço sem área cobrindo → tela "Ainda não chegamos aí" com captura de interesse (e-mail + cidade) (Phase 4: `AreaNotCoveredError` + `jx-sem-area` → POST /v1/interest)
- [ ] Admin de área enxerga fila de lojas `pending_validation` (UI de admin de área é phase futura — backend já marca o status)

### REQ-009: Planos de assinatura da loja `[ASSUMIDO — valores]`
**Categoria:** functional · **Prioridade:** must · **Origem:** `visao-geral.md:45-54`, `entidades.md:22-23`, wireframe 16
Free R$ 0/2 entregas/taxa R$ 2,00 · Início R$ 49/40/R$ 1,50 · Profissional R$ 129/150/R$ 1,00 · Sem Limite R$ 299/ilimitado/R$ 0,50. Plano Free é seed imutável. Atributos: quota SMS, acesso API, prioridade de despacho. Planos custom por área.
**Critérios de aceite:**
- [x] Seeds dos 4 planos com valores parametrizados (não hardcoded — facilita validação dos [ASSUMIDO]) (Phase 4: `PLAN_SEEDS` + `seed.py`, `test_seed_plan_values_are_data_not_hardcoded`)
- [x] Plano Free não editável/deletável (Phase 4: `is_free` flag imutável; seed não sobrescreve preço do Free)
- [~] Tela 16 exibe comparativo + plano atual + uso do mês (Phase 4: comparativo de 4 cards data-driven; "uso do mês" e faturas diferidos à Phase 10)

### REQ-010: Assinatura recorrente via Safe2Pay
**Categoria:** functional · **Prioridade:** must · **Origem:** ADR-009 v2 (`adrs.md:48-53`), `integracoes.md:7-36`
Checkout de plano pago (cartão ou PIX recorrente) na ativação ou upgrade. Status `active|past_due|cancelled`, id da recorrência Safe2Pay.
**Critérios de aceite:**
- [ ] Pagamento falha na ativação → loja fica `pending_payment`, usa Free, retry disponível (F-01 E3)
- [ ] Webhook Safe2Pay de cobrança recorrente processado idempotente

### REQ-011: Limite de entregas do plano + upgrade/downgrade
**Categoria:** functional · **Prioridade:** must · **Origem:** RN-028, RN-029 `[ASSUMIDO]` (`regras.md:34-35`), F-03 E4
Contador zera dia 1º. 3ª entrega no Free → modal de upgrade sem dark pattern (botão "agora não" visível). Upgrade imediato pro-rata; downgrade agendado próximo ciclo.
**Critérios de aceite:**
- [ ] Tentativa acima do limite → modal comparativo, sem cobrança automática
- [ ] Upgrade cobra pro-rata e libera limite na hora; downgrade só vira no ciclo

### REQ-012: Favoritos e bloqueados da loja
**Categoria:** functional · **Prioridade:** must · **Origem:** RN-014 (`regras.md:20`), `entidades.md:61`, wireframe 15
Bloqueio privado, vale só para a loja, não afeta score. Favoritos recebem cascata primeiro (REQ-027).
**Critérios de aceite:**
- [ ] Entregador bloqueado nunca recebe oferta da loja
- [ ] Bloqueio invisível ao entregador e sem efeito no score

---

## D. Entregador: cadastro, validação, cobertura, preços

### REQ-013: Cadastro do entregador em wizard com progresso salvo (F-02)
**Categoria:** functional · **Prioridade:** must · **Origem:** `fluxos.md:27-48`, wireframe 03
Etapas: área → dados (CPF validado, SMS, e-mail) → selfie com documento → veículo → [completa: CNH EAR, CRLV, MEI, antecedentes] → cobertura e preços. Abandono → retomada por 30 dias, lembretes dia 3 e 7.
**Critérios de aceite:**
- [x] Wizard com persistência de progresso por etapa (draft server-side + sessionStorage sem senha, E1)
- [x] Exceções E1–E5 de F-02 implementadas (CPF em outra área permite; MEI inativo → flag `mei_pending` com banner)
- [x] Submissão → `pending_kyc` na fila do admin de área

### REQ-014: Validação em 2 níveis (simples/completa) com aprovação item a item
**Categoria:** functional/regulatory · **Prioridade:** must · **Origem:** ADR-011 (`adrs.md:60-64`), RN-002, wireframe 19
Simples = CPF + selfie + telefone + e-mail. Completa = + CNH EAR + CRLV + MEI ativo + antecedentes (se a área exigir). Admin aprova/reprova POR ITEM com motivo; reenvio libera só o item reprovado. Admin sem revisar em 48h → escalação ao admin plataforma (F-02 E5).
**Critérios de aceite:**
- [x] Área configura nível mínimo; nunca menos que simples (RN-002, kyc.py)
- [x] Reprovação de item → motivo específico + reenvio isolado (E4: reprovar CNH não invalida selfie)
- [x] Escalação 48h visível na fila do admin plataforma (job `escalate_stale_reviews` + selo "Atrasada" E5)

### REQ-015: Documentos KYC em bucket privado B2
**Categoria:** functional/security · **Prioridade:** must · **Origem:** ADR-004 (`adrs.md:24-26`), `entidades.md:34`, `integracoes.md:85-88`
Upload por URL pré-assinada direto do cliente; compressão (máx 1920px, WebP); hash SHA-256; URL assinada de expiração curta para leitura; expiração de CNH/CRLV/MEI monitorada por job.
**Critérios de aceite:**
- [x] Nenhum documento acessível por URL pública (bucket privado; presigned GET ≤180s; test_no_public_access)
- [x] Job alerta sobre documento vencendo (`expire_documents` aware-UTC: CNH/CRLV/MEI approved→expired)
- [x] Upload com retry no cliente (presign PUT background; falha de rede → arquivo retido + retry ao reconectar)

### REQ-016: Cobertura por bairro (coleta E entrega) com exclusões
**Categoria:** functional · **Prioridade:** must · **Origem:** RN-003 (`regras.md:9`), ADR-006, wireframe 10
Entregador seleciona bairros do catálogo; exclusões vetam nos dois pontos.
**Critérios de aceite:**
- [ ] Elegibilidade de oferta exige cobertura na coleta E na entrega
- [ ] Tela 10 permite editar bairros e exclusões

### REQ-017: Tabela de frete do entregador com piso da área
**Categoria:** functional · **Prioridade:** must · **Origem:** RN-015 (`regras.md:21`), `entidades.md:38`
Linhas por bairro OU faixas por km, com % de retorno. Plataforma impõe apenas piso e calcula sugestão; nunca fixa preço.
**Critérios de aceite:**
- [ ] Valor abaixo do piso da área → rejeitado com mensagem citando o piso
- [ ] Tabela editável pelo próprio entregador (tela 10)

### REQ-018: Disponibilidade online/offline/busy + limite simultâneo
**Categoria:** functional · **Prioridade:** must · **Origem:** `entidades.md:32`, glossário, wireframe 04
`busy` automático ao atingir máx. de entregas simultâneas.
**Critérios de aceite:**
- [ ] Toggle online/offline na home do entregador
- [ ] Entregador `busy` não recebe novas ofertas até liberar carga

### REQ-019: Regras de MEI (RN-010 + RN-024)
**Categoria:** functional/regulatory · **Prioridade:** must · **Origem:** `regras.md:16,30`, ADR-012
Repasse via plataforma exige MEI ativo (CNAEs 4930-2/01, 4930-2/02, 5320-2/02, 5229-0/99) + chave PIX do MEI. SEM MEI → trabalha normalmente em pagamento direto; saldo acumula, saque bloqueado com passo a passo de regularização.
**Critérios de aceite:**
- [x] Entregador `mei_pending` (flag + banner permanente RN-024) — restrição lógica ao direto registrada (Phase 5); bloqueio efetivo de repasse é Phase 10/11
- [ ] MEI aprovado → cadastro como subconta/recebedor Safe2Pay disparado (Phase 10)
- [ ] MEI vencido com saldo → saldo preservado, saque bloqueado com aviso (F-07 E3) (Phase 11)

### REQ-020: Score explicável sem consequência financeira no M1
**Categoria:** functional · **Prioridade:** should · **Origem:** RN-008 (`regras.md:14`), ADR-013, `entidades.md:59`, wireframe 04/09
Janela 90 dias, 70–80% objetivo + 20–30% avaliação; níveis probation/bronze/prata/ouro/diamante; probation primeiras 30 entregas. Snapshot diário com componentes e pesos (explicabilidade — PLP 152/2025). Exibido com delta + causa ("Caiu 2,1 pts: 3 cancelamentos após aceite").
**Critérios de aceite:**
- [ ] "Por que esse valor?" mostra componentes, pesos e delta
- [ ] Nenhuma consequência financeira/prioridade automática ligada ao score no M1
- [ ] Snapshot diário em `courier_score_snapshots`

---

## E. Entrega: criação, despacho, execução, comprovação

### REQ-021: Criação manual de entrega pela loja (F-03)
**Categoria:** functional · **Prioridade:** must · **Origem:** `fluxos.md:51-69`, wireframe 12
Coleta pré-preenchida editável; destino com bairro do catálogo; destinatário; itens; método de comprovação (foto default | foto+referência | OTP desabilitado com badge "em breve"); forma de pagamento por entrega (cartão|PIX|direto — RN-023). Exceções E1–E5 obrigatórias.
**Critérios de aceite:**
- [~] Exceções de F-03: E1 fora da área (✅ bloqueia), E2 0 entregadores (✅ aviso não-bloqueante), E4 limite do plano (✅ modal upgrade). E3 pagamento falha (Phase 10 — só `direct` nesta phase) e E5 fatura vencida (Phase 11) deferidas com gancho.
- [x] OTP visível porém desabilitado com badge "em breve" (proof_method radiogroup, tela 12)
- [x] Estimativa exibida antes de confirmar: frete estimado (mediana RN-030) + taxa do plano (jx-estimate-box)

### REQ-022: Máquina de 7 estados com transições exclusivas e logadas
**Categoria:** functional · **Prioridade:** must · **Origem:** RN-019 (`regras.md:25`), RN-012, `fluxos.md:3`
CRIADA → ACEITA → COLETADA → ENTREGUE → FINALIZADA + RECUSADA_NO_DESTINO + CANCELADA. Transições só via máquina de estados; novo estado exige ADR. Entrega nunca deletada — anonimizada após 12 meses.
**Critérios de aceite:**
- [x] Transição inválida → erro de domínio 422 (teste exaustivo do produto cartesiano dos 7 estados)
- [x] Toda transição grava em `delivery_state_transitions` (append-only via trigger SIGNAL 45000)
- [x] Timestamps por transição na entidade entrega (accepted_at/collected_at/.../cancelled_at aware-UTC)

### REQ-023: Estimativa de frete `[ASSUMIDO — RN-030]`
**Categoria:** functional · **Prioridade:** should · **Origem:** RN-030 (`regras.md:36`)
Estimativa = mediana das tabelas dos entregadores online elegíveis; valor final = tabela de quem aceitou; se exceder teto exibido +10% → re-confirma com a loja.
**Critérios de aceite:**
- [x] Estimativa mostra faixa (min–max) + nº de entregadores online (jx-estimate-box, mediana RN-030)
- [ ] Aceite com valor > teto+10% → re-confirmação antes de prosseguir (Phase 8 — aceite/despacho)

### REQ-024: Despacho em cascata (favoritos → ranking automático)
**Categoria:** functional · **Prioridade:** must · **Origem:** ADR-007 (`adrs.md:38-41`), F-05, ADR-104
Elegíveis: online + cobre coleta E entrega + carga < limite + não bloqueado. Favoritos primeiro (1 por vez, timeout default 20s, janela 60s — configurável 10–60s por área via Redis TTL como fonte de verdade); depois ranking (distância em rota + score + carga + preço). Lock transacional no aceite; segundo aceite simultâneo → "essa entrega acabou de ser aceita" sem penalidade. Localização dos entregadores NUNCA exposta à loja.
**Critérios de aceite:**
- [ ] Cascata esgotada → loja notificada com opções: aumentar frete (re-oferta), aguardar (re-cascata 2 min), cancelar sem custo (F-05 E1)
- [ ] Teste de concorrência: 2 aceites simultâneos → 1 vence, outro recebe erro amigável
- [ ] Redis TTL é fonte de verdade do timer; cronômetro do app é visual
- [ ] Loja cancela durante cascata → ofertas canceladas, custo zero

### REQ-025: Oferta com privacidade do destino (RN-013)
**Categoria:** functional · **Prioridade:** must · **Origem:** `regras.md:19`, F-05 passo 4, wireframe 05
Oferta mostra: coleta completa, destino apenas BAIRRO + distância, valor da corrida, badge de pagamento direto, cronômetro, histórico com a loja. Endereço completo revelado só após COLETADA.
**Critérios de aceite:**
- [ ] API de oferta não retorna endereço completo do destino antes da coleta (teste de contrato)
- [ ] Wireframe 05 fiel: "(endereço completo após a coleta)"

### REQ-026: Execução coleta → entrega (F-06)
**Categoria:** functional · **Prioridade:** must · **Origem:** `fluxos.md:109-128`, wireframes 06/07
"Cheguei na coleta" → foto da coleta com GPS no raio → COLETADA (revela destino) → rota → notificação de aproximação ao destinatário → comprovação no destino → ENTREGUE → job FINALIZADA após 24h sem disputa. Exceções E1–E6 obrigatórias (ausente com espera de 10 min, recusa, referência 3 tentativas + liberação manual pela loja com log, acidente → admin redespacha, pagamento direto não recebido → disputa).
**Critérios de aceite:**
- [ ] Fluxo feliz completo + 6 exceções de F-06
- [ ] Botões ligar/mensagem respeitam janela de telefones (RN-022: ACEITA→FINALIZADA)
- [ ] Job de finalização roda 24h após ENTREGUE sem disputa

### REQ-027: Comprovação por foto + EXIF/GPS no raio (geofence)
**Categoria:** functional · **Prioridade:** must · **Origem:** RN-005, RN-017 (`regras.md:11,23`), ADR-008
Foto obrigatória em TODA entrega; EXIF + GPS validados server-side no raio (default 80 m configurável por área); rejeição na hora com motivo acionável; 3 falhas → `low_confidence` + revisão do admin com transição bloqueada. Upload offline-tolerante (flag `pending_upload`; transição só conclui com upload OK — `integracoes.md:88`).
**Critérios de aceite:**
- [ ] Foto sem GPS ou fora do raio → rejeitada com motivo ("ative a localização" / "aproxime-se")
- [ ] 3 falhas → flag + fila do admin de área
- [ ] B2 indisponível → foto retida no device, sobe ao reconectar

### REQ-028: Comprovação por número de referência
**Categoria:** functional · **Prioridade:** must · **Origem:** F-03 passo 3, F-06 passo 5 e E4, wireframe 07
Camada adicional à foto: digitação do número validada contra `reference_number`; 3 tentativas → orientação para ligar à loja; loja pode "liberar entrega" manualmente com log.
**Critérios de aceite:**
- [ ] Validação server-side; contador de tentativas visível ("tentativa 2 de 3")
- [ ] Liberação manual pela loja registrada em audit/transição

### REQ-029: Cancelamento com matriz de custos (RN-004)
**Categoria:** functional · **Prioridade:** must · **Origem:** `regras.md:10`, F-05 E2 `[ASSUMIDO]`, F-07 E1
Antes do aceite → zero; pós-aceite pré-coleta → 50% da corrida; pós-coleta → 100% + retorno (% da área). Culpa do entregador → loja não paga; evento no histórico. "Aceitou e sumiu" (2× ETA sem chegada) → loja cancela sem custo e redespacha `[ASSUMIDO]`. Estorno do excedente em até 5 dias úteis.
**Critérios de aceite:**
- [ ] Cada cenário de custo testado (0% / 50% / 100%+retorno / culpa do entregador)
- [ ] Cancelamento sempre com motivo + ator registrados

### REQ-030: Tracking público sem login
**Categoria:** functional · **Prioridade:** must · **Origem:** wireframe 26, glossário, referência Mercado Livre
Link curto (`jaxego.com.br/r/abc`); timeline de estados; dados do entregador (nome, veículo, placa, estrelas); banner de estado; link expirado → erro orientando. Mapa com posição aproximada é pós-M1 (ADR-101 — GPS polling é v1.1); no M1 a área do mapa mostra estado/timeline.
**Critérios de aceite:**
- [ ] Página pública sem autenticação, mobile-first, sem PII além do necessário
- [ ] Link expirado/inválido → estado de erro do wireframe 26
- [ ] Sem mapa em tempo real no M1 (placeholder honesto)

### REQ-031: Notificações ao destinatário em 3 momentos (RN-018)
**Categoria:** functional · **Prioridade:** must · **Origem:** `regras.md:24` `[ASSUMIDO economia de SMS]`, `integracoes.md:63-81`
Aceite, a caminho/aproximação, entregue. Push/e-mail; SMS SOMENTE no "a caminho" com link de tracking, limitado pela quota do plano. Geofence de aproximação dispara "está chegando".
**Critérios de aceite:**
- [ ] 3 momentos disparados; SMS só no segundo, debitando quota
- [ ] Quota esgotada → degrada para push/e-mail sem erro

### REQ-032: Janela de acesso a telefones (RN-022)
**Categoria:** functional/privacy · **Prioridade:** must · **Origem:** `regras.md:28`
Telefones de entregador/destinatário/loja acessíveis às partes apenas entre ACEITA e FINALIZADA.
**Critérios de aceite:**
- [ ] API nega telefone fora da janela (teste por estado)

### REQ-033: Avaliações multidirecionais
**Categoria:** functional · **Prioridade:** should · **Origem:** `entidades.md:57`, F-06 passo 7
Loja→entregador, destinatário→entregador, entregador→loja. Estrelas + dimensões JSON + comentário; única por entrega+avaliador; liberada em ENTREGUE.
**Critérios de aceite:**
- [ ] Constraint de unicidade entrega+avaliador
- [ ] Avaliação alimenta componente humano do score (REQ-020)

---

## F. Pagamentos e financeiro

### REQ-034: Cobrança por entrega cartão/PIX com split Safe2Pay
**Categoria:** functional · **Prioridade:** must · **Origem:** ADR-009 v2, RN-023, `integracoes.md:7-36`, F-07
Cobrança na criação (antes do despacho): corrida → subconta do entregador, taxa → conta Jaxegô (+ revenue share quando configurado). Idempotência por `Reference`. Recusa → entrega não nasce. Circuit breaker se API fora do ar (pagamento direto continua). Camada de pagamento atrás de interface própria (trocar PSP não pode doer).
**Critérios de aceite:**
- [ ] Abstração PSP própria; Safe2Pay como implementação
- [ ] Split correto corrida/taxa testado; revenue share parametrizado
- [ ] Webhooks Safe2Pay idempotentes por `IdTransaction`, resposta <5s, trabalho pesado em fila
- [ ] `[DECIDIR]` validado: split disponível no plano contratado, prazo de repasse, taxas (bloqueia execução desta funcionalidade)

### REQ-035: Pagamento direto como modalidade de 1ª classe
**Categoria:** functional · **Prioridade:** must · **Origem:** ADR-012 (`adrs.md:66-71`), RN-023/024/026
Loja paga na mão (dinheiro/PIX pessoal); plataforma registra valor declarado + confirmação do entregador na conclusão ("Recebi R$ X em dinheiro/PIX"); "não recebi" → entrega conclui mas abre `payment_dispute`. Taxa acumula na fatura mensal.
**Critérios de aceite:**
- [ ] Confirmação obrigatória na comprovação quando `payment_method=direct` (wireframe 07)
- [ ] "Não recebi" → disputa criada para o admin de área, entrega vira ENTREGUE normalmente
- [ ] Taxa da entrega lançada na fatura aberta do mês

### REQ-036: Escrow interno de 24h (RN-006)
**Categoria:** functional · **Prioridade:** must · **Origem:** `regras.md:12`, F-07
Corrida via plataforma só entra no saldo sacável 24h após FINALIZADA, sem disputa aberta. Disputa nas 24h → congela só aquela entrega (F-07 E4).
**Critérios de aceite:**
- [ ] Job de liberação respeita FINALIZADA+24h e ausência de disputa
- [ ] Disputa congela apenas a corrida em questão

### REQ-037: Fatura mensal de taxas `[ASSUMIDO — RN-025]`
**Categoria:** functional · **Prioridade:** must · **Origem:** `regras.md:31`, `entidades.md:27`, wireframe 16
Soma taxas de pagamento direto + excedentes (SMS). Fecha dia 1º, vence dia 8, Safe2Pay PIX/cartão/boleto. Vencida >7 dias → bloqueio de novas entregas até quitação, com link direto para pagar.
**Critérios de aceite:**
- [ ] Jobs de fechamento (dia 1º) e cobrança; status `open|closed|paid|overdue`
- [ ] Bloqueio em F-03 E5 testado; banner do wireframe 16
- [ ] 2ª via acessível

### REQ-038: Saque do entregador `[ASSUMIDO — mínimo R$ 20]`
**Categoria:** functional · **Prioridade:** must · **Origem:** `entidades.md:67`, F-07, wireframe 08
Automático semanal (terça) via PIX para chave do MEI, ou manual ≥ R$ 20. Exige MEI ativo (RN-010). Falha (chave inválida) → `failed` com motivo, saldo retorna.
**Critérios de aceite:**
- [ ] Job semanal + saque manual com validação de mínimo
- [ ] Falha de PIX → saldo restituído + orientação para corrigir chave

### REQ-039: Disputas e mediação
**Categoria:** functional · **Prioridade:** must · **Origem:** `entidades.md:53`, RN-026/027, F-08 passo 5
Tipos: `payment_direct`, `proof`, `damage`, `other`. Mediador: admin de área. Loja com 2+ disputas de pagamento direto PROCEDENTES em 30 dias perde modalidade direta por 90 dias `[ASSUMIDO — RN-027]` (aviso no wireframe 12).
**Critérios de aceite:**
- [ ] Fluxo de mediação com resolução + texto, notificando partes
- [ ] Contador de procedência aplica e expira o bloqueio de 90 dias automaticamente

### REQ-040: Conciliação diária Safe2Pay
**Categoria:** non-functional · **Prioridade:** should · **Origem:** `integracoes.md:34`
Job diário extrato × registros; diferença > R$ 0,01 → alerta admin plataforma.
**Critérios de aceite:**
- [ ] Job com relatório de divergências e alerta

---

## G. API pública e integração Menu Certo

### REQ-041: `POST /v1/deliveries` com idempotência (F-04)
**Categoria:** functional · **Prioridade:** must · **Origem:** ADR-010 (`adrs.md:55-58`), `fluxos.md:72-86`, `integracoes.md:40-51`
`Idempotency-Key` obrigatório (resposta cacheada 24h); 202 com `delivery_id`, `tracking_url`, estimativas; entrega `source=menu_certo`. Erros RFC 7807; 429 com `Retry-After`; 401 com código estável para chave revogada.
**Critérios de aceite:**
- [ ] Mesma key → mesma resposta sem duplicar (teste)
- [ ] Contrato documentado (OpenAPI) para o time Menu Certo

### REQ-042: API keys por área (RN-020)
**Categoria:** functional/security · **Prioridade:** must · **Origem:** `regras.md:26`, `entidades.md:71`, wireframe 22
Hash SHA-256; prefixo `jx_live_`/`jx_test_`; exibida UMA vez; escopos; rate limit por chave (Redis); revogação propaga <1 min; último uso visível.
**Critérios de aceite:**
- [ ] Chave em claro nunca persistida; exibição única na criação
- [ ] Revogação efetiva em <1 min (teste com cache)

### REQ-043: Webhooks de saída com HMAC e retry
**Categoria:** functional · **Prioridade:** must · **Origem:** ADR-010, `integracoes.md:47-51`
Eventos `delivery.accepted|picked_up|delivered|refused_at_destination|cancelled|finalized`. `X-Jaxego-Signature: t=<ts>,v1=<hmac>` + `X-Jaxego-Event-Id`; janela anti-replay 5 min; retry 0s/30s/2min/10min/1h/4h/12h/24h; 4xx≠429 = permanente; 8 falhas → endpoint `unhealthy` + alerta; entrega nunca afetada.
**Critérios de aceite:**
- [ ] Assinatura verificável pelo receptor (teste de integração com receptor fake)
- [ ] Fila arq com a política exata de retry; health do endpoint visível ao admin de área

---

## H. Administração

### REQ-044: Painel do admin de área (F-08)
**Categoria:** functional · **Prioridade:** must · **Origem:** `fluxos.md:156-171`, wireframes 17–22
Dashboard (entregas hoje, online, fila KYC, disputas, faturas vencidas); KYC item a item; configuração da área; API keys; disputas; suspensões com motivo enum + texto.
**Critérios de aceite:**
- [ ] Escopo de área no token: ação fora da área → 403 (F-08 E1)
- [ ] Ações sensíveis em audit_log com before/after

### REQ-045: Suspensão com recurso e reversão automática (RN-016)
**Categoria:** functional/regulatory · **Prioridade:** must · **Origem:** `regras.md:22` `[ASSUMIDO reversão]`, `entidades.md:81`
Motivo verificável (enum + texto); canal de recurso SLA 5 dias úteis; SLA estourado → suspensão automaticamente revertida + alerta ao admin plataforma.
**Critérios de aceite:**
- [ ] Job de SLA reverte suspensão sem resposta e alerta
- [ ] Copy de suspensão segue brand.md ("Conta suspensa: <motivo>. Você pode recorrer em até 5 dias úteis.")

### REQ-046: Painel do admin plataforma
**Categoria:** functional · **Prioridade:** must · **Origem:** `visao-geral.md:29`, wireframes 23–25
Criar/arquivar áreas, planos globais, visão cross-área, auditoria de admins de área, suspender qualquer conta, fila de escalações (KYC 48h, SLA de recurso). MFA obrigatório.
**Critérios de aceite:**
- [ ] Acesso só com TOTP ativo
- [ ] Visão cross-área com flag auditada (RN-001)

### REQ-047: Revenue share do admin de área `[DECIDIR — % default]`
**Categoria:** functional · **Prioridade:** should · **Origem:** `visao-geral.md:43,74`, `entidades.md:8`
% das taxas de plataforma da área, configurável por área. Entra no split (REQ-034) quando configurado.
**Critérios de aceite:**
- [ ] Campo por área com default global parametrizado (pendente decisão: sugestão 20%)
- [ ] Relatório financeiro da área mostra o share

---

## I. Não-funcionais e transversais

### REQ-048: LGPD by design (RN-021)
**Categoria:** regulatory · **Prioridade:** must · **Origem:** `regras.md:27`, `entidades.md:92-98`
Anonimização de PII em entregas >12 meses (job); exclusão de conta → anonimização em 30 dias; dado fiscal preservado sem PII; PII nunca em log; CPF mascarado em tela ("123.***.***-09"); hash de CPF do destinatário para antifraude (nunca CPF puro).
**Critérios de aceite:**
- [ ] Jobs de anonimização agendados e testados
- [ ] Lint/teste de logs sem campos PII (config observability já proíbe)

### REQ-049: Notificações multicanal com quota e fallback
**Categoria:** functional · **Prioridade:** must · **Origem:** `entidades.md:75`, `integracoes.md:63-81`
Push (VAPID) principal; e-mail SES; SMS Zenvia primário/Twilio fallback; ambos SMS falham → degrada para e-mail+push; bounce SES → supressão; tokens push expirados limpos por job; custo em centavos registrado por notificação.
**Critérios de aceite:**
- [ ] Cadeia de fallback testada por canal
- [ ] Quota de SMS por plano debitada; excedente vai à fatura

### REQ-050: Observabilidade e orçamentos de performance
**Categoria:** non-functional · **Prioridade:** must · **Origem:** `stacks/stack.md:38,55-56`
Sentry + Prometheus + logs estruturados stdout; métrica de despacho (tempo até aceite); p95 < 200 ms nos endpoints quentes (criar entrega, aceitar oferta); LCP < 2.500 ms em 4G.
**Critérios de aceite:**
- [ ] request_id em todo log; campos obrigatórios do config.json
- [ ] Dashboard/métrica do tempo criação→aceite (KPI norte)

### REQ-051: App do entregador como web Ionic + APK Android `[ASSUMIDO]`
**Categoria:** functional · **Prioridade:** must · **Origem:** ADR-003, `visao-geral.md:69`
Web responsivo + APK via Capacitor com distribuição direta no M1 (câmera, GPS, push). Lojas oficiais e iOS no M2.
**Critérios de aceite:**
- [ ] APK gerado em CI, instalável, com câmera/GPS/push funcionais
- [ ] Mesmo código serve web e app

### REQ-052: Infra Docker Compose + CI/CD
**Categoria:** non-functional · **Prioridade:** must · **Origem:** `stacks/stack.md:31-38`
Compose sobe API, worker arq, Redis, MySQL; Nginx TLS/rate limit; GitHub Actions lint → testes → build → deploy por tag.
**Critérios de aceite:**
- [ ] `docker compose up` funcional do zero
- [ ] Pipeline verde obrigatório para deploy

### REQ-053: Infraestrutura de LLM (sem features no M1)
**Categoria:** functional · **Prioridade:** could · **Origem:** `integracoes.md:99-102`, `entidades.md:77`
Router simples Claude/OpenAI + `ai_usage_log` (provedor, modelo, tokens, custo, latência). Nenhuma feature de IA no M1.
**Critérios de aceite:**
- [ ] Router e tabela existem e são testáveis; nenhum fluxo operacional depende deles

### REQ-054: Rotas/ETA via OSRM `[ASSUMIDO]`
**Categoria:** functional · **Prioridade:** should · **Origem:** `integracoes.md:92-95`, ADRs `[ASSUMIDO]`
OSRM self-hosted para distância em rota/ETA (ranking de despacho, estimativas); fallback haversine × 1,4 com flag `eta_degraded`; Google Distance Matrix como fallback pago opcional. Tiles OSM/MapLibre.
**Critérios de aceite:**
- [ ] OSRM fora → sistema continua com ETA degradado sinalizado

### REQ-055: Estados de UI obrigatórios em todas as telas
**Categoria:** UX · **Prioridade:** must · **Origem:** wireframes 01–26 (estados `empty-state`, `error-state`, `loading skeleton`, `warn` detectados no DOM)
Todas as 26 telas dos wireframes têm estados explícitos definidos. São contrato verificável (fidelidade enforced v0.9.7 — `wireframes/README.md:33-41`).
**Critérios de aceite:**
- [ ] Cada tela implementa os estados presentes no wireframe correspondente
- [ ] Copy de estados segue brand.md (empty: por que está vazio + ação)

### REQ-056: Vocabulário canônico e voz da marca em toda copy
**Categoria:** UX · **Prioridade:** must · **Origem:** `projeto/regras-negocio/glossario.md`, `projeto/identidade-visual/brand.md`
"entregador" (nunca motoboy), "corrida" no app do entregador / "frete" na UI da loja, "pagamento direto" (nunca "por fora"), "validação simples/completa" (KYC só em admin). Regra do italic Fraunces (1 palavra-chave por título, nunca em botões/labels/erros). Formatos de número/data/CPF do brand.md.
**Critérios de aceite:**
- [ ] Revisão de copy contra glossário em toda phase com UI
- [ ] Tokens tipográficos de tokens.json (Inter Tight/Fraunces/JetBrains Mono) aplicados conforme regra

---

## Resumo

| Categoria | REQs | must | should | could |
|---|---|---|---|---|
| A. Multi-área/plataforma | 001–004 | 4 | 0 | 0 |
| B. Auth/contas | 005–007 | 3 | 0 | 0 |
| C. Loja | 008–012 | 5 | 0 | 0 |
| D. Entregador | 013–020 | 7 | 1 | 0 |
| E. Entrega | 021–033 | 11 | 2 | 0 |
| F. Financeiro | 034–040 | 6 | 1 | 0 |
| G. API/Menu Certo | 041–043 | 3 | 0 | 0 |
| H. Admin | 044–047 | 3 | 1 | 0 |
| I. Transversais | 048–056 | 7 | 1 | 1 |
| **Total** | **56** | **49** | **6** | **1** |
