# SUGGESTIONS

> Sugestões descobertas durante execução do framework. Append-only.
> Itens aqui são **observações**, não decisões. Promover uma sugestão = abrir ADR em `docs/adrs/`.

---

## Como funciona

Qualquer artefato do framework (execução, review, reconciliation, audit) que encontrar padrão ou melhoria que merece registro deixa uma entrada aqui. Ao fechar uma fase, as sugestões por-fase (`.planning/phases/<N>/SUGGESTIONS.md`) são copiadas para este arquivo global.

Cada entrada tem:
- **Origem** — que workflow/fase a descobriu
- **Severidade** — nice-to-have / should / must
- **Categoria** — skill / process / tech-debt / opportunity / architecture
- **Ação sugerida** — concreta, acionável

Quando uma sugestão é endereçada (skill criada, ADR aberta, tech-debt registrada), marcar com ✅ e data.

---

## Lista de sugestões

### 2026-XX-XX — {sumário da sugestão}

- **Origem:** {fase/workflow}
- **Severidade:** {nice-to-have | should | must}
- **Categoria:** {skill | process | tech-debt | opportunity | architecture}
- **Contexto:** {2-3 linhas explicando}
- **Ação sugerida:** {concreta}
- **Status:** 🟡 aberto | 🟢 endereçado | 🔴 rejeitado

---

## Exemplo preenchido

### 2026-04-22 — Criar skill `mobile/offline-first` a partir de padrões observados no chat

- **Origem:** Phase 05 (mobile chat), execução + audit
- **Severidade:** must
- **Categoria:** skill
- **Contexto:** Múltiplas features mobile implementaram fila de envio, cache otimista e banner de offline ad-hoc. O mesmo padrão apareceu em 3+ lugares. Não havia skill para guiar — cada dev implementou diferente.
- **Ação sugerida:** Criar `.claude/skills/mobile/offline-first/SKILL.md` cobrindo:
  - Queue com Capacitor Preferences
  - Sync ao reconectar (dedup, retry, ordem)
  - Cache de listagens + invalidação
  - UX: banner persistente vs. toast efêmero
  - Casos bloqueados offline (pagamento) com modal explicativo
- **Status:** 🟢 endereçado em 2026-05-02 — skill criada em `.claude/skills/mobile/offline-first/`

### 2026-04-22 — Serviço de integração já completo, artefatos diziam parcial

- **Origem:** `/gsd-reconcile-state 08`
- **Severidade:** should
- **Categoria:** process
- **Contexto:** `STATE.md` reportou feature incompleta por 3 semanas. Código estava 100% pronto (26 métodos no service, artefato dizia "4/26"). Ninguém percebeu porque SUMMARY.md é gerado por intenção, não por verificação.
- **Ação sugerida:** Reconcile automático após cada fase (já no framework como Gate 6). Monitorar métrica "divergências por reconcile".
- **Status:** 🟢 endereçado pelo próprio Gate 6

---

## Métricas deste arquivo

- Total de sugestões: {N}
- 🟡 Abertas: {N}
- 🟢 Endereçadas: {N}
- 🔴 Rejeitadas: {N}

Sugestões abertas há > 3 fases sem movimento: revisar em `/gsd-suggestions review`.
