"""Módulo narrativa.

Guarda a história fixa do jogo (cenas, escolhas e transições) e conduz os
momentos em que a história chama outros módulos (combate, itens, personagem).

Convenções do projeto:
  - Todas as funções de acesso retornam (codigo_retorno, resultado).
  - Este módulo não guarda estado: o id da cena atual é sempre passado por
    parâmetro (quem controla a cena atual é o módulo principal).
  - Cada cena pode ter "variantes" por classe, que substituem partes dela
    (texto, escolhas...); o que não for listado vale o da cena base.
"""

import copy

import combate
import itens
import personagem

__all__ = ["iniciar_cena", "processar_escolha", "iniciar_combate"]

# Códigos de retorno (mesmos valores em todos os módulos)
SUCESSO = 0
ERRO_ABORT = 1
ERRO_DADOS_INVALIDOS = 3
ERRO_ID_INEXISTENTE = 4

# História fixa (textos de exemplo: substituir pelos reais)
#   escolhas : {id_escolha: {"texto": ..., "proxima": id_cena}}
#   combate  : None ou {"inimigo": id_inimigo, "vitoria": id_cena, "derrota": id_cena}
#   variantes: {nome_da_classe: {chaves da cena que mudam para essa classe}}
_CENAS = {
    "inicio": {
        "texto": (
            "O sol da manhã ilumina a entrada da caverna enquanto os pássaros "
            "cantam e o vento sopra no meio da floresta desconhecida. "
            "Você se sente preparado para uma aventura!"
        ),
        "escolhas": {
            "1": {"texto": "Entrar na caverna", "proxima": "caverna"},
        },
        "combate": None,
        "final": False,
    },
    "caverna": {
        "texto": (
            "Você entra na caverna. Os seus pés se molham por conta do rio que "
            "estava no caminho. É possível observar um caminho na entrada do "
            "local, muita gente passou por aqui.\n\n"
            ". . .\n\n"
            "Você caminha mais fundo e repara em um rastro viscoso, um monstro "
            "deve ter se perdido por aqui."
        ),
        "escolhas": {
            "1": {"texto": "Seguir o rastro viscoso", "proxima": "combate_slime"},
        },
        "combate": None,
        "final": False,
    },
    "combate_slime": {
        "texto": "O combate se inicia!",
        "escolhas": {},
        "combate": {"inimigo": "slime", "vitoria": "pos_combate", "derrota": "fim_derrota"},
        "final": False,
    },
    "pos_combate": {
        "texto": (
            "Não foi um combate difícil, você ainda tem muita energia para "
            "seguir pelo caminho feito por prévios exploradores."
        ),
        "escolhas": {
            "1": {"texto": "Vasculhar inimigo", "proxima": "vasculhar"},
            "2": {"texto": "Seguir caminho", "proxima": "escadas"},
        },
        "combate": None,
        "final": False,
    },
    "vasculhar": {
        "texto": "Nada foi encontrado",
        "escolhas": {
            "1": {"texto": "Voltar ao caminho", "proxima": "pos_combate"},
        },
        "combate": None,
        "final": False,
    },
    "escadas": {
        "texto": (
            "Após uma caminhada, você encontra escadas. Um corrimão bem firme e "
            "madeira de qualidade da floresta te dão a sensação de que a sua "
            "chegada é esperada..."
        ),
        "escolhas": {
            "1": {"texto": "Descer as escadas", "proxima": "npc"},
        },
        "combate": None,
        "final": False,
    },
        "npc": {
        "texto": (
            "As escadas te levam para uma outra repartição do local.\n"
            "A vista do céu recortada pelo relevo acima de você te banha com rastros da luz do sol\n\n"
            "Um outro viajante aguarda você se aproximando. Ele parece tranquilo, carrega uma grande "
            "mochila com equipamentos de mineração e acampamento.\n\n"
            "' Olá viajante! Seja bem-vindo à Estrada Alvorada. Meu nome é Flávio!'\n\n"
            "O aventureiro espera sua resposta...\n\n"
            "*Você se apresenta.\n\n"
            "É um prazer! Espero não estar te atrapalhando, sei que o caminho até a primeira Cidade "
            "Submersa. Sobre isso... eu estou desenvolvendo uma rota mais rápida, mas preciso de uma ajuda."
        ),
        "escolhas": {
            "1": {"texto": "Ouvir mais", "proxima": "npc_ouvir_mais"},
            "2": {"texto": "Seguir caminho", "proxima": "npc_recusa"},
        },
        "combate": None,
        "final": False,
    },
    "npc_ouvir_mais": {
        "texto": (
            "' É o caminho que eu abri vindo da cidade até a entrada do trajeto. Por descuido meu, o "
            "caminho ficou muito inseguro e aranhas enormes tomaram o local. Não esperava precisar "
            "engajar em nenhum combate no caminho até a superfície, mas parece que é meu dia de sorte. "
            "Posso te apontar o caminho e eu espero te encontrar na cidade.'\n\n"
            "Ele vai em direção à parede do lado oposto daonde o caminho segue, revelando uma "
            "bifurcação bem menor. Você consegue observar que o caminho está iluminado e sem nenhuma "
            "armadilha.\n\n"
            "' Tome aqui, pode ficar com esse amuleto dourado. Quando chegar em uma estalagem, vão "
            "reconhecer o brasão, é o símbolo da minha família.  Por conta dos monstros, eu devo chegar "
            "antes de você e te ver uma recompensa digna. Não esqueça de tapar os buracos no caminho "
            "para mantê-lo longe das pestes.'\n\n"
            "Brilhante."
        ),
        "escolhas": {
            "1": {"texto": "Aceitar a missão e pegar o amuleto", "proxima": "npc_aceita"},
            "2": {"texto": "Negar e seguir caminho", "proxima": "npc_recusa"},
        },
        "combate": None,
        "final": False,
    },
    "npc_recusa": {
        "texto": "Entendo, tenha uma ótima aventura.",
        "escolhas": {},
        "combate": None,
        "final": True,  # provisório: fim do ato 0
    },
    "npc_aceita": {
        "texto": "Muito obrigado!",
        "escolhas": {},
        "combate": None,
        "final": True, 
        "variantes": {
            "guerreiro": {"texto": "' Eu sabia que um guerreiro como você seria de confiança'"},
            "mago": {"texto": "'Sábia decisão vinda de um sábio aventureiro.'"},
            "arqueiro": {"texto": "'Espero que não tenha que lidar com nenhuma armadilha sua no caminho "
                                  "depois... vamos manter uma boa relação'."},
        },
    },
    "fim_derrota": {
        "texto": "Fim da aventura.",
        "escolhas": {},
        "combate": None,
        "final": True,
    },
}

def _texto_valido(valor):
    """True se valor é uma string não vazia."""
    return isinstance(valor, str) and valor.strip() != ""


def _classe_do_personagem():
    """Lê a classe pelo módulo personagem.

    Retorna (SUCESSO, nome_da_classe) ou (ERRO_ABORT, None) se a consulta
    ao personagem falhar (por exemplo, personagem ainda não criado).
    """
    codigo, dados = personagem.consultar_personagem()
    if codigo != personagem.SUCESSO:
        return ERRO_ABORT, None
    return SUCESSO, dados["classe"]["nome"]


def _cena_para_classe(id_cena, classe):
    """Cópia da cena com a variante da classe aplicada (se existir)."""
    cena = copy.deepcopy(_CENAS[id_cena])
    variantes = cena.pop("variantes", {})
    cena.update(variantes.get(classe, {}))
    cena["id"] = id_cena
    return cena


def iniciar_cena(id_cena):
    """Retorna uma cópia da cena, já adaptada à classe do personagem.

    Assertivas de entrada:
        id_cena (str): texto não vazio; deve ser o identificador de uma cena
            da história (o Principal guarda o identificador da cena atual).
        Exige que um personagem já tenha sido criado, porque a classe dele
        define a variante da cena.

    Retornos:
        (SUCESSO, cena)               cena encontrada e adaptada
        (ERRO_ABORT, None)            a consulta ao personagem falhou
        (ERRO_DADOS_INVALIDOS, None)  id_cena não é texto (ou é vazio)
        (ERRO_ID_INEXISTENTE, None)   não existe cena com esse identificador
    """
    if not _texto_valido(id_cena):
        return ERRO_DADOS_INVALIDOS, None
    if id_cena not in _CENAS:
        return ERRO_ID_INEXISTENTE, None

    codigo, classe = _classe_do_personagem()
    if codigo != SUCESSO:
        return ERRO_ABORT, None

    return SUCESSO, _cena_para_classe(id_cena, classe)


def processar_escolha(id_cena, id_escolha):
    """Informa para qual cena a escolha feita na cena atual leva.

    Assertivas de entrada:
        id_cena (str): texto não vazio; identificador da cena atual.
        id_escolha (str): texto não vazio; identificador de uma das escolhas
            dessa cena para a classe do personagem (escolhas exclusivas de
            outra classe não são aceitas).
        Exige que um personagem já tenha sido criado.

    Retornos:
        (SUCESSO, id_proxima_cena)    escolha válida
        (ERRO_ABORT, None)            a consulta ao personagem falhou
        (ERRO_DADOS_INVALIDOS, None)  id_cena ou id_escolha não é texto
        (ERRO_ID_INEXISTENTE, None)   cena inexistente, ou escolha inexistente
                                      nessa cena para a classe do personagem
    """
    if not _texto_valido(id_cena) or not _texto_valido(id_escolha):
        return ERRO_DADOS_INVALIDOS, None
    if id_cena not in _CENAS:
        return ERRO_ID_INEXISTENTE, None

    codigo, classe = _classe_do_personagem()
    if codigo != SUCESSO:
        return ERRO_ABORT, None

    escolhas = _cena_para_classe(id_cena, classe)["escolhas"]
    if id_escolha not in escolhas:
        return ERRO_ID_INEXISTENTE, None
    return SUCESSO, escolhas[id_escolha]["proxima"]


def iniciar_combate(id_cena, obter_acao):
    """Conduz o combate da cena e aplica as consequências.

    Chama combate.orquestrar_combate. Em caso de vitória, pega a recompensa
    em combate.dropar_itens e a entrega por itens.adicionar_ao_inventario,
    itens.adicionar_ouro e personagem.subir_xp. Em caso de derrota, chama
    personagem.matar_personagem.

    Assertivas de entrada:
        id_cena (str): texto não vazio; identificador de uma cena que tenha
            combate associado.
        obter_acao (função): recebe uma cópia do estado do combate e devolve
            a ação do jogador no turno; é fornecida pelo Principal e apenas
            repassada ao módulo Combate.

    Retornos:
        (SUCESSO, {"vitoria": bool, "proxima_cena": id})  combate concluído
        (ERRO_ABORT, None)            alguma chamada a Combate, Personagem
                                      ou Itens falhou
        (ERRO_DADOS_INVALIDOS, None)  id_cena não é texto ou obter_acao não
                                      é função
        (ERRO_ID_INEXISTENTE, None)   cena inexistente ou sem combate
    """
    if not _texto_valido(id_cena) or not callable(obter_acao):
        return ERRO_DADOS_INVALIDOS, None
    if id_cena not in _CENAS or _CENAS[id_cena]["combate"] is None:
        return ERRO_ID_INEXISTENTE, None

    dados = _CENAS[id_cena]["combate"]
    id_inimigo = dados["inimigo"]

    codigo, vencedor = combate.orquestrar_combate(id_inimigo, obter_acao)
    if codigo != combate.SUCESSO:
        return ERRO_ABORT, None

    if vencedor == "jogador":
        codigo, recompensa = combate.dropar_itens(id_inimigo)
        if codigo != combate.SUCESSO:
            return ERRO_ABORT, None

        for id_item, quantidade in recompensa["itens"].items():
            codigo, _ = itens.adicionar_ao_inventario(id_item, quantidade)
            if codigo != itens.SUCESSO:
                return ERRO_ABORT, None

        codigo, _ = itens.adicionar_ouro(recompensa["ouro"])
        if codigo != itens.SUCESSO:
            return ERRO_ABORT, None

        codigo, _ = personagem.subir_xp(recompensa["xp"])
        if codigo != personagem.SUCESSO:
            return ERRO_ABORT, None

        return SUCESSO, {"vitoria": True, "proxima_cena": dados["vitoria"]}

    if vencedor == "inimigo":
        codigo, _ = personagem.matar_personagem()
        if codigo != personagem.SUCESSO:
            return ERRO_ABORT, None
        return SUCESSO, {"vitoria": False, "proxima_cena": dados["derrota"]}

    return ERRO_ABORT, None