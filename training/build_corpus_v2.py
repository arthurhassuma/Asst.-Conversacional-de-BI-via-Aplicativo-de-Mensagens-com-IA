"""Gera o corpus sintético v2 de intenções, no domínio de revenda de autopeças.

Cada classe tem 24 formas de perguntar ("moldes"). Os moldes são sorteados, por classe,
para treino (16), validação (4) e teste (4) e **nunca se repetem entre partições**: a
validação e o teste medem perguntas escritas de um jeito que o modelo não viu, não só
outro mês ou outra métrica no mesmo molde. Dentro de cada molde, métricas e períodos
variam. Tudo é determinístico e sintético; nenhuma mensagem de gestor foi usada.

Uso: python -m training.build_corpus_v2 (grava training/questions-v2.json).
"""

import json
from pathlib import Path
from random import Random

from training.corpus import normalize, validate_corpus

SEED = 42
ROOT = Path(__file__).resolve().parent

# (forma sem artigo, forma com artigo)
METRICS = [
    ("faturamento emitido", "o faturamento emitido"),
    ("faturamento", "o faturamento"),
    ("recebimentos", "os recebimentos"),
    ("valor dos pedidos de venda", "o valor dos pedidos de venda"),
    ("quantidade de pedidos de venda", "a quantidade de pedidos de venda"),
    ("valor contratado", "o valor contratado"),
    ("quantidade de contratos de fornecimento", "a quantidade de contratos de fornecimento"),
    ("clientes novos", "os clientes novos"),
    ("horas de atendimento", "as horas de atendimento"),
    ("ocorrências de pós-venda", "as ocorrências de pós-venda"),
]
MONEY = METRICS[:4] + METRICS[5:6]
RANKABLE = METRICS[:5] + METRICS[5:7]
SEGMENTABLE = METRICS[:7]
MONTHS = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]  # fmt: skip
PERIODS_IN = (
    [f"em {m} de {y}" for y in (2025, 2026) for m in MONTHS if not (y == 2026 and m in MONTHS[10:])]
    + ["no mês passado", "neste ano", "no ano passado", "em 2025", "ontem", "hoje"]
    + ["de 01/09/2026 a 15/09/2026", "de 10/03/2025 a 20/03/2025"]
)
MONTH_YEAR = [f"{m} de {y}" for y in (2025, 2026) for m in MONTHS if not (y == 2026 and m in MONTHS[10:])]
RANGES = [
    "em 2025", "em 2026", "ao longo de 2026", "de janeiro a outubro de 2026",
    "de março a agosto de 2025", "durante 2025", "de janeiro a setembro de 2026",
]  # fmt: skip
GROUPS = [("cliente", "clientes"), ("contrato", "contratos")]
SEGMENTS = [("segmento", "segmentos"), ("cidade", "cidades"), ("tipo de cliente", "tipos de cliente")]

# Cada molde usa: {m} métrica sem artigo, {a} com artigo, {p} período ("em ..."),
# {p1}/{p2} meses para comparar, {r} intervalo mensal, {n} tamanho do ranking,
# {g}/{gs} cliente(s)/contrato(s), {s}/{ss} segmento(s)/cidade(s).
FRAMES = {
    "total": [
        "Qual o total de {m} {p}?",
        "Quanto tivemos de {m} {p}?",
        "Me diga o valor de {m} {p}.",
        "Preciso saber {a} {p}.",
        "Quero o número de {m} {p}.",
        "Pode me passar {a} {p}?",
        "Total de {m} {p}, por favor.",
        "Qual foi o resultado de {m} {p}?",
        "Me informa {a} {p}.",
        "Consulte {a} {p}.",
        "Só preciso do total de {m} {p}.",
        "{m} {p}: qual o valor?",
        "Qual é o montante de {m} {p}?",
        "Fechamos com quanto de {m} {p}?",
        "Me conta quanto foi {a} {p}.",
        "Gostaria de saber {a} {p}.",
        "Quanto registramos de {m} {p}?",
        "Traga {a} {p}.",
        "Preciso do valor de {m} {p} para a reunião.",
        "Qual o número fechado de {m} {p}?",
        "Diga quanto foi {a} {p}.",
        "Pode confirmar {a} {p}?",
        "Estou precisando de {m} {p}, qual o total?",
        "Qual ficou {a} {p}?",
    ],
    "comparacao": [
        "Compare {a} de {p1} com {p2}.",
        "{m}: {p1} versus {p2}.",
        "Como {a} de {p1} se compara a {p2}?",
        "Quero comparar {a} entre {p1} e {p2}.",
        "Houve aumento de {m} em {p1} em relação a {p2}?",
        "Qual a diferença de {m} entre {p1} e {p2}?",
        "Faça um comparativo de {m}: {p1} contra {p2}.",
        "Qual a variação de {m} de {p2} para {p1}?",
        "Me mostre {a} de {p1} e de {p2} lado a lado.",
        "Estamos melhor ou pior em {m} em {p1} frente a {p2}?",
        "Variação percentual de {m}, {p1} contra {p2}.",
        "O que mudou em {m} de {p2} para {p1}?",
        "Compare {m} deste ano com o ano passado.",
        "{m} neste ano versus no ano passado.",
        "{a} de {p1} foi maior ou menor que o de {p2}?",
        "Quanto {m} cresceu ou caiu entre {p2} e {p1}?",
        "Coloque {a} de {p1} ao lado do de {p2}.",
        "Em relação a {p2}, como ficou {a} de {p1}?",
        "Mostre a diferença de {m} entre {p1} e {p2}.",
        "Avalie {a} em {p1} contra {p2}.",
        "Houve queda de {m} em {p1} na comparação com {p2}?",
        "Compare os dois períodos, {p1} e {p2}, em {m}.",
        "{p1} contra {p2}: como foi {m}?",
        "Quero saber se {m} melhorou de {p2} para {p1}.",
    ],
    "tendencia": [
        "Qual a evolução de {m} mês a mês {r}?",
        "Quero ver a série mensal de {m} {r}.",
        "Como {m} se comportou ao longo dos meses {r}?",
        "Mostre {a} por mês {r}.",
        "Distribuição mensal de {m} {r}.",
        "Tendência de {m} {r}.",
        "{m} mês a mês, {r}.",
        "Acompanhe {a} a cada mês {r}.",
        "Me dê o histórico mensal de {m} {r}.",
        "Como foi o ritmo mensal de {m} {r}?",
        "Detalhe {a} por mês {r}.",
        "Evolução de {m} {r}.",
        "Mês a mês, como andou {m} {r}?",
        "Quero a curva mensal de {m} {r}.",
        "Mostre como {m} evoluiu mês a mês {r}.",
        "Preciso do comportamento mensal de {m} {r}.",
        "{a} em cada mês {r}, por favor.",
        "Liste {m} mês por mês {r}.",
        "Quero acompanhar a trajetória de {m} {r}.",
        "Série histórica mensal de {m} {r}.",
        "Como oscilou {m} de mês para mês {r}?",
        "Faça um quadro mensal de {m} {r}.",
        "Qual foi a progressão de {m} a cada mês {r}?",
        "Mostre a linha do tempo mensal de {m} {r}.",
    ],
    "ranking": [
        "Quais os {n} maiores {gs} em {m} {p}?",
        "Top {n} {gs} por {m} {p}.",
        "Ranking de {gs} por {m} {p}.",
        "Liste os {n} principais {gs} em {m} {p}.",
        "Quais {gs} lideram em {m} {p}?",
        "Classifique os {gs} por {m} {p}, do maior para o menor.",
        "Me dê o top {n} de {m} {p}.",
        "Os {n} {gs} que mais geraram {m} {p}.",
        "Quem são os {n} melhores {gs} em {m} {p}?",
        "{n} maiores {gs} por {m}, {p}.",
        "Qual a posição dos {gs} em {m} {p}?",
        "Ordene os {gs} por {m} {p} e mostre os {n} primeiros.",
        "Qual o ranking de {m} {p}?",
        "Quem mais contribuiu com {m} {p}? Quero os {n} primeiros.",
        "Quem são os {n} {gs} que mais renderam em {m} {p}?",
        "Mostre os {n} primeiros {gs} em {m} {p}.",
        "Lista dos {n} {gs} com maior {m} {p}.",
        "Quem está no topo em {m} {p}? Mostre {n}.",
        "Coloque os {gs} em ordem de {m} {p}, só os {n} primeiros.",
        "Quais são os campeões de {m} entre os {gs} {p}?",
        "Destaque os {n} {gs} de maior {m} {p}.",
        "Preciso do pódio de {gs} em {m} {p}.",
        "Os {n} {gs} no alto do ranking de {m} {p}.",
        "Quais {n} {gs} mais se destacaram em {m} {p}?",
    ],
    "segmentacao": [
        "Como se distribui {a} por {s} {p}?",
        "Qual a participação de cada {s} em {m} {p}?",
        "{m} por {s} {p}.",
        "Quanto cada {s} representa de {m} {p}?",
        "Divida {a} por {s} {p}.",
        "Distribuição de {m} por {s}, {p}.",
        "Qual {s} pesa mais em {m} {p}?",
        "Percentual de {m} por {s} {p}.",
        "Mostre {a} aberto por {s} {p}.",
        "Fatie {a} por {s} {p}.",
        "Como {m} se reparte entre {ss} {p}?",
        "De onde vem {a} {p}: por {s}?",
        "Participação de {ss} no total de {m} {p}.",
        "Qual {s} concentra mais {m} {p}?",
        "Quanto vem de cada {s} em {m} {p}?",
        "Abra {a} por {s} {p}.",
        "Qual a fatia de cada {s} em {m} {p}?",
        "Mostre a proporção de {m} por {s} {p}.",
        "{m} dividido por {s} {p}.",
        "Como {m} se espalha pelos {ss} {p}?",
        "Qual o peso de cada {s} em {m} {p}?",
        "Quero ver {a} separado por {s} {p}.",
        "Quanto do total de {m} {p} vem de cada {s}?",
        "Agrupe {a} por {s} {p}.",
    ],
    "operacional": [
        "Compare as horas previstas com as realizadas {p}.",
        "Qual o desvio de horas de atendimento {p}?",
        "Quantas horas passamos do previsto {p}?",
        "Taxa de resolução das ocorrências de pós-venda {p}.",
        "Ocorrências abertas e resolvidas, com saldo e taxa, {p}.",
        "Quantas ocorrências ficaram sem resolver {p}?",
        "Faturamento emitido versus recebimentos {p}.",
        "Quanto emitimos e quanto recebemos {p}?",
        "Horas previstas contra realizadas por contrato {p}.",
        "Qual a diferença entre o emitido e o recebido {p}?",
        "O atendimento estourou o previsto {p}?",
        "Qual o saldo de ocorrências em aberto {p}?",
        "Como está a resolução de garantias e devoluções {p}?",
        "Previsto versus realizado em horas de atendimento {p}.",
        "As horas de atendimento ficaram acima do previsto {p}?",
        "Quantas garantias e devoluções foram resolvidas {p}?",
        "Qual a taxa de resolução do pós-venda {p}?",
        "Quanto do faturamento emitido já foi recebido {p}?",
        "Mostre horas previstas e horas realizadas {p}.",
        "Qual o desvio entre o previsto e o realizado de atendimento {p}?",
        "Tem ocorrência de pós-venda aberta {p}? Quantas e qual o saldo?",
        "Emitido menos recebido {p}: qual a diferença?",
        "Como ficou a resolução das ocorrências {p}?",
        "Estourou o orçamento de horas de atendimento {p}?",
    ],
    "generica": [
        "Como foram as vendas {p}?",
        "Me fala como está o negócio {p}.",
        "Qual a situação da empresa {p}?",
        "Está tudo bem com a empresa {p}?",
        "Qual o lucro {p}?",
        "Qual a margem {p}?",
        "O faturamento vai subir depois de {p1}?",
        "Faça uma previsão de vendas a partir de {p1}.",
        "Por que as vendas mudaram {p}?",
        "Resuma o desempenho {p}.",
        "Me dá um panorama geral {p}.",
        "Quais clientes vão cancelar depois de {p1}?",
        "Bom dia, preciso de ajuda com os números {p}.",
        "O que devo fazer para vender mais {p}?",
        "Me ajuda a entender os números {p}.",
        "O que acha do desempenho {p}?",
        "Como estamos {p}?",
        "Qual o futuro da empresa depois de {p1}?",
        "Vale a pena investir mais em estoque depois de {p1}?",
        "Preciso de um resumo executivo {p}.",
        "O que aconteceu na empresa {p}?",
        "Quanto vamos lucrar a partir de {p1}?",
        "Quais são os problemas da empresa {p}?",
        "Me dá uma opinião sobre as vendas {p}.",
    ],
}
# Moldes de cada classe por partição: 16 treino, 4 validação, 4 teste.
SPLIT_SIZES = (("train", 16, 10), ("validation", 4, 8), ("test", 4, 8))  # (partição, moldes, perguntas)


def fill(label: str, frame: str, rng: Random) -> str:
    pool = {"ranking": RANKABLE, "segmentacao": SEGMENTABLE, "comparacao": MONEY + METRICS[7:8]}
    metric = rng.choice(pool.get(label, METRICS))
    first, second = rng.sample(MONTH_YEAR, 2)
    group = rng.choice(GROUPS)
    segment = rng.choice(SEGMENTS)
    text = frame.format(
        m=metric[0],
        a=metric[1],
        p=rng.choice(PERIODS_IN),
        p1=first,
        p2=second,
        r=rng.choice(RANGES),
        n=rng.choice((3, 5, 10)),
        g=group[0],
        gs=group[1],
        s=segment[0],
        ss=segment[1],
    )
    return text[0].upper() + text[1:]


def build() -> list[dict]:
    rng = Random(SEED)
    records, seen = [], set()
    for label, frames in FRAMES.items():
        order = list(range(len(frames)))
        rng.shuffle(order)
        cursor = 0
        for split, n_frames, n_questions in SPLIT_SIZES:
            for index in order[cursor : cursor + n_frames]:
                group_id = f"{label}-m{index + 1:02d}"
                made = 0
                for _ in range(400):
                    question = fill(label, frames[index], rng)
                    key = normalize(question)
                    if key in seen:
                        continue
                    seen.add(key)
                    made += 1
                    records.append(
                        {
                            "id": f"{group_id}-{made}",
                            "question": question,
                            "label": label,
                            "group_id": group_id,
                            "split": split,
                        }
                    )
                    if made == n_questions:
                        break
            cursor += n_frames
    return records


if __name__ == "__main__":
    rows = build()
    print(json.dumps(validate_corpus(rows), ensure_ascii=False))
    (ROOT / "questions-v2.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
