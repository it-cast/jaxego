# docs/integracoes/ — INDEX

> Gerado por `gsd-project-ingestor` em 2026-06-10. Fonte original: `projeto/docs-externos/integracoes.md` (canônico — sempre conferir lá em caso de dúvida).

| Arquivo | Integração | Criticidade | Relevância |
|---|---|---|---|
| `safe2pay.md` | Safe2Pay (PSP: assinaturas, split, fatura, saque) | **CRÍTICA** — pendência [DECIDIR] OQ-3 | canônico |
| `menu-certo.md` | Menu Certo (primeiro cliente da API) | **CRÍTICA** | canônico |
| `servicos-suporte.md` | Receita Federal, SMS (Zenvia/Twilio), AWS SES, Web Push, B2/Cloudflare, OSRM, LLMs | alta | canônico |

## Regra transversal de resiliência

Nenhuma integração externa pode bloquear o fluxo operacional de entrega: Receita fora → `pending_validation` + retry; Safe2Pay fora → pagamento direto continua; B2 fora → foto offline-tolerante; OSRM fora → haversine ×1,4 `eta_degraded`; SMS fora → e-mail+push; LLM fora → fila manual.
