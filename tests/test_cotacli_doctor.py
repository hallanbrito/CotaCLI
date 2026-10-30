"""Testes para o comando cotacli doctor (diagnóstico local e offline)."""

from io import StringIO
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

import cotacli


class DoctorCommandTests(unittest.TestCase):
    def test_doctor_success_on_standard_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cfg = temp_path / "config"
            cache = temp_path / "cache"
            cfg.mkdir()
            cache.mkdir()
            with patch.object(cotacli, "CONFIG_DIR", cfg), \
                 patch.object(cotacli, "CACHE_DIR", cache), \
                 patch.object(sys, "version_info", (3, 11, 0, "final", 0)), \
                 patch("sys.stdout", new_callable=StringIO) as out:
                code = cotacli.doctor()
                self.assertEqual(code, 0)
                output = out.getvalue()
                self.assertIn("COTACLI  /  DOCTOR", output)
                self.assertIn("APROVADO", output)

    def test_doctor_fails_when_python_version_below_310(self):
        with patch.object(sys, "version_info", (3, 9, 7, "final", 0)), \
             patch("sys.stdout", new_callable=StringIO) as out:
            code = cotacli.doctor()
            self.assertEqual(code, 1)
            output = out.getvalue()
            self.assertIn("FALHA", output)
            self.assertIn("não suportado (requer >= 3.10)", output)

    def test_doctor_fails_when_xdg_directories_not_accessible(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            locked_parent = temp_path / "locked"
            locked_parent.mkdir()
            os.chmod(locked_parent, 0o500)
            target = locked_parent / "cotacli"
            try:
                with patch.object(cotacli, "CONFIG_DIR", target), \
                     patch("sys.stdout", new_callable=StringIO) as out:
                    code = cotacli.doctor()
                    self.assertEqual(code, 1)
                    output = out.getvalue()
                    self.assertIn("FALHA", output)
                    self.assertIn("Config:", output)
            finally:
                os.chmod(locked_parent, 0o700)

    def test_doctor_fails_when_directory_lacks_traversal_permission(self):
        """AUD-01: diretório existente com rw- sem x (busca/travessia) deve falhar."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cfg = temp_path / "config"
            cache = temp_path / "cache"
            cfg.mkdir()
            cache.mkdir()
            # Remove permissão de execução/travessia (rw- apenas)
            os.chmod(cfg, 0o600)
            try:
                ok, msg = cotacli.check_dir_accessible(cfg)
                self.assertFalse(ok)
                self.assertIn("permissão insuficiente", msg)
                self.assertIn("travessia", msg)

                with patch.object(cotacli, "CONFIG_DIR", cfg), \
                     patch.object(cotacli, "CACHE_DIR", cache), \
                     patch("sys.stdout", new_callable=StringIO) as out:
                    code = cotacli.doctor()
                    self.assertEqual(code, 1)
                    output = out.getvalue()
                    self.assertIn("FALHA", output)
                    self.assertIn("Config:", output)
            finally:
                os.chmod(cfg, 0o700)

    def test_doctor_fails_when_directory_lacks_write_permission(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cfg = temp_path / "config"
            cfg.mkdir()
            os.chmod(cfg, 0o500)  # r-x apenas
            try:
                ok, msg = cotacli.check_dir_accessible(cfg)
                self.assertFalse(ok)
                self.assertIn("permissão insuficiente", msg)
            finally:
                os.chmod(cfg, 0o700)

    def test_doctor_fails_when_directory_lacks_read_permission(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cfg = temp_path / "config"
            cfg.mkdir()
            os.chmod(cfg, 0o300)  # -wx apenas
            try:
                ok, msg = cotacli.check_dir_accessible(cfg)
                self.assertFalse(ok)
                self.assertIn("permissão insuficiente", msg)
            finally:
                os.chmod(cfg, 0o700)

    def test_check_dir_accessible_succeeds_when_intermediate_ancestors_not_yet_created(self):
        """AUD-02: caminhos ainda não criados com ancestrais intermediários faltantes são criáveis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # temp_path existe, mas nonexistent_parent e cotacli ainda não existem
            target = temp_path / "nonexistent_parent" / "cotacli"
            ok, msg = cotacli.check_dir_accessible(target)
            self.assertTrue(ok)
            self.assertIn("pronto para criação", msg)
            self.assertIn("gravável", msg)
            # Garante que check_dir_accessible não criou nada
            self.assertFalse(target.exists())
            self.assertFalse((temp_path / "nonexistent_parent").exists())

    def test_check_dir_accessible_fails_when_ancestor_is_a_file(self):
        """AUD-02: se um ancestral existente for arquivo, não pode indicar pronto para criação."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file_ancestor = temp_path / "file_as_parent"
            file_ancestor.write_text("arquivo regular", encoding="utf-8")
            target = file_ancestor / "sub" / "cotacli"

            ok, msg = cotacli.check_dir_accessible(target)
            self.assertFalse(ok)
            self.assertIn("ancestral existente não é diretório", msg)
            self.assertNotIn("pronto para criação", msg)

    def test_check_dir_accessible_fails_when_target_itself_is_a_file(self):
        """Verifica se o alvo configurado existir como arquivo regular."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            target_file = temp_path / "target_file"
            target_file.write_text("arquivo", encoding="utf-8")

            ok, msg = cotacli.check_dir_accessible(target_file)
            self.assertFalse(ok)
            self.assertIn("caminho existe mas não é diretório", msg)

    def test_check_dir_accessible_fails_when_ancestor_lacks_write_or_exec_permission(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            locked = temp_path / "locked"
            locked.mkdir()
            os.chmod(locked, 0o500)  # r-x sem escrita
            target = locked / "missing_sub" / "cotacli"
            try:
                ok, msg = cotacli.check_dir_accessible(target)
                self.assertFalse(ok)
                self.assertIn("sem permissão de escrita/travessia", msg)
            finally:
                os.chmod(locked, 0o700)

    def test_doctor_optional_clis_missing_does_not_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cfg = temp_path / "config"
            cache = temp_path / "cache"
            cfg.mkdir()
            cache.mkdir()
            with patch.object(cotacli, "CONFIG_DIR", cfg), \
                 patch.object(cotacli, "CACHE_DIR", cache), \
                 patch.object(cotacli, "find_cli", return_value=None), \
                 patch.object(sys, "version_info", (3, 10, 0, "final", 0)), \
                 patch("sys.stdout", new_callable=StringIO) as out:
                code = cotacli.doctor()
                self.assertEqual(code, 0)
                output = out.getvalue()
                self.assertIn("INDISPONÍVEL", output)
                self.assertIn("Nenhuma ferramenta detectada", output)
                self.assertIn("APROVADO", output)

    def test_doctor_strictly_prohibits_quota_calls_and_side_effects(self):
        """Garante que o doctor NÃO executa processos, rede, escrita em cache ou chamadas de cota."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cfg = temp_path / "config"
            cache = temp_path / "cache"
            cfg.mkdir()
            cache.mkdir()

            mock_rpc = MagicMock()
            mock_read_agy = MagicMock()
            mock_get_codex = MagicMock()
            mock_get_agy = MagicMock()
            mock_snapshot = MagicMock()
            mock_discover = MagicMock()
            mock_save_json = MagicMock()
            mock_popen = MagicMock()
            mock_subproc_run = MagicMock()

            with patch.object(cotacli, "CONFIG_DIR", cfg), \
                 patch.object(cotacli, "CACHE_DIR", cache), \
                 patch.object(cotacli, "rpc_codex_rate_limits", mock_rpc), \
                 patch.object(cotacli, "read_agy_cli", mock_read_agy), \
                 patch.object(cotacli, "get_codex", mock_get_codex), \
                 patch.object(cotacli, "get_agy", mock_get_agy), \
                 patch.object(cotacli, "snapshot", mock_snapshot), \
                 patch.object(cotacli, "discover_cli_paths", mock_discover), \
                 patch.object(cotacli, "save_json", mock_save_json), \
                 patch("subprocess.Popen", mock_popen), \
                 patch("subprocess.run", mock_subproc_run), \
                 patch("sys.stdout", new_callable=StringIO):
                code = cotacli.doctor()
                self.assertEqual(code, 0)

            # Nenhuma chamada a funções proibidas
            mock_rpc.assert_not_called()
            mock_read_agy.assert_not_called()
            mock_get_codex.assert_not_called()
            mock_get_agy.assert_not_called()
            mock_snapshot.assert_not_called()
            mock_discover.assert_not_called()
            mock_save_json.assert_not_called()
            mock_popen.assert_not_called()
            mock_subproc_run.assert_not_called()

            # Nenhuma mutação de arquivo criada
            self.assertEqual(list(cfg.iterdir()), [])
            self.assertEqual(list(cache.iterdir()), [])

    def test_doctor_cache_metadata_recent_expired_and_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cache_file = temp_path / "codex.json"
            now = time.time()

            # Caso 1: Ausente
            status, msg = cotacli.check_cache_metadata(cache_file, "Teste")
            self.assertEqual(status, "INFO")
            self.assertIn("nenhum registro encontrado", msg)

            # Caso 2: Recente (100 segundos)
            cache_file.write_text('{"windows": {}}', encoding="utf-8")
            os.utime(cache_file, (now - 100, now - 100))
            status, msg = cotacli.check_cache_metadata(cache_file, "Teste")
            self.assertEqual(status, "OK")
            self.assertIn("cache recente", msg)

            # Caso 3: Expirado (> 600 segundos)
            os.utime(cache_file, (now - 1200, now - 1200))
            status, msg = cotacli.check_cache_metadata(cache_file, "Teste")
            self.assertEqual(status, "ALERTA")
            self.assertIn("cache antigo/expirado", msg)

    def test_doctor_non_kde_environment_does_not_require_plasma(self):
        with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "GNOME", "KDE_FULL_SESSION": ""}):
            results = cotacli.check_plasma_environment()
            self.assertEqual(len(results), 1)
            status, msg = results[0]
            self.assertEqual(status, "INFO")
            self.assertIn("modo terminal ativo", msg)

    def test_doctor_kde_environment_checks_plasma_tools(self):
        with patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "KDE"}), \
             patch("shutil.which", return_value="/usr/bin/kpackagetool6"):
            results = cotacli.check_plasma_environment()
            statuses = [r[0] for r in results]
            self.assertIn("OK", statuses)

    def test_widget_identifier_consistency_across_python_metadata_and_installer(self):
        """COTA-01.1: ID do widget deve ser idêntico em cotacli.py, metadata.json e install-widget.sh."""
        repo_root = Path(__file__).resolve().parent.parent
        metadata_file = repo_root / "cotacli-widget" / "metadata.json"
        installer_file = repo_root / "install-widget.sh"

        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        plugin_id = metadata.get("KPlugin", {}).get("Id")
        self.assertEqual(plugin_id, cotacli.PLASMA_WIDGET_ID)
        self.assertEqual(cotacli.PLASMA_WIDGET_ID, "org.cotacli.quotas")

        installer_content = installer_file.read_text(encoding="utf-8")
        self.assertIn(f"plasmoids/{cotacli.PLASMA_WIDGET_ID}", installer_content)

        widget_path = cotacli.plasma_widget_path()
        self.assertEqual(widget_path.name, cotacli.PLASMA_WIDGET_ID)

    def test_doctor_kde_environment_with_widget_installed_does_not_recommend_installation(self):
        """COTA-01.1: Se widget org.cotacli.quotas existir, relata OK e não instrui instalar."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cfg = temp_path / "config"
            cache = temp_path / "cache"
            cfg.mkdir()
            cache.mkdir()

            plasmoid_dir = temp_path / ".local" / "share" / "plasma" / "plasmoids" / cotacli.PLASMA_WIDGET_ID
            plasmoid_dir.mkdir(parents=True)

            with patch.object(Path, "home", return_value=temp_path), \
                 patch.object(cotacli, "CONFIG_DIR", cfg), \
                 patch.object(cotacli, "CACHE_DIR", cache), \
                 patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "KDE"}), \
                 patch("shutil.which", return_value="/usr/bin/kpackagetool6"), \
                 patch("sys.stdout", new_callable=StringIO) as out:
                results = cotacli.check_plasma_environment()
                statuses = [r[0] for r in results]
                self.assertIn("OK", statuses)
                installed_msg = [r[1] for r in results if "Widget do Plasma:" in r[1]][0]
                self.assertIn("instalado em", installed_msg)
                self.assertIn(cotacli.PLASMA_WIDGET_ID, installed_msg)

                code = cotacli.doctor()
                self.assertEqual(code, 0)
                output = out.getvalue()
                self.assertIn(f"Widget do Plasma: instalado em {plasmoid_dir}", output)
                self.assertNotIn("bash install-widget.sh", output)

    def test_doctor_kde_environment_with_widget_missing_recommends_installation(self):
        """COTA-01.1: Se widget estiver ausente em ambiente KDE, informa opcional e instrui instalar."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cfg = temp_path / "config"
            cache = temp_path / "cache"
            cfg.mkdir()
            cache.mkdir()

            with patch.object(Path, "home", return_value=temp_path), \
                 patch.object(cotacli, "CONFIG_DIR", cfg), \
                 patch.object(cotacli, "CACHE_DIR", cache), \
                 patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "KDE"}), \
                 patch("shutil.which", return_value="/usr/bin/kpackagetool6"), \
                 patch("sys.stdout", new_callable=StringIO) as out:
                results = cotacli.check_plasma_environment()
                missing_msg = [r[1] for r in results if "Widget do Plasma:" in r[1]][0]
                self.assertIn("não instalado", missing_msg)

                code = cotacli.doctor()
                self.assertEqual(code, 0)
                output = out.getvalue()
                self.assertIn("Widget do Plasma: não instalado", output)
                self.assertIn("bash install-widget.sh", output)

    def test_doctor_plasma_widget_handles_permission_error_gracefully(self):
        """COTA-01.1: PermissionError na verificação do widget é tratado como ALERTA sem traceback."""
        mock_widget_path = MagicMock(spec=Path)
        mock_widget_path.exists.side_effect = PermissionError(13, "Permission denied")

        with patch.object(cotacli, "plasma_widget_path", return_value=mock_widget_path), \
             patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "KDE"}), \
             patch("shutil.which", return_value="/usr/bin/kpackagetool6"):
            results = cotacli.check_plasma_environment()
            statuses = [r[0] for r in results]
            self.assertIn("ALERTA", statuses)
            error_msg = [r[1] for r in results if "Widget do Plasma:" in r[1]][0]
            self.assertIn("erro ao verificar instalação", error_msg)
            self.assertIn("Permission denied", error_msg)

    def test_main_cli_invokes_doctor(self):
        with patch.object(sys, "argv", ["cotacli", "doctor"]), \
             patch.object(cotacli, "doctor", return_value=0) as mock_doc:
            code = cotacli.main()
            self.assertEqual(code, 0)
            mock_doc.assert_called_once()

    def test_check_cache_metadata_handles_permission_error_on_exists(self):
        """AUD-04: PermissionError em path.exists() deve ser tratado como ALERTA sem lançar exceção."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.side_effect = PermissionError(13, "Permission denied")
        status, msg = cotacli.check_cache_metadata(mock_path, "Cache AGY")
        self.assertEqual(status, "ALERTA")
        self.assertIn("erro ao consultar metadados", msg)
        self.assertIn("Permission denied", msg)

    def test_check_cache_metadata_handles_permission_error_on_stat(self):
        """AUD-04: PermissionError em path.stat() deve ser tratado como ALERTA sem lançar exceção."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.stat.side_effect = PermissionError(13, "Permission denied")
        status, msg = cotacli.check_cache_metadata(mock_path, "Cache Codex")
        self.assertEqual(status, "ALERTA")
        self.assertIn("erro ao consultar metadados", msg)
        self.assertIn("Permission denied", msg)

    def test_doctor_handles_inaccessible_cache_and_config_without_traceback(self):
        """AUD-04 integração: diretório inacessível gera diagnóstico controlado com FALHA e exit code 1."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            locked_dir = temp_path / "locked_root"
            locked_dir.mkdir()
            # Diretório sem permissão de travessia e leitura
            os.chmod(locked_dir, 0o000)
            try:
                target_config = locked_dir / "cotacli_cfg"
                target_cache = locked_dir / "cotacli_cache"
                with patch.object(cotacli, "CONFIG_DIR", target_config), \
                     patch.object(cotacli, "CACHE_DIR", target_cache), \
                     patch.object(cotacli, "CODEX_PATH", target_cache / "codex.json"), \
                     patch.object(cotacli, "AGY_CACHE_PATH", target_cache / "agy.json"), \
                     patch.object(cotacli, "CLAUDE_PATH", target_cache / "claude.json"), \
                     patch.object(cotacli, "AGY_MANUAL_PATH", target_config / "antigravity.json"), \
                     patch.object(cotacli, "CLI_PATHS", target_config / "cli-paths.json"), \
                     patch("sys.stdout", new_callable=StringIO) as out:
                    code = cotacli.doctor()
                    self.assertEqual(code, 1)
                    output = out.getvalue()
                    self.assertIn("FALHA", output)
                    self.assertIn("RESUMO DO DIAGNÓSTICO", output)
                    self.assertIn("Resultado: FALHA", output)
                    self.assertNotIn("Traceback", output)
            finally:
                os.chmod(locked_dir, 0o700)


if __name__ == "__main__":
    unittest.main()
