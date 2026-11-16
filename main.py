
import flet as ft
import asyncio
import random
import json
import time

NOME_AUTORA = "Ana Carolina de Carvalho Xavier"
RA_AUTORA = "RA: 6023622"
MAX_NOME = 25
PONTOS_POR_ACERTO = 50
SEGUNDOS_POR_PERGUNTA = 10

PERGUNTAS = [
    ("12 + 8", 20, [18, 20, 22, 21]),
    ("15 − 7", 8, [6, 7, 8, 9]),
    ("6 × 4", 24, [20, 24, 28, 18]),
    ("9 + 14", 23, [13, 23, 24, 32]),
    ("25 + 17", 42, [32, 42, 43, 52]),
    ("30 − 12", 18, [28, 18, 17, 22]),
    ("8 × 5", 40, [35, 40, 45, 48]),
    ("20 − 9", 11, [10, 11, 12, 29]),
    ("7 × 6", 42, [36, 42, 48, 49]),
    ("9 × 7", 63, [56, 63, 54, 72]),
]

BRANCO = "#FFFFFF"
ROSA_BEBE = "#F8C8DC"
ROSA_CLARO = "#FDE9F0"
ROSA_FORTE = "#E87AA0"
ROSA_ESCURO = "#8E3358"
AMEIXA = "#5A3E4B"
VERDE = "#A8E6CF"
CORAL = "#FF9AA2"


def main(page: ft.Page):
    page.title = "Quiz Matemático"
    page.bgcolor = BRANCO
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    nome_jogador = ""
    nivel = 0
    pontos = 0
    inicio_partida = 0
    tempo_restante = SEGUNDOS_POR_PERGUNTA
    alternativas_atuais = []
    partida_encerrada = False
    timer_task = None
    bloqueado = False

    conteudo = ft.Column(
        spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    def atualizar():
        page.update()

    def carregar_historico():
        try:
            dados = page.client_storage.get("quiz_historico")
            return json.loads(dados) if dados else []
        except Exception:
            return []

    def salvar_historico(nome, pontuacao, duracao, resultado):
        historico = carregar_historico()
        historico.append({
            "nome": nome,
            "pontos": pontuacao,
            "tempo": round(duracao, 1),
            "resultado": resultado,
        })
        page.client_storage.set(
            "quiz_historico",
            json.dumps(historico, ensure_ascii=False)
        )

    def melhores_jogadores():
        historico = carregar_historico()
        melhores = {}

        for partida in historico:
            nome = partida["nome"]
            chave = nome.casefold()
            atual = melhores.get(chave)
            candidato = (
                partida["nome"],
                partida["pontos"],
                partida["tempo"]
            )

            if atual is None or (
                candidato[1] > atual[1]
                or (
                    candidato[1] == atual[1]
                    and candidato[2] < atual[2]
                )
            ):
                melhores[chave] = candidato

        return sorted(
            melhores.values(),
            key=lambda item: (-item[1], item[2])
        )

    def mostrar_tela(elementos):
        conteudo.controls.clear()
        conteudo.controls.extend(elementos)
        page.controls.clear()
        page.add(
            ft.Container(
                content=conteudo,
                width=500,
                padding=20,
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        )
        atualizar()

    def titulo(texto, tamanho=28):
        return ft.Text(
            texto,
            size=tamanho,
            weight=ft.FontWeight.BOLD,
            color=AMEIXA,
            text_align=ft.TextAlign.CENTER
        )

    def botao(texto, funcao, cor=ROSA_FORTE, largura=230):
        return ft.Button(
            content=texto,
            width=largura,
            height=52,
            on_click=funcao,
            style=ft.ButtonStyle(
                bgcolor=cor,
                color=BRANCO,
                shape=ft.RoundedRectangleBorder(radius=30),
                text_style=ft.TextStyle(
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
            ),
        )

    def cartao(conteudo_cartao, cor=ROSA_BEBE):
        return ft.Container(
            content=conteudo_cartao,
            bgcolor=cor,
            padding=22,
            border_radius=24,
            width=330,
            alignment=ft.Alignment.CENTER
        )

    def mostrar_inicio(e=None):
        nonlocal nivel, pontos, bloqueado, timer_task

        if timer_task:
            timer_task.cancel()
            timer_task = None

        nivel = 0
        pontos = 0
        bloqueado = False

        campo_nome = ft.TextField(
            label="Digite seu nome",
            hint_text="Seu nome",
            max_length=MAX_NOME,
            width=280,
            text_align=ft.TextAlign.CENTER,
            border_color=ROSA_FORTE,
            focused_border_color=ROSA_ESCURO,
            color=AMEIXA,
            on_submit=iniciar_partida,
        )

        mostrar_tela([
            ft.Container(height=25),
            cartao(
                ft.Column(
                    [
                        titulo("QUIZ MATEMÁTICO", 25),
                        ft.Text(
                            NOME_AUTORA,
                            color=AMEIXA,
                            size=16,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            RA_AUTORA,
                            color=ROSA_ESCURO,
                            size=14
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12
                )
            ),
            ft.Container(height=15),
            titulo("Vamos jogar?", 23),
            ft.Text(
                "Responda às 10 perguntas e conquiste 500 pontos!",
                color=AMEIXA,
                text_align=ft.TextAlign.CENTER
            ),
            campo_nome,
            botao(
                "JOGAR",
                lambda e: iniciar_partida(e, campo_nome)
            ),
            botao(
                "VER RANKING",
                mostrar_ranking,
                cor=ROSA_ESCURO
            ),
            ft.Container(height=15),
            ft.Text(
                "Cada acerto vale 50 pontos • 10 segundos por pergunta",
                size=12,
                color=ROSA_ESCURO,
                text_align=ft.TextAlign.CENTER
            ),
        ])

    def iniciar_partida(e=None, campo=None):
        nonlocal nome_jogador, nivel, pontos, inicio_partida

        if campo is None:
            campo = e.control if isinstance(e.control, ft.TextField) else None

        if campo is None:
            return

        nome = " ".join(campo.value.strip().split())

        if not nome:
            campo.error_text = "Digite seu nome para jogar"
            atualizar()
            return

        nome_jogador = nome[:MAX_NOME]
        nivel = 0
        pontos = 0
        inicio_partida = time.time()

        mostrar_pergunta()

    async def iniciar_timer():
        nonlocal tempo_restante, bloqueado

        while tempo_restante > 0 and not bloqueado:
            await asyncio.sleep(0.1)

            if bloqueado:
                return

            tempo_restante = max(0, tempo_restante - 0.1)

            if barra_tempo.page is not None:
                barra_tempo.value = (
                    tempo_restante / SEGUNDOS_POR_PERGUNTA
                )
                texto_tempo.value = f"{tempo_restante:.1f} s"
                atualizar()

        if not bloqueado:
            tempo_esgotado()

    barra_tempo = ft.ProgressBar(
        value=1,
        color=ROSA_FORTE,
        bgcolor=ROSA_CLARO,
        width=290
    )

    texto_tempo = ft.Text(
        "10.0 s",
        color=ROSA_ESCURO,
        size=15,
        weight=ft.FontWeight.BOLD
    )

    def mostrar_pergunta():
        nonlocal alternativas_atuais, tempo_restante
        nonlocal bloqueado, timer_task

        if timer_task:
            timer_task.cancel()

        bloqueado = False
        tempo_restante = SEGUNDOS_POR_PERGUNTA

        conta, certa, alternativas = PERGUNTAS[nivel]
        alternativas_atuais = alternativas[:]
        random.shuffle(alternativas_atuais)

        barra_tempo.value = 1
        texto_tempo.value = "10.0 s"

        botoes = []

        for valor in alternativas_atuais:
            botoes.append(
                ft.Container(
                    content=ft.Text(
                        str(valor),
                        size=25,
                        weight=ft.FontWeight.BOLD,
                        color=AMEIXA
                    ),
                    bgcolor=BRANCO,
                    border=ft.Border.all(3, ROSA_BEBE),
                    border_radius=20,
                    width=130,
                    height=75,
                    alignment=ft.Alignment.CENTER,
                    on_click=lambda e, resposta=valor: responder(resposta),
                )
            )

        grade = ft.GridView(
            runs_count=2,
            max_extent=150,
            child_aspect_ratio=1.7,
            spacing=12,
            run_spacing=12,
            height=175,
            controls=botoes,
        )

        mostrar_tela([
            ft.Row(
                [
                    ft.Text(
                        f"Pergunta {nivel + 1}/10",
                        color=AMEIXA,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        f"{pontos} pts",
                        color=ROSA_ESCURO,
                        weight=ft.FontWeight.BOLD
                    ),
                ],
                width=320
            ),
            ft.ProgressBar(
                value=nivel / len(PERGUNTAS),
                color=ROSA_FORTE,
                bgcolor=ROSA_CLARO,
                width=320
            ),
            cartao(
                ft.Column(
                    [
                        ft.Text(
                            "Quanto é?",
                            color=ROSA_ESCURO,
                            size=15
                        ),
                        titulo(f"{conta} = ?", 38),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            ),
            barra_tempo,
            texto_tempo,
            grade,
        ])

        timer_task = asyncio.create_task(iniciar_timer())

    def responder(resposta):
        nonlocal pontos, bloqueado, timer_task

        if bloqueado:
            return

        bloqueado = True

        if timer_task:
            timer_task.cancel()
            timer_task = None

        certa = PERGUNTAS[nivel][1]

        if resposta == certa:
            pontos += PONTOS_POR_ACERTO
            mostrar_mensagem(
                f"Acertou! +{PONTOS_POR_ACERTO} pontos",
                VERDE
            )
            page.run_task(avancar_nivel)
        else:
            mostrar_mensagem(
                f"Resposta incorreta! A resposta certa era {certa}.",
                CORAL
            )
            page.run_task(encerrar_partida, "Errou")

    def tempo_esgotado():
        nonlocal bloqueado

        if bloqueado:
            return

        bloqueado = True
        certa = PERGUNTAS[nivel][1]

        mostrar_mensagem(
            f"Tempo esgotado! A resposta era {certa}.",
            CORAL
        )

        page.run_task(encerrar_partida, "Tempo esgotado")

    def mostrar_mensagem(mensagem, cor):
        mostrar_tela([
            ft.Container(height=100),
            cartao(
                ft.Column(
                    [titulo(mensagem, 23)],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                cor
            ),
            ft.Text(
                f"Pontuação: {pontos}",
                size=18,
                color=AMEIXA,
                weight=ft.FontWeight.BOLD
            ),
        ])

    async def avancar_nivel():
        nonlocal nivel

        await asyncio.sleep(0.9)
        nivel += 1

        if nivel >= len(PERGUNTAS):
            finalizar_partida()
        else:
            mostrar_pergunta()

    async def encerrar_partida(motivo):
        duracao = time.time() - inicio_partida

        salvar_historico(
            nome_jogador,
            pontos,
            duracao,
            f"{motivo} na pergunta {nivel + 1}"
        )

        await asyncio.sleep(1.5)
        mostrar_inicio()

    def finalizar_partida():
        duracao = time.time() - inicio_partida

        salvar_historico(
            nome_jogador,
            pontos,
            duracao,
            "Concluiu as 10 perguntas"
        )

        mostrar_tela([
            ft.Container(height=35),
            cartao(
                ft.Column(
                    [
                        titulo("Parabéns!", 30),
                        titulo(f"{pontos} pontos", 25),
                        ft.Text(
                            f"Jogador: {nome_jogador}",
                            color=AMEIXA,
                            size=15,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            f"Tempo total: {duracao:.1f} s",
                            color=AMEIXA,
                            size=15
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15
                )
            ),
            titulo("Você completou o quiz!", 20),
            botao("JOGAR DE NOVO", mostrar_inicio),
            botao(
                "VER RANKING",
                mostrar_ranking,
                cor=ROSA_ESCURO
            ),
        ])

    def mostrar_ranking(e=None):
        ranking = melhores_jogadores()

        linhas = [
            titulo("RANKING", 28),
            ft.Text(
                "Melhor resultado de cada jogador",
                color=ROSA_ESCURO,
                size=13
            ),
        ]

        if not ranking:
            linhas.append(
                cartao(
                    ft.Text(
                        "Ainda não há partidas salvas.",
                        color=AMEIXA,
                        text_align=ft.TextAlign.CENTER
                    )
                )
            )

        for posicao, (nome, pontuacao, tempo) in enumerate(
            ranking[:8], 1
        ):
            linhas.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                f"{posicao}º",
                                color=ROSA_ESCURO,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                nome,
                                color=AMEIXA,
                                expand=True
                            ),
                            ft.Text(
                                f"{pontuacao} pts",
                                color=AMEIXA,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                f"{tempo:.1f} s",
                                color=ROSA_ESCURO,
                                size=12
                            ),
                        ]
                    ),
                    bgcolor=ROSA_BEBE,
                    padding=12,
                    border_radius=14,
                    width=330,
                )
            )

        linhas.append(botao("VOLTAR", mostrar_inicio))
        mostrar_tela(linhas)

    mostrar_inicio()


ft.run(main)
