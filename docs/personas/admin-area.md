# Persona — Admin de área

**Fonte:** `projeto/regras-negocio/visao-geral.md:30,43`, F-08, `referencias.md:19` (Delivery Much — força do gestor local)

Sócio/gestor local da cidade — modelo de expansão tipo franquia com revenue share (% das taxas da área `[DECIDIR]`). Conhece a cidade: sabe quais bairros informais existem, quem é confiável.

## O que pode fazer (SÓ na sua área — F-08 E1: fora dela → 403)
- Aprovar/reprovar KYC de entregadores **item a item** com motivo (F-02)
- Curar catálogo de bairros (inclui informais), configurar nível de validação, pisos, geofence, timeouts, política de retorno
- Gerir API keys da área; mediar disputas (pagamento direto, comprovação suspeita, recursos)
- Suspender entregador/loja com motivo enum + texto (abre canal de recurso)
- Ver financeiro da área. **Não vê outras áreas.**

## Pressões operacionais
- KYC sem revisão em 48h → escalação ao admin plataforma (F-02 E5)
- Recurso de suspensão sem resposta em 5 dias úteis → suspensão revertida automaticamente + alerta (RN-016) — o ônus do atraso é da gestão
- Toda ação sensível auditada com before/after (RN-012)

## Referência de UI
Densidade do Stripe Dashboard: mono em valores, audit acessível, dashboards operacionais (telas 17–22).
