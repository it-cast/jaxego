# DISCOVERY-REPORT.md

**Gerado por:** gsd-project-ingestor
**Data:** 2026-06-10
**Inputs lidos:** 47 arquivos em `projeto/` (36 de conteúdo + 11 READMEs)

---

## O que foi extraído

### Regras de negócio: 30 (RN-001..RN-030) + 8 fluxos (F-01..F-08) + ~27 entidades
- **REQ-001 a REQ-056** gerados em `.planning/REQUIREMENTS.md` (49 must, 6 should, 1 could), todos com origem citada
- Todas as exceções de fluxo (E1–E6 por fluxo) viraram critérios de aceite obrigatórios

### Decisões existentes: 17
- ADR-001..ADR-013 (Accepted) + ADR-101..104 (v1.1, travadas) integradas em `.planning/DECISIONS.md`
- - 10 decisões derivadas (`derived`) detectadas e registradas (convenções de API/banco/frontend, fallbacks, parametrização de planos)

### Wireframes: 26 telas HTML (todas com DOM analisado)
- 4 superfícies: entregador (03–10, mobile 420px + tabbar), loja (02, 11–16), admin área (17–22), admin plataforma (23–25), tracking público (26)
- Estados explícitos detectados em TODAS as telas (`empty-state`, `error-state`, `loading skeleton`, `warn`) → REQ-055
- CSS dos wireframes **100% consistente com tokens.json** (#E84E1B, #FAF6EE, Inter Tight/JetBrains Mono) — nenhuma divergência de identidade
- Mapeados para phases no ROADMAP (cada phase de UI lista seus wireframe-contracts)

### Identidade visual
- `tokens.json` v2-jaxego completo (paletas, estados de entrega, níveis de score, tipografia, sombras warm, motion) — tratado como **canônico**, não sugestão
- `brand.md` com voz, regra do italic Fraunces, tom por contexto, formatos
- Consolidado em `design-system/MASTER.md` + copiado para `docs/identidade-visual/`

### Stack
- Travada por ADR-002/003/004: Python 3.13/FastAPI/SQLAlchemy 2/MySQL 8/Redis/arq/uv · Angular 19/Ionic 8/Capacitor · VPS+Docker+Nginx+GitHub Actions+B2+Cloudflare+Sentry+Prometheus
- Orçamentos: API p95 <200ms (endpoints quentes), LCP <2,5s em 4G — já alinhados com `.planning/config.json`

### Integrações externas: 9
- **CRÍTICAS:** Safe2Pay (com pendência [DECIDIR]) e Menu Certo. Suporte: Receita Federal, Zenvia/Twilio, AWS SES, Web Push, B2/Cloudflare, OSRM, LLMs (infra only)
- Documentadas em `docs/integracoes/` com comportamento em falha de cada uma

---

## O que foi assumido (e por quê) — 14 itens `[ASSUMIDO]` preservados dos docs

Cada um está implementável de forma parametrizada para troca barata após validação:

1. **Valores e limites dos planos** (Free R$0/2 → Sem Limite R$299) — proposta do gerador de docs; implementar como seeds editáveis (DRV-009)
2. **Taxa de plataforma por entrega** (R$ 2,00 → R$ 0,50 conforme plano) — idem
3. **Fatura mensal:** fecha dia 1º, vence dia 8, bloqueio >7 dias (RN-025) — padrão razoável de mercado
4. **Saque:** automático semanal às terças; manual mínimo R$ 20
5. **OSRM self-hosted** para rotas, Google como fallback pago
6. **SMS apenas no "a caminho"** (RN-018) — economia de quota
7. **Reversão automática de suspensão** no estouro do SLA de recurso (RN-016)
8. **Bloqueio da modalidade direta por 90 dias** após 2 disputas procedentes/30d (RN-027)
9. **APK Android direto no M1**; lojas oficiais no M2
10. **"Aceitou e sumiu":** 2× ETA sem chegada → loja cancela sem custo (F-05 E2)
11. **Destinatário ausente:** 10 min de espera → retorno com cobrança (F-06 E2)
12. **Pagamento falha na criação:** entrega não nasce + opção de trocar para direto (F-03 E3)
13. **Mudança de plano:** upgrade pro-rata imediato, downgrade no próximo ciclo (RN-029)
14. **Estimativa de frete = mediana** das tabelas elegíveis; teto +10% re-confirma (RN-030); Receita via minhareceita.org primário

---

## Open Questions (precisam de você) — os `[DECIDIR]`

### OQ-1 · Percentual default de revenue share do admin de área **[crítica para modelo de expansão]**
- **Contexto:** modelo tipo franquia, % das taxas de plataforma da área, configurável por área (`visao-geral.md:74`)
- **Onde impacta:** REQ-047, split do Safe2Pay (Phase 10), tela 24/relatórios financeiros (Phase 13)
- **Default sugerido se não responder:** 20% (sugestão dos próprios docs), implementado como configuração com default global

### OQ-2 · Valor da mensalidade opcional do entregador **[não bloqueia o M1]**
- **Contexto:** receita 3 do modelo; desligada por padrão no M1 (`visao-geral.md:75`)
- **Onde impacta:** apenas schema/toggle por área (TD-012)
- **Default se não responder:** feature permanece desligada e sem valor; decidir quando uma área quiser ativar

### OQ-3 · Contrato Safe2Pay: split disponível? prazo de repasse de subconta? taxas? **[BLOQUEANTE para a Phase 10]**
- **Contexto:** ADR-009 v2 (`adrs.md:53`) e `integracoes.md:36` exigem validar na conta contratada: (a) split/marketplace disponível no plano, (b) prazo de repasse da subconta, (c) taxa por transação — **ajustar o escrow interno de 24h se o provedor já retiver** (ver SUG-005)
- **Onde impacta:** REQ-034/036/038, Phases 10–11 inteiras
- **Default se não responder:** NÃO há default seguro — Phases 1–9 prosseguem normalmente, mas a Phase 10 **não deve iniciar** sem essa resposta

---

## Conflitos e gaps detectados

1. **Tracking (tela 26) × ADR-101:** o wireframe mostra mapa "posição aproximada — atualiza a cada minuto", mas GPS polling é decisão travada para **v1.1** (ADR-101). **Resolução aplicada:** M1 entrega timeline + estado sem mapa em tempo real (DRV-010, TD-005). Confirme se concorda.
2. **`[GAP]` Logo:** não há arquivo de logo em `identidade-visual/` — só assinatura tipográfica. Marca é 100% tipográfica?
3. **`[GAP]` Dark mode:** tokens e wireframes são light-only. M1 suporta dark mode? (afeta skill obrigatória da matriz UI)
4. **OTP na UI (tela 12):** selecionável porém desabilitado com badge "em breve" — coerente com ADR-008 (pós-M1); registrado como TD-003, sem conflito.
5. **Sem conflitos entre RNs detectados.** RN-010 × RN-024 (MEI) se resolvem explicitamente (direto permitido sem MEI). RN-019 (7 estados) cobre todos os fluxos mapeados.

---

## Próximos passos

1. Revise `.planning/REQUIREMENTS.md` (56 REQs) e `.planning/ROADMAP.md` (14 phases) — primeiro ponto de falha de alinhamento
2. Responda as 3 Open Questions acima (OQ-3 antes da Phase 10; OQ-1 idealmente antes da Phase 10 também)
3. Valide (ou ajuste) os 14 `[ASSUMIDO]` — em especial valores de planos/taxas
4. Execute:
   - `/gsd:discuss-phase 1` — começar com revisão humana por phase, ou
   - `/gsd:autopilot MS-01` — executar o milestone Foundation end-to-end

---

## Estatísticas

- Arquivos lidos: 47 (5 regras-negocio, 1 adrs, 1 stack, 1 integracoes, 2 identidade-visual, 26 wireframes, 1 referencias, 11 READMEs estruturais)
- REQs gerados: **56** (49 must / 6 should / 1 could)
- ADRs integradas: **17** (13 Accepted + 4 v1.1) + 10 derived
- Phases planejadas: **14** · Milestones: **5** (compõem o release v1.0 piloto Pádua)
- Tech debts pré-registradas: **13** (todas com urgency_class)
- Open Questions: **3** (1 bloqueante de phase — OQ-3) · Suposições registradas: **14** · Conflitos: **1** (resolvido com DRV-010, aguarda confirmação) · Gaps: **2**
