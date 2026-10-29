# Contribuir

Obrigado por ajudar a tornar o monitor mais confiável. Este é um protótipo: mudanças pequenas e verificáveis são mais fáceis de revisar.

## Antes de propor uma alteração

1. Abra uma issue descrevendo o comportamento, sua distribuição/desktop, versões das CLIs e a saída relevante **sem credenciais nem e-mails**.
2. Para um novo provedor, documente uma fonte de cota real e estável; não deduza percentuais de logs de uso ou custos.
3. Mantenha o motor sem dependências Python externas, quando viável, e o widget como consumidor do JSON `snapshot`.

## Verificações locais

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile cotacli.py
bash -n install-widget.sh
python3 -m json.tool cotacli-widget/metadata.json >/dev/null
```

Se alterar o widget, teste no Plasma 6: ícone na bandeja, abertura pelo clique, três cartões completos, renovação em horário local, atualização manual e cenário sem alguma CLI instalada. Inclua um relato do teste visual no PR. Evite publicar capturas que revelem conta, notificações ou outros dados pessoais.

Não crie pré-release/release a partir de contribuições isoladas; a decisão de publicação depende de homologação do projeto.
