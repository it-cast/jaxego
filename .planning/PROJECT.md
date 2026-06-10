# Jaxegô

**Domínio:** Plataforma B2B2C de entregas last-mile por área (cidade/região) para o interior do Brasil
**Estágio:** novo (greenfield — nenhuma linha de código)
**Owner:** Grupo Itcast (família Menu Certo)
**Domínio prod:** jaxego.com.br
**Locale:** pt-BR (UI) · código e schema em inglês
**Última atualização do PROJECT.md:** 2026-06-10

## Visão de uma frase

Malha de entregadores estruturada para cidades de 30k–200k habitantes, dividida por **áreas** com regras locais, onde a loja assina um plano, paga a corrida por cartão, PIX ou direto ao entregador, e o pedido do Menu Certo vira entrega com 1 clique.

## Propósito

Estabelecimentos do interior não têm para quem ligar quando o motoboy próprio não dá conta: iFood Entregadores é fechado, Loggi/Lalamove não cobrem ou cobram caro, white-labels vendem app sem malha. Do outro lado, entregadores dessas cidades trabalham por WhatsApp, sem comprovação, score ou proteção. (`projeto/regras-negocio/visao-geral.md:5-9`)

O Jaxegô é uma aplicação única dividida por áreas — cada área com nível de validação de entregador, piso de preço, catálogo de bairros e política de cancelamento próprios (ADR-001). A demanda inicial vem capturada do Menu Certo (marketplace de food do grupo), resolvendo o cold start clássico de marketplace. (`projeto/referencias/referencias.md:45`)

**Meta de 6 meses:** piloto em Pádua com malha líquida (aceite <60s em horário comercial), lojas pagantes e "jaxegou?" virando verbo. (`projeto/regras-negocio/visao-geral.md:15`)

## Métrica norte

**Entregas FINALIZADAS por mês.** Metas: M1+3 meses → 600/mês em Pádua; M1+6 meses → 2.000/mês em 2–3 áreas. KPIs secundários: criação→aceite <60s mediano, >90% no SLA, conversão free→pago >15%, churn de loja <5%. (`projeto/regras-negocio/visao-geral.md:17-23`)

## Personas principais

Detalhes em `docs/personas/`:

1. **Loja (dono)** — assina plano, cria entregas, gere operadores e financeiro
2. **Loja (operador)** — cria/acompanha entregas; sem financeiro
3. **Entregador** — autônomo; online/offline, aceita ofertas, comprova, saca
4. **Admin de área** — sócio/gestor local; KYC, bairros, regras locais, disputas
5. **Admin plataforma** — equipe central; áreas, planos globais, auditoria (MFA obrigatório)
6. **Destinatário** — sem login; tracking público + notificações

## Modelo de receita

1. Assinatura mensal da loja via Safe2Pay (Free R$ 0/2 entregas → Sem Limite R$ 299) `[ASSUMIDO — valores]`
2. Taxa de plataforma por entrega — em TODA entrega, inclusive pagamento direto (acumula em fatura mensal)
3. Mensalidade opcional do entregador por área (desligada no M1) `[DECIDIR — valor]`
4. Revenue share do admin de área `[DECIDIR — % default, sugestão 20%]`

## Stack escolhida (travada — mudança exige ADR)

- **Backend:** Python 3.13 · FastAPI 0.115 · SQLAlchemy 2.x · Alembic · MySQL 8.0 (spatial) · Redis · arq · uv · ruff + basedpyright + pytest
- **Frontend:** Angular 19 standalone/signals · Ionic 8 · Capacitor (APK Android M1) · SCSS + CSS vars de tokens.json · 1 código, 3 superfícies
- **Infra:** VPS + Docker Compose · Nginx · GitHub Actions · Backblaze B2 + Cloudflare · Sentry + Prometheus
- **Orçamentos:** API p95 < 200 ms (endpoints quentes) · web LCP < 2.500 ms em 4G

Fonte: `projeto/stacks/stack.md` (íntegra). Detalhes de integração: `docs/integracoes/`.

## Restrições não-negociáveis (invariantes)

- **Multi-área shared-DB:** `area_id` em toda tabela de domínio; toda query filtrada por escopo; testes de isolamento com 2+ áreas em todo módulo (ADR-001, RN-001)
- **7 estados de entrega exatos** no M1 — novo estado exige ADR (RN-019)
- **Transições e ações administrativas append-only** com trigger negando UPDATE/DELETE (RN-012)
- **Endereço do destino revelado só após coleta** (RN-013)
- **Plataforma nunca fixa preço do frete** — entregador define tabela; área impõe piso (RN-015)
- **Pagamento direto é modalidade de 1ª classe** (ADR-012, RN-023/024)
- **Foto + GPS obrigatórios em toda comprovação** (ADR-008, RN-005)
- **LGPD by design:** PII nunca em log; anonimização 12 meses; exclusão→anonimização 30 dias (RN-021)
- **Timestamps UTC no banco**, conversão só na borda; cuidado com naive datetime (lição auditada)
- **pt-BR em toda UI**; código e schema em inglês; vocabulário canônico do glossário obrigatório em copy

## Fora de escopo do M1 (decidido — não re-discutir)

- iOS e publicação em lojas oficiais (M2) · OTP de comprovação (pós-M1) · score com consequência financeira (ADR-013, v1.1) · broadcast de despacho (RN-009, pós-M1) · mensalidade do entregador (desligada) · features de LLM (só infra `ai_usage_log` no M1) · cidades >500k hab · frota própria · marketplace de food

## Origem deste documento

Gerado por `gsd-project-ingestor` em 2026-06-10, lendo 47 arquivos em `projeto/`:
- 5 em regras-negocio/ (visão, 27 entidades, 8 fluxos F-01..F-08, 30 regras RN-001..RN-030, glossário)
- 1 em decisoes-existentes/ (ADR-001..013 + ADR-101..104 v1.1)
- 1 em stacks/ · 1 em docs-externos/ (9 integrações) · 2 em identidade-visual/ · 26 wireframes HTML · 1 em referencias/

Revisão humana: **pendente** (ver `DISCOVERY-REPORT.md` na raiz)
