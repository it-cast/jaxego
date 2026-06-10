# Persona — Entregador

**Fonte:** `projeto/regras-negocio/visao-geral.md:9,33`, F-02/F-05/F-06/F-07, `referencias.md:23` (correções ao iFood)

Autônomo do interior, "motoboy com capacete na mão" (mas a UI NUNCA diz motoboy — glossário). Hoje trabalha por WhatsApp: sem comprovação, sem score, sem proteção, recebendo "quando der". Muitos **não têm MEI** — e podem começar mesmo assim (RN-024, só pagamento direto).

## O que pode fazer
Online/offline, aceitar/recusar ofertas, executar e comprovar entregas, ver extrato, sacar (se MEI ativo), configurar cobertura (bairros) e a PRÓPRIA tabela de preços (RN-015 — a plataforma nunca fixa preço, só piso).

## Proteções desenhadas para ele (diferenciais vs. iFood/Uber)
- Score **explicável**: componentes, pesos, delta e causa — nunca opaco (ADR-013)
- Suspensão sempre com motivo verificável + recurso com SLA 5 dias úteis; estouro do SLA reverte a suspensão automaticamente (RN-016)
- Loja com 2+ disputas procedentes de pagamento direto perde a modalidade (RN-027) — proteção contra calote
- Bloqueio por loja é privado e não afeta o score (RN-014)

## Momentos críticos de UX
- Oferta com cronômetro (default 20s): decisão em segundos, no sol, com luva — botões grandes, valor da corrida em destaque (tela 05)
- Endereço do destino só após coleta (RN-013) — a UI explica o porquê
- Comprovação: GPS validado na hora com motivo acionável ("aproxime-se do endereço") (RN-005/017)
- Confirmação de pagamento direto na conclusão: "Recebi R$ X em dinheiro/PIX" / "Não recebi" → disputa (RN-026)

## Dispositivo
Android de entrada, rede 4G instável → APK direto (M1), upload offline-tolerante de fotos, app leve.
