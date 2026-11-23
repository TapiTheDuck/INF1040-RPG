"""Módulo personagem.

Guarda e manipula os dados do personagem do jogador. Existe um único
personagem por vez, mantido em estado privado do módulo.

Todas as funções de acesso retornam (codigo_retorno, resultado).

Persistência: durante o jogo os dados ficam só na memória do módulo; o arquivo
XML é usado apenas para gravar o personagem (gravar_personagem) e recuperá-lo
em uma execução posterior (recuperar_personagem).
"""

import copy
import os
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement

__all__ = [
    "criar_personagem",
    "consultar_personagem",
    "subir_xp",
    "aplicar_dano",
    "curar",
    "matar_personagem",
    "gravar_personagem",
    "recuperar_personagem",
]

# Códigos de retorno (mesmos valores em todos os módulos)
SUCESSO = 0
ERRO_ABORT = 1
ERRO_DADOS_INVALIDOS = 3
ERRO_ID_INEXISTENTE = 4
ERRO_ARQUIVO = 5

# XP para sair do nível N: _XP_BASE * N (nível 1 -> 100, nível 2 -> 200...)
_XP_BASE = 100

# Valores iniciais e ganhos por nível de cada classe.
# Os ganhos são valores provisórios: ajuste ao balancear o jogo.
_CLASSES = {
    "guerreiro": {
        "pv_inicial": 12,
        "atributos": {"forca": 15, "destreza": 13, "constituicao": 14,
                      "inteligencia": 8, "sabedoria": 10, "carisma": 12},
        "ganho_pv": 6,
        "ganho_atributos": {"forca": 2, "constituicao": 1},
    },
    "mago": {
        "pv_inicial": 7,
        "atributos": {"forca": 8, "destreza": 14, "constituicao": 12,
                      "inteligencia": 15, "sabedoria": 13, "carisma": 10},
        "ganho_pv": 4,
        "ganho_atributos": {"inteligencia": 2, "sabedoria": 1},
    },
    "arqueiro": {
        "pv_inicial": 9,
        "atributos": {"forca": 10, "destreza": 15, "constituicao": 13,
                      "inteligencia": 8, "sabedoria": 14, "carisma": 12},
        "ganho_pv": 5,
        "ganho_atributos": {"destreza": 2, "sabedoria": 1},
    },
}

# Estado privado do módulo (None = ainda não existe personagem)
_personagem = None


def _inteiro_nao_negativo(valor):
    """True se valor é um int (bool não vale) maior ou igual a zero."""
    return isinstance(valor, int) and not isinstance(valor, bool) and valor >= 0


def _passar_nivel():
    """Função interna: sobe o personagem um nível conforme a sua classe.

    Aumenta o nível, melhora os atributos e o PV máximo da classe e recalcula
    xp_max. Quem chama (subir_xp) já garantiu que o personagem existe, e o
    controle do xp excedente também fica com ela.
    """
    ficha = _CLASSES[_personagem["classe"]["nome"]]
    atributos = _personagem["classe"]["atributos"]
    for atributo, ganho in ficha["ganho_atributos"].items():
        atributos[atributo] += ganho

    _personagem["nivel"] += 1
    _personagem["pv_max"] += ficha["ganho_pv"]
    _personagem["pv"] += ficha["ganho_pv"]
    _personagem["xp_max"] = _XP_BASE * _personagem["nivel"]


def criar_personagem(nome, classe):
    """Cria o personagem do jogador, substituindo o anterior (se houver).

    Assertivas de entrada:
        nome (str): texto não vazio; espaços nas pontas são ignorados.
        classe (str): "guerreiro", "mago" ou "arqueiro".
        Não exige personagem prévio: se já existir um, é substituído.

    Retornos:
        (SUCESSO, None)               personagem criado
        (ERRO_DADOS_INVALIDOS, None)  nome não é texto ou é vazio, ou classe
                                      não é uma das três permitidas
    """
    global _personagem

    if not isinstance(nome, str) or nome.strip() == "":
        return ERRO_DADOS_INVALIDOS, None
    if not isinstance(classe, str) or classe not in _CLASSES:
        return ERRO_DADOS_INVALIDOS, None

    pv = _CLASSES[classe]["pv_inicial"]
    _personagem = {
        "nome": nome.strip(),
        "classe": {
            "nome": classe,
            "atributos": copy.deepcopy(_CLASSES[classe]["atributos"]),
        },
        "nivel": 1,
        "xp": 0,
        "xp_max": _XP_BASE,
        "pv": pv,
        "pv_max": pv,
        "vivo": True,
    }
    return SUCESSO, None


def consultar_personagem():
    """Retorna uma cópia dos dados atuais do personagem.

    Assertivas de entrada:
        Nenhum parâmetro.
        Exige que um personagem já tenha sido criado.

    Retornos:
        (SUCESSO, personagem)         cópia da estrutura Personagem
        (ERRO_ID_INEXISTENTE, None)   nenhum personagem foi criado
    """
    if _personagem is None:
        return ERRO_ID_INEXISTENTE, None
    return SUCESSO, copy.deepcopy(_personagem)


def subir_xp(valor):
    """Soma experiência ao personagem, subindo de nível quantas vezes for
    preciso; o excedente segue para o novo nível.

    Assertivas de entrada:
        valor (int): inteiro maior ou igual a zero (bool não é aceito).
        Exige que um personagem já tenha sido criado.

    Retornos:
        (SUCESSO, nivel)              xp somado; nivel é o nível atual
        (ERRO_DADOS_INVALIDOS, None)  valor não é inteiro ou é negativo
        (ERRO_ID_INEXISTENTE, None)   nenhum personagem foi criado
    """
    if not _inteiro_nao_negativo(valor):
        return ERRO_DADOS_INVALIDOS, None
    if _personagem is None:
        return ERRO_ID_INEXISTENTE, None

    _personagem["xp"] += valor
    while _personagem["xp"] >= _personagem["xp_max"]:
        _personagem["xp"] -= _personagem["xp_max"]
        _passar_nivel()
    return SUCESSO, _personagem["nivel"]


def aplicar_dano(valor):
    """Reduz o PV do personagem em valor, sem passar de zero. Se chegar a
    zero, o personagem passa a ser considerado morto.

    Assertivas de entrada:
        valor (int): inteiro maior ou igual a zero (bool não é aceito).
        Exige que um personagem já tenha sido criado.

    Retornos:
        (SUCESSO, pv)                 PV atual, nunca menor que 0
        (ERRO_DADOS_INVALIDOS, None)  valor não é inteiro ou é negativo
        (ERRO_ID_INEXISTENTE, None)   nenhum personagem foi criado
    """
    if not _inteiro_nao_negativo(valor):
        return ERRO_DADOS_INVALIDOS, None
    if _personagem is None:
        return ERRO_ID_INEXISTENTE, None

    _personagem["pv"] = max(0, _personagem["pv"] - valor)
    if _personagem["pv"] == 0:
        _personagem["vivo"] = False
    return SUCESSO, _personagem["pv"]


def curar(valor):
    """Aumenta o PV do personagem em valor, sem passar de pv_max.

    Assertivas de entrada:
        valor (int): inteiro maior ou igual a zero (bool não é aceito).
        Exige que um personagem já tenha sido criado.

    Retornos:
        (SUCESSO, pv)                 PV atual, nunca maior que pv_max
        (ERRO_DADOS_INVALIDOS, None)  valor não é inteiro ou é negativo
        (ERRO_ID_INEXISTENTE, None)   nenhum personagem foi criado
    """
    if not _inteiro_nao_negativo(valor):
        return ERRO_DADOS_INVALIDOS, None
    if _personagem is None:
        return ERRO_ID_INEXISTENTE, None

    _personagem["pv"] = min(_personagem["pv_max"], _personagem["pv"] + valor)
    return SUCESSO, _personagem["pv"]


def matar_personagem():
    """Registra a morte do personagem: zera o PV e marca vivo como False.

    Assertivas de entrada:
        Nenhum parâmetro.
        Exige que um personagem já tenha sido criado.

    Retornos:
        (SUCESSO, None)               morte registrada
        (ERRO_ID_INEXISTENTE, None)   nenhum personagem foi criado
    """
    if _personagem is None:
        return ERRO_ID_INEXISTENTE, None
    _personagem["pv"] = 0
    _personagem["vivo"] = False
    return SUCESSO, None


# ---------------------------------------------------------------------------
# Persistência em arquivo XML
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


def _personagem_para_xml(dados):
    """Função interna: monta o XML do personagem a partir do dicionário."""
    raiz = Element("personagem")
    SubElement(raiz, "nome").text = dados["nome"]
    classe = SubElement(raiz, "classe", nome=dados["classe"]["nome"])
    for nome, valor in dados["classe"]["atributos"].items():
        SubElement(classe, "atributo", nome=nome).text = str(valor)
    for campo in ("nivel", "xp", "xp_max", "pv", "pv_max"):
        SubElement(raiz, campo).text = str(dados[campo])
    SubElement(raiz, "vivo").text = str(dados["vivo"])
    return raiz


def _ler_inteiro(raiz, campo, minimo):
    """Função interna: lê um campo inteiro do XML, com valor mínimo."""
    valor = int(raiz.find(campo).text)
    if valor < minimo:
        raise ValueError(campo)
    return valor


def _xml_para_personagem(raiz):
    """Função interna: converte o XML no dicionário do personagem.

    Levanta ValueError (ou AttributeError/TypeError) se o conteúdo for
    inválido ou inconsistente.
    """
    if raiz.tag != "personagem":
        raise ValueError("raiz inesperada")
    nome = raiz.find("nome").text.strip()
    elemento_classe = raiz.find("classe")
    nome_classe = elemento_classe.get("nome")
    if nome == "" or nome_classe not in _CLASSES:
        raise ValueError("nome ou classe inválidos")

    atributos = {a.get("nome"): int(a.text) for a in elemento_classe.findall("atributo")}
    if set(atributos) != set(_CLASSES[nome_classe]["atributos"]):
        raise ValueError("atributos inválidos")

    nivel = _ler_inteiro(raiz, "nivel", 1)
    xp_max = _ler_inteiro(raiz, "xp_max", 1)
    xp = _ler_inteiro(raiz, "xp", 0)
    pv_max = _ler_inteiro(raiz, "pv_max", 1)
    pv = _ler_inteiro(raiz, "pv", 0)
    vivo = raiz.find("vivo").text.strip()
    if (xp_max != _XP_BASE * nivel or xp >= xp_max or pv > pv_max
            or vivo not in ("True", "False") or (vivo == "True") != (pv > 0)):
        raise ValueError("valores inconsistentes")

    return {
        "nome": nome,
        "classe": {"nome": nome_classe, "atributos": atributos},
        "nivel": nivel,
        "xp": xp,
        "xp_max": xp_max,
        "pv": pv,
        "pv_max": pv_max,
        "vivo": vivo == "True",
    }


def gravar_personagem(caminho):
    """Grava o personagem atual em um arquivo XML.

    Assertivas de entrada:
        caminho (str): texto não vazio com o caminho do arquivo a gravar; a
            pasta do arquivo precisa existir. Um arquivo já existente é
            substituído.
        Exige que um personagem já tenha sido criado.

    Retornos:
        (SUCESSO, None)               personagem gravado
        (ERRO_DADOS_INVALIDOS, None)  caminho não é texto ou é vazio
        (ERRO_ID_INEXISTENTE, None)   nenhum personagem foi criado
        (ERRO_ARQUIVO, None)          falha ao gravar o arquivo
    """
    if not isinstance(caminho, str) or caminho.strip() == "":
        return ERRO_DADOS_INVALIDOS, None
    if _personagem is None:
        return ERRO_ID_INEXISTENTE, None
    try:
        _escrever_xml(_personagem_para_xml(_personagem), caminho)
    except OSError:
        return ERRO_ARQUIVO, None
    return SUCESSO, None


def recuperar_personagem(caminho):
    """Recupera o personagem gravado em um arquivo XML, substituindo o atual.

    Assertivas de entrada:
        caminho (str): texto não vazio com o caminho de um arquivo gravado por
            gravar_personagem.
        Não exige personagem prévio.

    Retornos:
        (SUCESSO, None)               personagem restaurado
        (ERRO_DADOS_INVALIDOS, None)  caminho não é texto ou é vazio
        (ERRO_ID_INEXISTENTE, None)   o arquivo não existe
        (ERRO_ARQUIVO, None)          arquivo ilegível ou com conteúdo inválido;
                                      o personagem atual não é alterado
    """
    global _personagem

    if not isinstance(caminho, str) or caminho.strip() == "":
        return ERRO_DADOS_INVALIDOS, None
    if not os.path.isfile(caminho):
        return ERRO_ID_INEXISTENTE, None
    try:
        with open(caminho, "rt", encoding="utf-8") as arquivo:
            raiz = ElementTree.parse(arquivo).getroot()
        novo = _xml_para_personagem(raiz)
    except (OSError, ElementTree.ParseError, ValueError, AttributeError, TypeError, UnicodeError):
        return ERRO_ARQUIVO, None

    _personagem = novo
    return SUCESSO, None