#!/usr/bin/env python3
"""CotaCLI: cotas locais das ferramentas de IA instaladas."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import time

APP = "cotacli"
VERSION = "0.2.1.dev0"
CACHE_TTL_SECONDS = 600
CODEX_TIMEOUT_SECONDS = 8
AGY_TIMEOUT_SECONDS = 60
CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / APP
CACHE_DIR = Path(os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / APP
AGY_MANUAL_PATH = CONFIG_DIR / "antigravity.json"
AGY_CACHE_PATH = CACHE_DIR / "agy.json"
CODEX_PATH = CACHE_DIR / "codex.json"
CLAUDE_PATH = CACHE_DIR / "claude.json"
CLI_PATHS = CONFIG_DIR / "cli-paths.json"
GROUPS = {"agy-gemini": "AGY / Gemini", "agy-others": "AGY / Claude+GPT"}
PLASMA_WIDGET_ID = "org.cotacli.quotas"


def plasma_widget_path() -> Path:
    return Path.home() / ".local/share/plasma/plasmoids" / PLASMA_WIDGET_ID


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def save_json(path: Path, data: dict) -> None:
    """Salva JSON de forma atômica e com permissão somente para o usuário."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def find_cli(name: str) -> str | None:
    """Usa o PATH atual ou o executável registrado no terminal na instalação."""
    found = shutil.which(name)
    if found:
        return found
    candidate = read_json(CLI_PATHS).get(name)
    if isinstance(candidate, str) and Path(candidate).is_absolute() and os.access(candidate, os.X_OK):
        return candidate
    return None


def discover_cli_paths() -> dict:
    """Registra apenas caminhos de executáveis, sem credenciais ou variáveis."""
    previous = read_json(CLI_PATHS)
    detected = {}
    for name in ("codex", "agy", "claude"):
        path = shutil.which(name)
        if path:
            detected[name] = str(Path(path).resolve())
        elif isinstance(previous.get(name), str) and os.access(previous[name], os.X_OK):
            detected[name] = previous[name]
    save_json(CLI_PATHS, detected)
    return detected


def rpc_codex_rate_limits(timeout: int = CODEX_TIMEOUT_SECONDS) -> dict:
    """Solicita somente account/rateLimits/read via protocolo do Codex."""
    codex_path = find_cli("codex")
    if not codex_path:
        raise RuntimeError("Codex CLI não instalado no PATH")
    proc = subprocess.Popen(
        [codex_path, "app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, bufsize=0,
    )
    buffer = b""
    deadline = time.monotonic() + timeout

    def send(obj: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write((json.dumps(obj, separators=(",", ":")) + "\n").encode())
        proc.stdin.flush()

    def await_id(request_id: int) -> dict:
        nonlocal buffer
        assert proc.stdout is not None
        fd = proc.stdout.fileno()
        while time.monotonic() < deadline:
            if b"\n" in buffer:
                raw, buffer = buffer.split(b"\n", 1)
                try:
                    response = json.loads(raw)
                except ValueError:
                    continue
                if response.get("id") == request_id:
                    if "error" in response:
                        raise RuntimeError("Codex retornou erro na leitura de cotas")
                    return response.get("result") or {}
                continue
            wait = max(0.01, deadline - time.monotonic())
            ready, _, _ = select.select([fd], [], [], wait)
            if ready:
                fragment = os.read(fd, 16384)
                if not fragment:
                    raise RuntimeError("Codex encerrou sem responder")
                buffer += fragment
        raise TimeoutError("Codex não respondeu no prazo")

    try:
        send({"id": 1, "method": "initialize", "params": {
            "clientInfo": {
                "name": "cotacli",
                "title": "CotaCLI",
                "version": VERSION,
            }
        }})
        await_id(1)
        send({"method": "initialized", "params": {}})
        send({"id": 2, "method": "account/rateLimits/read", "params": {}})
        return await_id(2)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=1)


def window_summary(window: dict | None) -> dict | None:
    if not isinstance(window, dict) or not isinstance(window.get("usedPercent"), (float, int)):
        return None
    used = max(0.0, min(100.0, float(window["usedPercent"])))
    return {
        "remaining": round(100 - used, 1),
        "duration": window.get("windowDurationMins"),
        "reset": window.get("resetsAt"),
    }


def extract_codex(raw: dict) -> dict:
    buckets = raw.get("rateLimitsByLimitId") or {}
    default = raw.get("rateLimits") or {}
    bucket = buckets.get("codex") if isinstance(buckets, dict) else None
    if not isinstance(bucket, dict):
        bucket = default if isinstance(default, dict) else {}
    windows = [window_summary(bucket.get(key)) for key in ("primary", "secondary")]
    result = {"5h": None, "week": None}
    for window in (item for item in windows if item):
        duration = window["duration"]
        if isinstance(duration, (int, float)):
            if 240 <= duration <= 360:
                result["5h"] = window
            elif 7 * 24 * 60 - 120 <= duration <= 7 * 24 * 60 + 120:
                result["week"] = window
    return result


def get_codex(force: bool = False) -> tuple[dict, str]:
    cached = read_json(CODEX_PATH)
    age = time.time() - cached.get("updated", 0)
    if not force and 0 <= age < CACHE_TTL_SECONDS and cached.get("windows"):
        return cached["windows"], f"automático, cache {int(age // 60)}min"
    try:
        result = extract_codex(rpc_codex_rate_limits())
        save_json(CODEX_PATH, {"windows": result, "updated": time.time()})
        return result, "automático, atualizado agora"
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        if cached.get("windows"):
            minutes = int(max(0, age) // 60)
            return cached["windows"], f"SEM CONEXÃO, dados antigos ({minutes}min): {exc}"
        return {}, f"indisponível: {exc}"


def parse_reset_time(value: object) -> float | None:
    """Converte o horário ISO 8601 do AGY para timestamp Unix."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def extract_agy(raw: dict) -> dict:
    """Extrai os quatro buckets confirmados pela saída real do comando /usage."""
    command = raw.get("command") if isinstance(raw.get("command"), dict) else {}
    command_data = command.get("data") if isinstance(command.get("data"), dict) else {}
    response = raw.get("response") if isinstance(raw.get("response"), dict) else {}
    groups = command_data.get("groups") or raw.get("groups") or response.get("groups")
    if not isinstance(groups, list):
        raise ValueError("JSON do AGY sem command.data.groups")

    result = {
        "agy-gemini": {"5h": None, "week": None},
        "agy-others": {"5h": None, "week": None},
    }
    bucket_map = {
        "gemini-5h": ("agy-gemini", "5h"),
        "gemini-weekly": ("agy-gemini", "week"),
        "3p-5h": ("agy-others", "5h"),
        "3p-weekly": ("agy-others", "week"),
    }
    found = 0

    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("buckets"), list):
            continue
        for bucket in group["buckets"]:
            if not isinstance(bucket, dict):
                continue
            bucket_id = str(
                bucket.get("id") or bucket.get("bucket_id") or bucket.get("bucketId") or ""
            ).lower()
            destination = bucket_map.get(bucket_id)
            if destination is None:
                continue

            fraction = bucket.get("remaining_fraction")
            if fraction is None:
                fraction = bucket.get("remainingFraction")
            if not isinstance(fraction, (int, float)) or isinstance(fraction, bool):
                continue
            if not 0 <= float(fraction) <= 1:
                continue

            reset = bucket.get("reset_time")
            if reset is None:
                reset = bucket.get("resetTime") or bucket.get("resetsAt")
            group_key, window_key = destination
            result[group_key][window_key] = {
                "remaining": round(float(fraction) * 100, 1),
                "reset": parse_reset_time(reset),
            }
            found += 1

    if found == 0:
        raise ValueError("JSON do AGY sem buckets de cota reconhecidos")
    return result


def read_agy_cli(timeout: int = AGY_TIMEOUT_SECONDS) -> dict:
    """Executa somente o comando interno /usage da CLI Antigravity."""
    agy_path = find_cli("agy")
    if not agy_path:
        raise RuntimeError("AGY CLI não instalada no PATH")
    try:
        proc = subprocess.run(
            [agy_path, "-p", "/usage", "--output-format", "json"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("AGY não respondeu no prazo") from exc

    if proc.returncode != 0:
        raise RuntimeError(f"AGY encerrou com código {proc.returncode}")
    try:
        raw = json.loads(proc.stdout.strip())
    except (json.JSONDecodeError, AttributeError) as exc:
        raise ValueError("AGY não retornou JSON válido") from exc
    if not isinstance(raw, dict):
        raise ValueError("AGY retornou uma estrutura JSON inesperada")

    command = raw.get("command")
    if (
        raw.get("status") != "SUCCESS"
        or not isinstance(command, dict)
        or command.get("name") != "usage"
    ):
        raise RuntimeError("AGY não confirmou a execução do comando interno usage")

    usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
    total_tokens = usage.get("total_tokens", usage.get("totalTokens"))
    turns = raw.get("num_turns", raw.get("numTurns"))
    if total_tokens != 0 or turns != 0:
        raise RuntimeError(
            "AGY registrou turno ou tokens; leitura automática rejeitada por segurança"
        )
    return extract_agy(raw)


def get_agy(force: bool = False) -> tuple[dict, str]:
    cached = read_json(AGY_CACHE_PATH)
    age = time.time() - cached.get("updated", 0)
    if not force and 0 <= age < CACHE_TTL_SECONDS and cached.get("groups"):
        return cached["groups"], f"automático, cache {int(age // 60)}min"

    try:
        groups = read_agy_cli()
        save_json(AGY_CACHE_PATH, {"groups": groups, "updated": time.time()})
        return groups, "automático via AGY /usage, atualizado agora"
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        if cached.get("groups"):
            minutes = int(max(0, age) // 60)
            return cached["groups"], f"SEM CONEXÃO, dados antigos ({minutes}min): {exc}"
        manual = read_json(AGY_MANUAL_PATH)
        if manual:
            return manual, f"manual; leitura automática indisponível: {exc}"
        return {}, f"indisponível: {exc}"


def extract_claude(raw: dict) -> dict:
    """Extrai somente as janelas documentadas no JSON da status line."""
    limits = raw.get("rate_limits")
    if not isinstance(limits, dict):
        return {"5h": None, "week": None}
    result = {"5h": None, "week": None}
    for source_key, target_key in (("five_hour", "5h"), ("seven_day", "week")):
        window = limits.get(source_key)
        if not isinstance(window, dict):
            continue
        used = window.get("used_percentage")
        reset = window.get("resets_at")
        if not isinstance(used, (int, float)) or isinstance(used, bool):
            continue
        if not 0 <= float(used) <= 100:
            continue
        if not isinstance(reset, (int, float)) or isinstance(reset, bool):
            continue
        if reset <= time.time():
            continue
        result[target_key] = {"remaining": round(100 - float(used), 1), "reset": reset}
    return result


def capture_claude() -> int:
    """Recebe stdin da status line sem guardar sessão, modelo ou credenciais."""
    try:
        raw = json.load(sys.stdin)
        if not isinstance(raw, dict):
            return 1
        windows = extract_claude(raw)
        if any(window is not None for window in windows.values()):
            save_json(CLAUDE_PATH, {"windows": windows, "updated": time.time()})
        # A status line do Claude precisa imprimir algo para não ficar vazia.
        print("CotaCLI · Claude")
        return 0
    except (OSError, ValueError, TypeError):
        return 1


def get_claude() -> tuple[dict, str]:
    cached = read_json(CLAUDE_PATH)
    windows = cached.get("windows")
    if not isinstance(windows, dict) or not any(windows.get(key) for key in ("5h", "week")):
        return {}, "sem cota capturada; abra o Claude Code e use a status line"
    age = time.time() - cached.get("updated", 0)
    if age < 0 or age > 3600:
        return {}, "última leitura antiga; abra o Claude Code para atualizar"
    current = {
        key: window if isinstance(window, dict) and window.get("reset", 0) > time.time() else None
        for key, window in (("5h", windows.get("5h")), ("week", windows.get("week")))
    }
    return current, "" if any(current.values()) else "janelas expiradas; aguarde nova resposta do Claude"


def has_current_quota(windows: dict) -> bool:
    """A instalação da CLI sozinha não prova que existe assinatura com cota."""
    now = time.time()
    for window in windows.values():
        if not isinstance(window, dict):
            continue
        remaining, reset = window.get("remaining"), window.get("reset")
        if (isinstance(remaining, (int, float)) and not isinstance(remaining, bool)
                and 0 <= remaining <= 100 and isinstance(reset, (int, float))
                and not isinstance(reset, bool) and reset > now):
            return True
    return False


def color(text: str, code: str) -> str:
    if sys.stdout.isatty() and not os.getenv("NO_COLOR"):
        return f"\033[{code}m{text}\033[0m"
    return text


def quota_metric(window: dict | float | int | None) -> tuple[str, str]:
    """Formata percentual, barra e horário para uma coluna do painel."""
    if isinstance(window, dict):
        value = window.get("remaining")
        reset = window.get("reset")
    else:
        value, reset = window, None
    if not isinstance(value, (float, int)) or isinstance(value, bool):
        return color("  --  ░░░░░░░░░░", "2"), "—"
    value = max(0.0, min(100.0, float(value)))
    filled = round(value / 10)
    bar = "█" * filled + "░" * (10 - filled)
    shade = "32" if value >= 50 else "33" if value >= 20 else "31"
    formatted = color(f"{value:5.1f}% {bar}", shade)
    reset_text = (
        datetime.fromtimestamp(reset).strftime("%d/%m %H:%M")
        if isinstance(reset, (int, float)) and reset > 0 else "—"
    )
    return formatted, reset_text


def print_provider(label: str, quotas: dict, source: str) -> None:
    """Mantém valores e horário de renovação alinhados sem contar códigos ANSI."""
    five, five_reset = quota_metric(quotas.get("5h"))
    week, week_reset = quota_metric(quotas.get("week"))
    print(f"{label:<20}{five}    {week}")
    print(color(f"{'':20}↻ {five_reset:<18} ↻ {week_reset}", "2"))
    # Só problemas e dados manuais precisam de contexto no painel principal.
    if not source.startswith("automático"):
        print(color(f"{'':20}{source}", "2"))


def snapshot(force: bool = False) -> dict:
    """Contrato simples para interfaces: apenas CLIs presentes, sem dados de conta."""
    providers = []
    if find_cli("codex"):
        windows, status = get_codex(force)
        providers.append({"id": "codex", "name": "Codex", "windows": windows,
                          "status": status})
    if find_cli("agy"):
        groups, status = get_agy(force)
        for group_id, label in GROUPS.items():
            windows = groups.get(group_id) if isinstance(groups, dict) else None
            providers.append({"id": group_id, "name": label,
                              "windows": windows if isinstance(windows, dict) else {},
                              "status": status})
    if find_cli("claude"):
        windows, status = get_claude()
        if has_current_quota(windows):
            providers.append({"id": "claude", "name": "Claude Code",
                              "windows": windows, "status": status})
    return {"schema": 1, "providers": providers, "updated": time.time()}


def check_python_version() -> tuple[bool, str]:
    version = sys.version_info
    major = getattr(version, "major", version[0])
    minor = getattr(version, "minor", version[1])
    micro = getattr(version, "micro", version[2]) if len(version) > 2 else 0
    ver_str = f"{major}.{minor}.{micro}"
    if (major, minor) >= (3, 10):
        return True, f"Python {ver_str} (>= 3.10 suportado)"
    return False, f"Python {ver_str} não suportado (requer >= 3.10)"


def check_dir_accessible(path: Path) -> tuple[bool, str]:
    try:
        resolved = path.resolve()
        if resolved.exists():
            if not resolved.is_dir():
                return False, f"caminho existe mas não é diretório: {resolved}"
            if not os.access(resolved, os.R_OK | os.W_OK | os.X_OK):
                return False, f"permissão insuficiente (leitura/escrita/travessia) em {resolved}"
            return True, f"acessível ({resolved})"

        for ancestor in resolved.parents:
            try:
                if ancestor.exists():
                    if not ancestor.is_dir():
                        return False, f"ancestral existente não é diretório: {ancestor}"
                    if not os.access(ancestor, os.W_OK | os.X_OK):
                        return (
                            False,
                            f"ancestral existente ({ancestor}) sem permissão de escrita/travessia para criar {resolved}",
                        )
                    return True, f"pronto para criação (ancestral {ancestor} gravável)"
            except (PermissionError, OSError) as exc:
                return False, f"sem acesso ao ancestral {ancestor} ({exc})"

        return False, f"nenhum ancestral existente encontrado para {resolved}"
    except (PermissionError, OSError) as exc:
        return False, f"sem acesso ao caminho ({exc}): {path}"


def check_cli_tool(name: str, label: str) -> tuple[str, str]:
    """Verifica presença da CLI sem executar processos ou registrar caminhos."""
    path = find_cli(name)
    if path:
        return "OK", f"{label}: detectado em {path} (opcional; cotas requerem autenticação local)"
    return "INDISPONÍVEL", f"{label}: não encontrado no PATH nem no registro local (opcional)"


def check_cache_metadata(path: Path, label: str, is_expirable: bool = True) -> tuple[str, str]:
    """Consulta apenas stat do arquivo de cache/config, sem inspecionar conteúdo ou segredos."""
    try:
        if not path.exists():
            return "INFO", f"{label}: nenhum registro encontrado (normal na primeira execução ou se não configurado)"
        st = path.stat()
        age_seconds = time.time() - st.st_mtime
        age_minutes = int(max(0, age_seconds) // 60)
        size = st.st_size
        if not is_expirable:
            return "OK", f"{label}: presente ({size} bytes, salvo há {age_minutes}min)"
        if age_seconds < CACHE_TTL_SECONDS:
            return "OK", f"{label}: cache recente ({age_minutes}min, {size} bytes)"
        return "ALERTA", f"{label}: cache antigo/expirado há {age_minutes}min (será renovado no próximo acesso)"
    except (PermissionError, OSError) as exc:
        return "ALERTA", f"{label}: erro ao consultar metadados ({exc})"


def check_plasma_environment() -> list[tuple[str, str]]:
    """Avalia integração Plasma 6 sem exigir KDE para uso em terminal."""
    current_desktop = os.getenv("XDG_CURRENT_DESKTOP", "")
    kde_session = os.getenv("KDE_FULL_SESSION", "")
    is_kde = "KDE" in current_desktop.upper() or kde_session.lower() == "true"
    results = []
    if is_kde:
        results.append(("INFO", f"Ambiente de desktop: KDE Plasma detectado ({current_desktop})"))
        kpackagetool = shutil.which("kpackagetool6")
        if kpackagetool:
            results.append(("OK", f"kpackagetool6: detectado em {kpackagetool}"))
        else:
            results.append(("ALERTA", "kpackagetool6: não encontrado (necessário para instalar widget)"))
        widget_dir = plasma_widget_path()
        try:
            if widget_dir.exists():
                results.append(("OK", f"Widget do Plasma: instalado em {widget_dir}"))
            else:
                results.append(("INFO", "Widget do Plasma: não instalado (opcional; execute bash install-widget.sh)"))
        except (PermissionError, OSError) as exc:
            results.append(("ALERTA", f"Widget do Plasma: erro ao verificar instalação ({exc})"))
    else:
        results.append(("INFO", f"Ambiente de desktop: {current_desktop or 'terminal/outro'} (modo terminal ativo; Plasma 6 opcional)"))
    return results


def doctor() -> int:
    """Diagnóstico local, offline e estritamente somente leitura do ambiente."""
    print(color("COTACLI  /  DOCTOR", "1;36") + color(f"  v{VERSION}", "2"))
    print(color("─" * 60, "2"))

    essential_errors = 0
    warnings = 0

    print(color("1. AMBIENTE DE EXECUÇÃO", "1"))
    py_ok, py_msg = check_python_version()
    if py_ok:
        print(f"  [{color('OK', '32')}] {py_msg}")
    else:
        print(f"  [{color('FALHA', '31')}] {py_msg}")
        essential_errors += 1

    print(color("\n2. DIRETÓRIOS E PERMISSÕES (XDG)", "1"))
    cfg_ok, cfg_msg = check_dir_accessible(CONFIG_DIR)
    if cfg_ok:
        print(f"  [{color('OK', '32')}] Config: {cfg_msg}")
    else:
        print(f"  [{color('FALHA', '31')}] Config: {cfg_msg}")
        essential_errors += 1

    cache_ok, cache_msg = check_dir_accessible(CACHE_DIR)
    if cache_ok:
        print(f"  [{color('OK', '32')}] Cache: {cache_msg}")
    else:
        print(f"  [{color('FALHA', '31')}] Cache: {cache_msg}")
        essential_errors += 1

    print(color("\n3. FERRAMENTAS DE IA (OPCIONAIS)", "1"))
    cli_found_count = 0
    for name, label in (("codex", "Codex CLI"), ("agy", "Antigravity (AGY) CLI"), ("claude", "Claude Code")):
        status, msg = check_cli_tool(name, label)
        if status == "OK":
            cli_found_count += 1
            print(f"  [{color('OK', '32')}] {msg}")
        else:
            print(f"  [{color('INDISPONÍVEL', '33')}] {msg}")
    if cli_found_count == 0:
        print(f"  [{color('ALERTA', '33')}] Nenhuma ferramenta detectada (opcional para diagnóstico; cotas não serão exibidas)")
        warnings += 1

    print(color("\n4. ESTADO DO CACHE LOCAL (METADADOS)", "1"))
    cache_checks = [
        (CODEX_PATH, "Cache Codex", True),
        (AGY_CACHE_PATH, "Cache AGY", True),
        (CLAUDE_PATH, "Cache Claude Code", True),
        (AGY_MANUAL_PATH, "Contingência manual (antigravity.json)", False),
        (CLI_PATHS, "Registro de caminhos (cli-paths.json)", False),
    ]
    for path, label, expirable in cache_checks:
        status, msg = check_cache_metadata(path, label, expirable)
        tag_color = "32" if status == "OK" else "33" if status == "ALERTA" else "2"
        print(f"  [{color(status, tag_color)}] {msg}")
        if status == "ALERTA":
            warnings += 1

    print(color("\n5. INTERFACE GRÁFICA (KDE PLASMA 6 - OPCIONAL)", "1"))
    for status, msg in check_plasma_environment():
        tag_color = "32" if status == "OK" else "33" if status == "ALERTA" else "2"
        print(f"  [{color(status, tag_color)}] {msg}")
        if status == "ALERTA":
            warnings += 1

    print(color("\n" + "─" * 60, "2"))
    print(color("RESUMO DO DIAGNÓSTICO", "1"))
    if essential_errors == 0:
        print(f"  Resultado: {color('APROVADO', '32')} (0 falhas essenciais, {warnings} alerta(s)/informativo(s))")
        print("\nPróximos passos recomendados:")
        if cli_found_count == 0:
            print("  • Instale e autentique ao menos uma das ferramentas suportadas (Codex, AGY ou Claude Code).")
        else:
            print("  • Execute 'cotacli' para visualizar o painel de cotas no terminal.")
            print("  • Execute 'cotacli refresh' se precisar forçar nova consulta às CLIs.")
        current_desktop = os.getenv("XDG_CURRENT_DESKTOP", "")
        if "KDE" in current_desktop.upper():
            try:
                widget_installed = plasma_widget_path().exists()
            except (PermissionError, OSError):
                widget_installed = False
            if not widget_installed:
                print("  • Para instalar o widget na bandeja do KDE Plasma 6, execute: bash install-widget.sh")
        return 0

    print(f"  Resultado: {color('FALHA', '31')} ({essential_errors} falha(s) essencial(is) detectada(s))")
    print("\nPróximos passos para correção:")
    if not py_ok:
        print("  • Atualize a versão do Python para 3.10 ou superior.")
    if not (cfg_ok and cache_ok):
        print("  • Verifique as permissões de gravação nos diretórios XDG do usuário.")
    return 1


def show(force: bool = False) -> None:
    codex_installed = find_cli("codex") is not None
    agy_installed = find_cli("agy") is not None
    claude_windows, claude_source = get_claude() if find_cli("claude") else ({}, "")
    claude_visible = has_current_quota(claude_windows)
    if not (codex_installed or agy_installed or claude_visible):
        print("CotaCLI: nenhuma ferramenta compatível instalada (Codex, AGY ou Claude).")
        return

    print(color("COTACLI  /  COTAS", "1;36") + color(f"  v{VERSION}", "2"))
    print(color("─" * 56, "2"))
    print(color(f"{'':20}{'5 HORAS':<21}SEMANAL", "2"))
    if codex_installed:
        codex, codex_source = get_codex(force)
        print_provider("Codex", codex, codex_source)
    if agy_installed:
        agy, agy_source = get_agy(force)
        for key, label in GROUPS.items():
            item = agy.get(key, {}) if isinstance(agy.get(key), dict) else {}
            if codex_installed or key != "agy-gemini":
                print()
            print_provider(label.replace("AGY / ", "AGY · "), item, agy_source)
    if claude_visible:
        if codex_installed or agy_installed:
            print()
        print_provider("Claude Code", claude_windows, claude_source)


def main() -> int:
    parser = argparse.ArgumentParser(description="Consulta cotas de IA no Konsole.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("show", help="Mostra o painel (padrão)")
    sub.add_parser("refresh", help="Força nova leitura das cotas do Codex e do AGY")
    sub.add_parser("doctor", help="Diagnóstico local offline do ambiente e dependências")
    sub.add_parser("discover", help="Registra caminhos das CLIs para o widget do Plasma")
    snap = sub.add_parser("snapshot", help="Entrega JSON para o widget do Plasma")
    snap.add_argument("--refresh", action="store_true", help="Força nova leitura")
    sub.add_parser("capture-claude", help=argparse.SUPPRESS)
    setter = sub.add_parser(
        "set", help="Registra cotas do AGY manualmente como contingência"
    )
    setter.add_argument("group", choices=list(GROUPS))
    setter.add_argument("five_hour", type=float, help="Percentual restante 5h (0 a 100)")
    setter.add_argument("weekly", type=float, help="Percentual restante semanal (0 a 100)")
    args = parser.parse_args()
    if args.command == "capture-claude":
        return capture_claude()
    if args.command == "snapshot":
        print(json.dumps(snapshot(force=args.refresh), ensure_ascii=False))
        return 0
    if args.command == "doctor":
        return doctor()
    if args.command == "discover":
        detected = discover_cli_paths()
        print("CLIs detectadas: " + (", ".join(detected) if detected else "nenhuma"))
        return 0
    if args.command == "set":
        if not 0 <= args.five_hour <= 100 or not 0 <= args.weekly <= 100:
            parser.error("os percentuais devem estar entre 0 e 100")
        current = read_json(AGY_MANUAL_PATH)
        current[args.group] = {
            "5h": args.five_hour,
            "week": args.weekly,
            "updated": time.time(),
        }
        save_json(AGY_MANUAL_PATH, current)
        print(f"{GROUPS[args.group]} registrado (manual).")
        return 0
    show(force=args.command == "refresh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
