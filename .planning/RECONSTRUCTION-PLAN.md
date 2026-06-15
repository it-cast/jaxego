# Plano de Reconstrução — Jaxegô (produto pronto, fiel ao protótipo)

> Origem: auditoria `docs/AUDITORIA-FRONTEND-v1.md` + postmortem `feedback/`.
> Objetivo: levar o produto de "passa nos gates / não navega" para
> **navegável e funcional de ponta a ponta**, fiel ao `prototipo.html`,
> com o app do entregador **separado** (4 apps + lib compartilhada).
>
> Decisões já tomadas pelo dono:
> - Estrutura: **4 apps + `packages/shared`** (api, admin [área+plataforma], loja, entregador mobile).
> - Identidade visual: o `prototipo.html` é **contrato de wireframe**; tokens em
>   `docs/identidade-visual/tokens.json` (já idênticos à paleta do protótipo).

---

## Princípios inegociáveis (eat-our-own-dogfood do feedback ao GSD)

1. **Toda tela = funcionalidade real ligada a endpoint que já existe.** Nada de
   stub `<jx-empty-state>` onde o protótipo especifica conteúdo. (M2 do feedback)
2. **Toda rota é alcançável e todo endpoint de CRUD tem UI.** (M1 do feedback)
3. **Fidelidade ao protótipo:** cada tela referencia seu `tpl-*` e replica
   layout/copy/estados. Tokens only — zero hex (Gate 2 do framework).
4. **Definição de "pronto":** o fluxo fecha (clico e chego ao fim) **e** foi
   exercido contra backend real, não só teste de existência.
5. **Sem forward-reference solta:** nada de "wired in T-XX". Se adiar, vira task
   ou TD com `urgency_class`. (M3 do feedback)

---

## Pré-requisito visual (barato, antes de tudo)

- ✅ `tokens.json` já bate com o protótipo (brand-500 `#E84E1B`, cream/carvão,
  Inter Tight + Fraunces italic + JetBrains Mono, `--gold` = score ouro).
- **Mapear** os tokens auxiliares do protótipo que ainda não têm nome no design
  system: `--direct` (`#FFF8C2`) e `--direct-ink` (`#8B5A05`) — o amarelo de
  "pagamento direto". Adicionar como `color.payment.direct/direct_ink` no
  `tokens.json` e usar nos badges DIRETO. (Hoje provavelmente hex solto ou
  aproximado.)

---

## Estrutura-alvo (Fase R0)

```
jaxego/
  apps/
    api/          FastAPI (já existe; mover de apps/api — já está lá)
    admin/        Angular web — admin da ÁREA + admin da PLATAFORMA
    loja/         Angular web — lojista
    entregador/   Ionic + Capacitor — app mobile do entregador
  packages/
    shared/       design system (jx-*), models, http client, auth, tokens
```

---

## Fases

### R0 — Fundação: separação + navegação (DESTRAVA TUDO)

> Por que primeiro: a maior parte do trabalho restante é **tela nova**;
> construí-la já na casa certa evita retrabalho de mover. O move do código
> existente é mecânico e validado por build.

- **T-R0.1 — ADR-001 (separação de apps).** Escrever em `docs/adrs/ADR-001-separacao-apps.md`
  a decisão 4-apps + shared, com trade-offs (supera a recomendação monolítica anterior).
- **T-R0.2 — `packages/shared`.** Extrair: design system (`jx-*` de `shared/components`),
  `models`, http client (`core/http`), auth (`core/auth`), theme, tokens.
- **T-R0.3 — Split físico.** Mover `features/entregador` → `apps/entregador`;
  `features/{admin,admin-plataforma}` → `apps/admin`; `features/loja` + cadastros públicos → `apps/loja`.
  Cada app importa de `packages/shared`. `public-tracking` vai para `apps/loja` (web público) ou app próprio mínimo — decidir no ADR.
- **T-R0.4 — 🔴 Roteamento pós-login por papel.** Após `auth.login` ok, resolver
  o tipo de usuário (claim/endpoint `me`) e redirecionar: entregador→app entregador,
  lojista→`/loja`, admin de área→`/admin`, admin plataforma→`/plataforma`.
  Substitui o `navigate(['/'])` que faz loop (`login.page.ts:87`).
- **Aceite R0:** logo com cada papel e caio na superfície certa; os 4 apps buildam
  isolados consumindo `packages/shared`. ADR-001 existe.

---

### R1 — App do entregador (núcleo do produto) · telas `tpl-c-*`

A superfície mais incompleta. Backend pronto: `dispatch /active /accept /decline`,
`deliveries`, `proofs/*`, `withdrawals/*`, `scores`, `couriers/availability`.

- **T-R1.1 — Home (`tpl-c-home`).** Reescrever `inicio.page` com dados reais:
  - toggle online/offline → `PATCH couriers/{id}/availability`.
  - card "ganhos hoje" + "saldo p/ saque" → `GET withdrawals/balance`.
  - card score + selo (bronze/prata/ouro/diamante via `score_level` tokens) → `GET scores/{id}/score`.
  - "entregas recentes" → `GET deliveries` (do entregador).
  - **offer overlay** (sheet que sobe) → monta `offer-sheet.component` ao chegar oferta de `GET dispatch/active`; timer 20s (`offer-timer.component`); aceitar → `POST dispatch/{id}/accept`; recusar → `POST decline`.
- **T-R1.2 — Entrega ativa (`tpl-c-active`).** **Criar a página que falta** em
  `entrega-ativa/`: máquina de estados (ACEITA→NA COLETA→COLETADA→…), botão de avanço,
  mapa (jx-live-map lazy), timeline, ligar/mensagem. Lê/avança via `deliveries/{id}`.
  Liga o `location-polling.service` já existente.
- **T-R1.3 — Comprovação (`tpl-c-proof`).** Reusar `comprovacao.page` (já real) e
  **fiá-la no fluxo** vindo da entrega ativa; confirmar pagamento direto →
  `POST payments_direct/{id}/payment-confirmation`; foto+GPS → `proofs/*`.
- **T-R1.4 — Concluída (`tpl-c-done`).** Tela de sucesso com resumo (recebido,
  taxa, +score) + CTA voltar/nova oferta.
- **T-R1.5 — Perfil (`tpl-c-profile`).** Reescrever `perfil.page`: breakdown de
  score (barras por critério), documentos (status KYC), chave PIX (salvar).
- **T-R1.6 — Ganhos/Extrato (`tpl-c-earnings`).** Consolidar: `saldo.page` (já real)
  vira a tela de ganhos; **remover o stub `ganhos.page`** e apontar a tab para saldo;
  movimentações via `withdrawals/extract`, sacar via `POST withdrawals`.
- **T-R1.7 — Lista de entregas.** Substituir stub `entregas.page` por lista real
  (`GET deliveries` do entregador, jx-data-table compartilhado).
- **Aceite R1:** loop completo funciona contra backend — fico online → recebo oferta
  → aceito → entrega ativa avança estados → comprovo com foto/GPS → confirmo pgto →
  tela de concluída → score atualiza. Home/perfil/ganhos com dado real. Zero stub.

---

### R2 — Admin da área · telas `tpl-a-*`

Backend: `platform_admin/couriers|merchants|disputes|suspensions`, `invoices`,
admin KYC (`couriers/admin`), `proofs/manual-release`.

- **T-R2.1 — Dashboard (`tpl-a-dash`).** Substituir o stub `admin/inicio` pelo
  painel de "Filas que precisam de você" com contadores reais e clicáveis:
  validações KYC pendentes, disputas de pgto direto, comprovações low-confidence,
  recursos de suspensão, lojas com fatura vencida. KPIs do topo (entregas hoje,
  online agora, mediana aceite, taxas).
- **T-R2.2 — 🔴 Fila de KYC.** Criar rota+página de **fila** (usa o
  `queue-table.component` órfão) → linka para o detalhe (`kyc/:courierId`, já real).
- **T-R2.3 — Lista de entregadores.** Página de listagem → detalhe
  (`entregadores/:courierId`, já real). Hoje não há como chegar nele.
- **T-R2.4 — Lista de lojas.** Listagem das lojas da área.
- **Aceite R2:** admin vê as filas no painel, clica, chega no item, age
  (aprovar/reprovar KYC, ativar entregador, resolver disputa). Tudo navegável.

---

### R3 — Admin da plataforma (super-admin) · "adicionar área"

Backend: `areas` (POST/PATCH/archive — **CRUD completo já existe, sem UI**),
`platform_admin/areas/{id}/revenue-share`, `platform_admin/overview|disputes`.

- **T-R3.1 — 🔴 Criar/editar/arquivar área.** A tela que **não existe**. Form de
  criação (nome, slug, locale, nível de validação default) → `POST areas`; edição
  → `PATCH`; arquivar → `POST archive`. Lista de áreas com status.
- **T-R3.2 — Revenue-share por área.** UI para `PUT areas/{id}/revenue-share`
  (TD-13-01 — valor é decisão do dono).
- **T-R3.3 — Designar admin de área.** Em `pessoas`, vincular um usuário como
  `area_admin` de uma área (fecha o fluxo "criei área → quem opera").
- **Aceite R3:** crio uma área nova (ex.: "Itaperuna"), designo um admin, defino
  revenue-share — tudo pela UI, auditado.

---

### R4 — Loja: fechar lacunas finais · telas `tpl-m-*`

Loja é a superfície mais completa; só refinos:

- **T-R4.1 — "Procurando entregador" (`tpl-m-searching`).** Tela/estado pós-criação
  com polling do status até aceite; já há detalhe (`tpl-m-detail`).
- **T-R4.2 — Conferir dashboard (`tpl-m-dash`)** com dados reais (KPIs + "em curso").
- **Aceite R4:** loja cria entrega → vê "procurando" → vê aceite → acompanha no detalhe.

---

### R5 — Validação ao vivo + blockers de release (fecha o que o autopilot pulou)

- **T-R5.1 — Popular e rodar `HUMAN-UAT-BACKLOG.md`** com os "pendente ao vivo" do
  STATE: migrations reversíveis, triggers append-only (errno 1644), geofence
  `ST_Distance_Sphere`, concorrência `FOR UPDATE`, integration B2 (`pytest -m mysql`).
- **T-R5.2 — Resolver `pre_launch_blocker` Safe2Pay** (TD-10-01/03, TD-15-01):
  confirmar contrato (split, HMAC webhook, endpoint de repasse) → ADR que supera
  DEC-003 → ajustar `safe2pay_adapter.py`.
- **T-R5.3 — Lighthouse + p95 reais** (TD-14-03) num PR/tag.
- **T-R5.4 — APK release assinado** + UAT device real (câmera/GPS/push) (TD-14-04).
- **Aceite R5:** UAT humano por superfície verde; blockers resolvidos; deploy go.

---

## Sequência e dependências

```
R0 (separação + navegação)   ← destrava tudo
   ├── R1 (entregador)        ┐
   ├── R2 (admin área)        ├── paralelizáveis após R0
   ├── R3 (admin plataforma)  ┘
   └── R4 (loja, refino)
R5 (ao vivo + blockers)       ← depois que os fluxos existem
```

## Definição de pronto do produto (gate final)

- [ ] Login leva cada papel à sua superfície (R0).
- [ ] Loop do entregador fecha contra backend real (R1).
- [ ] Admin opera filas e KYC ponta a ponta (R2).
- [ ] Criar área + designar admin pela UI (R3).
- [ ] Loja: criar → procurar → acompanhar (R4).
- [ ] `HUMAN-UAT-BACKLOG` zerado; blockers Safe2Pay resolvidos (R5).
- [ ] Zero página stub onde o protótipo especifica conteúdo.
- [ ] Todo endpoint de CRUD tem UI; nenhum componente órfão.
- [ ] Fidelidade visual ao `prototipo.html`; zero hex.

## Como executar (recomendação)

Rodar **fase a fase com UAT humano ao fim de cada uma** (não autopilot puro — é
exatamente o que causou o estado atual; ver `feedback/POSTMORTEM-jaxego-v1.md`).
Cada fase fecha com `reconcile` + checagem de alcançabilidade (endpoint↔UI,
componente↔página) antes de seguir.
