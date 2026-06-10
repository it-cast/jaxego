# identidade-visual/

**Marca, paleta, tipografia, tokens.** Tudo que define a identidade visual.

## O que jogar aqui

- Logo (todas as variações)
- Paleta de cores (extraída ou definida)
- Tipografia (fontes escolhidas, hierarquia)
- Manual de marca (se houver)
- Tokens de design (se já estiverem em JSON)
- Inspirações de moodboard
- Brand voice (tom de comunicação)

## Formatos aceitos

`.svg`, `.png`, `.pdf`, `.ai`, `.md`, `.json` (tokens), `.txt`

## Exemplos

```
logo-primary.svg
logo-mono-light.svg
logo-mono-dark.svg
paleta-cores.png            # ou paleta.md descrevendo cores
tipografia.md               # "Inter para UI, Lora para títulos"
manual-marca.pdf            # se já existir
tokens.json                 # se já estiverem prontos
moodboard.pdf
brand-voice.md              # "Confiante, técnico, sem jargão"
```

## Tokens — formato esperado (se já existirem)

```json
{
  "colors": {
    "primary-500": "#0066FF",
    "background": "#FFFFFF",
    "text-primary": "#0A0A0A"
  },
  "typography": {
    "font-sans": "Inter, sans-serif",
    "font-serif": "Lora, serif"
  },
  "spacing": {
    "scale": [4, 8, 12, 16, 24, 32, 48, 64]
  }
}
```

Se você só tem a logo e umas referências de cor — Claude gera o resto seguindo seu input.

## O que NÃO jogar aqui

- Mockups de tela completa (vai em `wireframes/`)
- Inspirações de UI de concorrentes (vai em `referencias/`)
