---
description: Revisar codigo do projeto para bugs, seguranca e boas praticas
---
Faca uma revisao completa do codigo em: $ARGUMENTS

Verifique:
1. **Seguranca**: SQL injection, XSS, secrets hardcoded, validacao de input
2. **Performance**: queries N+1, loops desnecessarios, falta de cache
3. **Erros**: try/catch faltando, erros silenciosos, HTTPException correto
4. **Tipagem**: type hints faltando (Python), any usado (TypeScript)
5. **Convencoes**: segue o CLAUDE.md? Pydantic para I/O? Standalone components?
6. **Testes**: tem teste? Cobre edge cases?

Para cada problema:
- Arquivo e linha
- Severidade: CRITICO / ALTO / MEDIO / BAIXO
- Codigo problema
- Codigo corrigido
- Por que e melhor

Termine com resumo: X criticos, Y altos, Z medios.
