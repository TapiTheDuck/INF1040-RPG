"""Testes do módulo itens (casos I01 a I26 do documento, seção 7.4).

Cenário antes de cada caso: inventário reiniciado (vazio, nada equipado,
ouro 0) e personagem padrão (guerreiro Lia, PV 12) criado. Catálogo com
"espada_curta" (arma, dano 6), "armadura_couro" (armadura, bonus_ca 2) e
"pocao_vida" (consumível, cura 5). Nos casos "sem personagem", o testador
reinicia o módulo personagem antes da chamada.

Os casos I27 a I33 cobrem as funções de persistência (gravar_inventario e
recuperar_inventario), acrescentadas depois do documento.
"""

import importlib
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import itens  # noqa: E402
import personagem  # noqa: E402


class TestItens(unittest.TestCase):

    def setUp(self):
        itens.reiniciar_inventario()
        importlib.reload(personagem)  # sem acessar a estrutura privada
        personagem.criar_personagem("Lia", "guerreiro")
        pasta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, pasta, ignore_errors=True)
        self.caminho = os.path.join(pasta, "inventario.xml")

    def encher_inventario(self):
        """2 poções, 1 espada equipada e 25 de ouro."""
        itens.adicionar_ao_inventario("pocao_vida", 2)
        itens.adicionar_ao_inventario("espada_curta", 1)
        itens.equipar_item("espada_curta")
        itens.adicionar_ouro(25)

    def inventario(self):
        """Lê o inventário atual."""
        codigo, inventario = itens.listar_inventario()
        self.assertEqual(codigo, 0)
        return inventario

    # --- consultar_item -----------------------------------------------------
    def test_I01_consultar_item_existente(self):
        print("Caso de Teste I01 - Consultar item existente")
        codigo, ficha = itens.consultar_item("pocao_vida")
        self.assertEqual(codigo, 0)
        self.assertEqual(ficha["nome"], "Poção de Vida")
        self.assertEqual(ficha["tipo"], "consumível")
        self.assertEqual(ficha["cura"], 5)
        self.assertIn("descricao", ficha)

    def test_I02_consultar_item_tipo_incorreto(self):
        print("Caso de Teste I02 - Consultar item com parâmetro de tipo incorreto")
        self.assertEqual(itens.consultar_item(None), (3, None))

    def test_I03_consultar_item_inexistente(self):
        print("Caso de Teste I03 - Consultar item inexistente")
        self.assertEqual(itens.consultar_item("item_999"), (4, None))

    # --- listar_inventario --------------------------------------------------
    def test_I04_listar_inventario_vazio(self):
        print("Caso de Teste I04 - Listar inventário vazio")
        self.assertEqual(
            itens.listar_inventario(),
            (0, {"itens": {}, "equipados": {"arma": None, "armadura": None}, "ouro": 0}),
        )

    def test_I05_listar_inventario_com_itens(self):
        print("Caso de Teste I05 - Listar inventário com itens")
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
        print("Caso de Teste I06 - Adicionar item existente")
        self.assertEqual(itens.adicionar_ao_inventario("pocao_vida", 2), (0, None))
        self.assertEqual(itens.listar_inventario()[1]["itens"], {"pocao_vida": 2})

    def test_I07_adicionar_quantidade_invalida(self):
        print("Caso de Teste I07 - Adicionar quantidade inválida")
        self.assertEqual(itens.adicionar_ao_inventario("pocao_vida", 0), (3, None))
        self.assertEqual(itens.adicionar_ao_inventario("pocao_vida", True), (3, None))
        self.assertEqual(itens.listar_inventario()[1]["itens"], {})

    def test_I08_adicionar_identificador_tipo_incorreto(self):
        print("Caso de Teste I08 - Adicionar com identificador de tipo incorreto")
        self.assertEqual(itens.adicionar_ao_inventario(None, 1), (3, None))

    def test_I09_adicionar_item_inexistente(self):
        print("Caso de Teste I09 - Adicionar item inexistente")
        self.assertEqual(itens.adicionar_ao_inventario("item_999", 1), (4, None))

    # --- equipar_item -------------------------------------------------------
    def test_I10_equipar_arma_possuida(self):
        print("Caso de Teste I10 - Equipar arma possuída")
        itens.adicionar_ao_inventario("espada_curta", 1)
        self.assertEqual(itens.equipar_item("espada_curta"), (0, None))
        self.assertEqual(itens.listar_inventario()[1]["equipados"]["arma"], "espada_curta")

    def test_I11_equipar_consumivel(self):
        print("Caso de Teste I11 - Equipar item consumível")
        itens.adicionar_ao_inventario("pocao_vida", 1)
        self.assertEqual(itens.equipar_item("pocao_vida"), (3, None))

    def test_I12_equipar_item_fora_do_inventario(self):
        print("Caso de Teste I12 - Equipar item que não está no inventário")
        self.assertEqual(itens.equipar_item("armadura_couro"), (4, None))
        self.assertEqual(itens.listar_inventario()[1]["equipados"]["armadura"], None)

    def test_I13_equipar_item_inexistente(self):
        print("Caso de Teste I13 - Equipar item inexistente")
        self.assertEqual(itens.equipar_item("item_999"), (4, None))

    # --- largar_item --------------------------------------------------------
    def test_I14_largar_parte_do_item(self):
        print("Caso de Teste I14 - Largar parte de um item")
        itens.adicionar_ao_inventario("pocao_vida", 3)
        self.assertEqual(itens.largar_item("pocao_vida", 1), (0, None))
        self.assertEqual(itens.listar_inventario()[1]["itens"]["pocao_vida"], 2)

    def test_I15_largar_item_equipado(self):
        print("Caso de Teste I15 - Largar item equipado")
        itens.adicionar_ao_inventario("espada_curta", 1)
        itens.equipar_item("espada_curta")
        self.assertEqual(itens.largar_item("espada_curta", 1), (0, None))
        _, inv = itens.listar_inventario()
        self.assertEqual(inv["equipados"]["arma"], None)
        self.assertNotIn("espada_curta", inv["itens"])

    def test_I16_largar_mais_do_que_possui(self):
        print("Caso de Teste I16 - Largar mais do que possui")
        itens.adicionar_ao_inventario("pocao_vida", 2)
        self.assertEqual(itens.largar_item("pocao_vida", 5), (3, None))
        self.assertEqual(itens.listar_inventario()[1]["itens"]["pocao_vida"], 2)

    def test_I17_largar_item_que_nao_possui(self):
        print("Caso de Teste I17 - Largar item que não está no inventário")
        self.assertEqual(itens.largar_item("armadura_couro", 1), (4, None))

    # --- usar_item ----------------------------------------------------------
    def test_I18_usar_pocao_de_vida(self):
        print("Caso de Teste I18 - Usar poção de vida")
        personagem.aplicar_dano(5)
        itens.adicionar_ao_inventario("pocao_vida", 1)
        self.assertEqual(itens.usar_item("pocao_vida"), (0, 12))
        self.assertNotIn("pocao_vida", itens.listar_inventario()[1]["itens"])

    def test_I19_usar_pocao_sem_personagem(self):
        print("Caso de Teste I19 - Usar poção sem personagem criado")
        itens.adicionar_ao_inventario("pocao_vida", 1)
        importlib.reload(personagem)  # reinicia o módulo: nenhum personagem criado
        self.assertEqual(itens.usar_item("pocao_vida"), (1, None))
        self.assertEqual(itens.listar_inventario()[1]["itens"]["pocao_vida"], 1)

    def test_I20_usar_item_nao_consumivel(self):
        print("Caso de Teste I20 - Usar item não consumível")
        itens.adicionar_ao_inventario("espada_curta", 1)
        self.assertEqual(itens.usar_item("espada_curta"), (3, None))

    def test_I21_usar_item_fora_do_inventario(self):
        print("Caso de Teste I21 - Usar item que não está no inventário")
        self.assertEqual(itens.usar_item("pocao_vida"), (4, None))

    # --- consultar_equipamento ----------------------------------------------
    def test_I22_consultar_equipamento_vazio(self):
        print("Caso de Teste I22 - Consultar equipamento vazio")
        self.assertEqual(itens.consultar_equipamento(), (0, {"arma": None, "armadura": None}))

    def test_I23_consultar_equipamento_com_arma(self):
        print("Caso de Teste I23 - Consultar equipamento com arma equipada")
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
        print("Caso de Teste I24 - Adicionar quantidade válida de ouro")
        self.assertEqual(itens.adicionar_ouro(25), (0, 25))

    def test_I25_adicionar_ouro_negativo(self):
        print("Caso de Teste I25 - Adicionar quantidade negativa de ouro")
        self.assertEqual(itens.adicionar_ouro(-10), (3, None))
        self.assertEqual(itens.listar_inventario()[1]["ouro"], 0)

    # --- reiniciar_inventario -----------------------------------------------
    def test_I26_reiniciar_inventario_preenchido(self):
        print("Caso de Teste I26 - Reiniciar inventário preenchido")
        itens.adicionar_ao_inventario("pocao_vida", 2)
        itens.adicionar_ao_inventario("espada_curta", 1)
        itens.equipar_item("espada_curta")
        itens.adicionar_ouro(25)
        self.assertEqual(itens.reiniciar_inventario(), (0, None))
        self.assertEqual(
            itens.listar_inventario(),
            (0, {"itens": {}, "equipados": {"arma": None, "armadura": None}, "ouro": 0}),
        )

    # --- gravar_inventario --------------------------------------------------
    def test_I27_gravar_inventario_ok(self):
        print("Caso de Teste I27 - Gravar inventário em arquivo")
        self.encher_inventario()
        self.assertEqual(itens.gravar_inventario(self.caminho), (0, None))
        self.assertTrue(os.path.isfile(self.caminho))

    def test_I28_gravar_inventario_nok_caminho_invalido(self):
        print("Caso de Teste I28 - Gravar com caminho vazio ou de tipo incorreto")
        self.assertEqual(itens.gravar_inventario(""), (3, None))
        self.assertEqual(itens.gravar_inventario(123), (3, None))

    def test_I29_gravar_inventario_nok_falha_no_arquivo(self):
        print("Caso de Teste I29 - Gravar em pasta que não existe")
        caminho = os.path.join(os.path.dirname(self.caminho), "pasta_inexistente", "inventario.xml")
        self.assertEqual(itens.gravar_inventario(caminho), (5, None))

    # --- recuperar_inventario -----------------------------------------------
    def test_I30_recuperar_inventario_ok(self):
        print("Caso de Teste I30 - Recuperar inventário gravado")
        self.encher_inventario()
        gravado = self.inventario()
        self.assertEqual(itens.gravar_inventario(self.caminho), (0, None))
        itens.reiniciar_inventario()
        self.assertEqual(itens.recuperar_inventario(self.caminho), (0, None))
        self.assertEqual(self.inventario(), gravado)

    def test_I31_recuperar_inventario_nok_caminho_invalido(self):
        print("Caso de Teste I31 - Recuperar com caminho vazio ou de tipo incorreto")
        self.assertEqual(itens.recuperar_inventario(""), (3, None))
        self.assertEqual(itens.recuperar_inventario(None), (3, None))

    def test_I32_recuperar_inventario_nok_arquivo_inexistente(self):
        print("Caso de Teste I32 - Recuperar de arquivo que não existe")
        self.assertEqual(itens.recuperar_inventario(self.caminho), (4, None))

    def test_I33_recuperar_inventario_nok_arquivo_invalido(self):
        print("Caso de Teste I33 - Arquivo ilegível ou inválido não altera o inventário")
        itens.adicionar_ao_inventario("pocao_vida", 1)
        antes = self.inventario()
        with open(self.caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write("isto não é xml")
        self.assertEqual(itens.recuperar_inventario(self.caminho), (5, None))
        self.assertEqual(self.inventario(), antes)


if __name__ == "__main__":
    unittest.main()
