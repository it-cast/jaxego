# LGPD Compliance — conformidade operacional com Lei 13.709/2018

> Skill obrigatória para qualquer projeto que opere no Brasil e colete dados pessoais.
> **Disclaimer:** esta skill cobre práticas técnicas. Decisões finais sobre base legal, políticas e DPO exigem consulta jurídica.

## Princípio central

LGPD não é checklist único — é **disciplina operacional contínua**. Coletar menos, explicar mais, facilitar saída. Cada dado pessoal tratado precisa de base legal clara, finalidade específica, e mecanismos de exercício de direitos.

Framework mental: **"Se o titular me pedisse tudo o que tenho dele agora, eu consigo entregar em 15 dias?"** Se não, há pontos cegos a consertar.

## Conceitos (resumo operacional)

| Termo | O que significa |
|-------|-----------------|
| **Titular** | Pessoa a quem os dados pertencem |
| **Controlador** | Quem decide finalidade do tratamento (geralmente a empresa) |
| **Operador** | Quem trata dados em nome do controlador (ex: infra terceirizada, SaaS) |
| **Base legal** | Justificativa para tratar (uma de 10 na lei — 5 mais comuns abaixo) |
| **Dado pessoal** | Qualquer informação identificável ou identificadora |
| **Dado sensível** | Subset mais protegido (saúde, raça, orientação, etc.) |
| **Tratamento** | Qualquer operação com dado (coleta, uso, armazenamento, compartilhamento, descarte) |

## Bases legais (usar a certa por finalidade)

1. **Consentimento** — titular aceitou explicitamente para finalidade específica. Pode revogar a qualquer tempo.
2. **Execução de contrato** — dado necessário para cumprir contrato (não precisa consent para CPF do cliente em nota fiscal).
3. **Obrigação legal/regulatória** — exigido por outra lei (ex: guardar NF por 5 anos).
4. **Legítimo interesse** — interesse legítimo do controlador, com teste de balanceamento. Uso comum: fraud prevention, segurança.
5. **Proteção à vida/saúde** — emergências médicas.

Outras: execução de política pública, pesquisa, proteção de crédito, etc.

**Regra operacional:** cada campo coletado tem base legal documentada. Sem base = não coletar.

## Coleta: menos é mais

### Minimização

```python
# ❌ pede tudo sem razão
class UserSignupBody(BaseModel):
    email: EmailStr
    password: str
    cpf: str  # precisa MESMO?
    full_name: str
    phone: str
    birth_date: date
    mother_name: str  # precisa?
    address: str
    rg: str  # precisa?

# ✅ mínimo necessário
class UserSignupBody(BaseModel):
    email: EmailStr
    password: str
    full_name: str  # só para exibir
    # CPF e outros: pedir quando necessário (ex: primeiro pedido que exige NF)
```

### Finalidade explícita

Para cada campo sensível ou não-óbvio, explicar:

```html
<label for="cpf">
  CPF
  <span class="hint">Usado para emissão de nota fiscal. 
    <a href="/privacidade#cpf">Por que pedimos?</a>
  </span>
</label>
<input id="cpf" required />
```

### Consent granular

Checkbox NÃO pré-marcado, granular:

```html
<!-- ❌ tudo em um -->
<label>
  <input type="checkbox" checked />
  Aceito os termos e a política de privacidade e quero receber emails promocionais
</label>

<!-- ✅ separado, não pré-marcado -->
<label>
  <input type="checkbox" required />
  Li e aceito os <a href="/termos">Termos de Uso</a> e a 
  <a href="/privacidade">Política de Privacidade</a>
</label>

<label>
  <input type="checkbox" />
  Quero receber ofertas e novidades por email (opcional)
</label>
```

## Direitos do titular — endpoints obrigatórios

Art. 18 da LGPD. Titular pode solicitar:

| Direito | Endpoint/fluxo necessário |
|---------|----------------------------|
| **Confirmação** | "Vocês têm meus dados?" → listar |
| **Acesso** | Exportar todos os dados do titular em formato legível |
| **Correção** | Editar dados incorretos |
| **Anonimização/eliminação** | Remover ou anonimizar quando possível |
| **Portabilidade** | Exportar em formato estruturado (JSON/CSV) |
| **Informação sobre compartilhamento** | Listar com quem seus dados foram compartilhados |
| **Revogação de consent** | Retirar consent específico |

### Implementação mínima

```python
# backend/app/api/privacy.py

@router.get("/privacy/me", response_model=PersonalDataExport)
async def export_my_data(user: CurrentUser):
    """Retorna todos os dados pessoais do usuário."""
    return PersonalDataExport(
        account=await fetch_account(user.id),
        profile=await fetch_profile(user.id),
        orders=await fetch_orders(user.id),
        messages=await fetch_messages(user.id),
        audit_log=await fetch_audit_log_for(user.id),
        consents=await fetch_consents(user.id),
        exported_at=datetime.utcnow(),
    )

@router.get("/privacy/me/download")
async def download_my_data(user: CurrentUser):
    """Mesma info, em ZIP com JSON + CSVs."""
    data = await export_my_data(user)
    zip_path = await build_export_zip(data)
    return FileResponse(zip_path, filename=f"meus-dados-{user.id}.zip")

@router.post("/privacy/me/delete-account")
async def request_account_deletion(user: CurrentUser, body: DeletionRequestBody):
    """Inicia fluxo de exclusão de conta."""
    # Pode exigir confirmação por email, pode ter período de carência
    await queue.enqueue('process_account_deletion', user_id=user.id, reason=body.reason)
    return {"status": "scheduled", "will_complete_by": "2026-05-07"}

@router.get("/privacy/me/shared-with")
async def list_data_sharing(user: CurrentUser):
    """Com quem os dados foram compartilhados (Stripe para pagamento, SendGrid para email, etc.)."""
    return [
        {"service": "Stripe", "purpose": "Processamento de pagamento", "data_shared": ["email", "payment_token"]},
        {"service": "SendGrid", "purpose": "Envio de emails transacionais", "data_shared": ["email", "full_name"]},
    ]

@router.post("/privacy/consent")
async def update_consent(body: ConsentUpdateBody, user: CurrentUser):
    """Revogar ou conceder consent específico."""
    await db.update_consent(user.id, body.consent_type, body.granted)
    await audit_log("consent_updated", user_id=user.id, consent=body.consent_type, granted=body.granted)
    return {"ok": True}
```

### UI equivalente

Em settings/perfil:
```
Privacidade e dados

[ ] Baixar meus dados
    Exporta tudo em um arquivo ZIP.

[ ] Ver com quem meus dados são compartilhados
    Lista de serviços que processam meus dados em nome do app.

[ ] Gerenciar consentimentos
    Ativar/desativar comunicações opcionais.

[ ] Excluir minha conta
    Remove permanentemente sua conta e dados associados.
    Algumas informações podem ser retidas por obrigação legal.
```

## Exclusão vs anonimização

### Exclusão hard
- Remove fisicamente do banco
- Usar quando legalmente possível e não há razão de retenção

### Anonimização
- Mantém o registro mas remove dados identificadores
- Usar para preservar integridade analítica (ex: pedido continua no histórico de vendas, mas sem dados do cliente)

```python
async def anonymize_user(user_id: UUID):
    await db.execute("""
        UPDATE users SET
          email = :pseudo_email,
          full_name = '[removido]',
          cpf = NULL,
          phone = NULL,
          birth_date = NULL,
          deleted_at = NOW(),
          anonymized_at = NOW()
        WHERE id = :user_id
    """, {"user_id": user_id, "pseudo_email": f"anon-{user_id}@anonymized.local"})
    
    # Dados em outras tabelas
    await db.execute("UPDATE messages SET content = '[removido]' WHERE user_id = :user_id", ...)
    # ou delete conforme política
```

### Retenção obrigatória

Algumas leis exigem retenção mesmo após pedido de exclusão:
- Nota fiscal: 5 anos
- Relações trabalhistas: 5 anos após encerramento
- Dados bancários: variável

Explicar ao titular quando aplicável:
> "Removemos seus dados da plataforma. Algumas informações (notas fiscais emitidas) serão retidas por 5 anos conforme legislação fiscal, após o que serão excluídas automaticamente."

## Logs sem PII

Integrar com skill `observability-production`:

```python
PII_FIELDS = {
    "cpf", "cnpj", "rg", "full_name", "email", "phone", "birth_date",
    "address", "password", "password_hash", "token", "jwt", "refresh_token",
    "card_number", "cvv", "mother_name",
}

def scrub_pii(event_dict):
    for key in list(event_dict.keys()):
        if key.lower() in PII_FIELDS:
            event_dict[key] = "[REDACTED]"
    return event_dict
```

CPF/email podem aparecer em log **como identificador parcial** se necessário para debug:
```python
logger.info("auth_failed", user_email_hint=f"{email[:2]}***@{email.split('@')[1]}")
# Ex: "jo***@gmail.com"
```

Nunca logar:
- Senha (mesmo hash em alguns casos — depende do risco)
- Token completo (só últimos 4 chars)
- Dados de cartão
- PII sensível (saúde, orientação, etnia)

## Criptografia

### Em trânsito
- HTTPS obrigatório em produção (TLS 1.2+)
- Certificados válidos; HSTS header

### Em repouso
- Banco com encryption at rest (RDS/CloudSQL default OK)
- Campos especialmente sensíveis: criptografia adicional
  ```python
  # Campo CPF criptografado no banco
  cpf_encrypted = Column(LargeBinary)  # criptografado com AES-256 + chave rotativa
  ```
- Backups criptografados

### Hashing de senha
- Nunca plaintext
- Algoritmo: Argon2id (preferido) ou bcrypt cost ≥ 12
- Nunca MD5, SHA1, SHA256 direto

## Compartilhamento com operadores

Quando usa Stripe, SendGrid, AWS, Datadog, etc., são **operadores** sob LGPD:

### Exige contrato (DPA — Data Processing Agreement)
- Maioria dos SaaS modernos oferece DPA padrão
- Assinar e guardar

### Lista pública

Política de privacidade lista:
> Compartilhamos dados com os seguintes operadores:
> - **Stripe** (pagamentos) — EUA, dados trocados: email, valor da transação, ID
> - **SendGrid** (emails) — EUA, dados trocados: email, nome
> - **AWS** (infra) — região São Paulo, dados armazenados: todos

### Minimização em APIs externas
- Enviar só o necessário
- Pseudônimos onde possível

## Incidentes de segurança

Plano obrigatório:

1. **Detecção** — monitoramento ativo (Sentry, alerts, SIEM básico)
2. **Contenção** — isolar rapidamente; desabilitar acesso comprometido
3. **Avaliação** — dados afetados? quais titulares? qual risco?
4. **Notificação** — ANPD e titulares afetados em prazo razoável
5. **Documentação** — registro de tudo (obrigação legal)
6. **Postmortem** — análise de causa raiz; ação corretiva

Playbook escrito e ensaiado 1-2x por ano.

## DPO (Data Protection Officer)

- **Obrigatório** para alguns controladores (definido pela ANPD, geralmente operações de grande escala ou dados sensíveis)
- Pode ser interno ou terceirizado
- Contato público (email, canal dedicado)
- Responsabilidades: ponto focal com ANPD, atende titulares, orienta equipe

## Política de privacidade

Acessível em link claro ("/privacidade"). Deve cobrir:

1. **Identificação do controlador** (razão social, CNPJ, endereço, contato)
2. **Quais dados coleta** (lista concreta — não genérico)
3. **Finalidade de cada categoria**
4. **Base legal de cada categoria**
5. **Com quem compartilha** (lista de operadores/parceiros)
6. **Prazo de retenção** por categoria
7. **Direitos do titular** e como exercer
8. **Contato do DPO**
9. **Última atualização** (e histórico de versões)

Formato: legível. Não é documento jurídico pesado — é comunicação com usuário. Seções curtas, exemplos concretos.

## Cookies e tracking

Mesma lógica de consent:
- Cookies estritamente necessários: não precisam consent (funcionais)
- Analytics, marketing, personalização: precisam consent ativo
- Banner de cookies com opção granular — não "Aceitar todos" como único botão

## Menores de idade

Coleta de dados de menor de 18 (especialmente < 12) tem requisitos extras:
- Consent do responsável
- Minimização reforçada
- Finalidade específica e limitada

Se o projeto **não pretende** atender menores, declarar explicitamente nos termos e ter fluxo de idade mínima.

## Auditoria interna

Trimestral ou antes de releases grandes:

- [ ] Dados coletados ainda têm base legal atual?
- [ ] Política de privacidade reflete realidade do sistema?
- [ ] Endpoints de direitos funcionam? (testar manualmente)
- [ ] Lista de operadores atualizada?
- [ ] DPAs vigentes?
- [ ] Logs confirmam zero PII em cleartext?
- [ ] Incidentes de segurança do período: houve? foram tratados?
- [ ] Formulários ainda coletam mínimo necessário?

## Anti-patterns

- "Aceitar todos os termos" como único checkbox pré-marcado
- Política de privacidade genérica copiada de outro site
- Sem endpoints de acesso/exclusão (titular liga por telefone pedindo)
- CPF em URL (`/users/12345678900/orders`) — vaza para logs de proxy, analytics
- Log de endpoint com body completo que inclui PII
- Senha em plaintext em qualquer lugar
- Backup em cloud pública sem criptografia
- Coletar data de nascimento "por precaução" sem uso declarado
- Share de CPF com dezenas de operadores sem DPA
- Reter dados "caso precise depois" sem política de retenção
- Sem registro de quem acessou o quê (audit log ausente)
- Anonimização que é apenas "trocar nome" (outros campos ainda identificam)

## Checklist para PLAN.md

- [ ] Base legal declarada para cada campo novo coletado
- [ ] Consent granular, checkbox não pré-marcado (se aplicável)
- [ ] Link visível para política de privacidade em signup e footer
- [ ] Política de privacidade atualizada refletindo mudanças
- [ ] Endpoints de direitos do titular presentes (acesso, exclusão, portabilidade, consent)
- [ ] UI em settings para exercer direitos
- [ ] Logs sem PII (filtro ativo — ver observability-production)
- [ ] HTTPS em produção; certificado válido
- [ ] Hashing de senha com Argon2id ou bcrypt cost ≥ 12
- [ ] DPA assinado com todos os operadores (Stripe, SendGrid, etc.)
- [ ] Política de retenção declarada por tipo de dado
- [ ] Audit log registra acessos a dados sensíveis
- [ ] CPF/email nunca em URL
- [ ] Plano de resposta a incidente escrito e acessível
