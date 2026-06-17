# Telemetria do framework — interpretação humana (os `<FILL>` preenchidos)

> `FRAMEWORK-TELEMETRY.md` coleta números, mas deixa em branco os campos
> `interpretacao_humana` — que são o que "fecha o gap de field data" (palavras do
> próprio arquivo). Aqui estão preenchidos com base no caso Jaxegô v1.0.
> Estes são respostas reais, não placeholders.

```yaml
interpretacao_humana:

  gate8_vale_a_pena:
    veredito: "PARCIAL — citado em 31 planos, fail_block=0. Não bloqueou nada que
      tenha ido a produção, mas TAMBÉM não pegou o que importava: login-loop,
      componentes órfãos, endpoints sem UI. O Gate 8 mede qualidade de código
      (segredo, N+1, injection) e nesse escopo passou limpo. O buraco do v1.0 foi
      INTEGRAÇÃO DE PRODUTO, que nenhum gate cobre. Conclusão: Gate 8 é necessário
      mas insuficiente; falta um Gate 9 de alcançabilidade."

  paralelismo_compensou:
    veredito: "N/A — wave_dispatcher rodou 0 execuções paralelas no projeto inteiro
      (execucoes_paralelas=0). parallel-orchestration citada em 0 planos. O recurso
      existe mas não foi exercitado; sem dado para validar se compensa."

  go_reduziu_friccao:
    veredito: "SIM, parcialmente — /gsd:go teve 5 referências de uso. Reduziu a
      fricção de 'qual comando agora?'. MAS o autopilot por trás dele rodou 14 phases
      sem checkpoint de UAT humano, e foi exatamente essa autonomia sem freio que
      deixou a dívida de integração crescer invisível. Menos fricção de comando ≠
      melhor resultado de produto."

  skills_novas_uteis:
    veredito: "MISTO. data-tables-ux (citada 10×) só mudou código de fato na
      RECONSTRUÇÃO manual (jx-data-table, commit a4de718), não no autopilot — citação
      ≠ aplicação confirmada. fastapi-production-patterns (31×) guiou estrutura de
      endpoint real. github-actions-ci (3×) produziu CI, mas não impediu o deploy
      não-gated nem a falta de paridade local. A skill que FALTOU e teria tido o maior
      impacto: uma 'ci-parity / rodar o pipeline real antes do push'."

  # Campo novo proposto (não existe no schema atual, mas é o achado central):
  metricas_cegas:
    veredito: "As métricas que o framework coleta (fix-rate 5,3%, plan-revisions
      baixas, gates verdes) ficaram TODAS no verde enquanto o produto não navegava.
      O painel de saúde é insensível à dívida de integração. Adicionar: endpoints sem
      UI, componentes órfãos, páginas-stub, fluxos E2E fechados, UAT pendente×backlog."

  ci_real_vs_gate7:
    veredito: "O Gate 7 ('tests + lint verde') é genérico e NÃO conhece o CI real do
      repo. 9 falhas (ruff format, karma, zero-hex, deploy-order, DATABASE_URL) só
      apareceram pós-push. Maior aprendizado operacional do projeto: o GSD precisa
      detectar e rodar os jobs de .github/workflows como parte do 'pronto'."
```

## Snapshot de campo correspondente (para anexar ao FRAMEWORK-TELEMETRY)

```yaml
# Snapshot 2026-06-17 — pós-auditoria + reconstrução (field data REAL)
produto_integrado:
  phases_verdes: 14
  fluxos_e2e_fechados_no_autopilot: 0      # login→superfície→ação
  endpoints_crud_sem_ui: 3                  # areas, kyc-queue, admin-lists
  componentes_orfaos: 2                     # offer-sheet, queue-table
  paginas_stub_contadas_como_tela: 4
  uat_pendente_no_state: "dezenas"
  uat_no_backlog: 0

ci_paridade:
  jobs_no_repo_conhecidos_pelo_gsd: 0       # GSD não lê .github/workflows
  round_trips_push_vermelho_fix: 9
  fixes_ci_deploy: 8                        # 4 deploy + 3 ci + 1 style

veredito_geral: "Disciplina de planejamento/rastro: forte. Garantia de produto
  integrado e paridade de pipeline: ausente. As 2 correções de maior ROI são
  CI-real-local (B1/B2) e Gate-9-alcançabilidade + UAT-por-milestone."
```
