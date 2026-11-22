"""Módulo principal (main).

Integra os módulos Personagem, Narrativa e Itens: controla o loop do jogo,
o menu, a criação do personagem e a interação com o usuário. Não possui
funções de acesso (não é servidor de nenhum módulo) nem módulo testador.

Toda entrada e saída passa por _exibir e _ler, para que a interface possa
ser trocada (terminal, navegador) sem mexer na lógica do jogo.
"""

import itens
import narrativa
import personagem

# Códigos de retorno (mesmos valores em todos os módulos)
SUCESSO = 0
ERRO_ABORT = 1
ERRO_DADOS_INVALIDOS = 3
ERRO_ID_INEXISTENTE = 4

ID_CENA_INICIAL = "inicio"
CLASSES = ("guerreiro", "mago", "arqueiro")

# Dados de sessão do Principal:
#   id_cena         : cena em que o jogador está (DadoCenaAtual)
#   escolhas_feitas : pares (id_cena, id_escolha) já escolhidos, para marcar "[FEITO]"
#   encerrar        : True quando o jogador pede para encerrar o programa
_sessao = {"id_cena": ID_CENA_INICIAL, "escolhas_feitas": set(), "encerrar": False}

_MENSAGENS_ERRO = {
    ERRO_ABORT: "Não foi possível concluir a operação.",
    ERRO_DADOS_INVALIDOS: "Entrada inválida.",
    ERRO_ID_INEXISTENTE: "Opção inexistente.",
}


# ---------------------------------------------------------------------------
# Entrada e saída (único ponto de contato com o terminal)
# ---------------------------------------------------------------------------
def _exibir(texto=""):
    print(texto)


def _ler(prompt):
    return input(prompt).strip()


def _mostrar_erro(codigo, especificas=None):
    """Mostra a mensagem do código de erro, sem interromper o jogo.

    especificas (opcional) troca a mensagem padrão de alguns códigos.
    """
    mensagens = especificas or {}
    _exibir(mensagens.get(codigo, _MENSAGENS_ERRO.get(codigo, "Erro inesperado.")))


# ---------------------------------------------------------------------------
# Personagem
# ---------------------------------------------------------------------------
def criar_novo_personagem():
    """Pede nome e classe, cria o personagem e reinicia o inventário e o
    progresso. Devolve True se o jogo pode começar."""
    while True:
        nome = _ler("Nome do personagem: ")
        _exibir("Classes:")
        for n, classe in enumerate(CLASSES, 1):
            _exibir(f"{n}) {classe.capitalize()}")
        opcao = _ler("Classe: ")
        if not opcao.isdecimal() or not 1 <= int(opcao) <= len(CLASSES):
            _mostrar_erro(ERRO_DADOS_INVALIDOS)
            continue

        codigo, _ = personagem.criar_personagem(nome, CLASSES[int(opcao) - 1])
        if codigo != SUCESSO:
            _mostrar_erro(codigo, {ERRO_DADOS_INVALIDOS: "Nome inválido: não pode ser vazio."})
            continue

        codigo, _ = itens.reiniciar_inventario()
        if codigo != SUCESSO:
            _mostrar_erro(codigo)
            return False

        _sessao["id_cena"] = ID_CENA_INICIAL
        _sessao["escolhas_feitas"].clear()
        return True


def exibir_personagem():
    codigo, dados = personagem.consultar_personagem()
    if codigo != SUCESSO:
        _mostrar_erro(codigo, {ERRO_ID_INEXISTENTE: "Nenhum personagem criado."})
        return
    _exibir(f"\n== {dados['nome']} ({dados['classe']['nome']}) ==")
    _exibir(f"Nível {dados['nivel']}   XP {dados['xp']}/{dados['xp_max']}   "
            f"PV {dados['pv']}/{dados['pv_max']}")
    atributos = ", ".join(f"{nome}: {valor}"
                          for nome, valor in dados["classe"]["atributos"].items())
    _exibir(f"Atributos: {atributos}")


# ---------------------------------------------------------------------------
# Inventário
# ---------------------------------------------------------------------------
def _carregar_inventario():
    """Lê o inventário e as fichas dos itens.

    Devolve (lista, inventario), em que lista é [(id_item, ficha, quantidade)].
    Em caso de erro, mostra a mensagem e devolve (None, None).
    """
    codigo, inv = itens.listar_inventario()
    if codigo != SUCESSO:
        _mostrar_erro(codigo)
        return None, None
    lista = []
    for id_item, quantidade in inv["itens"].items():
        codigo, ficha = itens.consultar_item(id_item)
        if codigo != SUCESSO:
            ficha = {"nome": id_item}
        lista.append((id_item, ficha, quantidade))
    return lista, inv


def exibir_inventario():
    """Mostra o inventário numerado e devolve a lista [(id, ficha, qtd)]
    (ou None se houve erro)."""
    lista, inv = _carregar_inventario()
    if lista is None:
        return None
    _exibir("\n== Inventário ==")
    if not lista:
        _exibir("(vazio)")
    equipados = list(inv["equipados"].values())
    for n, (id_item, ficha, quantidade) in enumerate(lista, 1):
        marca = " [EQUIPADO]" if id_item in equipados else ""
        _exibir(f"{n}) {ficha['nome']} x{quantidade}{marca}")
    _exibir(f"Ouro: {inv['ouro']}")
    return lista


def _escolher_item(lista):
    """Pede o número de um item da lista. Devolve o id_item ou None."""
    texto = _ler("Número do item (Enter cancela): ")
    if texto == "":
        return None
    if not texto.isdecimal() or not 1 <= int(texto) <= len(lista):
        _mostrar_erro(ERRO_ID_INEXISTENTE)
        return None
    return lista[int(texto) - 1][0]


def _detalhes_item(id_item):
    codigo, ficha = itens.consultar_item(id_item)
    if codigo != SUCESSO:
        _mostrar_erro(codigo)
        return
    _exibir(f"\n{ficha['nome']} ({ficha['tipo']})")
    _exibir(ficha["descricao"])
    for campo, rotulo in (("dano", "Dano"), ("bonus_ca", "Bônus de CA"), ("cura", "Cura")):
        if ficha.get(campo) is not None:
            _exibir(f"{rotulo}: {ficha[campo]}")


def _equipar_item(id_item):
    codigo, _ = itens.equipar_item(id_item)
    if codigo == SUCESSO:
        _exibir("Item equipado.")
    else:
        _mostrar_erro(codigo, {
            ERRO_DADOS_INVALIDOS: "Esse item não pode ser equipado.",
            ERRO_ID_INEXISTENTE: "Você não possui esse item.",
        })


def _usar_item(id_item):
    """Usa um consumível. Devolve True se o item foi usado."""
    codigo, pv = itens.usar_item(id_item)
    if codigo == SUCESSO:
        _exibir(f"Item usado. PV atual: {pv}")
        return True
    _mostrar_erro(codigo, {
        ERRO_ABORT: "Não foi possível usar o item agora.",
        ERRO_DADOS_INVALIDOS: "Esse item não é consumível.",
        ERRO_ID_INEXISTENTE: "Você não possui esse item.",
    })
    return False


def _largar_item(id_item):
    texto = _ler("Quantidade a largar: ")
    if not texto.isdecimal():
        _mostrar_erro(ERRO_DADOS_INVALIDOS)
        return
    codigo, _ = itens.largar_item(id_item, int(texto))
    if codigo == SUCESSO:
        _exibir("Item largado.")
    else:
        _mostrar_erro(codigo, {
            ERRO_DADOS_INVALIDOS: "Quantidade inválida (de 1 até o que você possui).",
            ERRO_ID_INEXISTENTE: "Você não possui esse item.",
        })


def menu_inventario():
    while True:
        lista = exibir_inventario()
        if lista is None:
            return
        _exibir("\n1) Detalhes   2) Equipar   3) Usar   4) Largar   0) Voltar")
        opcao = _ler("> ")
        if opcao == "0":
            return
        if opcao not in ("1", "2", "3", "4"):
            _mostrar_erro(ERRO_DADOS_INVALIDOS)
            continue
        if not lista:
            _exibir("O inventário está vazio.")
            continue
        id_item = _escolher_item(lista)
        if id_item is None:
            continue
        if opcao == "1":
            _detalhes_item(id_item)
        elif opcao == "2":
            _equipar_item(id_item)
        elif opcao == "3":
            _usar_item(id_item)
        else:
            _largar_item(id_item)


# ---------------------------------------------------------------------------
# Combate
# ---------------------------------------------------------------------------
def _usar_item_em_combate():
    """Deixa o jogador escolher um consumível e o usa. True se o item foi
    usado (o turno é gasto)."""
    lista, _ = _carregar_inventario()
    consumiveis = [t for t in (lista or []) if t[1].get("tipo") == "consumível"]
    if not consumiveis:
        _exibir("Você não tem itens consumíveis.")
        return False
    for n, (_, ficha, quantidade) in enumerate(consumiveis, 1):
        _exibir(f"{n}) {ficha['nome']} x{quantidade}")
    id_item = _escolher_item(consumiveis)
    return id_item is not None and _usar_item(id_item)


def obter_acao(estado):
    """Função passada à Narrativa e repassada ao Combate: mostra o estado do
    combate e lê a ação do jogador no turno ("atacar" ou "usar_item").

    Se o jogador usa um item, ele já é aplicado aqui por itens.usar_item e o
    turno é gasto.
    """
    inimigo = estado.get("inimigo", {})
    _exibir(f"\n-- Turno {estado.get('turno', '?')} --")
    _exibir(f"{inimigo.get('nome', 'Inimigo')}: PV {inimigo.get('pv', '?')}")
    codigo, dados = personagem.consultar_personagem()
    if codigo == SUCESSO:
        _exibir(f"Você: PV {dados['pv']}/{dados['pv_max']}")
    # O formato de "relato" é definido pelo módulo Combate; ajustar se precisar.
    for linha in estado.get("relato", {}).values():
        _exibir(str(linha))

    while True:
        _exibir("1) Atacar   2) Usar item")
        opcao = _ler("> ")
        if opcao == "1":
            return "atacar"
        if opcao == "2":
            if _usar_item_em_combate():
                return "usar_item"
        else:
            _mostrar_erro(ERRO_DADOS_INVALIDOS)


def _jogar_combate(id_cena):
    """Conduz o combate da cena. Devolve False se o jogo não pode continuar."""
    codigo, resultado = narrativa.iniciar_combate(id_cena, obter_acao)
    if codigo != SUCESSO:
        _mostrar_erro(codigo, {ERRO_ABORT: "O combate foi interrompido por um erro."})
        return False
    if resultado["vitoria"]:
        _exibir("\nVocê venceu o combate!")
        exibir_personagem()
    else:
        _exibir("\nVocê foi derrotado...")
    _sessao["id_cena"] = resultado["proxima_cena"]
    return True


# ---------------------------------------------------------------------------
# Menu do jogo
# ---------------------------------------------------------------------------
def _salvar_aventura():
    """Grava a aventura em arquivo.

    A persistência ainda não foi implementada: este é o ponto onde ela será
    ligada (gravar personagem, inventário, cena atual e escolhas feitas).
    """
    _exibir("Salvar ainda não está disponível nesta versão.")


def abrir_menu():
    """Menu do jogo, aberto com [M] durante as cenas (não durante o combate).

    Devolve True se o jogador pediu para encerrar o programa.
    """
    while True:
        _exibir("\n== Menu ==")
        _exibir("1) Voltar ao jogo\n2) Salvar aventura\n0) Encerrar programa")
        opcao = _ler("> ")
        if opcao == "1":
            return False
        if opcao == "2":
            _salvar_aventura()
        elif opcao == "0":
            resposta = _ler("Encerrar o programa? O que não foi salvo será perdido (s/n): ")
            if resposta.lower() == "s":
                return True
        else:
            _mostrar_erro(ERRO_DADOS_INVALIDOS)


# ---------------------------------------------------------------------------
# Cenas e escolhas
# ---------------------------------------------------------------------------
def exibir_escolhas(id_cena, cena):
    """Mostra as escolhas da cena; as que o jogador já escolheu levam [FEITO]."""
    _exibir()
    for id_escolha, escolha in cena["escolhas"].items():
        feita = (id_cena, id_escolha) in _sessao["escolhas_feitas"]
        _exibir(f"{id_escolha}) {escolha['texto']}{' [FEITO]' if feita else ''}")
    _exibir("[P] Personagem   [I] Inventário   [M] Menu")


def _escolher_na_cena(id_cena, cena):
    """Lê comandos até uma escolha válida fazer a história avançar."""
    while True:
        exibir_escolhas(id_cena, cena)
        opcao = _ler("> ")
        if opcao.lower() == "p":
            exibir_personagem()
        elif opcao.lower() == "i":
            menu_inventario()
        elif opcao.lower() == "m":
            if abrir_menu():
                _sessao["encerrar"] = True
                return
        else:
            codigo, proxima = narrativa.processar_escolha(id_cena, opcao)
            if codigo == SUCESSO:
                _sessao["escolhas_feitas"].add((id_cena, opcao))
                _sessao["id_cena"] = proxima
                return
            _mostrar_erro(codigo)


def jogar():
    """Loop da aventura: exibe a cena atual e segue a história até um final."""
    while True:
        id_cena = _sessao["id_cena"]
        codigo, cena = narrativa.iniciar_cena(id_cena)
        if codigo != SUCESSO:
            _mostrar_erro(codigo, {
                ERRO_ABORT: "Não foi possível carregar a cena. Há um personagem criado?",
                ERRO_ID_INEXISTENTE: "Cena não encontrada na história.",
            })
            return

        _exibir("\n" + cena["texto"])
        if cena["final"]:
            _exibir("\n=== Fim da aventura ===")
            return
        if cena["combate"] is not None:
            if not _jogar_combate(id_cena):
                return
        elif not cena["escolhas"]:
            _exibir("Erro na história: esta cena não tem saída.")
            return
        else:
            _escolher_na_cena(id_cena, cena)
            if _sessao["encerrar"]:
                return


def main():
    _exibir("=== RPG Narrativo ===")
    while True:
        _exibir("\n1) Nova aventura\n0) Sair")
        opcao = _ler("> ")
        if opcao == "1":
            if criar_novo_personagem():
                jogar()
                if _sessao["encerrar"]:
                    _exibir("Até a próxima!")
                    return
        elif opcao == "0":
            _exibir("Até a próxima!")
            return
        else:
            _mostrar_erro(ERRO_DADOS_INVALIDOS)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nJogo encerrado.")