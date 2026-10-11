# Arquitetura planejada

## Princípio principal

A lógica das verificações não deve depender da interface de linha de comando
nem da forma usada para exibir os resultados. Essa separação permitirá que uma
interface futura reutilize o mesmo núcleo.

## Camadas

### Entrada

`cli.py` será responsável por interpretar argumentos, validar a entrada e
orquestrar as verificações solicitadas.

### Verificações

O pacote `checks` conterá funções independentes para DNS, TCP e HTTP/HTTPS.
Elas deverão retornar resultados estruturados e não imprimir diretamente no
terminal.

### Resultados

`models.py` concentrará os tipos compartilhados. O contrato deverá representar,
no mínimo:

- tipo e alvo da verificação;
- estado (`SUCCESS`, `WARNING`, `ERROR`, `INFO` ou `SKIPPED`);
- duração;
- mensagem curta;
- detalhes específicos opcionais.

### Apresentação

`presenters/terminal.py` converterá resultados em texto. As cores ANSI serão
opcionais, acompanhadas por legenda, e nunca serão a única indicação do estado.

## Fluxo previsto

```text
argumentos da CLI
      |
      v
validação e orquestração
      |
      +--> DNS
      +--> TCP
      +--> HTTP/HTTPS
      |
      v
resultados estruturados
      |
      v
relatório no terminal + código de saída
```

## Dependências

A Etapa 1 priorizará os seguintes módulos da biblioteca padrão:

- `argparse` para a CLI;
- `socket` para DNS e TCP;
- `urllib.request` e `urllib.error` para HTTP/HTTPS;
- `ssl` para erros e configuração TLS;
- `time` para medição de duração;
- `dataclasses` e `enum` para os resultados.

## Extensão futura

Uma possível interface web deverá consumir os mesmos serviços e modelos. A
tecnologia dessa interface será escolhida apenas após a conclusão da Etapa 1.
Não há pacote `web` nem dependência web nesta estrutura inicial.

