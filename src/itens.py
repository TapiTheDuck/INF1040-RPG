# ---------------------------------------------------------------------------
# TRECHO PARA O itens.py (persistência do inventário em XML)
#
# Como encaixar:
#   1. Junte os imports abaixo aos do topo do itens.py.
#   2. Defina ERRO_ARQUIVO = 5 junto das outras constantes de código.
#   3. Acrescente "gravar_inventario" e "recuperar_inventario" ao __all__.
#   4. Cole as funções no fim do arquivo.
#   5. Ajuste os nomes das duas estruturas privadas se forem diferentes:
#        _inventario : {"itens": {id: quantidade}, "equipados": {"arma": id|None,
#                       "armadura": id|None}, "ouro": int}
#        _CATALOGO   : {id: ficha}, em que a ficha tem a chave "tipo"
#                      ("arma", "armadura" ou "consumível")
# ---------------------------------------------------------------------------

import os
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement

ERRO_ARQUIVO = 5


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