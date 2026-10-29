#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v kpackagetool6 >/dev/null 2>&1; then
    echo "Precisa do KDE Plasma 6 (kpackagetool6)." >&2
    exit 1
fi

install -Dm755 "$project_dir/cotacli.py" "$HOME/.local/bin/cotacli"
"$HOME/.local/bin/cotacli" discover
applet_dir="$HOME/.local/share/plasma/plasmoids/org.cotacli.quotas"
if [[ -d "$applet_dir" ]]; then
    kpackagetool6 -t Plasma/Applet -u "$project_dir/cotacli-widget"
else
    kpackagetool6 -t Plasma/Applet -i "$project_dir/cotacli-widget"
fi
if command -v systemctl >/dev/null 2>&1 && systemctl --user is-active --quiet plasma-plasmashell.service; then
    echo "Recarregando o Plasma para aplicar o novo widget (o painel pode sumir por alguns segundos)…"
    systemctl --user restart plasma-plasmashell.service || \
        echo "Não consegui recarregar o Plasma. Saia da sessão e entre novamente."
fi
echo "CotaCLI instalado. Na bandeja: botão direito → Configurar bandeja do sistema → Entradas → CotaCLI."
