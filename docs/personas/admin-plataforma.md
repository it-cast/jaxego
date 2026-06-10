# Persona — Admin plataforma

**Fonte:** `projeto/regras-negocio/visao-geral.md:29`, wireframes 23–25

Equipe Jaxegô central (Grupo Itcast). **MFA (TOTP) obrigatório** (ADR-005).

## O que pode fazer
Tudo: criar/arquivar áreas, gerir planos globais, ver todas as áreas (bypass de escopo com flag **auditada** — RN-001), auditar ações de admins de área, suspender qualquer conta, receber escalações (KYC 48h, SLA de recursos, divergência de conciliação > R$ 0,01).

## Momentos críticos
- Onboarding de área nova: criar área + configs + primeiro admin local — caminho que define a velocidade de expansão (meta: 2–3 áreas em M1+6 meses)
- Edição de planos/taxas: dados parametrizados (DRV-009); na v1.1, versionamento temporal (ADR-103)
