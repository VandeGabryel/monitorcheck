# Roadmap

## Etapa 1 — MVP CLI

### 1. Contratos e CLI

- [x] definir os modelos de resultado e estados;
- [x] definir argumentos posicionais e opcionais;
- [x] validar host, portas, URL e timeout;
- [x] impedir que erros esperados exibam traceback ao usuário.

### 2. Resolução DNS

- [x] resolver IPv4 e IPv6 com `socket`;
- [x] remover endereços duplicados;
- [x] tratar host inexistente e falhas do resolvedor;
- [x] registrar duração e mensagem objetiva.

Critério de conclusão: host válido produz uma lista de endereços e host inválido
produz um resultado de erro controlado.

### 3. Testes TCP

- [x] testar somente portas informadas pelo usuário;
- [x] aplicar timeout por tentativa;
- [x] distinguir porta aberta, conexão recusada, timeout e erro;
- [x] validar o intervalo de portas de 1 a 65535.

Critério de conclusão: cada porta gera um resultado independente sem bloquear a
execução indefinidamente.

### 4. Testes HTTP/HTTPS

- [x] aceitar URL completa com esquema `http` ou `https`;
- [x] executar uma requisição `GET`;
- [x] registrar código, URL final e duração;
- [x] tratar erros HTTP, conexão, timeout e TLS.

Critério de conclusão: respostas e falhas comuns aparecem como resultados
controlados, sem traceback.

### 5. Relatório no terminal

- [x] exibir seções para DNS, TCP e HTTP;
- [x] apresentar estado, duração, mensagem e resumo final;
- [x] adicionar cores opcionais e uma legenda;
- [x] oferecer `--no-color` e respeitar terminais sem suporte a cor;
- [x] usar códigos de saída documentados.

Legenda planejada:

| Estado | Cor | Significado |
| --- | --- | --- |
| `SUCCESS` | verde | verificação concluída com sucesso |
| `WARNING` | amarelo | resposta disponível, mas inesperada ou parcial |
| `ERROR` | vermelho | verificação falhou |
| `INFO` | azul/ciano | informação neutra |
| `SKIPPED` | cinza | verificação não executada |

### 6. Qualidade e entrega

- cobrir os casos principais com testes automatizados;
- simular rede nos testes sempre que possível;
- documentar instalação, exemplos e limitações;
- verificar execução em Python 3.10 ou superior.

## Possível Etapa 2 — Interface web local

Esta etapa é uma melhoria futura, não um requisito do MVP.

- escolher entre biblioteca padrão e um microframework;
- criar formulário para host, portas, URL e timeout;
- reutilizar integralmente o núcleo da Etapa 1;
- apresentar cartões e legenda com os mesmos estados;
- escutar apenas em `127.0.0.1` por padrão;
- avaliar cuidados de segurança antes de permitir acesso pela rede.

## Fora do escopo atual

- ping ICMP;
- varredura de intervalos de portas;
- execução periódica ou monitoramento contínuo;
- banco de dados e histórico;
- autenticação HTTP;
- execução paralela;
- exportação de relatórios;
- interface web.

