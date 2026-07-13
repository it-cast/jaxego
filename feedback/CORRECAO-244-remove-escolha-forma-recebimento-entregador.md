# CORRECAO-244 — Remoção da escolha "Em mãos vs PIX" do entregador

## Data
2026-07-13

## Motivação
Com o repasse automático via Safe2Pay (CORRECAO-241/242), o entregador sempre
recebe pelo app — não faz mais sentido perguntar "Como vai cobrar?" ao coletar.

## Achado importante antes de mexer
Pesquisei o campo `courier_collection_method` (`in_hand`/`pix_app`) a fundo:
**nunca teve efeito real no backend**. Não é lido em `state_machine.py`, nem
em `payout.py` (o repasse automático), nem em nenhuma regra de negócio. Era
puramente um **gate de UX no cliente**: enquanto o campo ficasse `null`, o
botão de avançar depois de "COLETADA" ficava trocado por "Cobrar entrega"
(que abria o modal). Ou seja, a remoção é segura — não desliga nenhuma lógica
de servidor.

**Importante, mas fora do escopo desta correção**: esse campo é diferente de
`payment_method` (`direct`/`card`/`pix`, RN-023) — hoje TODA entrega nasce
com `payment_method="direct"`. Pela regra de negócio documentada (RN-023/024),
"direct" deveria significar "loja paga o entregador por fora, sem passar pela
plataforma", e é o que permite entregador com MEI pendente trabalhar sem
bloqueio (RN-010 só bloqueia repasse via plataforma). O repasse automático
que implementamos dispara pra QUALQUER entrega finalizada com
`s2p_recipient_id`, sem checar `payment_method` nem MEI. Isso pode estar
pagando via Safe2Pay entregas que deveriam, pela regra original, ser pagas
direto pela loja. Vale uma conversa de produto separada — não mexi nisso agora.

## Mudanças

### App do entregador (Ionic)
- `entrega-ativa/entrega-ativa.page.ts`:
  - Removido o modal "Como vai cobrar?" (in_hand/pix_app) inteiro.
  - Removida a linha de exibição "Forma de cobrança do entregador" (mantida
    "Forma de recebimento do cliente" — `receipt_method`, campo diferente,
    de como o CLIENTE paga a loja, não alterado).
  - Botão único ao aceitar: "Já coletei" → chama `collect()` (era
    `collectAndCharge()`) → só marca COLETADA e recarrega, sem abrir modal.
  - Ao ficar COLETADA, vai direto para "Cheguei no destino" / "Destinatário
    ausente" — sem o passo intermediário "Cobrar entrega".
  - Removidos: signal `showCollectionModal`, métodos `setCollection()` e
    `collectionLabel()`, ícones `faHandHoldingDollar`/`faMobileScreen` (só
    usados no modal removido).
- `entregador.service.ts`: removido `setCollectionMethod()` (chamava o
  endpoint agora removido).

### Backend
- `app/couriers/router.py`: removido `PATCH /{courier_id}/deliveries/{delivery_id}/collection-method`
  (`set_collection_method`) — sem mais nenhum caller.
- Campo `courier_collection_method` **mantido** no model/schema/serializer —
  só leitura, preserva o histórico de entregas antigas que já tinham o valor
  setado. Não fica mais NULL→preenchido daqui pra frente.

### Não alterado (fora de escopo)
- `receipt_method` (como o CLIENTE paga a loja) — campo diferente, continua
  intacto em todas as telas (loja cria, entregador vê).
- Exibição histórica em `concluida.page.ts`/`entregas.page.ts` — continuam
  mostrando `courier_collection_method` quando presente (entregas antigas);
  como o campo não é mais escrito, esses blocos simplesmente não aparecem
  para entregas novas (guardados por `@if`).

## Validado
Build do app (`ng build`) verde. API reiniciada, import limpo, grep confirma
zero escritas restantes de `courier_collection_method` (só leitura/serialização).
