"""Módulo itens.

Guarda o catálogo fixo de itens e administra, de forma encapsulada, o
inventário do jogador: itens com quantidades, equipamento (arma e armadura)
e ouro.

Convenções do projeto:
  - Todas as funções de acesso retornam (codigo_retorno, resultado).
  - Em caso de erro, nenhum dado do módulo é alterado.

Persistência: o inventário fica na memória; o arquivo XML é usado apenas por
gravar_inventario e recuperar_inventario.
"""

import copy
import os
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement

import personagem

__all__ = [
    "consultar_item",
    "listar_inventario",
    "adicionar_ao_inventario",
    "equipar_item",
    "largar_item",
    "usar_item",
    "consultar_equipamento",
    "adicionar_ouro",
    "reiniciar_inventario",
    "gravar_inventario",
    "recuperar_inventario",
]

# Códigos de retorno (mesmos valores em todos os módulos)
SUCESSO = 0
ERRO_ABORT = 1
ERRO_DADOS_INVALIDOS = 3
ERRO_ID_INEXISTENTE = 4
ERRO_ARQUIVO = 5

# Catálogo fixo (privado). Cada tipo tem seu campo de efeito:
#   arma: "dano" (lados do dado de dano) | armadura: "bonus_ca"
#   consumível: "cura" (PV restaurados) ou "mana" (reservado: ainda não há
#   sistema de mana no módulo Personagem)
# Campo opcional "classes": lista de classes que podem equipar o item
# (ausente = qualquer classe).
_CATALOGO = {
    # --- Armas do guerreiro ---
    "espada_curta": {
        "nome": "Espada Curta",
        "tipo": "arma",
        "descricao": "Uma espada leve e bem equilibrada. Dano: 1d6.",
        "dano": 6,
    },
    "espada_longa": {
        "nome": "Espada Longa",
        "tipo": "arma",
        "descricao": "Lâmina de aço de bom alcance e corte firme. Dano: 1d8.",
        "dano": 8,
        "classes": ["guerreiro"],
    },
    "montante": {
        "nome": "Montante",
        "tipo": "arma",
        "descricao": "Enorme espada de duas mãos, pesada e devastadora. Dano: 1d10.",
        "dano": 10,
        "classes": ["guerreiro"],
    },
    # --- Armas e feitiços do mago ---
    "cajado_arcano": {
        "nome": "Cajado Arcano",
        "tipo": "arma",
        "descricao": "Cajado de carvalho com um cristal que canaliza energia mágica. Dano: 1d6.",
        "dano": 6,
        "classes": ["mago"],
    },
    "feitico_chama": {
        "nome": "Feitiço: Chama Ardente",
        "tipo": "arma",
        "descricao": "Um feitiço que lança uma rajada de fogo no inimigo. Dano: 1d8.",
        "dano": 8,
        "classes": ["mago"],
    },
    "feitico_raio": {
        "nome": "Feitiço: Raio Arcano",
        "tipo": "arma",
        "descricao": "Um feitiço que descarrega um raio de energia pura. Dano: 1d10.",
        "dano": 10,
        "classes": ["mago"],
    },
    # --- Armas do arqueiro ---
    "arco_curto": {
        "nome": "Arco Curto",
        "tipo": "arma",
        "descricao": "Arco ágil, ideal para disparos rápidos. Dano: 1d6.",
        "dano": 6,
        "classes": ["arqueiro"],
    },
    "arco_longo": {
        "nome": "Arco Longo",
        "tipo": "arma",
        "descricao": "Arco de grande alcance e flechas potentes. Dano: 1d8.",
        "dano": 8,
        "classes": ["arqueiro"],
    },
    "besta_leve": {
        "nome": "Besta Leve",
        "tipo": "arma",
        "descricao": "Besta mecânica de disparo certeiro e muita força. Dano: 1d10.",
        "dano": 10,
        "classes": ["arqueiro"],
    },
    # --- Armaduras ---
    "armadura_couro": {
        "nome": "Armadura de Couro",
        "tipo": "armadura",
        "descricao": "Proteção leve de couro curtido. Aumenta a classe de armadura em 2.",
        "bonus_ca": 2,
    },
    "cota_malha": {
        "nome": "Cota de Malha",
        "tipo": "armadura",
        "descricao": "Anéis de aço entrelaçados, pesada e resistente. Aumenta a classe de armadura em 4.",
        "bonus_ca": 4,
        "classes": ["guerreiro"],
    },
    "manto_arcano": {
        "nome": "Manto Arcano",
        "tipo": "armadura",
        "descricao": "Manto encantado que desvia golpes. Aumenta a classe de armadura em 3.",
        "bonus_ca": 3,
        "classes": ["mago"],
    },
    # --- Consumíveis ---
    "pocao_vida": {
        "nome": "Poção de Vida",
        "tipo": "consumível",
        "descricao": "Um líquido vermelho que restaura 5 pontos de vida.",
        "cura": 5,
    },
    "pocao_mana": {
        "nome": "Poção de Mana",
        "tipo": "consumível",
        "descricao": "Um líquido azul cintilante que restauraria 5 pontos de mana.",
        "mana": 5,
    },
}

# Estado privado do módulo
_inventario = {
    "itens": {},
    "equipados": {"arma": None, "armadura": None},
    "ouro": 0,
}


def _texto_valido(valor):
    """Função interna: True se valor é uma string não vazia."""
    return isinstance(valor, str) and valor.strip() != ""


def _inteiro_valido(valor, minimo):
    """Função interna: True se valor é int (bool não vale) e >= minimo."""
    return isinstance(valor, int) and not isinstance(valor, bool) and valor >= minimo


def consultar_item(id_item):
    """Retorna uma cópia da ficha de um item do catálogo.

    Assertivas de entrada:
        id_item (str): texto não vazio.

    Retornos:
        (SUCESSO, item)               cópia da ficha do item
        (ERRO_DADOS_INVALIDOS, None)  id_item não é texto
        (ERRO_ID_INEXISTENTE, None)   o item não existe no catálogo
    """
    if not _texto_valido(id_item):
        return ERRO_DADOS_INVALIDOS, None
    if id_item not in _CATALOGO:
        return ERRO_ID_INEXISTENTE, None
    return SUCESSO, copy.deepcopy(_CATALOGO[id_item])


def listar_inventario():
    """Retorna uma cópia do inventário (itens, equipados e ouro).

    Retornos:
        (SUCESSO, inventario)         cópia da estrutura Inventário
    """
    return SUCESSO, copy.deepcopy(_inventario)


def adicionar_ao_inventario(id_item, quantidade):
    """Adiciona quantidade do item ao inventário, somando ao que já existe.

    Assertivas de entrada:
        id_item (str): texto não vazio, identificador do catálogo.
        quantidade (int): inteiro maior ou igual a 1.

    Retornos:
        (SUCESSO, None)               item adicionado
        (ERRO_DADOS_INVALIDOS, None)  id_item não é texto, ou quantidade
                                      inválida
        (ERRO_ID_INEXISTENTE, None)   o item não existe no catálogo
    """
    if not _texto_valido(id_item) or not _inteiro_valido(quantidade, 1):
        return ERRO_DADOS_INVALIDOS, None
    if id_item not in _CATALOGO:
        return ERRO_ID_INEXISTENTE, None

    _inventario["itens"][id_item] = _inventario["itens"].get(id_item, 0) + quantidade
    return SUCESSO, None


def equipar_item(id_item):
    """Equipa uma arma ou armadura que o jogador possui.

    O item que ocupava o slot continua no inventário e apenas deixa de estar
    equipado.

    Assertivas de entrada:
        id_item (str): texto não vazio, identificador de arma ou armadura
            presente no inventário.

    Retornos:
        (SUCESSO, None)               item equipado
        (ERRO_DADOS_INVALIDOS, None)  id_item não é texto, o item é
                                      consumível (não equipável) ou a classe
                                      do personagem não pode usá-lo
        (ERRO_ID_INEXISTENTE, None)   o item não existe no catálogo ou não
                                      está no inventário
    """
    if not _texto_valido(id_item):
        return ERRO_DADOS_INVALIDOS, None
    if id_item not in _CATALOGO:
        return ERRO_ID_INEXISTENTE, None

    tipo = _CATALOGO[id_item]["tipo"]
    if tipo not in ("arma", "armadura"):
        return ERRO_DADOS_INVALIDOS, None
    if id_item not in _inventario["itens"]:
        return ERRO_ID_INEXISTENTE, None

    # Restrição de classe (só vale se já existe personagem para consultar)
    classes = _CATALOGO[id_item].get("classes")
    if classes is not None:
        codigo, ficha = personagem.consultar_personagem()
        if codigo == personagem.SUCESSO and ficha["classe"]["nome"] not in classes:
            return ERRO_DADOS_INVALIDOS, None

    _inventario["equipados"][tipo] = id_item
    return SUCESSO, None


def largar_item(id_item, quantidade):
    """Remove quantidade do item do inventário.

    Se o item estava equipado e a quantidade chega a zero, ele é
    desequipado automaticamente.

    Assertivas de entrada:
        id_item (str): texto não vazio.
        quantidade (int): maior ou igual a 1 e no máximo a quantidade possuída.

    Retornos:
        (SUCESSO, None)               quantidade removida
        (ERRO_DADOS_INVALIDOS, None)  id_item não é texto, ou quantidade não
                                      é inteira, é menor que 1 ou maior que a
                                      possuída
        (ERRO_ID_INEXISTENTE, None)   o item não existe no catálogo ou não
                                      está no inventário
    """
    if not _texto_valido(id_item) or not _inteiro_valido(quantidade, 1):
        return ERRO_DADOS_INVALIDOS, None
    if id_item not in _CATALOGO or id_item not in _inventario["itens"]:
        return ERRO_ID_INEXISTENTE, None
    if quantidade > _inventario["itens"][id_item]:
        return ERRO_DADOS_INVALIDOS, None

    _inventario["itens"][id_item] -= quantidade
    if _inventario["itens"][id_item] == 0:
        del _inventario["itens"][id_item]
        for slot, equipado in _inventario["equipados"].items():
            if equipado == id_item:
                _inventario["equipados"][slot] = None
    return SUCESSO, None


def usar_item(id_item):
    """Usa um consumível do inventário, curando o personagem.

    O item só é consumido se personagem.curar tiver sucesso.

    Assertivas de entrada:
        id_item (str): texto não vazio, consumível presente no inventário.

    Retornos:
        (SUCESSO, pv)                 item usado e removido; pv atual
        (ERRO_ABORT, None)            personagem.curar falhou (ex.: nenhum
                                      personagem criado); item não consumido
        (ERRO_DADOS_INVALIDOS, None)  id_item não é texto ou o item não é
                                      consumível
        (ERRO_ID_INEXISTENTE, None)   o item não existe no catálogo ou não
                                      está no inventário
    """
    if not _texto_valido(id_item):
        return ERRO_DADOS_INVALIDOS, None
    if id_item not in _CATALOGO:
        return ERRO_ID_INEXISTENTE, None
    if _CATALOGO[id_item]["tipo"] != "consumível":
        return ERRO_DADOS_INVALIDOS, None
    if "cura" not in _CATALOGO[id_item]:
        return ERRO_DADOS_INVALIDOS, None  # ex.: poção de mana (sem sistema de mana ainda)
    if id_item not in _inventario["itens"]:
        return ERRO_ID_INEXISTENTE, None

    codigo, pv = personagem.curar(_CATALOGO[id_item]["cura"])
    if codigo != personagem.SUCESSO:
        return ERRO_ABORT, None

    largar_item(id_item, 1)
    return SUCESSO, pv


def consultar_equipamento():
    """Retorna as fichas da arma e da armadura equipadas.

    Usada pelo Combate para considerar o dano da arma e o bônus de CA.

    Retornos:
        (SUCESSO, equipamento)        {"arma": ficha ou None,
                                       "armadura": ficha ou None}
    """
    equipamento = {}
    for slot, id_item in _inventario["equipados"].items():
        equipamento[slot] = copy.deepcopy(_CATALOGO[id_item]) if id_item else None
    return SUCESSO, equipamento


def adicionar_ouro(quantidade):
    """Soma ouro ao total do jogador.

    Assertivas de entrada:
        quantidade (int): inteiro maior ou igual a zero (bool não é aceito).

    Retornos:
        (SUCESSO, ouro)               ouro somado; total atual
        (ERRO_DADOS_INVALIDOS, None)  quantidade não é inteira ou é negativa
    """
    if not _inteiro_valido(quantidade, 0):
        return ERRO_DADOS_INVALIDOS, None
    _inventario["ouro"] += quantidade
    return SUCESSO, _inventario["ouro"]


def reiniciar_inventario():
    """Esvazia o inventário, desequipa tudo e zera o ouro.

    Retornos:
        (SUCESSO, None)               inventário restaurado ao estado inicial
    """
    _inventario["itens"] = {}
    _inventario["equipados"] = {"arma": None, "armadura": None}
    _inventario["ouro"] = 0
    return SUCESSO, None


# ---------------------------------------------------------------------------
# Persistência do inventário em arquivo XML
# ---------------------------------------------------------------------------
def _escrever_xml(raiz, caminho):
    """Função interna: grava o XML formatado em caminho (UTF-8).

    Escreve num arquivo temporário e o renomeia no fim, para que uma falha no
    meio não corrompa o arquivo anterior. Levanta OSError se não conseguir.
    """
    texto = minidom.parseString(ElementTree.tostring(raiz, "utf-8")).toprettyxml(indent="  ")
    temporario = caminho + ".tmp"
    try:
        with open(temporario, "w", encoding="utf-8") as arquivo:
            arquivo.write(texto)
        os.replace(temporario, caminho)
    except OSError:
        try:
            os.remove(temporario)
        except OSError:
            pass
        raise


def _xml_para_inventario(raiz):
    """Função interna: converte o XML no dicionário do inventário.

    Levanta ValueError (ou AttributeError/TypeError) se o conteúdo for
    inválido ou inconsistente com o catálogo.
    """
    if raiz.tag != "inventario":
        raise ValueError("raiz inesperada")

    ouro = int(raiz.find("ouro").text)
    if ouro < 0:
        raise ValueError("ouro negativo")

    itens_lidos = {}
    for item in raiz.find("itens").findall("item"):
        id_item = item.get("id")
        quantidade = int(item.get("quantidade"))
        if id_item not in _CATALOGO or id_item in itens_lidos or quantidade < 1:
            raise ValueError("item inválido")
        itens_lidos[id_item] = quantidade

    equipados = {}
    for slot in raiz.find("equipados").findall("slot"):
        nome, id_item = slot.get("nome"), slot.get("item")
        equipados[nome] = id_item if id_item else None
    if set(equipados) != {"arma", "armadura"}:
        raise ValueError("slots inválidos")
    for nome, id_item in equipados.items():
        if id_item is not None and (id_item not in itens_lidos
                                    or _CATALOGO[id_item]["tipo"] != nome):
            raise ValueError("equipamento inválido")

    return {"itens": itens_lidos, "equipados": equipados, "ouro": ouro}


def gravar_inventario(caminho):
    """Grava o inventário atual em um arquivo XML.

    Assertivas de entrada:
        caminho (str): texto não vazio com o caminho do arquivo a gravar; a
            pasta do arquivo precisa existir. Um arquivo já existente é
            substituído.
        O inventário sempre existe (pode estar vazio).

    Retornos:
        (SUCESSO, None)               inventário gravado
        (ERRO_DADOS_INVALIDOS, None)  caminho não é texto ou é vazio
        (ERRO_ARQUIVO, None)          falha ao gravar o arquivo
    """
    if not isinstance(caminho, str) or caminho.strip() == "":
        return ERRO_DADOS_INVALIDOS, None

    raiz = Element("inventario")
    SubElement(raiz, "ouro").text = str(_inventario["ouro"])
    itens_xml = SubElement(raiz, "itens")
    for id_item, quantidade in _inventario["itens"].items():
        SubElement(itens_xml, "item", id=id_item, quantidade=str(quantidade))
    equipados_xml = SubElement(raiz, "equipados")
    for slot, id_item in _inventario["equipados"].items():
        SubElement(equipados_xml, "slot", nome=slot, item=id_item or "")

    try:
        _escrever_xml(raiz, caminho)
    except OSError:
        return ERRO_ARQUIVO, None
    return SUCESSO, None


def recuperar_inventario(caminho):
    """Recupera o inventário gravado em um arquivo XML, substituindo o atual.

    Assertivas de entrada:
        caminho (str): texto não vazio com o caminho de um arquivo gravado por
            gravar_inventario.

    Retornos:
        (SUCESSO, None)               inventário restaurado
        (ERRO_DADOS_INVALIDOS, None)  caminho não é texto ou é vazio
        (ERRO_ID_INEXISTENTE, None)   o arquivo não existe
        (ERRO_ARQUIVO, None)          arquivo ilegível ou com conteúdo inválido;
                                      o inventário atual não é alterado
    """
    global _inventario

    if not isinstance(caminho, str) or caminho.strip() == "":
        return ERRO_DADOS_INVALIDOS, None
    if not os.path.isfile(caminho):
        return ERRO_ID_INEXISTENTE, None
    try:
        with open(caminho, "rt", encoding="utf-8") as arquivo:
            raiz = ElementTree.parse(arquivo).getroot()
        novo = _xml_para_inventario(raiz)
    except (OSError, ElementTree.ParseError, ValueError, AttributeError, TypeError, UnicodeError):
        return ERRO_ARQUIVO, None

    _inventario = novo
    return SUCESSO, None
