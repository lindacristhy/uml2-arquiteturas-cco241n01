# Cliente de terminal

## Conversar pelo terminal

Pelo Docker (o servidor sobe junto, se ainda não estiver rodando):

```
docker compose run --rm cliente --usuario ana
```

Ou direto com Python:

```
python servicos/cliente/cliente.py --usuario ana --sala geral
```

Comandos dentro do chat: `/usuarios`, `/sala <nome>`, `/ajuda` e `/sair`.
Se a conexão cair, o cliente tenta reconectar sozinho (até 5 tentativas).

## Executar o fluxo principal

```
docker compose run --rm demo
```

O `demo.py` abre três clientes (ana, bruno e carla), executa o fluxo principal passo a passo, confere cada resposta do servidor e mede o tempo de entrega. Termina com código 0 se tudo deu certo. Os logs do `LOGS.md` foram gerados com ele.

## Arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| `conexao.py` | Conexão TCP com o servidor (envio e recebimento de JSON, resposta ao `ping`). |
| `cliente.py` | Cliente interativo para o terminal. |
| `demo.py` | Roteiro automático do fluxo principal. |
