# Framework Tests

Smoke tests do próprio GSD Framework. Valida que os gates funcionam como prometido — não a qualidade do que o dev produz, mas a **mecânica do framework** em si.

## O que isto testa

| Teste | Pergunta que responde |
|-------|----------------------|
| `test_plan_checker.sh` | Plano que ignora skill obrigatória é bloqueado? |
| `test_reconcile.sh` | Reconcile detecta divergência entre PLAN.md e código? |
| `test_gate_bypasses.sh` | `--skip-*` sem `--reason` é rejeitado? |
| `test_structure.sh` | Estrutura de `.claude/`, `.planning/`, `specs/` está íntegra? |

## Como rodar

```bash
cd tests/framework
bash run-all.sh
```

Output esperado:
```
=== GSD Framework smoke tests ===
✓ test_structure (7 checks)
✓ test_plan_checker (4 fixtures)
✓ test_reconcile (2 scenarios)
✓ test_gate_bypasses (3 cases)

4/4 suites passed
```

## Fixtures

```
fixtures/
├── good-plan/            # PLAN.md com skills corretas — esperado PASS
├── bad-plan-no-skills/   # PLAN.md sem seção "Skills Consultadas" — esperado BLOCK
├── bad-plan-bypass-no-reason/  # Usa --skip-gate-3 sem --reason — esperado BLOCK
└── reconcile-divergence/ # PLAN.md diz X, código não tem X — esperado DIVERGENCE
```

Cada fixture tem um `expected.txt` com o output esperado do checker.

## Limitações

Estes são **smoke tests**. Cobrem o caminho feliz + 3-4 cenários de erro por suite. Não são coverage completo — o valor é "framework não está completamente quebrado".

Para chegar a coverage real:
- Integração com CI (rodar em cada PR do framework)
- Fixtures de todos os gates (1-7)
- Mutation testing (alterar 1 coisa no checker, confirmar que algum teste falha)
- Property-based testing (gerar planos aleatórios, invariantes)

São todos pendentes da v0.3.

## Como adicionar teste

1. Criar fixture em `fixtures/<nome>/`
2. Script de asserção `test_<funcionalidade>.sh`
3. Adicionar ao `run-all.sh`
4. Se testa comportamento novo, documentar aqui
