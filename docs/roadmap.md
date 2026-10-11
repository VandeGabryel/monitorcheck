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
