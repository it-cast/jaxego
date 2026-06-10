# MILESTONES — Jaxegô

> Gerado por `gsd-project-ingestor` em 2026-06-10. Os 5 milestones abaixo compõem o **release v1.0 = "M1 piloto Pádua"** dos documentos de origem. Fora do M1 (decidido): iOS/lojas oficiais, OTP, score com consequência, broadcast, mensalidade do entregador, features de LLM.

| ID | Nome | Critério de Done | Phases | Release alvo | Status |
|----|------|------------------|--------|--------------|--------|
| MS-01 | Foundation | API skeleton + multi-área + auth + shell Angular/Ionic com design system de tokens.json; `docker compose up` + CI verdes; testes de isolamento 2 áreas passando | 1–3 | T+3 semanas | not_started |
| MS-02 | Cadastros & malha | Loja cadastra e ativa (Free, Receita validada); entregador completa wizard KYC 2 níveis; admin de área aprova item a item; cobertura + tabela de frete + catálogo de bairros operacionais | 4–6 | T+7 semanas | not_started |
| MS-03 | Core de entregas | Entrega manual (pagamento direto) nasce, despacha em cascata, é aceita, coletada, comprovada com foto+GPS e finalizada; tracking público no ar; notificações nos 3 momentos | 7–9 | T+12 semanas | not_started |
| MS-04 | Financeiro & integrações | Cartão/PIX com split Safe2Pay + escrow 24h + estornos; fatura mensal com bloqueio; saques; disputas; `POST /v1/deliveries` + webhooks HMAC prontos para o Menu Certo | 10–12 | T+17 semanas | not_started |
| MS-05 | Operação & release piloto | Admin plataforma completo; score explicável; suspensão/recurso com reversão automática; APK Android distribuível; jobs LGPD; conciliação; auditoria pré-release verde | 13–14 | T+20 semanas | not_started |

## Mapeamento REQs → Milestones

- **MS-01:** REQ-001, 002, 004, 005, 007, 050 (base), 052, 056 (design system base)
- **MS-02:** REQ-003, 006, 008, 009 (seeds), 013, 014, 015, 016, 017, 018, 019 (parcial — subconta fica no MS-04), 044 (KYC/config/bairros)
- **MS-03:** REQ-021 (modo direto), 022, 023, 024, 025, 026, 027, 028, 029, 030, 031, 032, 049, 055
- **MS-04:** REQ-010, 011, 012*, 034, 035, 036, 037, 038, 039, 040, 041, 042, 043, 047
- **MS-05:** REQ-020, 033, 045, 046, 048, 051, 053, 054 (refino)

\* REQ-012 (favoritos/bloqueados) é pré-requisito da cascata de favoritos — a parte de dados entra no MS-03 (Phase 8); a UI completa (tela 15) no MS-04.

## Dependências entre milestones

- MS-02 depende de MS-01 (auth, multi-área, shell)
- MS-03 depende de MS-02 (malha de entregadores ativa para despachar)
- MS-04 depende de MS-03 (entrega funcional antes de cobrar por ela) — **bloqueado por Open Question OQ-3 (contrato Safe2Pay) na Phase 10**
- MS-05 depende de MS-04 (release exige financeiro fechado)

## Riscos por milestone

- **MS-02:** dependência da API Receita Federal (mitigada: `pending_validation` + retry — F-01 E4)
- **MS-03:** concorrência no aceite (lock Redis/transacional — ADR-007); EXIF/GPS em fotos de devices variados
- **MS-04:** `[DECIDIR]` split/escrow no contrato Safe2Pay — **resolver antes da Phase 10**
- **MS-05:** distribuição direta de APK (instalação de fonte desconhecida) — fricção de onboarding do entregador
