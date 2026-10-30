# RUC/1.0 — CotaCLI — COTA-01 (Tentativa 2 — Correções CH-AUD-COTA-01)

> Relatório Universal C.H. em conformidade com o protocolo CHDevFlow. Registra as evidências verificáveis da implementação técnica e da rodada de correções da fatia COTA-01. Não constitui homologação de PO nem autorização de merge.

**Cabeçalho:** missão/Issue: [#1](https://github.com/hallanbrito/CotaCLI/issues/1) — COTA-01: `cotacli doctor` offline e somente leitura (CH-2) | executor declarado: AGY / Antigravity (Gemini 3.8 Flash) | coordenação e auditoria documental: ChatGPT | PO: Hallan de Sousa Brito | autonomia e prova: CH-2 autorizado na Daily C.H. de 30/10/2026 (Issue #1) | ambiente: Linux (CachyOS x86_64; Python 3.14.8 local / CI GitHub Actions Python 3.10, 3.12, 3.13) | fonte: LIVE_GITHUB (Issue #1, PR #2, GitHub Actions) + LOCAL_REPO | timestamp: 2026-10-30T14:00:00Z | run_id: 41067845608 | baseline SHA: `522405c5d389704edf69724fc78a03a02098daee` | branch: `agy/cota-01-doctor-offline` | PR: [#2](https://github.com/hallanbrito/CotaCLI/pull/2) | resultado técnico: APROVADO_TECNICAMENTE.

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
| HEAD auditado na Tentativa 1 | `964f6df861e383dee97582ac4c32e9f74bbd146c` (validado pela CI #41059158514) |
| CI Run ID mais recente (Tentativa 2) | [41067845608](https://github.com/hallanbrito/CotaCLI/actions/runs/41067845608) (Checks passing em Python 3.10, 3.12, 3.13) |
| Parecer da Auditoria CH-AUD-COTA-01 | [Comentário #6523536117](https://github.com/hallanbrito/CotaCLI/pull/2#issuecomment-6523536117) — AJUSTES PONTUAIS NECESSÁRIOS (AUD-01, AUD-02, AUD-03) |
| Custo financeiro adicional | R$ 0,00 |

---

## 2. Resumo executivo

Rodada de correções da auditoria independente CH-AUD-COTA-01 aplicada com sucesso na branch `agy/cota-01-doctor-offline`. Foram solucionados os apontamentos:
- **AUD-01**: Inclusão explícita de `os.X_OK` na checagem de permissões para diretórios existentes (`R_OK | W_OK | X_OK`), garantindo permissão POSIX de busca/travessia necessária para manipulação de arquivos.
- **AUD-02**: Para caminhos ainda não criados, o algoritmo percorre ancestrais até encontrar o primeiro existente, confirmando que é diretório (`is_dir()`) e possui permissões de escrita/travessia (`W_OK | X_OK`). Bloqueia e rejeita a criação quando o ancestral existente for um arquivo regular.
- **AUD-03**: Reconciliação completa do histórico de CI, rastreabilidade dos SHAs dos commits (incluindo o HEAD exato `964f6df861e383dee97582ac4c32e9f74bbd146c` da Tentativa 1 e o novo HEAD da Tentativa 2) e separação estrita de evidências OBSERVADO vs DECLARADO.

Suíte expandida de 16 para 23 testes unitários com 100% de aprovação local e na matriz remota da CI (Python 3.10, 3.12, 3.13). Custo adicional R$ 0,00. Nenhum merge, deploy ou escrita na branch `main`.

---

## 3. Consultas e atividades realizadas

| ID | Ação | Escopo / Resultado |
|---|---|---|
| A01 | Leitura integral da auditoria CH-AUD-COTA-01 | Identificados três itens de correção: AUD-01 (travessia X_OK), AUD-02 (ancestrais e parent como arquivo) e AUD-03 (rastreabilidade de SHAs e histórico da CI). |
| A02 | Refatoração de `check_dir_accessible` em `cotacli.py` | Exigência de `os.R_OK | os.W_OK | os.X_OK` para diretórios existentes. Travessia de `resolved.parents` para caminhos não criados com validação de `is_dir()` e `W_OK | X_OK`. |
| A03 | Expansão de testes em `tests/test_cotacli_doctor.py` | Adicionados 7 novos testes unitários cobrindo ausência de `X_OK` (rw- sem x), ausência de `W_OK`, ausência de `R_OK`, ancestrais intermediários faltantes, ancestral existente que é arquivo regular, alvo direto como arquivo e ancestral sem escrita. |
| A04 | Execução dos testes e validação da CI | 23 testes executados e aprovados localmente e na CI remota do GitHub Actions na matriz Python 3.10, 3.12 e 3.13. |
| A05 | Documentação e histórico factual no RUC | Registro transparente de todas as execuções da CI, do erro inicial corrigido na Tentativa 1 e dos SHAs auditados. |

---

## 4. Evidências verificáveis

| ID | Classe | Fonte / Referência | Fato observado e limite |
|---|---|---|---|
| E01 | OBSERVADO | `git rev-parse origin/main` | Baseline confirmada em `522405c5d389704edf69724fc78a03a02098daee`. |
| E02 | OBSERVADO | `python3 -m unittest discover -s tests -v` | 23 testes aprovados (100% PASS), sendo 16 testes de diagnóstico/doctor e 7 testes do widget. |
| E03 | OBSERVADO | `python3 -m compileall -q cotacli.py tests` | Compilação de bytecode sem erros sintáticos. |
| E04 | OBSERVADO | `bash -n install-widget.sh` | Validação de sintaxe do script de instalação aprovada sem erros. |
| E05 | OBSERVADO | `python3 -m json.tool cotacli-widget/metadata.json` | JSON do metadado do widget validado com sucesso. |
| E06 | OBSERVADO | GitHub Actions Runs (Histórico Completo) | Detalhado na tabela abaixo, com links e causas reais. |
| E07 | OBSERVADO | `test_doctor_strictly_prohibits_quota_calls_and_side_effects` | Confirmado por mock que `rpc_codex_rate_limits`, `read_agy_cli`, `get_codex`, `get_agy`, `snapshot`, `discover_cli_paths`, `save_json` e subprocessos não são invocados. |
| E08 | OBSERVADO | `test_doctor_fails_when_directory_lacks_traversal_permission` | Diretório `0o600` (rw-) sem travessia é rejeitado pelo diagnóstico gerando código 1 (AUD-01). |
| E09 | OBSERVADO | `test_check_dir_accessible_fails_when_ancestor_is_a_file` | Caminho cujo ancestral é arquivo regular é rejeitado sem reportar "pronto para criação" (AUD-02). |
| E10 | DECLARADO | Protocolo de execução | Custo financeiro adicional R$ 0,00; nenhuma chamada a provedores ou serviços pagos. |
| E11 | OBSERVADO | `git status` | Execução restrita à branch isolada `agy/cota-01-doctor-offline`. Árvore de trabalho limpa. |

### Histórico Factual de Execuções da CI no GitHub Actions

| Run ID | Evento | Commit Ref | Status | Resultado / Causa |
|---|---|---|---|---|
| [41058245828](https://github.com/hallanbrito/CotaCLI/actions/runs/41058245828) | `push` | `51337103af0c11eca3c6b3055ac76156f939f004` | completed | **failure**: teste apontando para `/root` gerou `PermissionError` no runner Ubuntu. |
| [41058276874](https://github.com/hallanbrito/CotaCLI/actions/runs/41058276874) | `pull_request` | `51337103af0c11eca3c6b3055ac76156f939f004` | completed | **failure**: mesma causa do push acima. |
| [41058476774](https://github.com/hallanbrito/CotaCLI/actions/runs/41058476774) | `push` | `f918f8509159b3b873d3c1fa379c5deaba6ee58b` | completed | **success**: captura de `PermissionError` e isolamento do teste em `tempfile`. |
| [41058488033](https://github.com/hallanbrito/CotaCLI/actions/runs/41058488033) | `pull_request` | `f918f8509159b3b873d3c1fa379c5deaba6ee58b` | completed | **success**: 16 testes passando nas 3 versões de Python. |
| [41059150577](https://github.com/hallanbrito/CotaCLI/actions/runs/41059150577) | `push` | `964f6df861e383dee97582ac4c32e9f74bbd146c` | completed | **success**: documentação inicial do RUC. |
| [41059158514](https://github.com/hallanbrito/CotaCLI/actions/runs/41059158514) | `pull_request` | `964f6df861e383dee97582ac4c32e9f74bbd146c` | completed | **success**: HEAD auditado pelo ChatGPT em CH-AUD-COTA-01. |
| [41067837263](https://github.com/hallanbrito/CotaCLI/actions/runs/41067837263) | `push` | `3558cd1eccc5125f192dc1438fb591457af2dd07` | completed | **success**: correções funcionais AUD-01 e AUD-02 com 23 testes. |
| [41067845608](https://github.com/hallanbrito/CotaCLI/actions/runs/41067845608) | `pull_request` | `3558cd1eccc5125f192dc1438fb591457af2dd07` | completed | **success**: 23 testes passando em Python 3.10, 3.12 e 3.13. |

---

## 5. Verificações e resultados

| Teste | Critério de Aceite | Resultado | Evidência |
|---|---|---|---|
| T01 | `cotacli doctor` funciona offline, sem consumo de tokens e sem mutações | PASSOU | Teste unitário e verificação local sem rede nem mutação de arquivos (E07). |
| T02 | Diagnóstico compreensível de ferramentas/config/cache/ambiente, inclusive sem KDE | PASSOU | Exibição estruturada com status OK / ALERTA / INDISPONÍVEL / FALHA / INFO e próximos passos didáticos em PT-BR (E02). |
| T03 | Ausência opcional diferenciada de falha essencial; exit code coerente | PASSOU | Falta de CLIs opcionais gera alerta e exit code 0; falha em runtime/permissão essencial gera exit code 1 (E02). |
| T04 | Nenhuma regressão do widget, snapshot, refresh e comandos prévios | PASSOU | 7 testes do contrato do widget continuam passando (E02). |
| T05 | Exigência de permissão de busca/travessia POSIX (AUD-01) | PASSOU | Diretório existente sem `X_OK` gera falha explícita no diagnóstico (E08). |
| T06 | Tratamento robusto de ancestrais não criados e ancestrais que são arquivo (AUD-02) | PASSOU | Caminhos sem pais criados são validados pelo primeiro ancestral existente; ancestrais que são arquivo são rejeitados (E09). |
| T07 | Testes offline e matriz de CI concluídos | PASSOU | 23 testes locais aprovados e CI do GitHub Actions ([run 41067845608](https://github.com/hallanbrito/CotaCLI/actions/runs/41067845608)) verde em 3.10, 3.12 e 3.13 (E02, E06). |
| T08 | Draft PR + RUC verificável; nenhum merge | PASSOU | Draft PR #2 mantido em branch isolada `agy/cota-01-doctor-offline`, sem merge na `main` (E11). |

---

## 6. Riscos e bloqueios

1. **Permissões de filesystem:** O `doctor` requer que os diretórios XDG do usuário (`~/.config` e `~/.cache`) possuam permissão de leitura, escrita e travessia (`rwx`) ou que o primeiro ancestral existente seja gravável e trafegável. Em ambientes restritos/sandboxed, o comando reporta a falha detalhada e orienta a correção sem interromper o interpretador abruptamente.
2. **Ambientes com montagens de arquivo em caminhos XDG:** Se uma configuração XDG apontar para um arquivo regular em vez de diretório, o diagnóstico identifica o erro estrutural e informa que o caminho não é um diretório.

---

## 7. Alterações realizadas

- **Novos arquivos:**
  - `tests/test_cotacli_doctor.py` (expandido para 16 testes de diagnóstico)
  - `docs/CH/RUC-COTA-01.md`
- **Arquivos modificados:**
  - `cotacli.py` (refatoração de `check_dir_accessible` com validação de `X_OK` e busca de ancestrais)
  - `README.md` (documentação do `cotacli doctor` com exemplo limpo)
  - `docs/cli.md` (tabela de comandos atualizada)

---

## 8. Recomendação técnica

**APROVADO_TECNICAMENTE** — Todas as correções solicitadas na auditoria independente CH-AUD-COTA-01 (AUD-01, AUD-02 e AUD-03) foram implementadas com rigor e validadas por testes unitários e CI remota verde na matriz completa. O Draft PR #2 está pronto para reavaliação independente pelo auditor ChatGPT.

---

## 9. Decisão necessária do PO

**PENDENTE** — Aguardando reavaliação e parecer final da auditoria independente do ChatGPT e subsequente decisão de homologação e merge pelo Product Owner (Hallan).
