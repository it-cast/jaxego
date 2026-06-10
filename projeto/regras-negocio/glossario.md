# Jaxegô — Glossário (vocabulário canônico)

> Em UI e copy, usar SEMPRE o termo canônico. Termos a evitar entre parênteses.

**Jaxegô** — a plataforma. Pronúncia "já-chegô". Em copy pode virar verbo: "jaxegou?". Grafia com acento; domínio sem (`jaxego.com.br`).

**área** — cidade ou região de cidade com regras próprias. Termo técnico: `area_id`. Em UI voltada a usuário final, preferir "cidade" ou "região" quando soar mais natural. (evitar: subdivisão, tenant)

**loja** — estabelecimento que cria entregas. (evitar: merchant, lojista, empresa — exceto em texto jurídico)

**operador** — funcionário da loja com acesso restrito a criar/acompanhar entregas.

**entregador** — autônomo que executa entregas. (evitar: motoboy, courier, rider, parceiro)

**destinatário** — quem recebe a entrega. Não tem login. (evitar: cliente final)

**entrega** — unidade transacional do sistema. (evitar: delivery, pedido — pedido é coisa do Menu Certo)

**corrida** — o valor do frete que pertence ao entregador. (evitar: frete em UI do entregador; "frete" só em UI da loja)

**taxa de plataforma** — valor por entrega que pertence ao Jaxegô, varia por plano, incide em toda entrega (RN-023).

**pagamento direto** — modalidade em que a loja paga o entregador na mão (dinheiro ou PIX pessoal); a plataforma só registra e fatura a taxa.

**fatura** — cobrança mensal das taxas de entregas com pagamento direto + excedentes.

**validação** — processo de verificação do entregador. Níveis: **simples** (CPF + selfie + telefone + e-mail) e **completa** (+ CNH EAR, CRLV, MEI, antecedentes se a área exigir). (evitar: KYC em UI — KYC só em contexto técnico/admin)

**coleta** — retirada da mercadoria na origem. Verbo: coletar. (evitar: pick-up, buscar, pegar)

**comprovação** — evidência da coleta/entrega: foto com GPS, número de referência ou código (pós-M1). Verbo: comprovar.

**número de referência** — identificador que o destinatário conhece (ex.: nº do pedido Menu Certo) usado como comprovação leve.

**cascata** — modelo de despacho: oferta vai a um entregador por vez, com cronômetro, na ordem favoritos → ranking automático.

**favorito** — entregador marcado pela loja para receber ofertas primeiro.

**bloqueado** — entregador que a loja não quer; lista privada, não afeta o score (RN-014).

**score** — pontuação 0–100 do entregador em janela de 90 dias, com níveis: probation, bronze, prata, ouro, diamante. Componentes sempre explicáveis.

**recusada no destino** — estado em que o destinatário recusou ou estava ausente; gera retorno ao estabelecimento.

**retorno** — trajeto de volta da mercadoria à loja após recusa/ausência; cobrado conforme política da área.

**saldo** — valor de corridas via plataforma já liberadas para saque (após escrow de 24h).

**saque** — transferência do saldo para a chave PIX do MEI do entregador.

**escrow** — retenção interna de 24h pós-finalização antes de liberar a corrida (termo só técnico; em UI: "liberado em 24h").

**disputa** — contestação aberta (pagamento direto não recebido, comprovação suspeita, avaria); mediada pelo admin de área.

**recurso** — contestação de suspensão pelo entregador; SLA de 5 dias úteis; estouro reverte a suspensão (RN-016).

**catálogo de bairros** — lista oficial de bairros da área, curada pelo admin local, inclui bairros informais.

**piso** — valor mínimo de frete da área; protege contra corrida ao fundo do poço (RN-015).

**tracking** — página pública de acompanhamento da entrega via link curto, sem login.

**Menu Certo** — marketplace de food do Grupo Itcast, primeiro cliente de integração via API.

**Safe2Pay** — PSP de pagamentos (assinaturas, cobranças, split, PIX, boleto).

**oferta** — proposta de entrega enviada a um entregador, com cronômetro de aceite.

**online / offline** — disponibilidade do entregador para receber ofertas. Estado `busy` é automático ao atingir o limite simultâneo.
