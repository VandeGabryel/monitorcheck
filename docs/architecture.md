# Arquitetura do MonitorCheck

Este documento descreve a arquitetura implementada no estado atual do projeto.

## Visão geral

```text
CLI ─┐
     ├─> validation.py
GUI ─┘
         |
         v
      runner.py
         |
         +--> DNS
         +--> TCP
         +--> HTTP/HTTPS
         |
         v
      CheckResult
```

CLI e GUI são camadas de apresentação independentes. Ambas validam entradas
pelas mesmas regras e enviam dados já validados ao runner. O núcleo não imprime
resultados e não conhece argumentos de linha de comando nem widgets.

## Componentes

### Entrypoints

- `monitorcheck.__main__` executa a CLI com `python -m monitorcheck`;
- o script `monitorcheck` aponta para `monitorcheck.cli:main`;
- `monitorcheck.gui.__main__` executa a GUI com `python -m monitorcheck.gui`.

### Validação compartilhada

`validation.py` valida sintaticamente:

- host ou endereço IP;
- lista explícita de portas TCP;
- URL HTTP/HTTPS;
- timeout positivo e finito.

O módulo não consulta a rede e não depende de `argparse` ou Tkinter. Erros usam
`ValidationError`. A CLI os adapta para `argparse.ArgumentTypeError`; a GUI os
apresenta em um `messagebox` antes de iniciar qualquer verificação.

### Orquestração

`runner.py` recebe host, portas opcionais, URL opcional e timeout já validados.
Ele:

1. sempre executa a resolução DNS;
2. executa TCP somente quando existem portas;
3. executa HTTP/HTTPS somente quando existe URL;
4. retorna `RunResults`, sem imprimir ou conhecer a interface chamadora.

A execução dentro do runner é sequencial. `RunResults.all_results` reúne apenas
as verificações efetivamente executadas.

### Contratos

`models.py` define os contratos usados por checks e interfaces:

- `CheckType`: `DNS`, `TCP` e `HTTP`;
- `ResultStatus`: `SUCCESS`, `WARNING`, `ERROR`, `INFO` e `SKIPPED`;
- `CheckResult`: tipo, alvo, status, mensagem, duração e detalhes.

`CheckResult` é congelado e não depende de rede, terminal ou Tkinter.

### Verificações de rede

`checks/dns.py` usa `socket.getaddrinfo`, considera IPv4 e IPv6, remove
duplicatas e converte falhas do resolvedor em `CheckResult`.

`checks/tcp.py` usa `socket.create_connection`, aplica o timeout por porta e
retorna um resultado independente para sucesso, recusa, timeout ou erro de
socket.

`checks/http.py` usa `urllib.request` para GET, preserva a validação TLS padrão
e registra URL solicitada, URL final, código HTTP e duração. Erros HTTP, de rede,
timeout e TLS são transformados em resultados controlados.

Nenhum check imprime diretamente ou importa código das interfaces.

## CLI

`cli.py` é responsável por:

- definir e interpretar os argumentos com `argparse`;
- adaptar as validações compartilhadas ao comportamento da CLI;
- criar `CliConfig`;
- chamar o runner;
- enviar os resultados ao presenter de terminal;
- retornar o código de saída.

`presenters/terminal.py` formata as seções, detalhes, legenda e resumo. As cores
ANSI são opcionais e nunca substituem os rótulos textuais. Uma execução retorna
`1` quando existe `ERROR`, `0` nos demais resultados válidos e `2` para entrada
inválida detectada pelo parser.

## GUI

`gui/app.py` contém somente responsabilidades da apresentação gráfica:

- formulário e validação antes da execução;
- painéis DNS e HTTP/HTTPS;
- tabela com uma linha por resultado TCP;
- resumo e estados textuais;
- bloqueio e restauração dos controles durante a execução;
- temas Claro e Escuro;
- redimensionamento e estilos `ttk`.

### Execução assíncrona

Tkinter deve ser atualizado pela thread que mantém seu loop de eventos. Para
evitar congelamento:

1. a thread principal valida os campos e desabilita controles conflitantes;
2. uma `threading.Thread` daemon chama `run_checks`;
3. o worker publica sucesso ou erro em uma `queue.Queue`;
4. a thread principal consulta a fila periodicamente com `after()`;
5. somente a thread principal atualiza widgets e restaura controles.

Falhas de rede esperadas já chegam como `CheckResult`. Uma proteção adicional
na fronteira da GUI apresenta erros inesperados sem derrubar a janela.

### Temas

Os temas `dark` e `light` são paletas declarativas aplicadas com `ttk.Style`
sobre o tema-base `clam`, quando disponível. A troca de tema reconfigura estilos
e tags da tabela existente; não recria widgets, não altera resultados e não
interfere na thread ou na fila.

As cores são complementares. Todos os estados continuam identificados por
texto. O tema inicial é Escuro e a escolha não é persistida.

## Separação entre lógica e apresentação

```text
entrada -> validation -> runner -> checks -> CheckResult
                                        |
                    +-------------------+-------------------+
                    |                                       |
                    v                                       v
            presenter de terminal                    apresentação GUI
```

Essa separação permite testar validação, orquestração, rede e apresentação sem
misturar regras de interface. A GUI não importa a CLI, e os checks não importam
nenhuma apresentação.

## Tratamento de falhas

Falhas esperadas são representadas por `ResultStatus.ERROR`, sem traceback para
o usuário. `WARNING` afeta o resultado geral, mas não é falha para o código de
saída da CLI. Checks opcionais ausentes não são executados; na GUI aparecem como
`SKIPPED`/não solicitados.

## Biblioteca padrão e dependências

O código em tempo de execução utiliza apenas a biblioteca padrão, incluindo:

- `argparse`, `dataclasses`, `enum` e `typing`;
- `socket`, `ssl`, `urllib.request` e `urllib.error`;
- `threading`, `queue`, `tkinter` e `ttk`;
- `time`, `ipaddress`, `re`, `math`, `sys` e `os`.

Não existem dependências externas declaradas em tempo de execução.

## Testes

A suíte cobre contratos, validação, runner, DNS, TCP, HTTP/HTTPS, relatório,
códigos de saída e lógica de apresentação da GUI. Rede e GUI são testadas com
mocks ou funções puras, sem exigir Internet ou display gráfico real.
