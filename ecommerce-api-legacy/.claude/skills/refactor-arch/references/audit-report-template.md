# Template do relatório de auditoria

Use exatamente esta estrutura (Markdown). O mesmo texto é impresso no terminal e salvo no arquivo.

Regras:
- Findings ordenados **CRITICAL → HIGH → MEDIUM → LOW**; dentro da mesma severidade, pelo ID do catálogo.
- Toda localização no formato `arquivo:linha` ou `arquivo:inicio-fim`, caminho relativo à raiz do projeto. Várias ocorrências: separe por vírgula.
- O resumo precisa bater com a contagem dos findings.
- "Deprecated APIs" sempre aparece: lista as ocorrências ou diz "nenhuma encontrada para <versões>".

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta>
Stack:   <linguagem> + <framework versão>
Files:   <n> analyzed | ~<n> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP02 | SQL Injection | models.py:28, models.py:47-50 |
| ... |

## Findings

### 1. [CRITICAL] AP02 — SQL Injection
File: models.py:28, models.py:47-50, models.py:109-111
Evidence: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`
Description: <o que o código faz de errado, em 1–3 frases>
Impact: <consequência concreta>
Recommendation: <o que fazer> (playbook T2)

### 2. [HIGH] ...

## Deprecated APIs
| API | Location | Modern replacement |
|---|---|---|
| `datetime.utcnow()` | models/task.py:15 | `datetime.now(timezone.utc)` |

## Endpoint inventory (contrato a preservar)
| Method | Route | Handler |
|---|---|---|
| GET | /produtos | controllers.py:5 |

Total: <n> findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
