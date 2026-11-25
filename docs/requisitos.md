# Requisitos

Sistema: **chat em tempo real** com arquitetura **cliente-servidor** (Modelo 5).
Os usuários conversam em salas; o servidor central recebe cada mensagem e a repassa na hora para os demais participantes da sala.

## Requisitos funcionais

| ID | Requisito |
| --- | --- |
| RF01 | O usuário deve entrar no chat informando um nome (até 20 caracteres) e uma sala. O sistema não pode aceitar dois usuários com o mesmo nome na mesma sala. |
| RF02 | O usuário deve poder enviar mensagens de texto (de 1 a 500 caracteres) para a sala em que está. |
| RF03 | Todos os participantes da sala devem receber as mensagens enviadas em tempo real, sem precisar atualizar a tela ou pedir novas mensagens. |
| RF04 | Ao entrar em uma sala, o usuário deve receber o histórico com as últimas 50 mensagens daquela sala. |
| RF05 | O usuário deve ver a lista de quem está online na sala e ser avisado quando alguém entra, sai ou está digitando. |

## Requisitos não funcionais

| ID | Requisito |
| --- | --- |
| RNF01 | **Desempenho:** uma mensagem deve chegar aos demais participantes da sala em menos de 1 segundo numa rede local. |
| RNF02 | **Confiabilidade:** o servidor deve validar todo dado recebido (formato JSON, tamanho e caracteres) e recusar entradas inválidas com uma mensagem de erro, sem cair. Conexões que param de responder devem ser encerradas em até 45 segundos (heartbeat), e o cliente deve tentar reconectar sozinho se a conexão cair. |
| RNF03 | **Portabilidade:** o sistema deve subir com um único comando (`docker compose up --build`) em qualquer máquina com Docker, e os componentes devem usar apenas a biblioteca padrão do Python 3.12, sem dependências externas. |

## Critérios de aceitação

| Requisito | Como verificar | Evidência |
| --- | --- | --- |
| RF01 | Entrar como `ana` na sala `geral`; tentar entrar de novo como `Ana` na mesma sala. A segunda tentativa recebe o erro `NOME_EM_USO`. | `LOGS.md`, passos 1 e 6 · `tests/test_salas.py` |
| RF02 | Enviar "Oi, Bruno!". Uma mensagem vazia é recusada com `MENSAGEM_VAZIA`; uma com mais de 500 caracteres, com `MENSAGEM_LONGA`. | `LOGS.md`, passos 2 e 6 · `tests/test_protocolo.py` |
| RF03 | Com `ana` e `bruno` na sala, a mensagem de `ana` aparece para `bruno` sem nenhuma ação dele. | `LOGS.md`, passo 3 |
| RF04 | Depois da conversa entre `ana` e `bruno`, `carla` entra e recebe as mensagens anteriores. | `LOGS.md`, passo 5 · `tests/test_salas.py` |
| RF05 | Quando `bruno` entra ou sai, os outros recebem o aviso de presença com a lista de online atualizada; ao digitar, os outros veem "digitando...". | `LOGS.md`, passos 1, 2 e 7 |
| RNF01 | O roteiro `demo.py` mede o tempo entre o envio da `ana` e a chegada no `bruno` e falha se passar de 1000 ms. | `LOGS.md`, passo 3 ("mensagem entregue em 0.6 ms") |
| RNF02 | Enviar JSON inválido, tipo desconhecido, nome repetido e mensagem vazia: o servidor responde com erro e continua atendendo os outros. Derrubar o servidor e religá-lo: o cliente reconecta sozinho. | `tests/test_protocolo.py` · `LOGS.md`, passo 6 |
| RNF03 | Em uma máquina só com Docker, rodar `docker compose up --build` e depois `docker compose run --rm demo`. | `README.md` (Como rodar) · `docker-compose.yml` |

## Rastreabilidade (requisito → componente)

| Requisito | Componente responsável |
| --- | --- |
| RF01 | `servicos/servidor/salas.py` (`GerenciadorDeSalas.entrar`) e `protocolo.py` (validação do nome) |
| RF02 | `servicos/servidor/protocolo.py` (validação do texto) e clientes (`cliente.py`, `cliente_gui.py`) |
| RF03 | `servicos/servidor/salas.py` (`difundir`) e `servidor.py` (conexões TCP abertas) |
| RF04 | `servicos/servidor/salas.py` (histórico de 50 mensagens por sala) |
| RF05 | `servicos/servidor/servidor.py` (eventos `presenca` e `digitando`) e `cliente-gui/interface.py` (lista de online) |
| RNF01 | `servicos/servidor/servidor.py` (difusão sem bloqueio, asyncio) |
| RNF02 | `servicos/servidor/protocolo.py`, `servidor.py` (heartbeat) e `cliente/cliente.py`, `cliente-gui/rede.py` (reconexão) |
| RNF03 | `docker-compose.yml` e `Dockerfile` de cada componente |
