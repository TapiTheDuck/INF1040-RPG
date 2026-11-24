"""Testes do módulo combate (casos C01 a C10 do documento, seção 7.3).

Cenário antes de cada caso: personagem padrão (guerreiro Lia, PV 12) criado,
inventário reiniciado e nada equipado. Inimigo "goblin" da tabela fixa
(pv 7, ca 12, bonus_ataque 4, ouro 5, xp 50, drops {"pocao_vida": 1}).
A semente do gerador aleatório é fixada em cada caso de combate.
"""

import importlib
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import combate  # noqa: E402
import itens  # noqa: E402
import personagem  # noqa: E402

SEMENTE_VITORIA = 0   # com guerreiro Lia desarmado, o jogador vence o goblin
SEMENTE_DERROTA = 5   # com guerreiro Lia desarmado, o goblin vence


def acao_atacar(estado):
    """Ação do jogador: sempre ataca."""
    return "atacar"


def acao_invalida(estado):
    """Ação inexistente, para provocar interrupção do combate."""
    return "voar"


class TestCombate(unittest.TestCase):

    def setUp(self):
        importlib.reload(personagem)  # sem personagem, sem acessar a estrutura privada
        itens.reiniciar_inventario()
        personagem.criar_personagem("Lia", "guerreiro")

    # --- orquestrar_combate -------------------------------------------------
    def test_C01_combate_vencido_pelo_jogador(self):
        print("Caso de Teste C01 - Combate vencido pelo jogador")
        random.seed(SEMENTE_VITORIA)
        self.assertEqual(combate.orquestrar_combate("goblin", acao_atacar), (0, "jogador"))
        # A ficha original não pode ter sido alterada: com o mesmo personagem e a
        # mesma semente, um segundo combate tem de terminar exatamente igual.
        importlib.reload(personagem)
        personagem.criar_personagem("Lia", "guerreiro")
        random.seed(SEMENTE_VITORIA)
        self.assertEqual(combate.orquestrar_combate("goblin", acao_atacar), (0, "jogador"))

    def test_C02_combate_vencido_pelo_inimigo(self):
        print("Caso de Teste C02 - Combate vencido pelo inimigo")
        random.seed(SEMENTE_DERROTA)
        self.assertEqual(combate.orquestrar_combate("goblin", acao_atacar), (0, "inimigo"))
        codigo, ficha = personagem.consultar_personagem()
        self.assertEqual(codigo, 0)
        self.assertEqual(ficha["pv"], 0)
        self.assertFalse(ficha["vivo"])

    def test_C03_acao_invalida_interrompe_combate(self):
        print("Caso de Teste C03 - Ação inválida devolvida por obter_acao")
        random.seed(SEMENTE_VITORIA)
        self.assertEqual(combate.orquestrar_combate("goblin", acao_invalida), (1, None))

    def test_C04_combate_sem_personagem(self):
        print("Caso de Teste C04 - Combate sem personagem criado")
        importlib.reload(personagem)  # reinicia o módulo: nenhum personagem criado
        random.seed(SEMENTE_VITORIA)
        self.assertEqual(combate.orquestrar_combate("goblin", acao_atacar), (1, None))

    def test_C05_identificador_de_tipo_incorreto(self):
        print("Caso de Teste C05 - Identificador de inimigo de tipo incorreto")
        self.assertEqual(combate.orquestrar_combate(123, acao_atacar), (3, None))

    def test_C06_obter_acao_nao_e_funcao(self):
        print("Caso de Teste C06 - obter_acao que não é função")
        self.assertEqual(combate.orquestrar_combate("goblin", None), (3, None))

    def test_C07_inimigo_inexistente(self):
        print("Caso de Teste C07 - Inimigo inexistente")
        self.assertEqual(combate.orquestrar_combate("dragao_999", acao_atacar), (4, None))

    # --- dropar_itens -------------------------------------------------------
    def test_C08_recompensa_de_inimigo_existente(self):
        print("Caso de Teste C08 - Consultar recompensa de inimigo existente")
        self.assertEqual(
            combate.dropar_itens("goblin"),
            (0, {"itens": {"pocao_vida": 1}, "ouro": 5, "xp": 50}),
        )

    def test_C09_recompensa_com_tipo_incorreto(self):
        print("Caso de Teste C09 - Consultar recompensa com parâmetro de tipo incorreto")
        self.assertEqual(combate.dropar_itens(None), (3, None))

    def test_C10_recompensa_de_inimigo_inexistente(self):
        print("Caso de Teste C10 - Consultar recompensa de inimigo inexistente")
        self.assertEqual(combate.dropar_itens("dragao_999"), (4, None))


if __name__ == "__main__":
    unittest.main()
