# Prompt para adaptar o CotaCLI ao meu sistema

O CotaCLI tem uma CLI Python e um widget para KDE Plasma 6. Este texto é um **pedido de trabalho para um agente de código**, não um instalador. Copie o bloco abaixo, preencha os campos entre colchetes e execute-o em um clone ou fork de <https://github.com/hallanbrito/CotaCLI>. Só considere a adaptação pronta depois de testar no ambiente informado.

```text
Quero adaptar o projeto CotaCLI (https://github.com/hallanbrito/CotaCLI) para:
- Sistema operacional e versão: [ex.: Windows 11, macOS 15, Ubuntu 26.04]
- Desktop, barra ou shell: [ex.: GNOME, XFCE, Windows Explorer, macOS menu bar]
- Versão do Python: [versão]
- CLIs instaladas e autenticadas: [codex, agy, claude; indique somente as que você realmente usa]

Objetivo: preservar a leitura de cotas do projeto e oferecer uma interface gráfica
simples na área de notificações/barra do meu ambiente. Ao passar o mouse, mostrar
um resumo; ao clicar, abrir cartões com percentuais RESTANTES das janelas de 5h
e semanal, horários locais de renovação, status de atualização e botão de refresh.
Mostrar somente provedores detectados; Claude Code só deve aparecer se houver
cota atual válida. A CLI de terminal também deve continuar utilizável.

Trabalhe em uma branch própria. Primeiro leia README.md, docs/arquitetura.md,
docs/provedores.md, docs/cli.md, cotacli.py, install-widget.sh,
cotacli-widget/contents/ui/main.qml e os testes. Explique brevemente quais
partes são portáveis e quais dependem do Linux/KDE. Em especial, verifique se
o protocolo do Codex que usa select() em um pipe funciona no sistema alvo;
não suponha que funciona no Windows. Revise caminhos de configuração/cache,
descoberta de executáveis, subprocessos, permissões e instalação sem sudo.

Implemente um adaptador de interface adequado ao sistema informado. Mantenha
snapshot (schema: 1) como contrato entre motor e interface, ou evolua o
contrato com migração e testes se for indispensável. Não faça consulta de
provedor na thread da interface. Preserve o cache e sinalize dados antigos.
Não leia nem copie credenciais, cookies ou tokens; as CLIs originais cuidam
da autenticação. A chamada automática do AGY /usage só pode ser aceita quando
confirmar zero turnos e zero tokens. Não estime cota por custo ou logs.

Entregue:
1. Código da CLI e da interface adaptados, com comentários didáticos em PT-BR.
2. Instalação, atualização e remoção para o sistema alvo, sem alterar o KDE
   original de quem já usa Plasma.
3. Testes automatizados para detecção, parsing, cache, ausência de provedores
   e contrato JSON; teste manual da bandeja/barra com evidência do clique,
   tooltip, refresh, reset no horário local e caso sem uma CLI instalada.
4. README e docs atualizados com uma tabela de suporte: testado, parcial ou
   ainda não testado. Não declare suporte oficial sem validar no sistema real.
5. Um PR com resumo, comandos de teste, resultado e limitações conhecidas.

Não publique pré-release ou release. Se você não puder testar no meu sistema,
entregue o código e um roteiro de homologação, deixando o suporte como parcial.
```

Se você só quer o terminal em outra distribuição Linux, use a seção **Somente terminal** em [Instalação](instalacao.md); talvez não seja necessário adaptar nada. O widget atual é exclusivo do Plasma 6. Uma porta para outro sistema deve verificar as diferenças de `select`, caminhos e subprocessos antes de prometer funcionamento.
