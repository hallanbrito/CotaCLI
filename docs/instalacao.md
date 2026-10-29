# Instalação e atualização

## Requisitos

- Linux e Python 3.10 ou superior.
- KDE Plasma 6 com `kpackagetool6` e `plasma5support` para o widget. O terminal funciona sem KDE.
- `codex` e/ou `agy` instalados para as cotas correspondentes. Claude Code é opcional.

No Arch/CachyOS, se faltar o módulo do Plasma, instale o pacote `plasma5support` pelo gerenciador do sistema. O CotaCLI não instala nem autentica as CLIs dos provedores.

## Instalação local

```sh
git clone https://github.com/hallanbrito/CotaCLI.git
cd CotaCLI
bash install-widget.sh
```

O script instala `~/.local/bin/cotacli` e o applet `org.cotacli.quotas` em `~/.local/share/plasma/plasmoids/`. Ele não altera os arquivos do KodexBar Suite. Se `plasma-plasmashell.service` estiver ativo, o script o reinicia para carregar a nova versão. A sessão pode ficar sem painel por alguns segundos.

Para atualizar um clone existente:

```sh
git pull --ff-only
bash install-widget.sh
```

Após instalar, abra **Configurar bandeja do sistema → Entradas → CotaCLI → Sempre visível**. Clique no ícone para abrir as cotas. O botão de atualizar fica no cabeçalho nativo do Plasma e no menu de contexto.

## Somente terminal

```sh
install -Dm755 cotacli.py "$HOME/.local/bin/cotacli"
"$HOME/.local/bin/cotacli" discover
"$HOME/.local/bin/cotacli" refresh
```

`discover` grava somente os caminhos absolutos dos executáveis encontrados no `PATH` da sessão de terminal. Isso permite que o widget encontre `agy` mesmo quando o Plasma usa outro `PATH`. Repita `cotacli discover` depois de instalar ou mover uma CLI.

## Solução de problemas

| Sintoma | Verificação |
| --- | --- |
| `cotacli: command not found` | Execute `~/.local/bin/cotacli` ou adicione `~/.local/bin` ao seu `PATH`. |
| Ícone ausente | Confira as **Entradas** da bandeja; saia e entre na sessão se o Plasma não tiver carregado o applet. |
| AGY ausente | Rode `command -v agy`, `cotacli discover` e `cotacli snapshot --refresh` no Konsole. |
| Popup sem cotas | Rode `cotacli snapshot --refresh` para ver os dados e erros antes de depurar o widget. |
| Claude Code ausente | É esperado sem uma cota atual capturada pela status line. Instalar a CLI não cria uma assinatura. |
| Versão visual antiga | Execute `bash install-widget.sh` no clone atualizado; se necessário, encerre a sessão e entre novamente. |

## Remoção

```sh
kpackagetool6 -t Plasma/Applet -r org.cotacli.quotas
rm "$HOME/.local/bin/cotacli"
```

Os arquivos de cache e descoberta ficam em `~/.cache/cotacli/` e `~/.config/cotacli/`; remova-os somente se quiser apagar também os dados locais salvos. O comando de remoção acima não toca nos CLIs dos provedores.
