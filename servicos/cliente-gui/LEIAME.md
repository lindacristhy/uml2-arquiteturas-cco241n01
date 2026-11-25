# Cliente gráfico (Tkinter)

Janela de chat feita com Tkinter, que já vem instalado com o Python no Windows e no macOS. No Linux pode ser preciso instalar o pacote `python3-tk`.

## Como abrir

Com o servidor rodando (`docker compose up --build` na raiz do projeto):

```
python servicos/cliente-gui/cliente_gui.py
```

Também dá para preencher a tela de entrada direto pela linha de comando:

```
python servicos/cliente-gui/cliente_gui.py --usuario ana --sala geral --host 127.0.0.1 --porta 5000
```

Abra duas janelas com nomes diferentes para ver as mensagens chegando em tempo real.

## O que a janela mostra

- mensagens da sala (as suas em azul) e o histórico ao entrar;
- lista de usuários online, atualizada quando alguém entra ou sai;
- aviso "fulano está digitando...";
- estado da conexão. Se o servidor cair, o cliente tenta reconectar sozinho.

## Arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| `interface.py` | Telas (entrada e conversa). Só desenha; não sabe nada de rede. |
| `rede.py` | Conexão TCP numa thread separada, reconexão automática e resposta ao `ping`. |
| `cliente_gui.py` | Liga a interface à rede: lê a fila de eventos e atualiza a tela. |
