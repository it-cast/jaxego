# Jaxegô — Referências e concorrentes

> O que tirar de cada um. Base do benchmark que orientou produto e identidade.

## Copiar (o melhor de cada)

**Mercado Livre** — tracking público por link curto sem app; foto de comprovação como prova padrão; identidade do destinatário separada do endereço; notificação proativa em momentos-chave. → Telas 26 (tracking), fluxo F-06.

**Amazon** — validação da foto no momento da captura (enquadramento, GPS, luz) impedindo comprovação ruim de nascer. → F-06 E1; IA de apoio pós-M1.

**Uber Driver** — heatmap de demanda para decisão de posicionamento; bônus/quests transparentes com progresso visível; ganhos do dia em destaque. → Tela 04 (home do entregador); bônus pós-M1.

**Stripe Dashboard** — densidade de informação correta para operação financeira; mono em valores; audit log acessível. → Admins (telas 17–25).

**Linear** — hierarquia visual brutal: o que importa é grande; estado = cor única; velocidade percebida. → Todo o design system.

**Loggi** — tipologia clara de urgência (expressa/agendada); profissionalização da entrega avulsa. → Campo urgency (pós-M1 para agendada).

**Delivery Much** — prova de que modelo regional de interior funciona como negócio; força do gestor local. → Papel do admin de área + revenue share.

## Corrigir (o que eles erram)

**iFood** — score opaco (entregador não sabe por que caiu) → nosso score mostra componentes, pesos, delta e causa (ADR-013). Suspensão sem recurso efetivo → recurso com SLA de 5 dias úteis e reversão automática no estouro (RN-016).

**Rappi** — laranja neon saturado que cansa em uso prolongado → Persimmon queimado #E84E1B, cinemático.

**99** — interface visualmente saturada → cream warm #FAF6EE como papel, densidade só onde a operação exige.

**Lalamove** — preço tabelado pela plataforma (risco trabalhista + injusto com o entregador local) → entregador define a própria tabela; plataforma só impõe piso por área (RN-015).

**Uber/iFood** — pagamento exclusivamente intermediado → modalidade de pagamento direto como 1ª classe (ADR-012), respeitando o costume do interior e destravando entregador sem MEI.

**Loggi** — cobertura e preços confusos para o entregador → tabela do entregador editável por ele mesmo, com piso explícito.

## Não competir / não copiar

- iFood marketplace de food: o Menu Certo já ocupa esse espaço no grupo; Jaxegô é a camada logística.
- Frota própria, centro de distribuição, dark store: capital intensivo, fora da tese.
- Cidades >500k hab: guerra de gigantes; nossa vantagem é hiperlocal.

## Diferenciais próprios (sem referência externa)

1. **Áreas com regras locais** numa aplicação única (nível de validação, pisos, bairros informais curados pelo gestor local).
2. **Pagamento direto registrado** — formaliza o costume informal sem matá-lo.
3. **Integração nativa Menu Certo** — demanda capturada no dia 1 (resolve o cold start clássico de marketplace).
4. **Entregador sem MEI pode começar** (só pagamento direto) — onboarding sem barreira, regularização incentivada depois.
