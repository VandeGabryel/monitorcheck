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

## Etapa 2 — GUI local — concluída

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

### GUI-G3 — Refinamento visual e de uso

- [x] reorganizar cabeçalho, configuração, ações, resultados e resumo;
- [x] aplicar uma identidade visual consistente com `ttk.Style`;
- [x] combinar cores e rótulos textuais para todos os estados;
- [x] estruturar os detalhes de DNS e HTTP/HTTPS;
- [x] apresentar cada porta TCP em uma linha independente;
- [x] destacar o resultado geral e manter uma legenda textual;
- [x] desabilitar campos e ações conflitantes durante a execução;
- [x] adicionar a ação de limpar resultados sem apagar a configuração;
- [x] melhorar o redimensionamento e evitar larguras fixas de texto;
- [x] oferecer temas Claro e Escuro, iniciando no tema Escuro;
- [x] atualizar imediatamente estilos e linhas TCP sem recriar widgets;
- [x] manter testes visuais restritos à lógica testável sem display.

O GUI-G3 foi concluído com os temas Claro e Escuro, apresentação estruturada e
padronização visual dos componentes.

### GUI-G4 — Qualidade final e preparação da entrega

- [x] revisar código e documentação final;
- [x] confirmar separação entre núcleo, CLI e GUI;
- [x] executar compilação e suíte automatizada completas;
- [x] verificar dependências instaladas e integridade do diff;
- [x] executar smoke test da CLI;
- [x] confirmar consistência da versão declarada;
- [x] registrar limitações e checklist de homologação manual.

O GUI-G4 foi concluído após compilação, suíte automatizada, verificação de
dependências, integridade do diff e smoke tests locais da CLI.

## Escopo entregue

- [x] CLI com relatório, cores opcionais e códigos de saída;
- [x] resolução DNS IPv4/IPv6;
- [x] testes de portas TCP explícitas;
- [x] verificação HTTP/HTTPS GET;
- [x] contratos e validações compartilhados;
- [x] runner independente das interfaces;
- [x] GUI local responsiva em Tkinter;
- [x] execução da rede fora da thread principal da GUI;
- [x] temas Claro e Escuro com troca em tempo de execução;
- [x] testes automatizados sem Internet ou display real.

## Fora do escopo

Os itens abaixo são possibilidades, não compromissos nem requisitos do MVP:

- interface web local, com tecnologia ainda a decidir;
- execução paralela, periódica ou monitoramento contínuo;
- persistência e histórico;
- exportação estruturada, incluindo JSON;
- métodos HTTP adicionais, autenticação e cabeçalhos personalizados;
- ping ICMP;
- varredura automática ou por intervalos de portas;
- banco de dados e API;
- Docker e CI/CD;
- novas verificações de rede;
- empacotamento adicional ou automação de entrega.

Qualquer evolução deverá reutilizar os contratos e as verificações existentes
sem acoplar o núcleo a uma interface específica.
