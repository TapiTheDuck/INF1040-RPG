"""Testes do módulo itens (casos I01 a I26 do documento, seção 7.4).

Cenário antes de cada caso: inventário reiniciado (vazio, nada equipado,
ouro 0) e personagem padrão (guerreiro Lia, PV 12) criado. Catálogo com
"espada_curta" (arma, dano 6), "armadura_couro" (armadura, bonus_ca 2) e
"pocao_vida" (consumível, cura 5). Nos casos "sem personagem", o testador
reinicia o módulo personagem antes da chamada.

Os casos de persistência (I27 a I33) ficam na mesma classe TestItens: basta
colar os métodos abaixo na classe do arquivo existente.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import itens  # noqa: E402
import personagem  # noqa: E402


class TestItens(unittest.TestCase):

    def setUp(self):
        itens.reiniciar_inventario()
        personagem._personagem = None
        personagem.criar_personagem("Lia", "guerreiro")

    # --- consultar_item -----------------------------------------------------
    def test_I01_consultar_item_existente(self):
        codigo, ficha = itens.consultar_item("pocao_vida")
        self.assertEqual(codigo, 0)
        self.assertEqual(ficha["nome"], "Poção de Vida")
        self.assertEqual(ficha["tipo"], "consumível")
        self.assertEqual(ficha["cura"], 5)
        self.assertIn("descricao", ficha)

    def test_I02_consultar_item_tipo_incorreto(self):
        self.assertEqual(itens.consultar_item(None), (3, None))

    def test_I03_consultar_item_inexistente(self):
        self.assertEqual(itens.consultar_item("item_999"), (4, None))

    # --- listar_inventario --------------------------------------------------
    def test_I04_listar_inventario_vazio(self):
        self.assertEqual(
            itens.listar_inventario(),
            (0, {"itens": {}, "equipados": {"arma": None, "armadura": None}, "ouro": 0}),
        )

    def test_I05_listar_inventario_com_itens(self):
        itens.adicionar_ao_inventario("pocao_vida", 2)
        itens.adicionar_ao_inventario("espada_curta", 1)
        itens.equipar_item("espada_curta")
        self.assertEqual(
            itens.listar_inventario(),
            (0, {"itens": {"pocao_vida": 2, "espada_curta": 1},
                 "equipados": {"arma": "espada_curta", "armadura": None},
                 "ouro": 0}),
        )

    # --- adicionar_ao_inventario --------------------------------------------
    def test_I06_adicionar_item_existente(self):
        self.assertEqual(itens.adicionar_ao_inventario("pocao_vida", 2), (0, None))
        self.assertEqual(itens.listar_inventario()[1]["itens"], {"pocao_vida": 2})

    def test_I07_adicionar_quantidade_invalida(self):
        self.assertEqual(itens.adicionar_ao_inventario("pocao_vida", 0), (3, None))
        self.assertEqual(itens.adicionar_ao_inventario("pocao_vida", True), (3, None))
        self.assertEqual(itens.listar_inventario()[1]["itens"], {})

    def test_I08_adicionar_identificador_tipo_incorreto(self):
        self.assertEqual(itens.adicionar_ao_inventario(None, 1), (3, None))

    def test_I09_adicionar_item_inexistente(self):
        self.assertEqual(itens.adicionar_ao_inventario("item_999", 1), (4, None))

    # --- equipar_item -------------------------------------------------------
    def test_I10_equipar_arma_possuida(self):
        itens.adicionar_ao_inventario("espada_curta", 1)
        self.assertEqual(itens.equipar_item("espada_curta"), (0, None))
        self.assertEqual(itens.listar_inventario()[1]["equipados"]["arma"], "espada_curta")

    def test_I11_equipar_consumivel(self):
        itens.adicionar_ao_inventario("pocao_vida", 1)
        self.assertEqual(itens.equipar_item("pocao_vida"), (3, None))

    def test_I12_equipar_item_fora_do_inventario(self):
        self.assertEqual(itens.equipar_item("armadura_couro"), (4, None))
        self.assertEqual(itens.listar_inventario()[1]["equipados"]["armadura"], None)

    def test_I13_equipar_item_inexistente(self):
        self.assertEqual(itens.equipar_item("item_999"), (4, None))

    # --- largar_item --------------------------------------------------------
    def test_I14_largar_parte_do_item(self):
        itens.adicionar_ao_inventario("pocao_vida", 3)
        self.assertEqual(itens.largar_item("pocao_vida", 1), (0, None))
        self.assertEqual(itens.listar_inventario()[1]["itens"]["pocao_vida"], 2)

    def test_I15_largar_item_equipado(self):
        itens.adicionar_ao_inventario("espada_curta", 1)
        itens.equipar_item("espada_curta")
        self.assertEqual(itens.largar_item("espada_curta", 1), (0, None))
        _, inv = itens.listar_inventario()
        self.assertEqual(inv["equipados"]["arma"], None)
        self.assertNotIn("espada_curta", inv["itens"])

    def test_I16_largar_mais_do_que_possui(self):
        itens.adicionar_ao_inventario("pocao_vida", 2)
        self.assertEqual(itens.largar_item("pocao_vida", 5), (3, None))
        self.assertEqual(itens.listar_inventario()[1]["itens"]["pocao_vida"], 2)

    def test_I17_largar_item_que_nao_possui(self):
        self.assertEqual(itens.largar_item("armadura_couro", 1), (4, None))

    # --- usar_item ----------------------------------------------------------
    def test_I18_usar_pocao_de_vida(self):
        personagem.aplicar_dano(5)
        itens.adicionar_ao_inventario("pocao_vida", 1)
        self.assertEqual(itens.usar_item("pocao_vida"), (0, 12))
        self.assertNotIn("pocao_vida", itens.listar_inventario()[1]["itens"])

    def test_I19_usar_pocao_sem_personagem(self):
        itens.adicionar_ao_inventario("pocao_vida", 1)
        personagem._personagem = None
        self.assertEqual(itens.usar_item("pocao_vida"), (1, None))
        self.assertEqual(itens.listar_inventario()[1]["itens"]["pocao_vida"], 1)

    def test_I20_usar_item_nao_consumivel(self):
        itens.adicionar_ao_inventario("espada_curta", 1)
        self.assertEqual(itens.usar_item("espada_curta"), (3, None))

    def test_I21_usar_item_fora_do_inventario(self):
        self.assertEqual(itens.usar_item("pocao_vida"), (4, None))

    # --- consultar_equipamento ----------------------------------------------
    def test_I22_consultar_equipamento_vazio(self):
        self.assertEqual(itens.consultar_equipamento(), (0, {"arma": None, "armadura": None}))

    def test_I23_consultar_equipamento_com_arma(self):
        itens.adicionar_ao_inventario("espada_curta", 1)
        itens.equipar_item("espada_curta")
        codigo, equipamento = itens.consultar_equipamento()
        self.assertEqual(codigo, 0)
        self.assertEqual(equipamento["arma"]["nome"], "Espada Curta")
        self.assertEqual(equipamento["arma"]["tipo"], "arma")
        self.assertEqual(equipamento["arma"]["dano"], 6)
        self.assertIsNone(equipamento["armadura"])

    # --- adicionar_ouro -----------------------------------------------------
    def test_I24_adicionar_ouro_valido(self):
        self.assertEqual(itens.adicionar_ouro(25), (0, 25))

    def test_I25_adicionar_ouro_negativo(self):
        self.assertEqual(itens.adicionar_ouro(-10), (3, None))
        self.assertEqual(itens.listar_inventario()[1]["ouro"], 0)

    # --- reiniciar_inventario -----------------------------------------------
    def test_I26_reiniciar_inventario_preenchido(self):
        itens.adicionar_ao_inventario("pocao_vida", 2)
        itens.adicionar_ao_inventario("espada_curta", 1)
        itens.equipar_item("espada_curta")
        itens.adicionar_ouro(25)
        self.assertEqual(itens.reiniciar_inventario(), (0, None))
        self.assertEqual(
            itens.listar_inventario(),
            (0, {"itens": {}, "equipados": {"arma": None, "armadura": None}, "ouro": 0}),
        )


if __name__ == "__main__":
    unittest.main()
