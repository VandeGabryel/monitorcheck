# MonitorCheck

MonitorCheck é uma aplicação CLI acadêmica, escrita em Python, para verificações
básicas de conectividade de hosts e serviços. O MVP utiliza somente a biblioteca
padrão em tempo de execução e apresenta os resultados diretamente no terminal.

> Use o MonitorCheck apenas em hosts e serviços próprios ou para os quais exista
> autorização de teste.

## Objetivo

O projeto reúne, em um fluxo simples e legível, verificações de DNS, portas TCP
e endpoints HTTP/HTTPS. Cada operação gera um resultado estruturado, e a camada
de apresentação consolida esses resultados em um relatório com resumo final.

## Funcionalidades

- resolução DNS com endereços IPv4 e IPv6;
- remoção de endereços DNS duplicados em ordem determinística;
- teste sequencial de portas TCP explicitamente informadas;
- distinção entre porta aberta, conexão recusada, timeout e erro de socket;
- requisição HTTP/HTTPS com método GET;
- acompanhamento da URL final após redirecionamentos;
- tratamento controlado de erro HTTP, timeout, falha de rede e erro TLS;
- medição individual da duração das verificações;
- relatório consolidado com resumo e códigos de saída;
- cores ANSI opcionais, sem depender delas para comunicar o resultado.

## Requisitos

- Python 3.10 ou superior;
- `pip` e `setuptools` para instalação do pacote;
- nenhuma dependência externa em tempo de execução.

## Instalação

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

### Linux ou macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

A instalação editável cria o comando monitorcheck.
Caso o diretório de scripts do Python não esteja disponível no PATH,
 utilize python -m monitorcheck, que executa o mesmo entrypoint.
## Uso

```text
monitorcheck HOST [--ports PORTA,...] [--url URL] [--timeout SEGUNDOS] [--no-color]
```

Equivalente pelo módulo Python:

```text
python -m monitorcheck HOST [opções]
```

### Parâmetros da CLI

| Parâmetro | Obrigatório | Descrição |
| --- | --- | --- |
| `HOST` | sim | Nome de host, endereço IPv4 ou endereço IPv6 usado no DNS e nos testes TCP. |
| `--ports PORTA,...` | não | Portas TCP explícitas, separadas por vírgulas. Valores válidos: 1 a 65535. |
| `--url URL` | não | URL completa com esquema `http` ou `https`. |
| `--timeout SEGUNDOS` | não | Timeout positivo e finito para cada teste TCP e para a operação HTTP. Padrão: `3`. |
| `--no-color` | não | Desativa completamente as sequências ANSI. |
| `-h`, `--help` | não | Exibe a ajuda da CLI. |

Portas repetidas são deduplicadas, preservando a primeira ocorrência. O host
principal sempre passa pela verificação DNS. TCP e HTTP/HTTPS só são executados
quando `--ports` e `--url`, respectivamente, forem fornecidos.

## Exemplos

Somente DNS:

```powershell
monitorcheck example.com
```

DNS e portas TCP:

```powershell
monitorcheck example.com --ports 80,443 --timeout 2
```

Todas as verificações:

```powershell
monitorcheck example.com --ports 80,443 --url https://example.com --timeout 3
```

Teste local sem cores:

```powershell
monitorcheck 127.0.0.1 --ports 8000 --url http://127.0.0.1:8000 --no-color
```

## Relatório e status

O relatório apresenta cabeçalho, alvo, timeout, seções para as verificações
solicitadas, durações, detalhes relevantes e um resumo. Os rótulos permanecem
visíveis mesmo quando as cores estão desativadas.

| Status | Cor | Interpretação |
| --- | --- | --- |
| `SUCCESS` | verde | Verificação concluída com sucesso. |
| `WARNING` | amarelo | Resposta disponível, mas inesperada ou parcial. |
| `ERROR` | vermelho | Verificação falhou. |
| `INFO` | ciano | Informação neutra. |
| `SKIPPED` | cinza | Verificação não executada. |

As cores são usadas somente em terminais interativos compatíveis. `--no-color`,
a variável de ambiente `NO_COLOR`, `TERM=dumb` e saída redirecionada desativam
ANSI.

## Códigos de saída

| Código | Significado |
| --- | --- |
| `0` | Nenhuma verificação terminou com `ERROR`; avisos não são falhas. |
| `1` | Pelo menos uma verificação terminou com `ERROR`. |
| `2` | Entrada inválida detectada pelo parser da CLI. |

## Testes

A suíte usa `unittest` e mocks para evitar dependência de Internet ou serviços
externos:

```powershell
python -m unittest discover -s tests -v
```

Sem instalar o pacote, defina `PYTHONPATH` antes da execução:

```powershell
$env:PYTHONPATH="src"
py -3 -m unittest discover -s tests -v
```

## Arquitetura resumida

```text
CLI e validação
      |
      +--> resolução DNS
      +--> testes TCP sequenciais
      +--> requisição HTTP/HTTPS
      |
      v
CheckResult
      |
      v
presenter de terminal + resumo + código de saída
```

- `cli.py`: parsing, validação e orquestração;
- `models.py`: contratos compartilhados;
- `checks/`: lógica independente de DNS, TCP e HTTP/HTTPS;
- `presenters/terminal.py`: consolidação, cores e resumo;
- `tests/`: testes unitários e de integração da CLI.

Detalhes adicionais estão em [docs/architecture.md](docs/architecture.md). O
histórico dos gates e as possibilidades futuras estão em
[docs/roadmap.md](docs/roadmap.md).

## Limitações conhecidas

- a resolução DNS usa o timeout do resolvedor do sistema operacional;
- as verificações são sequenciais;
- não há varredura de intervalos: somente portas explícitas são aceitas;
- um teste TCP confirma apenas o estabelecimento da conexão, não o protocolo;
- o timeout HTTP limita operações bloqueantes, mas não é um prazo global rígido
  para toda uma cadeia de redirecionamentos;
- HTTP/HTTPS suporta apenas GET, sem autenticação, corpo, download ou cabeçalhos
  personalizados;
- HTTPS usa a validação TLS padrão e rejeita certificados inválidos;
- não há persistência, histórico, exportação, monitoramento contínuo ou interface
  web;
- o suporte visual a ANSI depende do terminal; a informação textual é sempre
  preservada.

## Estado do projeto

O MVP funcional está concluído na versão 1.0.0. A publicação do repositório,
criação da tag e da release são etapas de distribuição posteriores à homologação do código.
