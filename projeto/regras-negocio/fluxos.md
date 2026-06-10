# Jaxegô — Fluxos principais

> Numeração F-NN. Toda exceção mapeada vira comportamento obrigatório. Estados da entrega: CRIADA → ACEITA → COLETADA → ENTREGUE → FINALIZADA, com desvios RECUSADA_NO_DESTINO e CANCELADA. Transições só via máquina de estados, sempre logadas (RN-012).

---

## F-01 · Cadastro e ativação de loja

**Ator:** dono do estabelecimento. **Telas:** 02-cadastro-loja, 16-loja-plano.

1. Dono acessa jaxego.com.br → "Cadastrar minha loja".
2. Informa: CNPJ (ou CPF para autônomo), nome fantasia, categoria, telefone, e-mail, senha.
3. Sistema valida CNPJ na Receita (situação ativa) e unicidade de CNPJ/CPF + telefone + e-mail (RN-011).
4. Confirma e-mail (link) e telefone (código SMS).
5. Informa endereço da loja → sistema geocodifica e vincula à **área** correspondente. Se nenhuma área cobre o endereço → tela "Ainda não chegamos aí" com captura de interesse (e-mail + cidade) [estado vazio obrigatório].
6. Escolhe plano (Free pré-selecionado). Plano pago → checkout assinatura Safe2Pay (cartão ou PIX recorrente).
7. Loja ativa. Dashboard liberado com onboarding de primeira entrega.

**Exceções:**
- E1. CNPJ inativo/inexistente na Receita → bloqueia com mensagem "CNPJ não está ativo na Receita Federal" + link para suporte.
- E2. CNPJ/telefone/e-mail já cadastrado → "Já existe conta com esse dado. Recuperar acesso?" (nunca dizer QUAL dado colide além do informado — antifraude).
- E3. Pagamento da assinatura falha → loja fica criada em `pending_payment`, pode usar plano Free imediatamente e tentar de novo; aviso persistente no dashboard.
- E4. Receita Federal fora do ar → cadastro segue como `pending_validation`, loja usa Free com limite, validação reprocessada em job (retry 6/6/12/24h); admin de área enxerga fila de pendentes.

---

## F-02 · Cadastro e validação de entregador (KYC simples ou completa)

**Ator:** entregador; admin de área aprova. **Telas:** 03-cadastro-entregador, 19-admin-area-entregador-detalhe.

1. Entregador acessa app/site → "Quero entregar".
2. Escolhe a área onde vai atuar (lista de áreas ativas).
3. Wizard etapa 1 — dados: nome completo, CPF, data de nascimento, telefone, e-mail, senha. Valida CPF (formato + dígito + situação), confirma telefone (SMS) e e-mail (link).
4. Wizard etapa 2 — selfie com documento (foto do rosto segurando o CPF/CNH). Upload para Backblaze B2.
5. Wizard etapa 3 — veículo: tipo (moto/bicicleta/carro/a pé), placa se motorizado.
6. **Se a área exige validação COMPLETA** (configuração da área): etapa 4 — CNH com EAR (foto), CRLV (foto), CNPJ do MEI (consulta automática de situação + CNAEs), antecedentes criminais (upload, se a área exigir).
7. Wizard etapa 5 — cobertura e preços: seleciona bairros do catálogo da área onde atende (coleta E entrega), define tabela de preço (por bairro ou por km), respeitando piso da área (RN-015).
8. Submete → status `pending_kyc`. Admin de área recebe na fila de revisão.
9. Admin aprova item a item (selfie ok? CNH ok?) → status `active`. Reprovação de item → notificação com motivo específico e reenvio liberado só daquele item.
10. Entregador ativo: pode ficar online e receber ofertas.

**Exceções:**
- E1. Wizard abandonado no meio → progresso salvo; retomada de onde parou por até 30 dias; lembrete por e-mail no dia 3 e dia 7.
- E2. CPF já cadastrado na MESMA área → bloqueia ("você já tem cadastro, recupere o acesso"). CPF em OUTRA área → permite (mesmo usuário, novo vínculo de entregador na nova área).
- E3. MEI inexistente/inativo na validação completa → cadastro segue, mas com flag `mei_pending`: pode trabalhar APENAS com entregas de pagamento direto (RN-024); banner permanente explicando como regularizar.
- E4. Documento ilegível → admin reprova o item com motivo; entregador reenvia sem refazer o resto.
- E5. Admin não revisa em 48h → escalação: notificação ao admin de área + visibilidade na fila do admin plataforma.

---

## F-03 · Criação de entrega pela loja (manual)

**Ator:** loja (dono ou operador). **Telas:** 12-loja-nova-entrega.

1. Loja clica "Nova entrega".
2. Preenche: endereço de coleta (pré-preenchido com a loja, editável), endereço de entrega (CEP/autocomplete → bairro do catálogo), dados do destinatário (nome, telefone), itens (descrição, quantidade; valor declarado opcional), observações.
3. Escolhe método de comprovação: foto (default) | foto + número de referência | foto + código OTP [OTP fora do M1 — selecível mas desabilitado com badge "em breve"].
4. Escolhe forma de pagamento da corrida: **cartão** | **PIX** | **direto ao entregador** (RN-023).
5. Sistema calcula estimativa de frete (com base nas tabelas dos entregadores online elegíveis) e mostra: frete estimado + taxa de plataforma do plano.
6. Confirma. Se cartão/PIX → pré-autorização/cobrança via Safe2Pay ANTES do despacho. Se direto → entrega nasce sem cobrança online (taxa vai para a fatura mensal).
7. Entrega `CRIADA` → entra no despacho (F-05).

**Exceções:**
- E1. Endereço de entrega fora da área → "Endereço fora da nossa área de cobertura" + sugestão de avisar interesse.
- E2. Nenhum entregador online cobre origem E destino → criação permitida com aviso "0 entregadores disponíveis agora — sua entrega pode demorar"; loja decide criar mesmo assim ou cancelar.
- E3. Pagamento cartão/PIX falha → entrega NÃO nasce; erro claro + retry + opção "trocar para pagamento direto".
- E4. Loja atingiu limite de entregas do plano → modal de upgrade com comparativo de planos; sem dark pattern: botão "agora não" visível.
- E5. Loja com fatura de taxas vencida >7 dias → criação bloqueada (RN-025) com link direto para pagar fatura.

---

## F-04 · Criação de entrega via Menu Certo (API)

**Ator:** sistema Menu Certo. **Integração:** docs-externos/integracoes.md.

1. Pedido pronto no Menu Certo → operador clica "Chamar Jaxegô".
2. Menu Certo faz `POST /v1/deliveries` com API key da área + `Idempotency-Key` única por pedido. Payload traz endereços, destinatário, itens, `reference_number` (nº do pedido), `payment_method`.
3. Jaxegô valida API key, escopo, rate limit e idempotência. Cria entrega `source=menu_certo`.
4. Resposta 202 com `delivery_id`, `tracking_url`, estimativas.
5. Eventos voltam por webhook HMAC: `delivery.accepted`, `delivery.picked_up`, `delivery.delivered`, `delivery.cancelled` (retry exponencial 8 tentativas).

**Exceções:**
- E1. Idempotency-Key repetida → retorna a MESMA resposta da primeira chamada (sem duplicar).
- E2. API key revogada/expirada → 401 com código de erro estável; Menu Certo exibe "reconfigurar integração".
- E3. Webhook do Menu Certo fora do ar → retries 0s/30s/2min/10min/1h/4h/12h/24h; após 8 falhas, endpoint `unhealthy` + alerta ao admin de área; entrega NÃO é afetada (desacoplamento).
- E4. Rate limit excedido → 429 com `Retry-After`.

---

## F-05 · Despacho e aceite (favoritos → auto, cascata)

**Ator:** sistema; entregador decide. **Telas:** 05-entregador-oferta.

1. Entrega `CRIADA` → monta lista de elegíveis: online + cobre coleta E entrega + carga atual < limite + não bloqueado pela loja + (tags requeridas, quando existirem).
2. Se a loja tem favoritos elegíveis → cascata nos favoritos (1 por vez, timeout configurável da área, default 20s; janela total de favoritos default 60s).
3. Esgotou favoritos (ou não há) → cascata no ranking automático: distância em rota + score + carga + preço da tabela do entregador.
4. Oferta no app: origem (endereço completo da coleta), destino (apenas BAIRRO + distância — endereço completo só após coleta, RN-013), valor da corrida, cronômetro.
5. Entregador aceita → `ACEITA`; demais ofertas pendentes da cascata são canceladas; loja e destinatário notificados; nome/foto/placa/score do entregador visíveis para a loja.
6. Recusa ou timeout → próximo da cascata.

**Exceções:**
- E1. Cascata esgotada sem aceite → loja notificada com opções: aumentar o frete (re-oferta), aguardar (re-cascata em 2 min), cancelar sem custo.
- E2. Entregador aceita e fica parado (sem chegar à coleta em 2× o ETA) → loja pode cancelar sem custo e redespachar; evento conta como cancelamento-pós-aceite do entregador [ASSUMIDO].
- E3. Dois aceites simultâneos (corrida de rede) → lock transacional; o segundo recebe "essa entrega acabou de ser aceita" sem penalidade.
- E4. Loja cancela durante a cascata → ofertas canceladas; sem custo (RN-004 só cobra após aceite).

---

## F-06 · Coleta → entrega → comprovação

**Ator:** entregador. **Telas:** 06-entregador-entrega-ativa, 07-entregador-comprovacao.

1. `ACEITA` → app mostra rota até a coleta + botões ligar/mensagem.
2. Chegou → "Cheguei na coleta" → loja vê status. Confere itens.
3. Tira FOTO da coleta (mercadoria/fachada). GPS validado no raio da coleta (80 m default da área). → `COLETADA`. **Endereço completo do destino é revelado agora.**
4. Rota até o destino. Geofence de aproximação dispara notificação "está chegando" ao destinatário (push/e-mail; SMS se quota).
5. No destino: foto da entrega (porta/fachada/recebedor conforme método). Se método = número de referência → digita o nº que o destinatário informar; valida contra `reference_number`.
6. Se pagamento = **direto** → tela "Recebeu o pagamento da loja/destinatário?" → confirma "Recebi R$ X em dinheiro/PIX" (RN-026).
7. → `ENTREGUE`. Loja, destinatário notificados. Avaliação liberada.
8. Após 24h sem disputa → `FINALIZADA` (job); valor da corrida (quando via plataforma) liberado no saldo do entregador (RN-006).

**Exceções:**
- E1. Foto sem GPS ou fora do raio → upload rejeitado na hora com motivo ("ative a localização" / "aproxime-se do endereço"); 3 falhas → flag `low_confidence` + revisão do admin de área; transição bloqueada até resolver.
- E2. Destinatário AUSENTE → botão "destinatário ausente" → sistema notifica destinatário (SMS/push) e exibe telefone para o entregador ligar → 10 min sem resposta → "retornar ao estabelecimento" → `RECUSADA_NO_DESTINO` (reason `absent`); loja paga corrida + retorno conforme política da área [ASSUMIDO].
- E3. Destinatário RECUSA o item → foto da recusa + motivo → `RECUSADA_NO_DESTINO` (reason `refused`); retorno idem.
- E4. Número de referência não bate (3 tentativas) → orientação para ligar à loja; loja pode confirmar manualmente pelo painel ("liberar entrega") com log.
- E5. Acidente/imprevisto do entregador no meio → botão "não consigo concluir" com motivo → admin de área notificado → redespacho manual ou cancelamento; corrida parcial avaliada caso a caso pelo admin (M1: manual).
- E6. Pagamento direto e loja/destinatário NÃO pagou → entregador marca "não recebi" → entrega conclui (`ENTREGUE`) mas abre `payment_dispute` para o admin de área mediar; loja com 2+ disputas procedentes em 30 dias perde a opção de pagamento direto (RN-027).

---

## F-07 · Pagamento da corrida e taxas

**Ator:** loja paga; entregador recebe. **Telas:** 16-loja-plano (faturas), 08-entregador-extrato.

**Modalidade cartão/PIX (via plataforma):**
1. Cobrança Safe2Pay na criação (F-03 passo 6): valor = corrida + taxa de plataforma.
2. Split: corrida → subconta do entregador (retida em escrow interno), taxa → conta Jaxegô (+ revenue share da área, quando configurado).
3. `FINALIZADA` + 24h → corrida liberada no saldo sacável do entregador.
4. Saque: automático semanal (terça) via PIX para a chave do entregador, ou manual a qualquer momento acima de R$ 20 [ASSUMIDO]. Exige MEI ativo (RN-010).

**Modalidade direta:**
1. Loja paga o entregador na mão (dinheiro ou PIX pessoal) na coleta ou entrega.
2. Plataforma NÃO processa a corrida; registra o valor declarado e a confirmação do entregador (F-06 passo 6).
3. Taxa de plataforma da entrega acumula na **fatura mensal** da loja.
4. Fatura fecha dia 1º, vence dia 8, paga via Safe2Pay (PIX/cartão/boleto). Vencida >7 dias → bloqueio de novas entregas (RN-025).

**Exceções:**
- E1. Cancelamento pós-aceite/pós-coleta → cobranças parciais conforme RN-004 (50% / 100% + retorno); estorno do excedente em cartão/PIX em até 5 dias úteis.
- E2. Saque falha (chave PIX inválida) → status `failed` com motivo, saldo volta ao disponível, entregador corrige a chave.
- E3. MEI vencido com saldo acumulado → saldo preservado, saque bloqueado com aviso e passo a passo de regularização; pagamento direto continua permitido.
- E4. Disputa aberta dentro das 24h → corrida daquela entrega congelada até resolução do admin de área; demais entregas seguem normais.

---

## F-08 · Gestão da área pelo admin local

**Ator:** admin de área. **Telas:** 17 a 22.

1. Dashboard da área: entregas hoje, entregadores online, fila de KYC, disputas abertas, faturas vencidas.
2. KYC: fila de revisão → aprovar/reprovar item a item com motivo (F-02 passo 9).
3. Configuração da área: nível de validação exigido (simples/completa), piso de frete, raio de geofence, timeouts de despacho, catálogo de bairros (CRUD), política de retorno.
4. API keys: criar (escopos + nome), revogar, ver último uso. Chave exibida UMA vez (RN-020).
5. Disputas: mediar pagamento direto não recebido, comprovações low_confidence, recursos de suspensão (SLA 5 dias úteis, RN-016).
6. Suspensão de entregador/loja: sempre com motivo de enum + texto; gera notificação e abre canal de recurso.

**Exceções:**
- E1. Admin tenta agir fora da própria área → 403 (escopo de área no token, RN-001).
- E2. Ação sensível (suspensão, mudança de piso) → registrada em audit_log com before/after (RN-012).
- E3. Recurso de suspensão sem resposta no SLA → suspensão automaticamente SUSPENSA (entregador volta) + alerta ao admin plataforma [melhoria: o ônus do atraso é da gestão, não do trabalhador].
