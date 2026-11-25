# Logs do fluxo principal

**Fluxo:** os usuários `ana` e `bruno` entram na sala `geral`, `ana` envia uma mensagem que o servidor difunde em tempo real para `bruno`, `bruno` responde, `carla` entra depois e recebe o histórico da sala, o servidor recusa um nome repetido e uma mensagem vazia, e por fim `bruno` sai e os demais são avisados.

Logs gerados em 18/11/2026 com os comandos abaixo (horários em UTC):

```
docker compose up --build -d
docker compose run --rm demo
docker compose logs servidor
```

## Terminal 1: servidor (`docker compose logs servidor`)

Cada linha é um evento tratado pelo servidor. `destinatarios` indica para quantos clientes a mensagem foi difundida e `tempo_ms` quanto tempo o servidor levou para fazer isso.

```
servidor-1  | 2026-11-18T22:20:20.803Z [servidor] INFO  servidor.iniciado host=0.0.0.0 porta=5000
servidor-1  | 2026-11-18T22:20:35.925Z [servidor] INFO  conexao.aberta cliente=c1 endereco=172.19.0.3:56620
servidor-1  | 2026-11-18T22:20:35.926Z [servidor] INFO  usuario.entrou sala=geral usuario=ana cliente=c1 online_na_sala=1 historico_enviado=0
servidor-1  | 2026-11-18T22:20:35.928Z [servidor] INFO  conexao.aberta cliente=c2 endereco=172.19.0.3:56630
servidor-1  | 2026-11-18T22:20:35.929Z [servidor] INFO  usuario.entrou sala=geral usuario=bruno cliente=c2 online_na_sala=2 historico_enviado=0
servidor-1  | 2026-11-18T22:20:35.930Z [servidor] INFO  mensagem.difundida sala=geral de=ana id=1 destinatarios=2 tempo_ms=0.18
servidor-1  | 2026-11-18T22:20:35.932Z [servidor] INFO  mensagem.difundida sala=geral de=bruno id=2 destinatarios=2 tempo_ms=0.40
servidor-1  | 2026-11-18T22:20:35.935Z [servidor] INFO  conexao.aberta cliente=c3 endereco=172.19.0.3:56644
servidor-1  | 2026-11-18T22:20:35.936Z [servidor] INFO  usuario.entrou sala=geral usuario=carla cliente=c3 online_na_sala=3 historico_enviado=2
servidor-1  | 2026-11-18T22:20:35.938Z [servidor] INFO  conexao.aberta cliente=c4 endereco=172.19.0.3:56654
servidor-1  | 2026-11-18T22:20:35.938Z [servidor] AVISO comando.recusado cliente=c4 codigo=NOME_EM_USO
servidor-1  | 2026-11-18T22:20:35.939Z [servidor] INFO  conexao.fechada cliente=c4 motivo="cliente saiu" online=3
servidor-1  | 2026-11-18T22:20:35.940Z [servidor] AVISO comando.recusado cliente=c3 codigo=MENSAGEM_VAZIA
servidor-1  | 2026-11-18T22:20:35.941Z [servidor] INFO  usuario.saiu sala=geral usuario=bruno online_na_sala=2
servidor-1  | 2026-11-18T22:20:35.941Z [servidor] INFO  conexao.fechada cliente=c2 motivo="cliente saiu" online=2
servidor-1  | 2026-11-18T22:20:35.943Z [servidor] INFO  usuario.saiu sala=geral usuario=carla online_na_sala=1
servidor-1  | 2026-11-18T22:20:35.943Z [servidor] INFO  conexao.fechada cliente=c3 motivo="cliente saiu" online=1
servidor-1  | 2026-11-18T22:20:35.944Z [servidor] INFO  usuario.saiu sala=geral usuario=ana online_na_sala=0
servidor-1  | 2026-11-18T22:20:35.944Z [servidor] INFO  conexao.fechada cliente=c1 motivo="cliente saiu" online=0
```

## Terminal 2: clientes (`docker compose run --rm demo`)

O roteiro `servicos/cliente/demo.py` abre três clientes (ana, bruno e carla) e mostra cada mensagem trocada com o servidor: `->` é o que o cliente enviou e `<-` é o que ele recebeu. As linhas `OK` são as verificações automáticas de cada passo.

```
#1 [internal] load local bake definitions
#1 reading from stdin 749B 0.0s done
#1 DONE 0.0s

#2 [internal] load build definition from Dockerfile
#2 DONE 0.0s

#2 [internal] load build definition from Dockerfile
#2 transferring dockerfile: 616B done
#2 DONE 0.0s

#3 [internal] load metadata for docker.io/library/python:3.12-slim
#3 DONE 0.3s

#4 [internal] load .dockerignore
#4 transferring context: 2B done
#4 DONE 0.0s

#5 [1/5] FROM docker.io/library/python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
#5 resolve docker.io/library/python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b 0.0s done
#5 DONE 0.0s

#6 [internal] load build context
#6 transferring context: 400B done
#6 DONE 0.0s

#7 [2/5] WORKDIR /app
#7 CACHED

#8 [3/5] COPY *.py ./
#8 CACHED

#9 [4/5] COPY tests ./tests
#9 CACHED

#10 [5/5] RUN python -m unittest discover -s tests
#10 CACHED

#11 exporting to image
#11 exporting layers done
#11 exporting manifest sha256:e35786e3a67fcc0cbb72228f39a61d0cf068635048fd80194ed2fc0726b0032a done
#11 exporting config sha256:e97cf81c764c27231c462a9c61b1692162d0ad0d329274cac3871f86b28367fd done
#11 exporting attestation manifest sha256:a147f887a9473c31b42a5f899cdfc6b301a022b99f6e3ed7a1cd857781a4807d
#11 exporting attestation manifest sha256:a147f887a9473c31b42a5f899cdfc6b301a022b99f6e3ed7a1cd857781a4807d 0.0s done
#11 exporting manifest list sha256:4a17e9522517934df50936c020b5ccce87047165617798ca4d0fce639849fc9b 0.0s done
#11 naming to docker.io/library/chat-teste-servidor:latest done
#11 unpacking to docker.io/library/chat-teste-servidor:latest 0.0s done
#11 DONE 0.1s

#12 resolving provenance for metadata file
#12 DONE 0.0s
#1 [internal] load local bake definitions
#1 reading from stdin 1.37kB 0.0s done
#1 DONE 0.0s

#2 [internal] load build definition from Dockerfile
#2 transferring dockerfile: 304B done
#2 DONE 0.0s

#3 [internal] load metadata for docker.io/library/python:3.12-slim
#3 DONE 0.3s

#4 [internal] load .dockerignore
#4 transferring context: 2B done
#4 DONE 0.0s

#5 [internal] load build context
#5 transferring context: 89B done
#5 DONE 0.0s

#6 [1/3] FROM docker.io/library/python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
#6 resolve docker.io/library/python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b 0.0s done
#6 DONE 0.0s

#7 [2/3] WORKDIR /app
#7 CACHED

#8 [3/3] COPY *.py ./
#8 CACHED

#9 exporting to image
#9 exporting layers done
#9 exporting manifest sha256:f922c51a4f6a49ae9f7801dca8db96307fc67f0d577aad2e464f751c04d02ae1 done
#9 exporting config sha256:6f2e93beda6353d85dbb840d4e31d21e3be2a44024ed41a8d6d18febf637c19d done
#9 exporting attestation manifest sha256:3340c1e8e619e01147a361df5d22285f25d928210276be9649f6f4cd5e0f0b79
#9 exporting attestation manifest sha256:3340c1e8e619e01147a361df5d22285f25d928210276be9649f6f4cd5e0f0b79 0.0s done
#9 exporting manifest list sha256:8f140edfb7936516c42319c35c136ead070233c3c0e3e166dba254c7cc64e02d 0.0s done
#9 naming to docker.io/library/chat-teste-demo:latest done
#9 unpacking to docker.io/library/chat-teste-demo:latest 0.0s done
#9 DONE 0.1s

#10 resolving provenance for metadata file
#10 DONE 0.0s
2026-11-18T22:20:35.904Z [demo] Iniciando o fluxo principal contra o servidor servidor:5000
2026-11-18T22:20:35.904Z [demo] 
2026-11-18T22:20:35.904Z [demo] ===== Passo 1: ana e bruno entram na sala 'geral' =====
2026-11-18T22:20:35.925Z [demo] ana    conectou em servidor:5000
2026-11-18T22:20:35.925Z [demo] ana    -> servidor  {"tipo": "entrar", "usuario": "ana", "sala": "geral"}
2026-11-18T22:20:35.926Z [demo] ana    <- servidor  {"tipo": "entrou", "sala": "geral", "usuario": "ana", "historico": [], "usuarios": ["ana"]}
2026-11-18T22:20:35.926Z [demo] OK    ana entrou e é a única online
2026-11-18T22:20:35.928Z [demo] bruno  conectou em servidor:5000
2026-11-18T22:20:35.928Z [demo] bruno  -> servidor  {"tipo": "entrar", "usuario": "bruno", "sala": "geral"}
2026-11-18T22:20:35.929Z [demo] bruno  <- servidor  {"tipo": "entrou", "sala": "geral", "usuario": "bruno", "historico": [], "usuarios": ["ana", "bruno"]}
2026-11-18T22:20:35.929Z [demo] OK    bruno entrou e vê ana online
2026-11-18T22:20:35.929Z [demo] ana    <- servidor  {"tipo": "presenca", "evento": "entrou", "usuario": "bruno", "usuarios": ["ana", "bruno"]}
2026-11-18T22:20:35.929Z [demo] OK    ana foi avisada da entrada de bruno
2026-11-18T22:20:35.929Z [demo] 
2026-11-18T22:20:35.929Z [demo] ===== Passo 2: ana digita e envia uma mensagem =====
2026-11-18T22:20:35.929Z [demo] ana    -> servidor  {"tipo": "digitando"}
2026-11-18T22:20:35.930Z [demo] bruno  <- servidor  {"tipo": "digitando", "usuario": "ana"}
2026-11-18T22:20:35.930Z [demo] OK    bruno viu o aviso 'ana está digitando'
2026-11-18T22:20:35.930Z [demo] ana    -> servidor  {"tipo": "mensagem", "texto": "Oi, Bruno! O servidor de chat está no ar?", "id_local": "ana-1"}
2026-11-18T22:20:35.930Z [demo] 
2026-11-18T22:20:35.930Z [demo] ===== Passo 3: bruno recebe a mensagem em tempo real =====
2026-11-18T22:20:35.930Z [demo] bruno  <- servidor  {"tipo": "mensagem", "id": 1, "sala": "geral", "usuario": "ana", "texto": "Oi, Bruno! O servidor de chat está no ar?", "enviada_em": "2026-11-18T22:20:35.930Z", "id_local": "ana-1"}
2026-11-18T22:20:35.931Z [demo] OK    bruno recebeu exatamente o texto enviado por ana
2026-11-18T22:20:35.931Z [demo] OK    mensagem entregue em 0.6 ms (limite do RNF01: 1000 ms)
2026-11-18T22:20:35.931Z [demo] ana    <- servidor  {"tipo": "mensagem", "id": 1, "sala": "geral", "usuario": "ana", "texto": "Oi, Bruno! O servidor de chat está no ar?", "enviada_em": "2026-11-18T22:20:35.930Z", "id_local": "ana-1"}
2026-11-18T22:20:35.931Z [demo] OK    ana recebeu a confirmação de entrega (id=1)
2026-11-18T22:20:35.931Z [demo] 
2026-11-18T22:20:35.931Z [demo] ===== Passo 4: bruno responde e ana recebe =====
2026-11-18T22:20:35.931Z [demo] bruno  -> servidor  {"tipo": "mensagem", "texto": "Está sim, Ana! Mensagem recebida na hora.", "id_local": "bruno-1"}
2026-11-18T22:20:35.932Z [demo] ana    <- servidor  {"tipo": "mensagem", "id": 2, "sala": "geral", "usuario": "bruno", "texto": "Está sim, Ana! Mensagem recebida na hora.", "enviada_em": "2026-11-18T22:20:35.931Z", "id_local": "bruno-1"}
2026-11-18T22:20:35.932Z [demo] OK    ana recebeu a resposta de bruno
2026-11-18T22:20:35.932Z [demo] bruno  <- servidor  {"tipo": "mensagem", "id": 2, "sala": "geral", "usuario": "bruno", "texto": "Está sim, Ana! Mensagem recebida na hora.", "enviada_em": "2026-11-18T22:20:35.931Z", "id_local": "bruno-1"}
2026-11-18T22:20:35.932Z [demo] 
2026-11-18T22:20:35.933Z [demo] ===== Passo 5: carla entra depois e recebe o histórico da sala =====
2026-11-18T22:20:35.935Z [demo] carla  conectou em servidor:5000
2026-11-18T22:20:35.935Z [demo] carla  -> servidor  {"tipo": "entrar", "usuario": "carla", "sala": "geral"}
2026-11-18T22:20:35.936Z [demo] carla  <- servidor  {"tipo": "entrou", "sala": "geral", "usuario": "carla", "historico": [{"tipo": "mensagem", "id": 1, "sala": "geral", "usuario": "ana", "texto": "Oi, Bruno! O servidor de chat está no ar?", "enviada_em": "2026-11-18T22:20:35.930Z", "id_local": "ana-1"}, {"tipo": "mensagem", "id": 2, "sala": "geral", "usuario": "bruno", "texto": "Está sim, Ana! Mensagem recebida na hora.", "enviada_em": "2026-11-18T22:20:35.931Z", "id_local": "bruno-1"}], "usuarios": ["ana", "bruno", "carla"]}
2026-11-18T22:20:35.936Z [demo] OK    carla recebeu o histórico (2 mensagens)
2026-11-18T22:20:35.936Z [demo] OK    carla vê ana e bruno online
2026-11-18T22:20:35.936Z [demo] ana    <- servidor  {"tipo": "presenca", "evento": "entrou", "usuario": "carla", "usuarios": ["ana", "bruno", "carla"]}
2026-11-18T22:20:35.936Z [demo] bruno  <- servidor  {"tipo": "presenca", "evento": "entrou", "usuario": "carla", "usuarios": ["ana", "bruno", "carla"]}
2026-11-18T22:20:35.936Z [demo] 
2026-11-18T22:20:35.936Z [demo] ===== Passo 6: o servidor recusa entradas inválidas =====
2026-11-18T22:20:35.938Z [demo] outro  conectou em servidor:5000
2026-11-18T22:20:35.938Z [demo] outro  -> servidor  {"tipo": "entrar", "usuario": "Ana", "sala": "geral"}
2026-11-18T22:20:35.939Z [demo] outro  <- servidor  {"tipo": "erro", "codigo": "NOME_EM_USO", "motivo": "Já existe alguém chamado 'ana' na sala 'geral'."}
2026-11-18T22:20:35.939Z [demo] OK    nome repetido na sala foi recusado (NOME_EM_USO)
2026-11-18T22:20:35.939Z [demo] outro  -> servidor  {"tipo": "sair"}
2026-11-18T22:20:35.939Z [demo] carla  -> servidor  {"tipo": "mensagem", "texto": "   "}
2026-11-18T22:20:35.941Z [demo] carla  <- servidor  {"tipo": "erro", "codigo": "MENSAGEM_VAZIA", "motivo": "A mensagem não pode ser vazia."}
2026-11-18T22:20:35.941Z [demo] OK    mensagem vazia foi recusada (MENSAGEM_VAZIA)
2026-11-18T22:20:35.941Z [demo] 
2026-11-18T22:20:35.941Z [demo] ===== Passo 7: bruno sai e os outros são avisados =====
2026-11-18T22:20:35.941Z [demo] bruno  -> servidor  {"tipo": "sair"}
2026-11-18T22:20:35.942Z [demo] bruno  desconectou
2026-11-18T22:20:35.942Z [demo] ana    <- servidor  {"tipo": "presenca", "evento": "saiu", "usuario": "bruno", "usuarios": ["ana", "carla"]}
2026-11-18T22:20:35.942Z [demo] OK    ana foi avisada da saída de bruno
2026-11-18T22:20:35.942Z [demo] carla  <- servidor  {"tipo": "presenca", "evento": "saiu", "usuario": "bruno", "usuarios": ["ana", "carla"]}
2026-11-18T22:20:35.942Z [demo] OK    carla foi avisada da saída de bruno
2026-11-18T22:20:35.942Z [demo] carla  -> servidor  {"tipo": "sair"}
2026-11-18T22:20:35.942Z [demo] ana    -> servidor  {"tipo": "sair"}
2026-11-18T22:20:35.942Z [demo] ana e carla desconectaram
2026-11-18T22:20:35.943Z [demo] 
2026-11-18T22:20:35.943Z [demo] RESULTADO: fluxo principal concluído com sucesso (14 verificações OK).
```

## Resumo

| Passo | O que aconteceu | Requisito |
| --- | --- | --- |
| 1 | `ana` e `bruno` entram na sala `geral`, e `ana` é avisada da entrada de `bruno` | RF01, RF05 |
| 2 | `ana` digita (aviso "digitando") e envia a mensagem | RF02 |
| 3 | `bruno` recebe a mensagem em tempo real, e `ana` recebe a confirmação de entrega | RF03, RNF01 |
| 4 | `bruno` responde e `ana` recebe | RF02, RF03 |
| 5 | `carla` entra depois e recebe as 2 mensagens do histórico | RF04 |
| 6 | O servidor recusa nome repetido (`NOME_EM_USO`) e mensagem vazia (`MENSAGEM_VAZIA`) | RNF02 |
| 7 | `bruno` sai, e `ana` e `carla` recebem a lista de online atualizada | RF05 |
