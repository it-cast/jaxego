# wireframes/

**Mockups, telas, fluxos visuais, wireframes interativos.** Qualquer coisa que mostre COMO algo deve parecer ou funcionar.

## O que jogar aqui

- Wireframes (low-fi e high-fi)
- Mockups e protótipos
- **Wireframes HTML interativos** (Lovable, v0, bolt outputs — pasta completa ou arquivos individuais)
- **Componentes JSX/TSX/Vue/Svelte de protótipo**
- Screenshots de outras ferramentas que você quer replicar
- Fluxos visuais entre telas
- Sketches em foto do papel

## Formatos aceitos

- **Imagens estáticas:** `.png`, `.jpg`, `.jpeg`, `.svg`, `.pdf` (Figma export, Sketch export)
- **Wireframes interativos:** `.html`, `.htm`, `.jsx`, `.tsx`, `.vue`, `.svelte` (extraídos com **análise estrutural**, não como imagem)
- **Descrições:** `.md` com texto narrando telas inexistentes

## Por que HTML é especial

Quando você joga aqui o **output de Lovable/v0/bolt** (ou wireframe HTML que você fez), o ingestor não trata como "imagem que precisa OCR" — ele **lê o DOM real**:

- Detecta componentes por nome (Button, Card, Input, Sidebar)
- Mapeia fluxos via `<a href>` e `<button onClick>`
- Identifica estados (loading, error, empty, success)
- Extrai tokens (cores, spacing, fontes) das classes/CSS
- Sugere design system base a partir dos tokens detectados

**Resultado:** REQs gerados mencionam componentes específicos, e `design-system/MASTER.md` herda decisões visuais do wireframe.

## Fidelidade ENFORCED (v0.9.7)

Wireframe HTML aqui não é só inspiração — é **contrato verificável** em 4 elos:
1. `gsd-tools wireframe-contract <arquivo>` extrai regiões, headings, botões/links (texto + destino), inputs, estados e cores
2. O `ui-phase` (passo 2.5) é obrigado a cobrir cada item no UI-SPEC ou declarar a divergência em `deviations:` com razão
3. O `ui-checker` (Dimension 7) re-roda o contrato e bloqueia omissão silenciosa
4. O Gate 8 confere os elementos do contrato no código construído

Divergir é permitido; divergir em silêncio, não. Limites: o contrato cobre o DOM **estático**; wireframes-imagem têm fidelidade visual (sem contrato mecânico) — se fidelidade estrutural importa, use HTML.

## Exemplos

```
01-login.png
02-dashboard.png
03-checkout-flow.pdf
mobile/01-home.jpg
mobile/02-product-detail.jpg
descricao-fluxos.md          # texto descrevendo telas inexistentes
```

## Dica de organização

Numere os arquivos em ordem de fluxo (`01-`, `02-`, `03-`) para que Claude entenda sequência.

## O que NÃO jogar aqui

- Logo / paleta (vai em `identidade-visual/`)
- Print de concorrente como referência (vai em `referencias/`)
- Fluxograma de regra de negócio em ASCII (vai em `regras-negocio/`)
