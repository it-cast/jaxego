# CORRECAO-232 — Tela de login identifica o perfil de acesso

## Data
2026-07-10

## Contexto
A LoginPage compartilhada é usada pelas 4 rotas web (/entrar, /equipe/entrar,
/admin/entrar, /plataforma/entrar) com o mesmo HTML — só o endpoint mudava.

## Mudanças (packages/shared/src/shared/features/auth/login.page.*)
- `profile` exposto ao template + mapas `profileTitle`/`profileSubtitle`:
  - loja: "Bem-vindo de volta!" / "Faça login para acessar sua loja"
  - equipe: "Painel da Equipe" / "Acesso do responsável da equipe"
  - admin: "Admin da Cidade" / "Acesso do administrador da cidade"
  - plataforma: "Admin da Plataforma" / "Acesso restrito · verificação em duas etapas"
- CTA de cadastro agora só aparece onde faz sentido: "Cadastrar minha loja"
  no perfil loja, "Cadastre-se agora" no entregador; equipe/admin/plataforma
  não têm CTA (contas criadas pelo admin).
