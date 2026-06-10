---
description: Checklist de deploy para producao
---
Execute o checklist de deploy:

1. [ ] Testes passando (pytest + ng test)
2. [ ] Lint limpo (ruff + eslint)
3. [ ] .env.production configurado
4. [ ] Migrations aplicadas
5. [ ] Docker build sem erros
6. [ ] CORS configurado para dominio de producao
7. [ ] Rate limiting ativo
8. [ ] HTTPS configurado (Certbot)
9. [ ] Headers de seguranca no Nginx
10. [ ] {gateway-pagamento} em modo producao (nao sandbox)
11. [ ] {storage-provider} bucket com policy correta
12. [ ] Backup do banco configurado
13. [ ] Monitoramento/logs funcionando
14. [ ] DNS apontando para VPS
15. [ ] docker compose -f docker-compose.prod.yml up -d

Verifique cada item e reporte o status.
