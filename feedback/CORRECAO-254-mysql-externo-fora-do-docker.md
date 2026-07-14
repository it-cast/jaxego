# CORRECAO-254 — MySQL migrado pra fora do Docker (host local)

## Data
2026-07-14

## Pedido
"Perfeito, o clonei o banco de dados para meu localhost:3306 user: root
password: admin banco: jaxego. Use ele e remova do docker o banco antigo."

## O que foi feito

### 1. Achado antes de trocar: triggers não foram clonados
O clone trouxe schema + dados, mas **nenhum trigger**. As 3 tabelas
append-only (`audit_log`, `delivery_state_transitions`, `delivery_locations`)
ficariam sem a proteção contra UPDATE/DELETE. Recriei os 6 triggers no banco
novo — e de quebra encontrei que o banco ANTIGO (Docker) já estava faltando
`trg_dst_no_delete` desde sempre (a migration 0006 cria os dois, só o de
UPDATE sobreviveu — não investiguei quando/como sumiu). O banco novo ficou
com o conjunto completo e correto, mais completo que o antigo tinha.

### 2. Config — `.env` e `docker-compose.yml`
- `.env`: `DATABASE_URL` agora aponta pro MySQL externo:
  `mysql+aiomysql://root:admin@host.docker.internal:3306/jaxego?charset=utf8mb4`.
- `infra/docker-compose.yml`:
  - Removido o serviço `mysql` inteiro (imagem, healthcheck, volume).
  - Removido o `depends_on: mysql` de `api`/`worker`.
  - Removido o override `DATABASE_URL` fixo em `environment:` (hardcoded pro
    serviço `mysql:3306`) — agora vem só do `.env`, mesmo padrão que
    `docker-compose.prod.yml` já usava pra "MySQL externo".
  - Adicionado `extra_hosts: host.docker.internal:host-gateway` em `api` e
    `worker` — necessário no Linux (diferente do Docker Desktop
    Mac/Windows, que resolve isso nativamente).
  - Removida a declaração do volume `mysql_data` do compose (o volume
    `jaxego_mysql_data` em si **não foi apagado** — fica como backup até
    você decidir removê-lo).

### 3. Duas travas de rede do MySQL do host (fora do repo, feitas por você)
- `bind-address` em `/etc/mysql/mysql.conf.d/mysqld.cnf`: `127.0.0.1` →
  `127.0.0.1,172.17.0.1` (o segundo é o gateway da bridge padrão do Docker,
  o mesmo IP que `host.docker.internal` resolve de dentro dos containers).
- Grant: `CREATE USER 'root'@'172.21.%.%' ...` — o IP de ORIGEM que o MySQL
  via não era o da bridge (172.17.0.1), era o IP do próprio container na
  rede do projeto (`172.21.0.0/16`, rede `jaxego_default`) — por isso o
  grant precisou ser por sub-rede com wildcard, não IP fixo (o IP do
  container muda a cada recriação).

## Removido
- Container `jaxego-mysql-1` — parado e removido (`docker compose up -d
  --remove-orphans`, órfão porque saiu do compose).
- Volume `jaxego_mysql_data` — **mantido intacto**, só desreferenciado do
  compose. Não apaguei os dados; se quiser liberar espaço, é
  `docker volume rm jaxego_mysql_data` manual quando tiver certeza que não
  precisa mais dele.

## Validado
- `curl localhost:8000/health` → `{"status":"ok","db":"ok","redis":"ok"}`.
- Worker reiniciado, crons rodando sem erro de conexão contra o banco novo
  (`lifecycle.absent_timeout`, `lifecycle.finalize_deliveries`, etc.).
- Confirmado antes da troca: banco novo com o mesmo `alembic_version`
  (0048), mesma contagem de linhas em `delivery_locations`, mesmo estado da
  entrega 120 (CANCELADA) que o antigo — clone estava consistente.

## Observação (não é bug novo)
`docker compose ps` mostra o worker como "unhealthy" — é cosmético,
pré-existente: o `HEALTHCHECK` do Dockerfile testa `curl localhost:8000`,
mas o worker não sobe servidor HTTP (só roda `arq`). Não tem relação com o
banco; sempre foi assim.

## Tech debt / pontos em aberto
- `trg_dst_no_delete` sumido no banco antigo (Docker, agora desativado) —
  não investiguei a causa raiz, mas o banco novo já nasceu correto.
- Se algum dia rodar em outra máquina/rede Docker, o IP `172.21.%.%` do
  grant e o `172.17.0.1` do bind-address são específicos desta instalação —
  não são portáveis pra outro host sem ajuste.
