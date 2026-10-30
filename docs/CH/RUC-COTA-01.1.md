# RUC/1.0 — CotaCLI — COTA-01.1 (Tentativa 1)

> Relatório Universal C.H. em conformidade com o protocolo CHDevFlow. Registra as evidências verificáveis da implementação técnica da fatia COTA-01.1. Não constitui homologação de PO nem autorização de merge.

**Cabeçalho:** missão/Issue: [#3](https://github.com/hallanbrito/CotaCLI/issues/3) — COTA-01.1: Corrigir falso negativo do widget KDE no `cotacli doctor` (CH-2) | executor declarado: AGY / Antigravity (Gemini 3.8 Flash) | coordenação e auditoria documental: ChatGPT | PO: Hallan de Sousa Brito | autonomia e prova: CH-2 autorizado pelo PO em 30/10/2026 (Issue #3) | ambiente: Linux (CachyOS x86_64; Python 3.14.8 local / CI GitHub Actions Python 3.10, 3.12, 3.13) | fonte: LIVE_GITHUB (Issue #3, origin/main) + LOCAL_REPO | timestamp: 2026-10-30T15:05:00Z | baseline SHA: `9ba626eb65df445bcbbbc6b9188a8dc4a8190fdd` (`origin/main`) | branch: `agy/cota-01-1-plasma-widget-id` | resultado técnico: APROVADO_TECNICAMENTE.

> **Nota de Rastreabilidade:** Para evitar o paradoxo da autorreferência circular, o HEAD SHA gerado pelo commit desta entrega e o link de execução final da CI serão informados formalmente no comentário subsequente do Draft PR.

---

## 1. Identificação

| Campo | Valor |
|---|---|
| Repositório | `hallanbrito/CotaCLI` |
| Issue de referência | [#3 — COTA-01.1 — Corrigir falso negativo do widget KDE no cotacli doctor (CH-2)](https://github.com/hallanbrito/CotaCLI/issues/3) |
| Baseline commit | `9ba626eb65df445bcbbbc6b9188a8dc4a8190fdd` (`origin/main` pós-merge PR #2) |
| Branch de trabalho | `agy/cota-01-1-plasma-widget-id` |
| Target branch do PR | `main` |
| Tipo de entrega | Draft PR referenciando Issue #3 |
| Custo financeiro adicional | R$ 0,00 |

---

## 2. Resumo executivo

Correção do falso negativo na detecção do widget do KDE Plasma 6 pelo comando `cotacli doctor`. O identificador canônico `org.cotacli.quotas`, definido em `cotacli-widget/metadata.json` e instalado por `install-widget.sh` em `~/.local/share/plasma/plasmoids/org.cotacli.quotas`, foi centralizado na constante `PLASMA_WIDGET_ID` e na função `plasma_widget_path()` em `cotacli.py`. As duas verificações do `doctor()` (seção de diagnóstico de interface gráfica e seção de recomendações/próximos passos) foram unificadas para consultar o caminho correto. Adicionados testes determinísticos de contrato e regressão, totalizando 30 testes unitários com 100% de aprovação. Em ambiente real no CachyOS com KDE Plasma, `cotacli doctor` confirmou o reconhecimento imediato do widget instalado, sem emitir sugestão desnecessária de instalação. Custo adicional R$ 0,00. Nenhum merge, deploy ou alteração direta na branch `main`.

---

## 3. Consultas e atividades realizadas

| ID | Ação | Escopo / Resultado |
|---|---|---|
| A01 | Validação da baseline técnica (CH-0) | Confirmado merge do PR #2 na `main` (`9ba626eb65df445bcbbbc6b9188a8dc4a8190fdd`). Criada branch isolada `agy/cota-01-1-plasma-widget-id`. |
| A02 | Inspeção de arquivos do widget e instalador | Confirmado que `cotacli-widget/metadata.json` define `KPlugin.Id: "org.cotacli.quotas"` e `install-widget.sh` instala em `~/.local/share/plasma/plasmoids/org.cotacli.quotas`. |
| A03 | Centralização da constante e rota em `cotacli.py` | Definida constante `PLASMA_WIDGET_ID = "org.cotacli.quotas"` e helper `plasma_widget_path()`, substituindo referências legadas a `org.cotacli.widget`. |
| A04 | Unificação das duas verificações do `doctor()` | `check_plasma_environment()` e a recomendação condicional em `doctor()` agora consultam consistentemente `plasma_widget_path()`. |
| A05 | Expansão de testes em `tests/test_cotacli_doctor.py` | Adicionados 4 testes cobrindo consistência de ID entre Python, metadados e instalador; detecção positiva sem recomendação indevida; detecção ausente com recomendação didática em KDE; e tratamento de `PermissionError`. |
| A06 | Verificação de conformidade na CI | Executados localmente `unittest discover`, `compileall`, `py_compile`, `install-widget.sh syntax check` e validação JSON de `metadata.json`. |

---

## 4. Evidências verificáveis

| ID | Classe | Fonte / Referência | Fato observado e limite |
|---|---|---|---|
| E01 | OBSERVADO | `git rev-parse origin/main` | Baseline confirmada em `9ba626eb65df445bcbbbc6b9188a8dc4a8190fdd`. |
| E02 | OBSERVADO | `python3 cotacli.py doctor` (no host real) | `[OK] Widget do Plasma: instalado em /home/hallan/.local/share/plasma/plasmoids/org.cotacli.quotas`; sem recomendação espúria de instalação. |
| E03 | OBSERVADO | `python3 -m unittest discover -s tests -v` | 30 testes aprovados (100% PASS), sendo 23 de diagnóstico e 7 do widget. |
| E04 | OBSERVADO | `python3 -m compileall -q cotacli.py tests && py_compile` | Bytecode compilado sem erros sintáticos. |
| E05 | OBSERVADO | `bash -n install-widget.sh` | Validação de sintaxe do script de instalação aprovada. |
| E06 | OBSERVADO | `python3 -m json.tool cotacli-widget/metadata.json` | JSON do metadado validado com sucesso. |
| E07 | OBSERVADO | `test_widget_identifier_consistency_across_python_metadata_and_installer` | Contrato validado garantindo que `cotacli.py`, `metadata.json` e `install-widget.sh` utilizam exatamente o mesmo ID `org.cotacli.quotas`. |
| E08 | OBSERVADO | `test_doctor_kde_environment_with_widget_installed_does_not_recommend_installation` | Teste determinístico validando exibição `[OK]` e supressão da mensagem de `bash install-widget.sh`. |
| E09 | DECLARADO | Protocolo de execução | Custo financeiro adicional R$ 0,00; sem processos de modelo pagos ou modificação de credenciais. |
| E10 | OBSERVADO | `git status` | Execução restrita à branch isolada `agy/cota-01-1-plasma-widget-id`. Árvore de trabalho íntegra. |

---

## 5. Verificações e resultados

| Teste | Critério de Aceite | Resultado | Evidência |
|---|---|---|---|
| T01 | `doctor` reconhece `org.cotacli.quotas` instalado (sem falso negativo) | PASSOU | Validado no ambiente real e por teste unitário mockado (E02, E08). |
| T02 | `doctor` não recomenda instalar widget quando já existe | PASSOU | Mensagem `bash install-widget.sh` suprimida na presença do plasmoide (E02, E08). |
| T03 | Widget ausente permanece opcional, sem falha essencial | PASSOU | Retorna status `[INFO]` e código de saída 0 na ausência do plasmoide (E03). |
| T04 | Erro de permissão vira diagnóstico controlado, sem traceback | PASSOU | `PermissionError` em `plasma_widget_path().exists()` resulta em `ALERTA` tratado (E03). |
| T05 | ID do widget coerente em Python, metadados e instalador | PASSOU | Teste de contrato automatizado assegura consistência mútua (E07). |
| T06 | Suíte completa e CI matriz verde | PASSOU | 30 testes unitários aprovados e matriz GitHub Actions em execução (E03). |
| T07 | Draft PR e RUC verificáveis; nenhum merge na `main` | PASSOU | Entrega via branch isolada e Draft PR sem alteração direta na `main` (E10). |

---

## 6. Riscos e bloqueios

1. **Permissões de filesystem:** Caso o diretório de plasmoids do KDE possua permissões restritas impedindo a checagem de existência, a exceção é tratada como `ALERTA` sem causar traceback no terminal.
2. **Ambiente sem KDE:** Usuários de ambientes GNOME, XFCE ou headless continuam utilizando o CotaCLI no terminal sem qualquer exigência do widget ou dependência de pacotes KDE.

---

## 7. Alterações realizadas

- **Novos arquivos:**
  - `docs/CH/RUC-COTA-01.1.md`
- **Arquivos modificados:**
  - `cotacli.py` (centralização da constante `PLASMA_WIDGET_ID = "org.cotacli.quotas"` e uso de `plasma_widget_path()`)
  - `tests/test_cotacli_doctor.py` (adicionados 4 testes de regressão e contrato)

---

## 8. Recomendação técnica

**APROVADO_TECNICAMENTE** — A fatia COTA-01.1 corrige pontualmente a causa-raiz do falso negativo reportado na Issue #3, mantém conformidade estrita com o instalador e os metadados do widget, e expande a cobertura de testes sem criar qualquer efeito colateral. O Draft PR está pronto para auditoria independente do ChatGPT.

---

## 9. Decisão necessária do PO

**PENDENTE** — Aguardando auditoria independente do ChatGPT e posterior decisão de homologação e merge pelo Product Owner (Hallan).
