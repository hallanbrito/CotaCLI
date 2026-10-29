# CLI e contrato JSON

| Comando | Efeito |
| --- | --- |
| `cotacli` / `cotacli show` | Exibe a tabela com cache de até 10 minutos. |
| `cotacli refresh` | Força leitura do Codex e do AGY; Claude Code depende da próxima captura da status line. |
| `cotacli snapshot` | Retorna um único objeto JSON para interfaces. |
| `cotacli snapshot --refresh` | Retorna JSON após forçar as leituras disponíveis. |
| `cotacli discover` | Salva caminhos das CLIs para ambientes com `PATH` diferente. |
| `cotacli --version` | Mostra a versão do motor. |

O widget usa `snapshot` e `snapshot --refresh`. O contrato atual tem `schema: 1` e uma lista ordenada de provedores. Exemplo **ilustrativo**:

```json
{
  "schema": 1,
  "providers": [
    {
      "id": "agy-gemini",
      "name": "AGY / Gemini",
      "windows": {
        "5h": {"remaining": 96.5, "reset": 1793309400},
        "week": {"remaining": 89.1, "reset": 1793465820}
      },
      "status": "automático, cache 2min"
    }
  ],
  "updated": 1793290000
}
```

`remaining` é um percentual entre 0 e 100. `reset` e `updated` são timestamps Unix em segundos; a interface os converte para o fuso local. Uma janela pode ser `null` quando o provedor não a informou. A lista omite CLIs não detectadas; Claude Code também é omitido sem cota atual válida. Valores de cache antigo podem ser exibidos com um `status` explícito, então integrações devem mostrar essa condição ao usuário.

## Contingência manual do AGY

```sh
cotacli set agy-gemini 65 82
cotacli set agy-others 100 90
```

Os valores são percentuais **restantes** confirmados manualmente. O CotaCLI usa essa contingência somente se a leitura automática falhar e não houver cache automático; não trate o registro manual como sincronização com o provedor.

## Claude Code: captura opcional

A [status line do Claude Code](https://code.claude.com/docs/en/statusline) recebe JSON pelo stdin após eventos da sessão. Para uma conta Pro/Max elegível, o JSON pode conter `rate_limits.five_hour` e `rate_limits.seven_day`, com `used_percentage` e `resets_at`. Os campos podem não existir antes da primeira resposta, em contas sem assinatura ou quando uma janela expirou.

Configure `~/.claude/settings.json` preservando os campos já existentes:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.local/bin/cotacli capture-claude"
  }
}
```

Se você já tem outra status line, integre `cotacli capture-claude` ao script atual em vez de substituí-lo. O comando salva somente percentual restante, reset e instante de captura, mas imprime `CotaCLI · Claude` na linha do Claude. O `refresh` não inicia uma conversa nem força atualização da cota do Claude; uma nova resposta na sessão traz a leitura seguinte.
