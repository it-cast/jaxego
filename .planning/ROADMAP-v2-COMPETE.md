# Roadmap v2 — capacidades para competir (classe-Loggi)

> **Status: PLANO. Nada executado.** Documento para dimensionar o salto de
> "MVP de piloto regional" → "plataforma de last-mile competitiva".
> Origem: benchmark de plataformas last-mile (Loggi/LogiNext/Track-POD) + gaps
> da auditoria (`docs/AUDITORIA-FRONTEND-v1.md`) e da revisão de fidelidade.
>
> **Pré-requisito de qualquer go-live:** MR-6 (Safe2Pay + validação ao vivo) —
> já planejada em `RECONSTRUCTION-MILESTONES.md`. v2 assume MR-6 fechada.
>
> Legenda esforço: **P** (≈dias) · **M** (≈1-2 semanas) · **G** (≈3-6 semanas) · **GG** (mês+).
> Cada milestone marca o que exige **decisão de produto**, **segredo/conta** ou **infra**.

---

## Onde estamos (baseline v1.1)

Pronto em dev/test: 4 superfícies navegáveis, loop de entrega completo, mapa no
entregador (OSM) e no rastreio, despacho em cascata (favoritos→ranking), pagamento
direto. **Não tem:** tempo-real, navegação turn-by-turn, otimização de rota, tiles
comerciais, app nativo publicado, escala horizontal. É um **piloto regional**, não
uma plataforma de last-mile em escala.

---

## MR-7 — Mapa comercial + navegação do entregador  · **M**

Fecha o "mapa de verdade" do app do motorista.

- **F7.1** — Provider de tiles comercial (MapTiler/Mapbox/self-host) ligado via
  `core/map/map-tiles.ts` (já é ponto único). _Requer: **segredo** (token) + decisão de provider._
- **F7.2** — Mapa da entrega ativa com **rota desenhada** coleta→destino (linha +
  pinos A/B), não só o pino central atual.
- **F7.3** — **Navegação turn-by-turn por handoff**: botão "Navegar" abre
  Google Maps/Waze com o destino (deep link) — padrão de mercado para apps de
  entregador, sem reescrever um motor de navegação.
- **Decisões:** provider de mapa; usar handoff (barato) vs navegação embarcada (caro).
- **Depende de:** nada além do token. **Risco:** baixo.

## MR-8 — Rastreamento em tempo real  · **G**

O "real-time tracking" que o benchmark cita como núcleo.

- **F8.1** — **Background geolocation nativo** (Capacitor BackgroundGeolocation):
  posição mesmo com app em 2º plano (hoje pausa — TD-020). _Requer: permissão
  "sempre" + UX de bateria + plugin nativo._
- **F8.2** — Transporte **tempo-real** (WebSocket/SSE) backend↔clientes em vez de
  polling 60-120s; posição do entregador empurrada para loja + rastreio público.
- **F8.3** — Retenção/PII da posição ao vivo (já há `delivery_locations` 24h) +
  throttle/precisão.
- **Decisões:** WebSocket vs SSE; janela de rastreio; consumo de bateria aceitável.
- **Depende de:** infra (servidor WS), MR-6. **Risco:** médio-alto (nativo + infra).

## MR-9 — Despacho inteligente / otimização de rota  · **GG**

O diferencial logístico da Loggi (matching + roteirização).

- **F9.1** — **Matching multi-fator** (distância, score, capacidade, histórico)
  além da cascata favoritos→ranking atual (RN-009 hoje é opt-in pós-M1 → exige **ADR**).
- **F9.2** — **Roteirização multi-parada** (VRP): agrupar entregas, ordem ótima,
  ETA por OSRM/serviço de rotas (o `EtaResolver` já existe como gancho — TD-14-02).
- **F9.3** — **Broadcast/leilão** de oferta opcional por área (hoje só cascata — TD-011).
- **Decisões:** algoritmo (heurística própria vs serviço de VRP); quando otimizar.
- **Depende de:** dados de volume reais (calibrar). **Risco:** alto (algoritmo + produto).

## MR-10 — App nativo publicado (Android + iOS)  · **G**

Hoje: APK debug, sem assinatura, iOS fora (ADR-003/TD-06/TD-14-04).

- **F10.1** — **Keystore + assinatura** Android no CI; build release. _Requer: **segredo** (keystore)._
- **F10.2** — **Publicação Play Store** (ficha, política, app record). _Requer: **conta** Play Console._
- **F10.3** — **iOS** (Xcode build, TestFlight, App Store). _Requer: **conta** Apple Developer + Mac CI._
- **F10.4** — **Push real** (VAPID já existe no backend; falta exercer em device + APNs/FCM).
- **Decisões:** distribuir fora da loja vs lojas oficiais; iOS no escopo?
- **Depende de:** contas + segredos. **Risco:** baixo técnico, alto burocrático (revisão das lojas).

## MR-11 — Escala & confiabilidade  · **G**

Tirar os limites conscientes do M1 (TD-001, TD-12-02, TD-13-02).

- **F11.1** — Rate-limit + cache de API key em **Redis** (hoje in-process — TD-12-02).
- **F11.2** — Estratégia de **particionamento/sharding** quando passar de ~50 áreas (TD-001 → ADR).
- **F11.3** — Sinais de score **reais** (aceite via `dispatch_offers`, pontualidade real — TD-13-02).
- **F11.4** — Backups/PITR validados (B2 dump+binlog — já desenhado na skill de deploy).
- **Decisões:** quando sharding; nível de RPO. **Depende de:** MR-6 + volume. **Risco:** médio.

## MR-12 — Observabilidade, SLA & growth  · **M**

O que diferencia operação madura.

- **F12.1** — Dashboards operacionais reais (tempo até aceite, taxa de conclusão,
  fila por área) — hoje os KPIs vêm de queries simples.
- **F12.2** — **Alertas/SLO** (Sentry já desenhado; falta SLO + on-call).
- **F12.3** — Analytics de produto (funil de cadastro, retenção de entregador/loja).
- **F12.4** — Lighthouse/p95 reais anexados (TD-14-03).
- **Risco:** baixo. **Depende de:** infra de observabilidade.

---

## Sequência recomendada e dependências

```
MR-6 (gate de produção: Safe2Pay + ao vivo)  ← OBRIGATÓRIO antes de qualquer v2
  │
  ├─ MR-7 (mapa comercial + navegação)   ← rápido, alto impacto percebido
  ├─ MR-10 (app nativo publicado)        ← burocrático, começar cedo (revisão das lojas)
  │
  ├─ MR-8 (tempo-real)                   ← núcleo competitivo
  │     └─ habilita MR-9 (otimização usa posição real)
  ├─ MR-11 (escala)                      ← quando o volume exigir
  └─ MR-12 (observabilidade/SLA)         ← contínuo
```

## Resumo de esforço e bloqueios

| Milestone | Esforço | Bloqueio principal |
|---|---|---|
| MR-7 mapa+navegação | M | token de provider (segredo) |
| MR-8 tempo-real | G | plugin nativo + infra WS |
| MR-9 otimização de rota | GG | ADR (supera RN-009) + dados reais |
| MR-10 app nativo publicado | G | keystore + contas de loja |
| MR-11 escala | G | decisão de sharding + volume |
| MR-12 observabilidade | M | infra de monitoring |

**Leitura honesta:** chegar a "competir com a Loggi" é **~3-5 meses** de trabalho
focado além do MVP atual, e depende de **decisões de produto** (otimização de rota,
escopo iOS), **segredos/contas** (mapa, lojas) e **infra** (WS, monitoring). O MVP
de piloto regional **não precisa** disso para entrar em Pádua — precisa só do MR-6.

## Decisões que destravam o planejamento (suas)

1. Provider de mapa (MapTiler/Mapbox/self-host)?
2. Escopo iOS além de Android?
3. Otimização de rota é prioridade de v2 ou fica para v3 (depende de volume)?
4. Tempo-real: WebSocket próprio vs serviço gerenciado?
