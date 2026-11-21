"""Módulo personagem.

Guarda e manipula os dados do personagem do jogador. Existe um único
personagem por vez, mantido em estado privado do módulo.

Todas as funções de acesso retornam (codigo_retorno, resultado).
"""

import copy

__all__ = [
    "criar_personagem",
    "consultar_personagem",
    "subir_xp",
    "aplicar_dano",
    "curar",
    "matar_personagem",
]

# Códigos de retorno (mesmos valores em todos os módulos)
SUCESSO = 0
ERRO_ABORT = 1
ERRO_DADOS_INVALIDOS = 3
ERRO_ID_INEXISTENTE = 4

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


def passar_nivel():
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
        passar_nivel()
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