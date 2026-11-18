import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from protocolo import ErroDeProtocolo  # noqa: E402
from salas import GerenciadorDeSalas  # noqa: E402


class ParticipanteFalso:
    def __init__(self, usuario, sessao=None):
        self.usuario = usuario
        self.sessao = sessao
        self.recebidas = []

    def enviar(self, mensagem):
        self.recebidas.append(mensagem)
        return True


class TestSalas(unittest.TestCase):
    def setUp(self):
        self.salas = GerenciadorDeSalas(tamanho_historico=3)

    def test_entrar_e_listar_usuarios_em_ordem(self):
        self.salas.entrar("geral", ParticipanteFalso("bruno"))
        self.salas.entrar("geral", ParticipanteFalso("Ana"))
        self.assertEqual(self.salas.usuarios("geral"), ["Ana", "bruno"])

    def test_nome_repetido_na_mesma_sala_e_recusado(self):
        self.salas.entrar("geral", ParticipanteFalso("ana"))
        with self.assertRaises(ErroDeProtocolo) as ctx:
            self.salas.entrar("geral", ParticipanteFalso("ANA"))
        self.assertEqual(ctx.exception.codigo, "NOME_EM_USO")

    def test_mesmo_nome_em_salas_diferentes_e_permitido(self):
        self.salas.entrar("geral", ParticipanteFalso("ana"))
        self.salas.entrar("estudos", ParticipanteFalso("ana"))
        self.assertEqual(self.salas.usuarios("estudos"), ["ana"])

    def test_reconexao_com_mesma_sessao_substitui_a_antiga(self):
        antiga = ParticipanteFalso("ana", sessao="s1")
        nova = ParticipanteFalso("ana", sessao="s1")
        self.salas.entrar("geral", antiga)
        self.assertIs(self.salas.entrar("geral", nova), antiga)
        self.assertFalse(self.salas.sair("geral", antiga))  # a antiga já não está na sala
        self.assertTrue(self.salas.sair("geral", nova))

    def test_difundir_entrega_para_todos_menos_o_excluido(self):
        ana, bruno = ParticipanteFalso("ana"), ParticipanteFalso("bruno")
        self.salas.entrar("geral", ana)
        self.salas.entrar("geral", bruno)
        entregues = self.salas.difundir("geral", {"tipo": "digitando", "usuario": "ana"}, exceto=ana)
        self.assertEqual(entregues, 1)
        self.assertEqual(ana.recebidas, [])
        self.assertEqual(bruno.recebidas[0]["usuario"], "ana")

    def test_historico_guarda_so_as_ultimas_mensagens(self):
        for i in range(5):
            self.salas.registrar_mensagem("geral", "ana", f"msg {i}")
        textos = [m["texto"] for m in self.salas.historico("geral")]
        self.assertEqual(textos, ["msg 2", "msg 3", "msg 4"])

    def test_ids_das_mensagens_sao_crescentes(self):
        m1 = self.salas.registrar_mensagem("geral", "ana", "a")
        m2 = self.salas.registrar_mensagem("outra", "bruno", "b")
        self.assertLess(m1["id"], m2["id"])


if __name__ == "__main__":
    unittest.main()
