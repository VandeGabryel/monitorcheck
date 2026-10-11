# Arquitetura do MonitorCheck

Este documento descreve a arquitetura implementada na versão 1.0.0.

## Princípio

A lógica de conectividade é independente da CLI e da apresentação. As
verificações não imprimem no terminal: elas retornam `CheckResult`, permitindo
que a orquestração e o relatório permaneçam separados.

## Componentes

### Entrypoints

- `monitorcheck.__main__` permite `python -m monitorcheck`;
- o script `monitorcheck` aponta para `monitorcheck.cli:main`.

### Interfaces e validação

`validation.py` concentra as regras sintáticas de host, portas, URL e timeout,
sem depender de `argparse` ou de widgets. A CLI adapta erros de validação para
`argparse.ArgumentTypeError`; a GUI apresenta os mesmos erros em uma caixa de
diálogo.

`cli.py` mantém:

- parsing de host, portas, URL, timeout e `--no-color`;
- criação de `CliConfig`;
- envio dos resultados ao presenter;
- definição do código de saída.

Erros de entrada seguem o comportamento controlado do `argparse`, com mensagem
de uso e código `2`, sem traceback.

`gui/app.py` mantém os widgets e a apresentação gráfica. A rede é executada em
uma `threading.Thread`; o worker publica o desfecho em uma `queue.Queue`, e a
thread principal consulta a fila com `after()` antes de atualizar os widgets.

### Orquestração compartilhada

`runner.py` recebe entradas já validadas, sempre executa DNS e condiciona TCP e
HTTP às opções recebidas. Ele retorna `RunResults`, que agrupa os `CheckResult`
sem imprimir, conhecer widgets ou depender de uma interface específica.

### Contratos

`models.py` define:

- `CheckType`: `DNS`, `TCP` e `HTTP`;
- `ResultStatus`: `SUCCESS`, `WARNING`, `ERROR`, `INFO` e `SKIPPED`;
- `CheckResult`: tipo, alvo, status, mensagem, duração e detalhes.

`CheckResult` possui atributos congelados e não depende de terminal ou rede.

### Verificações

`checks/dns.py`:

- usa `socket.getaddrinfo` com IPv4 e IPv6;
- remove duplicatas e ordena IPv4 antes de IPv6;
- converte falhas de resolução em `CheckResult`.

`checks/tcp.py`:

- testa sequencialmente somente as portas informadas;
- usa `socket.create_connection` com timeout por porta;
- fecha conexões bem-sucedidas imediatamente;
- distingue sucesso, recusa, timeout e outros erros de socket;
- retorna um `CheckResult` por porta.

`checks/http.py`:

- cria uma requisição GET com `urllib.request`;
- preserva a validação TLS padrão;
- não lê nem armazena o corpo;
- registra URL solicitada, URL final, código e duração;
- distingue resposta, erro HTTP, timeout, erro de rede e erro TLS.

### Apresentação

`presenters/terminal.py`:

- valida o tipo de resultado esperado por seção;
- apresenta detalhes específicos de DNS, TCP e HTTP/HTTPS;
- calcula totais com `ReportSummary`;
- determina o resultado geral;
- aplica cores ANSI opcionais sem remover os rótulos textuais;
- desativa cores em saída não interativa, `TERM=dumb` ou `NO_COLOR`.

## Fluxo de execução

```text
CLI/GUI -> validação -> runner
                         |
   +--> resolve_host(host)
   +--> check_tcp_ports(host, ports, timeout), se solicitado
   +--> check_http(url, timeout), se solicitado
                         |
                         v
                    RunResults
                      /     \
        presenter terminal   apresentação GUI
```

A execução é intencionalmente sequencial. DNS é sempre executado; TCP e HTTP
são condicionais aos argumentos `--ports` e `--url`.

## Tratamento de falhas

Falhas esperadas de rede são representadas por `ResultStatus.ERROR` e não
escapam como traceback. Um aviso altera o resultado geral para `WARNING`, mas
somente a presença de `ERROR` produz código de saída `1`.

## Biblioteca padrão utilizada

- `argparse`, `dataclasses`, `enum`, `typing`;
- `socket`, `ssl`, `urllib.request`, `urllib.error`;
- `time`, `ipaddress`, `re`, `math`, `sys` e `os`.

Não existem dependências externas em tempo de execução.

## Testes

A suíte em `tests/` cobre contratos, validação da CLI, DNS, TCP, HTTP/HTTPS,
presenter, cores, resumo e códigos de saída. Operações de rede são simuladas
com `unittest.mock`, evitando dependência de Internet.

## Camada GUI em desenvolvimento

Os Gates GUI-G1 e GUI-G2 adicionam uma camada de apresentação separada em
`monitorcheck.gui`, implementada somente com `tkinter` e `ttk`:

- `gui/__main__.py`: entrypoint de `python -m monitorcheck.gui`;
- `gui/app.py`: janela, formulário e áreas visuais de resultados;
- `gui/__init__.py`: API pública mínima da camada.

O botão inicia a orquestração compartilhada fora da thread principal, permanece
desabilitado durante a execução e volta a ser habilitado ao final. Os painéis
começam no estado “Nenhuma verificação foi executada.” TCP e HTTP não
solicitados são identificados explicitamente, sem serem contabilizados como
falha. A integração não altera os checks nem a arquitetura pública da CLI
1.0.0; refinamentos visuais pertencem ao GUI-G3.
