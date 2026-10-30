# RUC/1.0 — CotaCLI — COTA-01 (Tentativa 1)

> Relatório Universal C.H. em conformidade com o protocolo CHDevFlow. Registra as evidências verificáveis da implementação técnica da fatia COTA-01. Não constitui homologação de PO nem autorização de merge.

**Cabeçalho:** missão/Issue: [#1](https://github.com/hallanbrito/CotaCLI/issues/1) — COTA-01: `cotacli doctor` offline e somente leitura (CH-2) | executor declarado: AGY / Antigravity (Gemini 3.8 Flash) | coordenação e auditoria documental: ChatGPT | PO: Hallan de Sousa Brito | autonomia e prova: CH-2 autorizado na Daily C.H. de 30/10/2026 (Issue #1) | ambiente: Linux (CachyOS x86_64; Python 3.14.8 / CI GitHub Actions Python 3.10, 3.12, 3.13) | fonte: LIVE_GITHUB (Issue #1, PR #2, GitHub Actions) + LOCAL_REPO | timestamp: 2026-10-30T12:55:00Z | run_id: 41058488033 | baseline SHA: `522405c5d389704edf69724fc78a03a02098daee` | branch: `agy/cota-01-doctor-offline` | PR: [#2](https://github.com/hallanbrito/CotaCLI/pull/2) | resultado técnico: APROVADO_TECNICAMENTE.

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
| CI Run ID | `41058488033` (Checks passing em Python 3.10, 3.12, 3.13) |
| Custo financeiro adicional | R$ 0,00 |

---

## 2. Resumo executivo

Implementação da fatia COTA-01 com a criação do comando `cotacli doctor` para diagnóstico local, estritamente offline e somente leitura. O comando inspeciona versão mínima do Python (>= 3.10), acessibilidade e permissões dos diretórios XDG (`CONFIG_DIR` e `CACHE_DIR`), presença opcional das CLIs de IA (Codex, AGY e Claude Code) sem inferir cota pela mera existência do binário, integridade e idade do cache por metadados (`stat`, `mtime`), e ferramentas do KDE Plasma 6 sem exigir ambiente gráfico para uso em terminal. Adicionados 9 testes unitários em `tests/test_cotacli_doctor.py`, totalizando 16 testes aprovados com 100% de sucesso localmente e na CI do GitHub Actions. Custo adicional R$ 0,00. Nenhum merge, deploy ou alteração direta na branch `main`.

---

## 3. Consultas e atividades realizadas

| ID | Ação | Escopo / Resultado |
|---|---|---|
| A01 | Inspecionar código, CLI, testes e documentação (CH-0) | Confirmada arquitetura de cotacli.py, convenções de cache XDG e formato de snapshot consumido pelo widget. |
| A02 | Validação da baseline técnica | `origin/main` confirmada em `522405c5d389704edf69724fc78a03a02098daee`. Branch isolada `agy/cota-01-doctor-offline` criada. |
| A03 | Implementação do comando `doctor` em `cotacli.py` | Criadas funções `check_python_version`, `check_dir_accessible`, `check_cli_tool`, `check_cache_metadata`, `check_plasma_environment` e `doctor()`. |
| A04 | Blindagem contra efeitos colaterais e consumo | Proibidas chamadas a subprocessos de provedores, leitura de cota remota, gravação em cache/config ou exposição de tokens/segredos. |
| A05 | Suíte de testes automatizados | Criado `tests/test_cotacli_doctor.py` com mocks de PATH, XDG, versão de Python, ausência de KDE e asserção de não-mutação. |
| A06 | Atualização da documentação | Documentado comando `cotacli doctor` com saída de exemplo sem dados reais em `README.md` e `docs/cli.md`. |
| A07 | Verificação de conformidade na CI | Executados `python -m unittest discover -s tests -v`, `compileall`, `py_compile`, `install-widget.sh` syntax check e `json.tool`. |

---

## 4. Evidências verificáveis

| ID | Classe | Fonte / Referência | Fato observado e limite |
|---|---|---|---|
| E01 | OBSERVADO | `git rev-parse origin/main` | Baseline confirmada em `522405c5d389704edf69724fc78a03a02098daee`. |
| E02 | OBSERVADO | `python3 -m unittest discover -s tests -v` | 16 testes aprovados (100% PASS), sendo 9 novos testes específicos do `doctor`. |
| E03 | OBSERVADO | `python3 -m compileall -q cotacli.py tests` | Compilação de bytecode sem erros sintáticos. |
| E04 | OBSERVADO | `bash -n install-widget.sh` | Validação de sintaxe do script de instalação aprovada sem erros. |
| E05 | OBSERVADO | `python3 -m json.tool cotacli-widget/metadata.json` | JSON do metadado do widget validado com sucesso. |
| E06 | OBSERVADO | GitHub Actions Run `41058488033` | CI verde (success) na matriz Python 3.10, 3.12 e 3.13. |
| E07 | OBSERVADO | `test_doctor_strictly_prohibits_quota_calls_and_side_effects` | Confirmado por mock que `rpc_codex_rate_limits`, `read_agy_cli`, `get_codex`, `get_agy`, `snapshot`, `discover_cli_paths`, `save_json` e subprocessos não são invocados. |
| E08 | DECLARADO | Protocolo de execução | Custo financeiro adicional R$ 0,00; sem chamadas de modelo pagas. |
| E09 | OBSERVADO | `git status` | Execução restrita à branch isolada `agy/cota-01-doctor-offline`. |

---

## 5. Verificações e resultados

| Teste | Critério de Aceite | Resultado | Evidência |
|---|---|---|---|
| T01 | `cotacli doctor` funciona offline, sem consumo de tokens e sem mutações | PASSOU | Teste unitário e verificação local sem rede nem mutação de arquivos (E07). |
| T02 | Diagnóstico compreensível de ferramentas/config/cache/ambiente, inclusive sem KDE | PASSOU | Exibição estruturada com status OK / ALERTA / INDISPONÍVEL / FALHA / INFO e próximos passos didáticos em PT-BR (E02). |
| T03 | Ausência opcional diferenciada de falha essencial; exit code coerente | PASSOU | Falta de CLIs opcionais gera alerta e exit code 0; falha em runtime/permissão essencial gera exit code 1 (E02). |
| T04 | Nenhuma regressão do widget, snapshot, refresh e comandos prévios | PASSOU | 7 testes prévios do contrato do widget continuam passando (E02). |
| T05 | Testes offline e CI concluídos | PASSOU | 16 testes locais aprovados e CI do GitHub Actions (run 41058488033) verde (E02, E06). |
| T06 | Draft PR + RUC verificável; nenhum merge | PASSOU | Draft PR #2 criado contra `main`, sem merge ou deploy executado (E09). |

---

## 6. Riscos e bloqueios

1. **Permissões de filesystem:** O `doctor` requer que os diretórios XDG do usuário (`~/.config` e `~/.cache`) sejam acessíveis ou que seus diretórios pais sejam graváveis. Em ambientes restritos/sandboxed, o comando reporta a falha e orienta a correção sem quebrar.
2. **CLIs em caminhos não-padrão:** Se o usuário instalar CLIs fora do PATH e ainda não tiver executado `cotacli discover`, o `doctor` reportará as ferramentas como não detectadas (opcional), orientando a instalação ou uso normal.

---

## 7. Alterações realizadas

- **Novos arquivos:**
  - `tests/test_cotacli_doctor.py`
  - `docs/CH/RUC-COTA-01.md`
- **Arquivos modificados:**
  - `cotacli.py` (adicionadas funções de diagnóstico e subcomando `doctor`)
  - `README.md` (documentação do `cotacli doctor` com exemplo limpo)
  - `docs/cli.md` (tabela de comandos atualizada)

---

## 8. Recomendação técnica

**APROVADO_TECNICAMENTE** — A fatia COTA-01 atende com rigor a todos os requisitos e critérios de aceite da Issue #1. O Draft PR #2 está pronto para auditoria independente do ChatGPT.

---

## 9. Decisão necessária do PO

**PENDENTE** — Aguardando parecer de auditoria independente do ChatGPT e subsequente decisão explícita de homologação e merge pelo Product Owner (Hallan).
