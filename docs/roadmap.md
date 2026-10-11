# Roadmap do MonitorCheck

## MVP 1.0.0 — concluído

Os seis gates da Etapa 1 foram concluídos. O escopo entregue permanece limitado
a DNS, TCP, HTTP/HTTPS e relatório no terminal.

### MC-G3.1 — Contratos e CLI

- [x] definir modelos de resultado e estados;
- [x] definir argumentos posicionais e opcionais;
- [x] validar host, portas, URL e timeout;
- [x] apresentar erros de entrada sem traceback.

### MC-G3.2 — Resolução DNS

- [x] resolver IPv4 e IPv6 com `socket`;
- [x] remover endereços duplicados em ordem determinística;
- [x] tratar host inexistente e falhas do resolvedor;
- [x] registrar duração e mensagem.

### MC-G3.3 — Testes TCP

- [x] testar somente portas explícitas;
- [x] aplicar timeout por porta;
- [x] distinguir sucesso, recusa, timeout e erro de socket;
- [x] manter resultados independentes e execução sequencial.

### MC-G3.4 — HTTP/HTTPS

- [x] aceitar URL HTTP ou HTTPS validada;
- [x] executar GET com a biblioteca padrão;
- [x] registrar código, URL final e duração;
- [x] tratar erro HTTP, conexão, timeout e TLS;
- [x] preservar a validação TLS padrão.

### MC-G3.5 — Relatório no terminal

- [x] consolidar seções DNS, TCP e HTTP/HTTPS;
- [x] apresentar estado, mensagem, duração e detalhes;
- [x] calcular resumo e resultado geral;
- [x] adicionar cores opcionais e legenda textual;
- [x] implementar `--no-color` e detecção de saída sem ANSI;
- [x] documentar códigos de saída.

### MC-G3.6 — Qualidade e entrega

- [x] revisar código, imports, mensagens e documentação;
- [x] executar a suíte automatizada completa;
- [x] manter testes de rede independentes da Internet;
- [x] documentar instalação, uso, arquitetura e limitações;
- [x] atualizar a versão para 1.0.0.

## Critérios do MVP

- [x] Python 3.10 ou superior;
- [x] nenhuma dependência externa em tempo de execução;
- [x] falhas esperadas apresentadas sem traceback;
- [x] código de saída adequado para automação;
- [x] lógica de rede separada da apresentação;
- [x] cobertura automatizada dos fluxos principais.

## Etapa 2 — GUI local em desenvolvimento

### GUI-G1 — Estrutura visual inicial

- [x] criar o pacote separado `monitorcheck.gui`;
- [x] adicionar o entrypoint `python -m monitorcheck.gui`;
- [x] criar os campos de host, portas, URL e timeout;
- [x] criar áreas separadas para DNS, TCP, HTTP/HTTPS e resumo;
- [x] manter o botão de execução desabilitado;
- [x] preservar integralmente o comportamento da CLI e dos checks;
- [x] reservar a integração das verificações para um gate posterior.

Nesse gate, a interface permaneceu somente visual, sem execução de rede.

### GUI-G2 — Integração com o núcleo

- [x] extrair validações para um módulo neutro e compartilhado;
- [x] criar uma camada de orquestração independente de CLI e GUI;
- [x] preservar argumentos, relatório e códigos de saída da CLI;
- [x] validar os campos da GUI antes da execução;
- [x] executar DNS e, opcionalmente, TCP e HTTP/HTTPS;
- [x] realizar operações de rede fora da thread principal do Tkinter;
- [x] impedir execuções simultâneas e indicar o estado em andamento;
- [x] atualizar widgets somente pela thread principal;
- [x] apresentar resultados e indicar verificações não solicitadas;
- [x] cobrir validação e orquestração com testes sem Internet ou display.

A integração funcional básica está concluída. Cores, refinamento visual e UX
final permanecem reservados ao GUI-G3 e não fazem parte deste gate.

## Evolução futura — fora da versão 1.0.0

Os itens abaixo são possibilidades, não compromissos nem requisitos do MVP:

- interface web local, com tecnologia ainda a decidir;
- execução paralela e monitoramento periódico;
- persistência e histórico;
- exportação estruturada, incluindo JSON;
- métodos HTTP adicionais, autenticação e cabeçalhos personalizados;
- novas verificações de rede;
- empacotamento adicional ou automação de entrega.

Qualquer evolução deverá reutilizar os contratos e as verificações existentes
sem acoplar o núcleo a uma interface específica.

## Fora do escopo do MVP entregue

- ping ICMP;
- varredura de intervalos de portas;
- banco de dados;
- API ou interface web;
- Docker;
- CI/CD;
