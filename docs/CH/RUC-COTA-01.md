# RUC/1.0 — CotaCLI — COTA-01 (Tentativa 3 — Correção AUD-04 e Reconciliação AUD-03)

> Relatório Universal C.H. em conformidade com o protocolo CHDevFlow. Registra as evidências verificáveis da implementação técnica e das rodadas de correção da fatia COTA-01. Não constitui homologação de PO nem autorização de merge.

**Cabeçalho:** missão/Issue: [#1](https://github.com/hallanbrito/CotaCLI/issues/1) — COTA-01: `cotacli doctor` offline e somente leitura (CH-2) | executor declarado: AGY / Antigravity (Gemini 3.8 Flash) | coordenação e auditoria documental: ChatGPT | PO: Hallan de Sousa Brito | autonomia e prova: CH-2 autorizado na Daily C.H. de 30/10/2026 (Issue #1) | ambiente: Linux (CachyOS x86_64; Python 3.14.8 local / CI GitHub Actions Python 3.10, 3.12, 3.13) | fonte: LIVE_GITHUB (Issue #1, PR #2, GitHub Actions) + LOCAL_REPO | timestamp: 2026-10-30T14:25:00Z | baseline SHA: `522405c5d389704edf69724fc78a03a02098daee` | branch: `agy/cota-01-doctor-offline` | PR: [#2](https://github.com/hallanbrito/CotaCLI/pull/2) | resultado técnico: APROVADO_TECNICAMENTE.

> **Nota de Rastreabilidade (AUD-03):** Para evitar o ciclo paradoxal de autorreferência (onde versionar o SHA e a CI de um commit alteraria o próprio commit gerando novo SHA), o RUC versionado registra os commits e execuções de CI efetivamente confirmados até a edição deste arquivo. O HEAD SHA gerado por este commit e a execução correspondente da CI são informados formalmente no comentário subsequente do Pull Request.

---

## 1. Identificação

| Campo | Valor |
|---|---|
| Repositório | `hallanbrito/CotaCLI` |
| Issue de referência | [#1 — COTA-01 — cotacli doctor offline e somente leitura (CH-2)](https://github.com/hallanbrito/CotaCLI/issues/1) |
| Baseline commit | `522405c5d389704edf69724fc78a03a02098daee` (`origin/main`) |
| Branch de trabalho | `agy/cota-01-doctor-offline` |
| Target branch do PR | `main` |
| Pull Request | [Draft PR #2](https://github.com/hallanbrito/CotaCLI/pull/2) |
| HEAD auditado na Revisão 1 | `964f6df861e383dee97582ac4c32e9f74bbd146c` (validado pela CI #41059158514) |
| HEAD auditado na Revisão 2 | `477a317f85637df3135ce40528c096c36d090b50` (validado pela CI #41068111823) |
| Parecer da Auditoria (Revisão 2) | [Comentário #6524839307](https://github.com/hallanbrito/CotaCLI/pull/2#issuecomment-6524839307) — AUD-01 e AUD-02 resolvidos; AUD-03 parcial/reconciliado; AUD-04 apontado |
| Custo financeiro adicional | R$ 0,00 |

---

## 2. Resumo executivo

Rodada final de correções técnicas aplicada com sucesso na branch `agy/cota-01-doctor-offline`:
- **AUD-04**: Corrigida a função `check_cache_metadata` para encapsular `path.exists()` dentro do bloco protegido `try/except (PermissionError, OSError)`. Sob diretórios inacessíveis ou sem permissão de travessia, o comando não gera traceback e converte a falha em `ALERTA` no bloco de cache, permitindo que o `doctor()` conclua seu fluxo de forma resiliente, reportando o resumo final e código de saída `1` em caso de diretório essencial (`CONFIG_DIR` / `CACHE_DIR`) inacessível. Também foram protegidas checagens de existência de arquivos de widget em `check_plasma_environment` e na seção de próximos passos do `doctor()`.
- **AUD-03**: Reconciliação documental e factual: o RUC registra o histórico de commits e execuções de CI auditadas, evitando autorreferência de commits não gerados; a entrega externa no PR reportará o HEAD SHA e o link da CI final disparada após este push.
- **Suíte de Testes**: Ampliada de 23 para 26 testes unitários com aprovação integral (100% PASS), incluindo testes determinísticos de `PermissionError` em `exists()` e `stat()`, e teste de integração do `doctor()` com diretórios inacessíveis.

Custo adicional R$ 0,00. Nenhum merge, deploy ou escrita na branch `main`.

---

## 3. Consultas e atividades realizadas

| ID | Ação | Escopo / Resultado |
|---|---|---|
| A01 | Análise da revisão 2 da auditoria independente | Identificados itens AUD-04 (proteção de `path.exists()` contra `PermissionError`) e AUD-03 (reconciliação do RUC e protocolo contra autorreferência). |
| A02 | Refatoração de `check_cache_metadata` em `cotacli.py` | Movida a chamada `path.exists()` para dentro do bloco `try ... except (PermissionError, OSError)`, eliminando riscos de traceback sob restrições de permissão. |
| A03 | Blindagem adicional de chamadas de filesystem | Protegidas checagens de `widget_dir.exists()` em `check_plasma_environment` e `doctor()` contra exceções de acesso em diretórios pessoais restritos. |
| A04 | Implementação de novos testes de regressão | Adicionados 3 novos testes em `tests/test_cotacli_doctor.py` cobrindo `PermissionError` em `path.exists()`, `PermissionError` em `path.stat()` e execução integrada do `doctor()` em árvore com permissões `0o000`. |
| A05 | Validação local completa | 26 testes aprovados via `unittest discover`, compilação sem warnings, validação de script shell e metadados JSON. |
| A06 | Reconciliação documental no RUC | Histórico completo de runs e commits organizado sem contradições temporais. |

---

## 4. Evidências verificáveis

| ID | Classe | Fonte / Referência | Fato observado e limite |
|---|---|---|---|
| E01 | OBSERVADO | `git rev-parse origin/main` | Baseline confirmada em `522405c5d389704edf69724fc78a03a02098daee`. |
| E02 | OBSERVADO | `python3 -m unittest discover -s tests -v` | 26 testes aprovados (100% PASS), sendo 19 testes do diagnóstico e 7 do widget. |
| E03 | OBSERVADO | `python3 -m compileall -q cotacli.py tests` | Compilação de bytecode sem erros sintáticos. |
| E04 | OBSERVADO | `bash -n install-widget.sh` | Validação de sintaxe do script de instalação aprovada sem erros. |
| E05 | OBSERVADO | `python3 -m json.tool cotacli-widget/metadata.json` | JSON do metadado do widget validado com sucesso. |
| E06 | OBSERVADO | `test_check_cache_metadata_handles_permission_error_on_exists` | Teste unitário confirmando que `PermissionError` em `path.exists()` retorna `ALERTA` sem propagar exceção (AUD-04). |
| E07 | OBSERVADO | `test_doctor_handles_inaccessible_cache_and_config_without_traceback` | Teste de integração confirmando que `doctor()` exibe `[FALHA]`, resumo e retorna código `1` sem traceback sob raiz `chmod 000` (AUD-04). |
| E08 | OBSERVADO | `test_doctor_strictly_prohibits_quota_calls_and_side_effects` | Confirmado por mock que não há subprocessos de provedores, rede, leitura de cota remota ou escrita de arquivos. |
| E09 | DECLARADO | Protocolo de execução | Custo financeiro adicional R$ 0,00; nenhuma chamada a provedores ou serviços pagos. |
| E10 | OBSERVADO | `git status` | Execução restrita à branch isolada `agy/cota-01-doctor-offline`. Árvore de trabalho limpa. |

### Histórico Completo de Execuções da CI (GitHub Actions)

| Run ID | Evento | Commit Ref | Status | Resultado / Causa |
|---|---|---|---|---|
| [41058245828](https://github.com/hallanbrito/CotaCLI/actions/runs/41058245828) | `push` | `51337103af0c11eca3c6b3055ac76156f939f004` | completed | **failure**: teste apontando para `/root` gerou `PermissionError` no runner Ubuntu. |
| [41058276874](https://github.com/hallanbrito/CotaCLI/actions/runs/41058276874) | `pull_request` | `51337103af0c11eca3c6b3055ac76156f939f004` | completed | **failure**: mesma causa do push acima. |
| [41058476774](https://github.com/hallanbrito/CotaCLI/actions/runs/41058476774) | `push` | `f918f8509159b3b873d3c1fa379c5deaba6ee58b` | completed | **success**: captura de `PermissionError` e isolamento do teste em `tempfile`. |
| [41058488033](https://github.com/hallanbrito/CotaCLI/actions/runs/41058488033) | `pull_request` | `f918f8509159b3b873d3c1fa379c5deaba6ee58b` | completed | **success**: 16 testes passando nas 3 versões de Python. |
| [41059150577](https://github.com/hallanbrito/CotaCLI/actions/runs/41059150577) | `push` | `964f6df861e383dee97582ac4c32e9f74bbd146c` | completed | **success**: documentação inicial do RUC. |
| [41059158514](https://github.com/hallanbrito/CotaCLI/actions/runs/41059158514) | `pull_request` | `964f6df861e383dee97582ac4c32e9f74bbd146c` | completed | **success**: HEAD auditado pelo ChatGPT em CH-AUD-COTA-01 (Revisão 1). |
| [41067837263](https://github.com/hallanbrito/CotaCLI/actions/runs/41067837263) | `push` | `3558cd1eccc5125f192dc1438fb591457af2dd07` | completed | **success**: correções funcionais AUD-01 e AUD-02 com 23 testes. |
| [41067845608](https://github.com/hallanbrito/CotaCLI/actions/runs/41067845608) | `pull_request` | `3558cd1eccc5125f192dc1438fb591457af2dd07` | completed | **success**: 23 testes passando em Python 3.10, 3.12 e 3.13. |
| [41068101102](https://github.com/hallanbrito/CotaCLI/actions/runs/41068101102) | `push` | `477a317f85637df3135ce40528c096c36d090b50` | completed | **success**: RUC Tentativa 2 versionado. |
| [41068111823](https://github.com/hallanbrito/CotaCLI/actions/runs/41068111823) | `pull_request` | `477a317f85637df3135ce40528c096c36d090b50` | completed | **success**: HEAD auditado pelo ChatGPT em CH-AUD-COTA-01 (Revisão 2). |

---

## 5. Verificações e resultados

| Teste | Critério de Aceite | Resultado | Evidência |
|---|---|---|---|
| T01 | `cotacli doctor` funciona offline, sem consumo de tokens e sem mutações | PASSOU | Teste unitário e verificação local sem rede nem mutação de arquivos (E08). |
| T02 | Diagnóstico compreensível de ferramentas/config/cache/ambiente, inclusive sem KDE | PASSOU | Exibição estruturada com status OK / ALERTA / INDISPONÍVEL / FALHA / INFO e próximos passos didáticos em PT-BR (E02). |
| T03 | Ausência opcional diferenciada de falha essencial; exit code coerente | PASSOU | Falta de CLIs opcionais gera alerta e exit code 0; falha em runtime/permissão essencial gera exit code 1 (E02, E07). |
| T04 | Nenhuma regressão do widget, snapshot, refresh e comandos prévios | PASSOU | 7 testes do contrato do widget continuam passando (E02). |
| T05 | Exigência de permissão de busca/travessia POSIX (AUD-01) | PASSOU | Diretório existente sem `X_OK` gera falha explícita no diagnóstico (E02). |
| T06 | Tratamento robusto de ancestrais não criados e ancestrais que são arquivo (AUD-02) | PASSOU | Caminhos sem pais criados são validados pelo primeiro ancestral existente; ancestrais que são arquivo são rejeitados (E02). |
| T07 | Resiliência contra PermissionError em metadados de cache (AUD-04) | PASSOU | `check_cache_metadata` e `doctor()` capturam `PermissionError` em `path.exists()` e `stat()`, convertendo em ALERTA e finalizando com código 1 sem traceback (E06, E07). |
| T08 | Reconciliação documental e rastreabilidade (AUD-03) | PASSOU | RUC registra snapshot factual de runs e SHAs confirmados sem autorreferência impossível. |
| T09 | Draft PR + RUC verificável; nenhum merge | PASSOU | Draft PR #2 mantido em branch isolada `agy/cota-01-doctor-offline`, sem merge na `main` (E10). |

---

## 6. Riscos e bloqueios

1. **Permissões de filesystem:** O `doctor` requer que os diretórios XDG do usuário (`~/.config` e `~/.cache`) possuam permissão de leitura, escrita e travessia (`rwx`) ou que o primeiro ancestral existente seja gravável e trafegável. Em ambientes restritos/sandboxed, o comando reporta a falha detalhada e orienta a correção com código de saída 1, de forma estritamente controlada e sem traceback.
2. **Ambientes com montagens de arquivo em caminhos XDG:** Se uma configuração XDG apontar para um arquivo regular em vez de diretório, o diagnóstico identifica o erro estrutural e informa que o caminho não é um diretório.

---

## 7. Alterações realizadas

- **Novos arquivos:**
  - `tests/test_cotacli_doctor.py` (expandido para 19 testes de diagnóstico; 26 testes no total do projeto)
  - `docs/CH/RUC-COTA-01.md`
- **Arquivos modificados:**
  - `cotacli.py` (proteção de `check_cache_metadata`, `check_plasma_environment` e `doctor` contra `PermissionError` em `exists()`)
  - `README.md` (documentação do `cotacli doctor` com exemplo limpo)
  - `docs/cli.md` (tabela de comandos atualizada)

---

## 8. Recomendação técnica

**APROVADO_TECNICAMENTE** — Todos os apontamentos da auditoria independente (AUD-01, AUD-02, AUD-03 e AUD-04) foram plenamente sanados, com proteção contra tracebacks, testes negativos determinísticos, rastreabilidade documental consolidada e integridade estrita do protocolo CH-2. O Draft PR #2 está pronto para auditoria independente final pelo ChatGPT.

---

## 9. Decisão necessária do PO

**PENDENTE** — Aguardando parecer final da auditoria independente do ChatGPT e subsequente decisão de homologação e merge pelo Product Owner (Hallan).
