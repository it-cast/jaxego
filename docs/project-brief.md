# PROJECT BRIEF — Jaxegô

> Fonte de verdade do projeto. Tudo o mais (PROJECT.md, ROADMAP.md) deriva deste arquivo.
> Populado por `gsd-project-ingestor` em 2026-06-10 a partir de `projeto/`. Mudanças aqui = considere abrir ADR em `docs/adrs/`.

---

## 1. Identidade

- **Nome:** Jaxegô (com acento; pronúncia "já-chegô")
- **Código interno/slug:** jaxego
- **Dono:** Grupo Itcast
- **Domínio prod:** jaxego.com.br (sem acento)
- **Locale primário:** pt-BR (UI); código e schema em inglês

## 2. Visão

Plataforma de entregas por **área** (cidade ou região) para o interior brasileiro (30k–200k habitantes), integrada nativamente ao Menu Certo. A loja assina um plano para acessar a malha de entregadores da sua área e paga cada corrida por cartão, PIX ou **direto ao entregador**. Pedido do Menu Certo vira entrega com 1 clique.

## 3. Problema

Estabelecimentos do interior não têm para quem ligar quando o motoboy próprio não dá conta (iFood fechado, Loggi/Lalamove ausentes ou caros, white-labels sem malha). Entregadores trabalham por WhatsApp, sem comprovação, score ou proteção. (`projeto/regras-negocio/visao-geral.md:5-9`)

## 4. Usuários-alvo

6 papéis: loja (dono/operador), entregador, admin de área (gestor local tipo franquia), admin plataforma, destinatário (sem login). Detalhes: `docs/personas/`.

## 5. Modelo de negócio

1. Assinatura mensal da loja (Free → Sem Limite R$ 299) `[ASSUMIDO — valores]`
2. Taxa de plataforma em TODA entrega (split no cartão/PIX; fatura mensal no pagamento direto)
3. Mensalidade opcional do entregador (desligada no M1) `[DECIDIR]`
4. Revenue share do admin de área `[DECIDIR — sugestão 20%]`

## 6. KPIs

**Norte:** entregas FINALIZADAS/mês (600/mês em Pádua em M1+3m; 2.000/mês em 2–3 áreas em M1+6m). Secundários: criação→aceite <60s, >90% no SLA, free→pago >15%, churn loja <5%, % pagamento direto (termômetro, sem meta).

## 7. Escopo do MVP (M1 = piloto Pádua)

Cadastros + KYC 2 níveis, despacho em cascata, execução com comprovação foto+GPS, tracking público, Safe2Pay (assinatura/split/fatura/saque), pagamento direto 1ª classe, API pública + Menu Certo, admins de área e plataforma, score explicável (sem consequência), APK Android direto.

## 8. Fora de escopo (decidido)

iOS e lojas oficiais (M2) · OTP de comprovação · score com consequência financeira · broadcast de despacho · mensalidade do entregador · features de LLM (só infra) · cidades >500k · frota própria · marketplace de food · transporte de passageiros · preço fixado pela plataforma.

## 9. Stack (travada — `specs/stack.yaml` + `projeto/stacks/stack.md`)

Python 3.13/FastAPI/SQLAlchemy 2/MySQL 8/Redis/arq/uv · Angular 19/Ionic 8/Capacitor · VPS+Docker+Nginx+GitHub Actions+B2+Cloudflare+Sentry+Prometheus. Orçamentos: API p95 <200ms, LCP <2,5s em 4G.

## 10. Referências

`projeto/referencias/referencias.md` — copiar: ML (tracking), Amazon (validação de foto), Uber Driver (ganhos), Stripe (densidade), Linear (hierarquia). Corrigir: iFood (score opaco, suspensão sem recurso), Rappi (neon), Lalamove (preço tabelado).
