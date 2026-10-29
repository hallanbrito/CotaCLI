# Provedores e limites

## Codex

O CotaCLI consulta `account/rateLimits/read` em `codex app-server`. Identifica janelas próximas de 5 horas e 7 dias pela duração retornada, converte o percentual usado em restante e mostra o horário de renovação. Precisa da CLI instalada e autenticada. Essa é a cota da **CLI Codex**, não um contador geral de conversas do ChatGPT.

## Antigravity

O CotaCLI executa `agy -p /usage --output-format json` com timeout de 60 segundos. Só aceita uma resposta `SUCCESS` do comando interno `usage` com zero turnos e zero tokens registrados. Lê os buckets `gemini-5h`, `gemini-weekly`, `3p-5h` e `3p-weekly` e os apresenta como **AGY / Gemini** e **AGY / Claude+GPT**. Os dois últimos são a cota compartilhada dos modelos Claude e GPT oferecidos dentro do AGY, e não uma assinatura separada em Anthropic ou OpenAI.

Se a versão da CLI mudar o contrato de `/usage`, o monitor não inventa um número novo: informa erro ou mostra cache anterior rotulado como antigo. O comando de diagnóstico é `cotacli snapshot --refresh`.

## Claude Code

A integração é opcional e passiva: `capture-claude` recebe o JSON da status line depois de uma resposta em uma conta elegível. Claude só aparece quando há cota real atual e não expirada. A leitura é descartada da tela depois de uma hora sem nova captura. Ainda falta homologação com uma conta Pro/Max real; os testes cobrem a estrutura documentada com dados sintéticos.

## Fora do escopo atual

O projeto não monitora cotas de APIs cobradas por token, consumo geral de ChatGPT, outras IDEs/CLIs ou limites de modelos que os provedores não informaram. Instalar uma CLI sem conta autenticada não cria uma cota.
