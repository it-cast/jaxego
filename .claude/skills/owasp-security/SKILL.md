---
name: owasp-security
description: >
  Auditoria de segurança baseada no OWASP Top 10:2025 e ASVS 5.0.
  Padrões seguros, anti-patterns e decisões contextualizadas para Python/FastAPI,
  TypeScript/Angular, MySQL e APIs REST. Use quando: revisar segurança, auditar
  endpoints, verificar autenticação/autorização, validar inputs, proteger
  contra injection, XSS, CSRF, SSRF, ou qualquer questão de segurança.
  Esta skill é a fonte do Bloco B do Gate 8 (senior-quality-bar).
---

# OWASP Security — profundidade sênior

> **Princípio desta skill:** segurança sênior não é decorar regras — é saber POR QUE
> cada regra existe e QUANDO ela muda. Onde a decisão depende de contexto, esta skill
> dá a tabela de decisão, não um número mágico. Onde não depende (segredo no repo,
> SQL via f-string), a regra é absoluta e mapeia para FAIL-BLOCK do Gate 8.

## Mapa Gate 8 (Bloco B) → seções desta skill

| Item FAIL-BLOCK do Gate 8 | Seção |
|---|---|
| Segredo no código/repo | A02 + Gestão de Segredos |
| SQL injection possível | A03 |
| Endpoint sem decisão de auth | A01 + A07 |
| PII em log | A09 + LGPD |
| Deploy irreversível / backup ausente | (skill `monorepo-deploy-safety`) |
| N+1 em lista | (skill `fastapi-production-patterns` §5) |

---

## A01 — Broken Access Control

**A regra de ouro:** TODA rota tem uma decisão EXPLÍCITA de auth. Não existe "esqueci
de proteger" — existe rota com `Depends(get_current_user)`, rota com
`Depends(get_admin_user)`, ou rota com comentário `# público: <justificativa>`.
Ausência de qualquer um dos três = FAIL-BLOCK.

**Ownership (o erro nº 1 em B2B multi-tenant):**
```python
# ❌ ERRADO — autentica mas não verifica posse
@router.get("/forecasts/{forecast_id}")
async def get_forecast(forecast_id: int, user: User = Depends(get_current_user)):
    return await repo.get(forecast_id)  # qualquer logado lê qualquer forecast

# ✅ CERTO — escopo de tenant na QUERY, não em if posterior
@router.get("/forecasts/{forecast_id}")
async def get_forecast(forecast_id: int, user: User = Depends(get_current_user)):
    forecast = await repo.get_for_tenant(forecast_id, tenant_id=user.tenant_id)
    if forecast is None:
        raise NotFoundError()  # 404, não 403 — não vaze que o recurso existe
```
Por que na query: filtro em `if` depois do fetch é esquecível e não compõe com
paginação. `WHERE tenant_id = :tid` em todo repositório multi-tenant é estrutural.

**IDs:** UUIDs (ou ULIDs) em recursos expostos. IDs sequenciais permitem enumeração
(`/users/1`, `/users/2`...) e vazam volume de negócio para concorrentes.

**Checklist A01:**
- [ ] Toda rota: auth dependency OU `# público:` justificado
- [ ] Multi-tenant: tenant_id no WHERE de todo repositório, não em if
- [ ] 404 (não 403) para recurso de outro tenant
- [ ] Rotas admin: dependency separada (`get_admin_user`), nunca `if user.is_admin` no corpo
- [ ] IDs expostos não-sequenciais

## A02 — Cryptographic Failures

**Senhas:** bcrypt (custo 12+) ou argon2id. NUNCA MD5/SHA-qualquer-coisa para senha,
nem com salt — são rápidos demais por design. Comparações de tokens/assinaturas:
`secrets.compare_digest`, nunca `==` (timing attack).

**JWT — tabela de decisão de algoritmo (não há um "certo" universal):**

| Cenário | Algoritmo | Por quê |
|---|---|---|
| Um único serviço emite E valida (monolito FastAPI) | HS256, secret ≥256 bits | Simples, rápido; o segredo nunca sai do serviço |
| Mais de um serviço valida (API + worker + gateway, multi-serviço) | RS256 ou ES256 | Validadores recebem só a chave PÚBLICA; comprometer um validador não permite FORJAR tokens |
| Tokens validados por terceiros / SDK de cliente | RS256/ES256 + JWKS endpoint | Rotação de chave sem redeploy dos validadores |

A pergunta a fazer no research da phase: "quantos processos distintos validam este
token?" Se a resposta é >1 ou "vai crescer", assimétrico. Migrar depois é caro
(invalidar todos os tokens vivos ou suportar dois algoritmos no período de transição).

**JWT — claims obrigatórias:** `exp` (access 15–60min conforme sensibilidade; 30min
é um default razoável, não uma lei), `iat`, `iss`, `aud` — e VALIDAR todas no decode
(`decode(..., options={"require": ["exp","iss","aud"]})`). Algoritmo PINADO no
decode (`algorithms=["RS256"]`) — aceitar lista aberta habilita o ataque `alg:none`.

**Refresh tokens:** opacos (random 256-bit, não JWT), armazenados com hash no banco,
rotacionados a cada uso, com detecção de reuso (reuso de refresh já rotacionado =
sessão comprometida → revogar a família inteira).

**Em trânsito/repouso:** HTTPS obrigatório (HSTS, ver A05). Dados sensíveis em
repouso: avaliar criptografia em nível de coluna para PII crítica (CPF) — decisão
de ADR, não default.

## A03 — Injection

**SQL:** APENAS via ORM ou prepared statements. Raw SQL com f-string/concat = FAIL-BLOCK
sem exceção. Quando raw SQL é necessário (relatórios complexos), parâmetros nomeados:
```python
# ✅ aceitável quando ORM não basta
await session.execute(text("SELECT ... WHERE tenant_id = :tid"), {"tid": tenant_id})
# ❌ FAIL-BLOCK — mesmo "sabendo" que tenant_id é int hoje
await session.execute(text(f"SELECT ... WHERE tenant_id = {tenant_id}"))
```
Cuidado especial: `ORDER BY` e nomes de coluna não são parametrizáveis — use
allowlist explícita (`SORTABLE = {"created_at", "name"}`).

**Validação de entrada:** Pydantic v2 em TODO endpoint, com tipos estreitos
(`EmailStr`, `conint(ge=1)`, enums) — `str` genérico onde caberia enum é validação
de mentira. `extra="forbid"` em schemas de escrita (campo inesperado = erro, não
silêncio — previne mass assignment).

**Shell/OS:** `subprocess` com lista de args, nunca `shell=True` com input do usuário.
**Path traversal:** uploads/downloads resolvem path e verificam prefixo
(`resolved.is_relative_to(BASE_DIR)`).

## A04 — Insecure Design

**Rate limiting — derive do contexto, não copie números:**

| Endpoint | Heurística | Exemplo de partida |
|---|---|---|
| Login / reset de senha | Baixo o bastante para inviabilizar brute force, alto o bastante para usuário com caps lock | 5/min por IP **e** por conta (as duas dimensões) |
| API autenticada geral | 2–3× o pico legítimo observado/projetado por tenant | 60–120/min por tenant |
| Endpoints caros (simulação, geração de relatório, chamada a LLM) | Orçamento de custo: quanto cada chamada custa × o que o plano do tenant paga | quota por plano, não por minuto |
| Webhooks de entrada (PSP) | Generoso — quem limita demais perde notificação de pagamento | validar assinatura primeiro, limitar depois |

Registrar a derivação no PLAN.md ("login: 5/min porque X"). Número sem derivação
documentada = FAIL-DEBT.

**Invariantes de negócio no backend:** preço, desconto, plano, limites de quota —
recalculados/validados no servidor SEMPRE. Frontend é sugestão, não autoridade.

**Threat model curto (15 min, features de dinheiro/auth/PII):** quem pode abusar?
o que ganha? qual o pior caso? — 3 perguntas escritas no research da phase.

## A05 — Security Misconfiguration

- CORS: allowlist explícita de origens em produção. `allow_origins=["*"]` com
  `allow_credentials=True` é pior que inútil — navegadores rejeitam, e a "correção"
  apressada costuma ser refletir o Origin, que é o mesmo que `*` com credenciais.
- Headers obrigatórios (middleware único, testável):
  `Strict-Transport-Security: max-age=31536000; includeSubDomains`,
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` (ou CSP `frame-ancestors`),
  `Content-Security-Policy` ao menos com `default-src 'self'` em apps Angular
  (Angular ajuda contra XSS, CSP é a segunda camada),
  `Referrer-Policy: strict-origin-when-cross-origin`.
- `DEBUG=False`, docs interativas (`/docs`, `/redoc`) desligadas ou atrás de auth
  em produção, stack traces nunca no corpo da resposta (ver A09).
- Docker: non-root user, imagem base slim, `COPY` seletivo (não `COPY . .` com .env junto).
- Mensagens de erro de login: "credenciais inválidas" — nunca "usuário não existe"
  (enumeração de contas).

## A06 — Vulnerable & Outdated Components

- `pip-audit` (ou `uv audit`) + `npm audit --omit=dev` no CI, **bloqueante para
  severidade high/critical** — a skill `github-actions-ci` define o job canônico.
- Lockfiles commitados sempre; dependabot/renovate ou revisão mensal manual.
- Remover dependência não usada é patch de segurança gratuito.

## A07 — Identification & Authentication Failures

- Política de senha: mínimo 10–12 chars, SEM regras de composição arbitrárias
  (NIST 800-63B); checar contra lista de senhas vazadas se viável.
- Lockout progressivo (não permanente — DoS de conta alheia) + as duas dimensões
  de rate limit do A04.
- Sessão/token invalidado em troca de senha e logout (denylist de jti ou versão
  de sessão no usuário).
- MFA: obrigatório para admin de plataforma; oferecido para usuários B2B (decisão
  de produto registrada em ADR, não esquecida).

## A08 — Software & Data Integrity Failures

- **Webhooks (Pagar.me e afins):** validar assinatura HMAC com `compare_digest`
  ANTES de qualquer parse de negócio; processar com chave de idempotência única
  (event_id) — webhook reentregue não pode duplicar crédito/baixa.
- Nunca `pickle`/`eval`/`yaml.load` (sem SafeLoader) com dados externos.
- CI: actions pinadas por SHA (não `@main`), artefatos de deploy com checksum.

## A09 — Security Logging & Monitoring Failures

**Logar (com request_id correlacionável):** login sucesso/falha, mudança de
permissão, acesso admin, erro 5xx, gate de pagamento, validação de webhook falhada.

**NUNCA logar:** senha (nem errada — usuários erram digitando a senha de outro
lugar), token/refresh/api-key, número de cartão, CPF/CNPJ completo, corpo de
request de auth. PII em log = FAIL-BLOCK.

**Redação estrutural, não disciplina:** filtro de logging central que mascara
campos por nome (`password`, `token`, `authorization`, `card`, `cpf`, `document`)
— confiar que cada `logger.info` individual vai lembrar é design para falhar.
A skill `quality/observability-production` define o setup; esta skill define o
que jamais pode passar por ele.

**LGPD (conexão com `br/lgpd-compliance`):** log com PII é tratamento de dado
pessoal — precisa de base legal, retenção definida e entra no escopo de pedido
de eliminação do titular. Retenção de logs: defina (30–90 dias app logs é prática
comum; auditoria de acesso pode exigir mais) e automatize a expiração.

## A10 — Server-Side Request Forgery (SSRF)

Relevante sempre que o servidor busca URL influenciada por usuário — incluindo
**integrações LLM com fetch de contexto** e import de dados por URL:
- Allowlist de hosts de saída (PSP, Backblaze B2, APIs LLM contratadas) no nível
  de aplicação; idealmente também egress firewall no VPS.
- Resolver DNS e rejeitar IPs privados/link-local (10.x, 172.16–31.x, 192.168.x,
  169.254.x, ::1) ANTES de conectar; revalidar pós-redirect (redirect para IP
  interno é o bypass clássico).
- Timeout curto e sem credenciais ambientes (metadata endpoints de cloud:
  169.254.169.254 é o alvo nº 1).

## Gestão de Segredos (transversal — FAIL-BLOCK)

- Segredo em código, em arquivo commitado, em log ou em mensagem de erro = FAIL-BLOCK.
- `.env` no `.gitignore` DESDE O PRIMEIRO COMMIT; `.env.example` com placeholders.
- **Segredo já commitado = comprometido.** Remover do histórico não basta:
  ROTACIONAR a credencial é a correção; o rewrite de histórico é cosmético.
- Detecção: o verify-phase roda grep de padrões de segredo (ver workflow); para
  defesa em profundidade, gitleaks/trufflehog no CI.
- Produção: variáveis de ambiente injetadas pelo deploy (systemd EnvironmentFile
  com permissão 600, ou secrets do GitHub Actions → ambiente), nunca arquivo
  no repo.

## Anti-patterns que reprovam code review (resumo executável)

```text
❌ f-string/concat em SQL                      → A03, FAIL-BLOCK
❌ rota sem dependency de auth nem "# público:" → A01, FAIL-BLOCK
❌ segredo literal em código/commit             → Segredos, FAIL-BLOCK
❌ print/log de token, senha, CPF, cartão       → A09, FAIL-BLOCK
❌ algorithms não pinado no jwt.decode          → A02
❌ allow_origins=["*"] + credenciais            → A05
❌ comparação de assinatura com ==              → A02/A08
❌ webhook processado antes de validar HMAC     → A08
❌ rate limit copiado sem derivação documentada → A04, FAIL-DEBT
❌ fetch de URL do usuário sem allowlist/checagem de IP privado → A10
```

## Relação com outras skills

- `quality/senior-quality-bar` — Bloco B referencia esta skill; os FAIL-BLOCKs daqui são os dele
- `domain/fastapi-production-patterns` — auth baseline, erros padronizados, N+1
- `domain/github-actions-ci` — jobs de audit de dependência e secret scanning
- `br/lgpd-compliance` — base legal, titular, retenção (A09 toca, ela aprofunda)
- `quality/observability-production` — implementação do logging que A09 restringe
- `domain/saas-billing-canonical` + `safe2pay-escrow-br` — webhooks de pagamento (A08)
