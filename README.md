# MonitorCheck

MonitorCheck é um mini-projeto acadêmico para executar verificações básicas de
conectividade de hosts e serviços.

O projeto concluiu o Gate MC-G3.5. Os contratos, a validação da CLI, as
verificações DNS, TCP e HTTP/HTTPS e o relatório de terminal estão disponíveis.

## Objetivo da Etapa 1

Entregar uma aplicação de linha de comando em Python capaz de:

- resolver nomes DNS;
- testar uma lista explícita de portas TCP;
- consultar endereços HTTP e HTTPS;
- apresentar um relatório legível no terminal;
- não possuir dependências externas em tempo de execução.

As cores do relatório serão apenas um recurso de apresentação. A saída também
deverá permanecer compreensível sem cores e permitir sua desativação.

## Uso planejado

```text
python -m pip install -e .
python -m monitorcheck example.com --ports 80,443 --url https://example.com
```

A CLI consolida as verificações executadas em um relatório com seções, resumo,
legenda e cores opcionais. O código de saída é `0` quando não há falhas e `1`
quando pelo menos uma verificação falha.

## Estrutura

```text
src/monitorcheck/
  __init__.py
  __main__.py
  cli.py
  models.py
  checks/
    dns.py
    tcp.py
    http.py
  presenters/
    terminal.py
tests/
docs/
  architecture.md
  roadmap.md
```

## Requisitos

- Python 3.10 ou superior.
- Nenhuma dependência externa na Etapa 1.

## Estado atual

- [x] Escopo inicial definido.
- [x] Estrutura do projeto criada.
- [x] Contratos dos resultados definidos em código.
- [x] Parsing e validação básica da CLI implementados.
- [x] Resolução DNS implementada.
- [x] Testes TCP implementados.
- [x] Testes HTTP/HTTPS implementados.
- [x] Relatório de terminal implementado.
- [ ] Testes automatizados concluídos.

Consulte [docs/roadmap.md](docs/roadmap.md) para as etapas e critérios de
conclusão.

