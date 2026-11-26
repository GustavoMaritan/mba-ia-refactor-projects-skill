---
name: refactor-arch
description: Audita e refatora um projeto backend para o padrão MVC em 3 fases — (1) detecta linguagem, framework, banco e arquitetura; (2) gera relatório de auditoria com anti-patterns classificados por severidade (CRITICAL/HIGH/MEDIUM/LOW) com arquivo e linha exatos e pede confirmação; (3) reestrutura em camadas (config, models, views/routes, controllers, services, middlewares) e valida boot e endpoints. Use quando pedirem /refactor-arch, auditoria de arquitetura, "refatorar para MVC", levantar code smells ou anti-patterns, ou reorganizar as camadas de uma API legada, em qualquer stack (Python, Node.js, Java, PHP, Go, Ruby...). Não use para corrigir um bug isolado, criar feature nova ou só formatar código.
argument-hint: "[--report <caminho-do-relatorio>] [--yes]"
---

# refactor-arch

Você é um arquiteto de software fazendo auditoria e refatoração de um projeto backend legado.
O alvo é o diretório atual (raiz do projeto), a menos que o usuário indique outro.

Trabalhe em **3 fases sequenciais**. Não pule fases e não altere nenhum arquivo antes da confirmação da Fase 2.

Referências (leia sob demanda, na fase indicada):

| Arquivo | Quando ler |
|---|---|
| `references/project-analysis.md` | Fase 1 — heurísticas de linguagem, framework, banco, arquitetura e inventário de endpoints |
| `references/anti-patterns-catalog.md` | Fase 2 — catálogo de anti-patterns com sinais de detecção e severidade (inclui APIs deprecated) |
| `references/audit-report-template.md` | Fase 2 — formato obrigatório do relatório |
| `references/mvc-guidelines.md` | Fase 3 — camadas, responsabilidades e estrutura-alvo por stack |
| `references/refactoring-playbook.md` | Fase 3 — transformações com antes/depois para cada anti-pattern |

Os caminhos são relativos à pasta desta skill (`.claude/skills/refactor-arch/`).

---

## Fase 1 — Análise do projeto

1. Leia `references/project-analysis.md`.
2. Liste os arquivos do projeto ignorando dependências e artefatos (`node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `.git`, `*.db`, lockfiles, a própria pasta `.claude`).
3. Identifique, **com evidência de arquivo** (manifesto, imports, código):
   - linguagem e versão quando houver;
   - framework e versão (manifesto/lockfile);
   - dependências relevantes;
   - banco de dados e tabelas/entidades;
   - domínio da aplicação (pelos nomes de tabelas, rotas e entidades);
   - arquitetura atual (classificação da referência);
   - entry point e como a app sobe (comando, porta);
   - inventário de endpoints (método + rota + handler em `arquivo:linha`).
4. Conte os arquivos-fonte analisados e as linhas de código (`wc -l` ou equivalente).
5. Imprima o resumo **exatamente** neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <deps relevantes>
Domain:        <domínio em uma linha>
Architecture:  <classificação — justificativa curta>
Entry point:   <arquivo> (<comando de boot>, porta <n>)
Source files:  <n> files analyzed | ~<n> lines of code
DB tables:     <tabelas>
Endpoints:     <n> (<lista curta ou "ver inventário">)
================================
```

Siga direto para a Fase 2.

---

## Fase 2 — Auditoria

1. Leia `references/anti-patterns-catalog.md` e `references/audit-report-template.md`.
2. Leia **todos** os arquivos-fonte com numeração de linha. Para cada item do catálogo, procure os sinais de detecção (grep ajuda, mas confirme lendo o trecho).
3. Para cada ocorrência, registre um finding com:
   - ID do catálogo e nome;
   - severidade do catálogo (ajuste só com justificativa explícita no texto);
   - `arquivo:linha` ou `arquivo:inicio-fim` **exatos** — releia o trecho antes de escrever o número;
   - descrição do que está no código (cite o trecho curto), impacto e recomendação apontando a transformação do playbook.
4. Agrupe ocorrências iguais do mesmo anti-pattern em um finding com várias linhas (ex.: SQL injection em 12 funções = 1 finding listando as linhas), mas mantenha anti-patterns diferentes separados. **Todo finding tem bloco completo** (File, Evidence, Description, Impact, Recommendation), inclusive os LOW — não resuma vários findings num bloco só.
5. Verifique explicitamente o uso de **APIs deprecated** (seção própria do catálogo) na versão de linguagem/framework detectada. Se não houver, diga isso no relatório.
6. Ordene os findings: CRITICAL → HIGH → MEDIUM → LOW.
7. Monte o relatório seguindo o template e imprima-o.
8. Salve o relatório em Markdown:
   - no caminho passado em `--report <caminho>`, se houver;
   - senão em `reports/audit-<nome-do-projeto>.md` na raiz do repositório (crie a pasta se preciso).
   O arquivo começa com o bloco da Fase 1 e segue com o relatório completo (o mesmo texto impresso).
   Este é o **único** arquivo que pode ser escrito antes da confirmação. Se a escrita for negada, imprima o relatório e siga para a pergunta, sem tentar outro caminho.
9. Termine a fase com a pergunta, exatamente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**PARE AQUI e espere a resposta do usuário.** Não edite, mova ou apague nenhum arquivo do projeto até receber "y"/"sim"/"yes".
- Resposta negativa: encerre deixando só o relatório.
- Execução não interativa (sem como perguntar): encerre após imprimir o relatório, a menos que `--yes` tenha sido passado.

---

## Fase 3 — Refatoração

1. Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.
2. **Baseline antes de mexer**: suba a app original (comando da Fase 1, porta livre via variável de ambiente/flag quando possível), chame todos os endpoints do inventário com casos de sucesso e de erro e guarde status + corpo. Pare o processo depois. Se a app não subir, registre o motivo e use o inventário estático como referência.
3. Planeje a estrutura-alvo (árvore de diretórios) conforme as guidelines da stack. Projetos já parcialmente organizados: preserve o que está correto e mova só o que viola as camadas.
4. Aplique as transformações do playbook nesta ordem, uma camada por vez:
   1. configuração extraída para settings + variáveis de ambiente (sem segredo hardcoded);
   2. acesso a dados (conexão/ORM, schema e seed isolados);
   3. models (entidades + queries parametrizadas, sem N+1);
   4. services (regras de negócio, transações, efeitos colaterais);
   5. controllers (finos: lê request → chama service → devolve resposta);
   6. views/routes (só mapeamento URL → controller, serialização da resposta);
   7. middlewares (error handler centralizado, auth de rotas administrativas);
   8. composition root / entry point (app factory com injeção de dependências).
5. **Preserve o contrato HTTP**: mesmas rotas, métodos, status codes, chaves e formato dos corpos. Exceções permitidas apenas para correções de segurança (ex.: não devolver senha/segredo, bloquear SQL arbitrário, hash de senha) — liste cada uma no resumo final.
6. Remova os arquivos antigos que foram substituídos (nada de código morto duplicado) e atualize o README do projeto com o novo comando de execução se ele mudar.
7. **Validação** (obrigatória):
   - a app sobe sem erros nem warnings de deprecated;
   - repita as mesmas chamadas da baseline e compare status + corpo, campo a campo, ignorando timestamps;
   - toda diferença precisa ser uma correção documentada; caso contrário, corrija e valide de novo;
   - refaça a varredura do catálogo nos arquivos novos e confirme que os findings CRITICAL/HIGH sumiram.
   - pare os processos que você subiu.
8. Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Findings resolved
<ID — como foi resolvido>   (um por linha; marque os que ficaram pendentes e por quê)

## Intentional behavior changes
<endpoint — antes → depois — motivo>

## Validation
✓/✗ Application boots without errors
✓/✗ All endpoints respond correctly (<n>/<n> iguais à baseline, <n> diferenças documentadas)
✓/✗ Zero CRITICAL/HIGH anti-patterns remaining
================================
```

Seja honesto no ✓/✗: só marque ✓ o que você executou e viu passar.
