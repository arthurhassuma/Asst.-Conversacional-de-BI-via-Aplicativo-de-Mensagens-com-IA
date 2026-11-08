"""Corpus, modelo congelado e uso do classificador de intenções v2 (revenda de autopeças)."""

import hashlib
import json
import logging
from pathlib import Path

import pytest

from app.bi_agent import BIAgent
from app.config import Settings
from app.intent_classifier import load_classifier
from tests.test_agent import PLAN, Client, Database, plan_response
from training.corpus import load_corpus, validate_corpus
from training.fit import evaluate_model

CORPUS = Path("training/questions-v2.json")
MODEL = Path("training/intent-model-v2.json")
PROTOCOL = Path("training/protocol-v2.json")
# Sem período o agente pede esclarecimento depois do planejador, sem consultar o banco.
NO_PERIOD = {**PLAN, "period": None}


def test_corpus_v2_is_balanced_domain_specific_and_phrasings_never_cross_partitions():
    rows = load_corpus(CORPUS)
    report = validate_corpus(rows)
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert report["splits"] == protocol["splits"]
    assert len(report["classes"]) == 7 and min(report["classes"].values()) >= 200
    text = " ".join(r["question"] for r in rows).lower()
    for word in ("sprint", "software", "sustentação de aplic", "desenvolvimento de sistema"):
        assert word not in text
    assert "pedidos de venda" in text and "pós-venda" in text
    # Cada molde (group_id) pertence a uma única partição, e os de validação e teste são
    # moldes que o treino nunca viu.
    partitions = {}
    for row in rows:
        partitions.setdefault(row["group_id"], set()).add(row["split"])
    assert all(len(splits) == 1 for splits in partitions.values())


def test_frozen_model_belongs_to_the_committed_corpus():
    artifact = json.loads(MODEL.read_text(encoding="utf-8"))
    records = json.loads(CORPUS.read_text(encoding="utf-8"))
    digest = hashlib.sha256(
        json.dumps(records, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    assert artifact["corpus_sha256"] == digest
    assert artifact["threshold"] == 0.5 and artifact["C"] == 100.0


def test_frozen_model_still_meets_the_usage_criterion_declared_before_the_test():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))["usage_criterion"]
    artifact = json.loads(MODEL.read_text(encoding="utf-8"))
    result = evaluate_model(artifact, load_corpus(CORPUS), "test")["with_abstention"]
    assert result["accepted_precision"] >= protocol["accepted_precision_min"]
    assert result["coverage"] >= protocol["coverage_min"]


def test_packaged_default_loads_without_sklearn_and_classifies_clear_questions():
    model = load_classifier(MODEL)
    ranking = model.predict("Top 3 clientes por faturamento em janeiro de 2025")
    assert ranking["label"] == "ranking" and ranking["accepted"]
    vague = model.predict("Como foram as vendas em janeiro de 2025?")
    assert vague["label"] == "generica" and not vague["accepted"]


async def test_enabled_classifier_feeds_examples_to_the_planner_and_logs_without_the_question(
    caplog,
):
    question = "Top 3 clientes por faturamento em janeiro de 2025"
    client, trace = Client([plan_response(NO_PERIOD)]), {}
    agent = BIAgent(Settings(_env_file=None, intent_classifier_enabled=True), client, Database())
    with caplog.at_level(logging.INFO, logger="app.bi_agent"):
        await agent.answer(question, [], trace=trace)
    assert trace["intent"]["available"] and trace["intent"]["label"] == "ranking"
    assert trace["intent"]["accepted"] and len(trace["intent"]["examples"]) == 2
    instruction = client.calls[0]["config"].system_instruction
    assert "Exemplos de intenção" in instruction and "ranking" in instruction
    logged = " ".join(record.getMessage() for record in caplog.records)
    assert "intencao rotulo=ranking" in logged and "aceita=True" in logged
    assert "faturamento" not in logged and "2025" not in logged


async def test_enabled_classifier_abstains_on_a_vague_question_and_adds_no_examples():
    client, trace = Client([plan_response(NO_PERIOD)]), {}
    agent = BIAgent(Settings(_env_file=None, intent_classifier_enabled=True), client, Database())
    await agent.answer("Como foram as vendas em janeiro de 2025?", [], trace=trace)
    assert trace["intent"]["accepted"] is False and trace["intent"]["examples"] == []
    assert "Exemplos de intenção" not in client.calls[0]["config"].system_instruction


@pytest.mark.parametrize("enabled", [True, False])
async def test_the_flag_controls_whether_the_classifier_runs(enabled):
    trace = {}
    agent = BIAgent(
        Settings(_env_file=None, intent_classifier_enabled=enabled),
        Client([plan_response(NO_PERIOD)]),
        Database(),
    )
    await agent.answer("Faturamento em janeiro de 2025", [], trace=trace)
    assert trace["intent"]["enabled"] is enabled
    assert trace["intent"]["available"] is enabled
