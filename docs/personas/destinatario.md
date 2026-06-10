# Persona — Destinatário

**Fonte:** `projeto/regras-negocio/visao-geral.md:34`, tela 26, `referencias.md:7` (Mercado Livre)

Quem recebe a entrega. **Sem login, sem app** — ninguém instala app para receber uma pizza (ADR-008 rejeitou app do destinatário).

## Pontos de contato
- Link público de tracking (`jaxego.com.br/r/abc`) recebido por SMS no momento "saiu para entrega" (RN-018)
- Notificações em 3 momentos: aceite, a caminho/aproximação, entregue (push/e-mail; SMS só no 2º, com quota)
- Pode avaliar o entregador após a entrega
- Em comprovação por referência: informa o número do pedido ao entregador

## Privacidade
- Identidade separada do endereço (`recipients`); hash de CPF para antifraude — nunca CPF puro
- Telefone acessível ao entregador só durante a janela ativa (RN-022)
- PII anonimizada em entregas >12 meses (RN-021)

## Exceções que o envolvem
Ausente → notificação + ligação + 10 min → retorno (reason `absent`); recusa do item → foto da recusa (reason `refused`).
