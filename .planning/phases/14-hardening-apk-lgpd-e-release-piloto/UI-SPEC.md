# Phase 14: UI-SPEC — Hardening visual & auditoria pré-release (sem telas novas)

**Status:** Visual contract — Gate 2 (auditoria, não novas telas) · **Date:** 2026-06-11 (autopilot)
**Design system:** `docs/identidade-visual/tokens.json`. **Zero hex.** Dark mode (DEC-001).

## Natureza desta phase
Phase de **release/hardening**: **não introduz telas nem tokens novos**. A componente de UI é
**auditoria** da interface já entregue nas Phases 3–13 + empacotamento no APK. Gate 2 satisfeito por
contrato: nenhum token novo é citado; a verificação é de **conformidade** do que já existe.

## Escopo de UI (auditoria)
1. **Visual regression** (`product/visual-regression-testing`) das telas críticas já entregues
   (login, dashboard loja, nova entrega, tracking público, KYC, área operável, governança, tela 22):
   snapshots claro+escuro; diff bloqueia regressão.
2. **Acessibilidade** (`quality/accessibility-pro`): axe sem violações críticas nas telas-chave nos 2
   temas; foco, contraste AA, navegação por teclado, touch targets no APK.
3. **Web-design-audit** (`ui-ux-pro-max`): varredura anti-AI-slop / consistência de tokens — **zero
   hex hardcoded** em todo `apps/web/src` (gate de release).
4. **Performance visual** (`quality/performance-web-vitals`): LCP < 2500ms / INP < 200ms / CLS < 0.1 /
   bundle main < 400KB gzip (orçamento já em `config.json` + `lighthouserc.json`).
5. **APK**: as telas existentes empacotadas via Capacitor; checklist UAT humano de câmera/GPS/push em
   device real.

## Tokens
Nenhum token novo. A auditoria **verifica** que todo o `apps/web/src` consome apenas variáveis dos
tokens canônicos (`docs/identidade-visual/tokens.json`) — confirmado por `grep` de hex = 0.

## Critérios de aceite (UI)
- Visual regression verde (sem diffs não-intencionais) nos 2 temas.
- axe sem violações críticas nas telas-chave (claro+escuro).
- `grep -rn "#[0-9A-Fa-f]{3,6}"` em `apps/web/src` (fora de comentários/tokens gerados) = 0.
- Lighthouse dentro do orçamento; bundlesize ok.
- APK debug instala e renderiza as superfícies (checklist UAT humano para câmera/GPS/push).

---
*Gate 2: phase de auditoria — nenhum token novo citado; conformidade dos tokens existentes verificada.*
