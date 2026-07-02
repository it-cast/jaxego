# CORRECAO-189 — Volume mount Docker para desenvolvimento

## Problema
`docker compose up -d` recria o container a partir da imagem original, descartando todos os arquivos copiados via `docker compose cp`. Toda vez que o container era recriado (novo env var, nova config), os patches eram perdidos e os erros voltavam.

## Solução
Adicionado volume mount em `infra/docker-compose.yml` para os serviços `api` e `worker`:

```yaml
volumes:
  - ../apps/api/app:/app/app
```

O diretório local `apps/api/app/` é montado sobre `/app/app` no container. Qualquer alteração no código fonte é refletida imediatamente — sem rebuild, sem `docker compose cp`.

## Por que funciona
- O Dockerfile copia `apps/api/` para `/app/` no container (WORKDIR `/app`), então o código Python fica em `/app/app/`
- O volume mount sobrescreve esse diretório com o diretório local em tempo de execução
- `PYTHONDONTWRITEBYTECODE=1` está ativo na imagem, então não há conflito de permissão de escrita de `.pyc` entre o usuário não-root do container e o host

## Atenção
- `alembic/` não está no mount — migrations ainda precisam de `docker compose cp` ou rebuild para aparecer no container (ou mount adicional se necessário)
- Para produção, remover os volumes mounts ou usar imagem sem mount
