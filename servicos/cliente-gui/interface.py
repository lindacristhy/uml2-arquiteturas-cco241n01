"""Telas do cliente gráfico (Tkinter): tela de entrada e tela da conversa.

As telas só desenham e repassam o que o usuário faz por meio de funções
(ao_entrar, ao_enviar, ao_digitar, ao_sair). Elas não sabem nada de rede.
"""

import tkinter as tk
from tkinter import scrolledtext, ttk

LIMITE_TEXTO = 500  # o mesmo limite que o servidor aplica

CORES = {
    "fundo": "#f4f6f8",
    "painel": "#ffffff",
    "texto": "#1f2933",
    "suave": "#6b7785",
    "destaque": "#1b7f5a",
    "proprio": "#0b5cad",
    "erro": "#b42318",
}


class TelaEntrada(ttk.Frame):
    """Pede nome, sala e endereço do servidor."""

    def __init__(self, mestre, ao_entrar, padrao: dict, erro: str = None):
        super().__init__(mestre, padding=32)
        self._ao_entrar = ao_entrar

        ttk.Label(self, text="Chat em tempo real", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 4)
        )
        ttk.Label(self, text="Tartarugas Ninja · cliente-servidor", foreground=CORES["suave"]).grid(
            row=1, column=0, columnspan=2, pady=(0, 20)
        )

        self.campos = {}
        rotulos = [("usuario", "Seu nome"), ("sala", "Sala"), ("host", "Servidor"), ("porta", "Porta")]
        for linha, (chave, rotulo) in enumerate(rotulos, start=2):
            ttk.Label(self, text=rotulo).grid(row=linha, column=0, sticky="w", pady=4, padx=(0, 12))
            campo = ttk.Entry(self, width=28)
            campo.insert(0, str(padrao.get(chave) or ""))
            campo.grid(row=linha, column=1, sticky="ew", pady=4)
            campo.bind("<Return>", lambda _e: self._confirmar())
            self.campos[chave] = campo

        ttk.Button(self, text="Entrar", command=self._confirmar).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(16, 4)
        )
        self.erro = ttk.Label(self, text=erro or "", foreground=CORES["erro"], wraplength=320)
        self.erro.grid(row=7, column=0, columnspan=2)

        self.columnconfigure(1, weight=1)
        self.campos["usuario"].focus_set()

    def _confirmar(self) -> None:
        valores = {chave: campo.get().strip() for chave, campo in self.campos.items()}
        if not valores["usuario"]:
            self.erro.config(text="Informe seu nome.")
            return
        if not valores["sala"]:
            self.erro.config(text="Informe a sala.")
            return
        try:
            valores["porta"] = int(valores["porta"])
        except ValueError:
            self.erro.config(text="A porta precisa ser um número.")
            return
        self._ao_entrar(valores["usuario"], valores["sala"].lower(), valores["host"] or "127.0.0.1", valores["porta"])


class TelaChat(ttk.Frame):
    """Conversa: mensagens à esquerda, usuários online à direita, caixa de texto embaixo."""

    def __init__(self, mestre, usuario: str, sala: str, ao_enviar, ao_digitar, ao_sair):
        super().__init__(mestre, padding=8)
        self.usuario = usuario
        self._ao_enviar = ao_enviar
        self._ao_digitar = ao_digitar
        self._limpar_digitando = None

        # Cabeçalho
        topo = ttk.Frame(self)
        topo.pack(fill="x", pady=(0, 6))
        ttk.Label(topo, text=f"#{sala}", font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Label(topo, text=f"  você é {usuario}", foreground=CORES["suave"]).pack(side="left")
        ttk.Button(topo, text="Sair", command=ao_sair).pack(side="right")
        self.estado = ttk.Label(topo, text="● conectando...", foreground=CORES["suave"])
        self.estado.pack(side="right", padx=12)

        # Corpo: mensagens + lista de online
        corpo = ttk.Frame(self)
        corpo.pack(fill="both", expand=True)

        self.mensagens = scrolledtext.ScrolledText(
            corpo, wrap="word", state="disabled", relief="flat", padx=10, pady=8,
            font=("Segoe UI", 10), background=CORES["painel"], foreground=CORES["texto"],
        )
        self.mensagens.pack(side="left", fill="both", expand=True)
        self.mensagens.tag_config("hora", foreground=CORES["suave"])
        self.mensagens.tag_config("autor", foreground=CORES["destaque"], font=("Segoe UI", 10, "bold"))
        self.mensagens.tag_config("proprio", foreground=CORES["proprio"], font=("Segoe UI", 10, "bold"))
        self.mensagens.tag_config("sistema", foreground=CORES["suave"], font=("Segoe UI", 9, "italic"))
        self.mensagens.tag_config("erro", foreground=CORES["erro"])

        lateral = ttk.Frame(corpo, padding=(8, 0, 0, 0))
        lateral.pack(side="right", fill="y")
        self.titulo_online = ttk.Label(lateral, text="Online (0)", font=("Segoe UI", 10, "bold"))
        self.titulo_online.pack(anchor="w")
        self.online = tk.Listbox(lateral, width=18, relief="flat", activestyle="none", background=CORES["painel"])
        self.online.pack(fill="y", expand=True, pady=(4, 0))

        # Rodapé: "fulano está digitando..." + caixa de texto
        self.digitando = ttk.Label(self, text="", foreground=CORES["suave"])
        self.digitando.pack(anchor="w", pady=(4, 0))
        rodape = ttk.Frame(self)
        rodape.pack(fill="x")
        self.entrada = ttk.Entry(rodape)
        self.entrada.pack(side="left", fill="x", expand=True, ipady=4)
        self.entrada.bind("<Return>", lambda _e: self._enviar())
        self.entrada.bind("<KeyPress>", self._tecla)
        ttk.Button(rodape, text="Enviar", command=self._enviar).pack(side="right", padx=(6, 0))
        self.entrada.focus_set()

    # ----------------------------------------------------------- ações do usuário

    def _tecla(self, evento) -> None:
        if evento.keysym not in ("Return", "Tab") and evento.char:
            self._ao_digitar()

    def _enviar(self) -> None:
        texto = self.entrada.get().strip()
        if not texto:
            return
        if len(texto) > LIMITE_TEXTO:
            self.adicionar_sistema(f"A mensagem tem {len(texto)} caracteres; o limite é {LIMITE_TEXTO}.", erro=True)
            return
        if self._ao_enviar(texto):
            self.entrada.delete(0, "end")

    # ----------------------------------------------------------- atualizações da tela

    def _escrever(self, partes) -> None:
        self.mensagens.config(state="normal")
        for texto, tag in partes:
            self.mensagens.insert("end", texto, tag)
        self.mensagens.insert("end", "\n")
        self.mensagens.config(state="disabled")
        self.mensagens.see("end")

    def adicionar_mensagem(self, usuario: str, texto: str, hora: str) -> None:
        tag = "proprio" if usuario.casefold() == self.usuario.casefold() else "autor"
        self._escrever([(f"{hora}  ", "hora"), (usuario, tag), (f": {texto}", None)])
        if self.digitando.cget("text").startswith(usuario):
            self.digitando.config(text="")

    def adicionar_sistema(self, texto: str, erro: bool = False) -> None:
        self._escrever([(f"— {texto}", "erro" if erro else "sistema")])

    def atualizar_usuarios(self, usuarios: list) -> None:
        self.online.delete(0, "end")
        for nome in usuarios:
            self.online.insert("end", f"● {nome}" + ("  (você)" if nome.casefold() == self.usuario.casefold() else ""))
        self.titulo_online.config(text=f"Online ({len(usuarios)})")

    def mostrar_digitando(self, usuario: str) -> None:
        self.digitando.config(text=f"{usuario} está digitando...")
        if self._limpar_digitando:
            self.after_cancel(self._limpar_digitando)
        self._limpar_digitando = self.after(3000, lambda: self.digitando.config(text=""))

    def definir_estado(self, texto: str, conectado: bool) -> None:
        self.estado.config(text=f"● {texto}", foreground=CORES["destaque"] if conectado else CORES["erro"])
