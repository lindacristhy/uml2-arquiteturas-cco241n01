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
