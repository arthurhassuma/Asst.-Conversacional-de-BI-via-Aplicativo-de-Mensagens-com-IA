"""Planejamento sem SQL, loop de tools e saída final com proveniência das células."""

import asyncio
import copy
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import Settings
from app.database_tools import DatabaseTools
from app.prompts import PLANNER_PROMPT, PLANNER_SCHEMA, SYSTEM_PROMPT, TOOLS
from app.query_templates import total_query
from app.rendering import METRICS, InvalidAnswer, render_answer

FAILURE = "Não consegui concluir a consulta com segurança. Reformule a pergunta ou tente novamente."
PERIOD_QUESTION = "Qual período deseja consultar? Informe as datas ou o mês e o ano."
METRIC_QUESTION = (
    "Qual métrica deseja consultar: faturamento emitido, recebimentos, "
    "pedidos, contratos, clientes, horas ou chamados?"
)


def response_content(response):
    if not response.candidates:
        raise ValueError("O Gemini não retornou conteúdo utilizável.")
    candidate = response.candidates[0]
    if candidate.finish_reason != types.FinishReason.STOP or not candidate.content:
        raise ValueError("Resposta incompleta do modelo.")
    return candidate.content


def parse_json(response):
    content = response_content(response)
    text = "".join(part.text for part in content.parts or [] if part.text and not part.thought)
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Formato de resposta inválido.")
    return payload


def gemini_contents(messages):
    """Preserva partes e thought_signature originais nos turnos de function calling."""
    contents = []
    for message in messages:
        value = message["content"]
        if isinstance(value, str):
            contents.append(
                types.Content(
                    role="model" if message["role"] == "assistant" else "user",
                    parts=[types.Part(text=value)],
                )
            )
        else:
            contents.append(types.Content.model_validate(copy.deepcopy(value)))
    return contents


def api_error_message(code):
    if code == 429:
        return (
            "A cota ou o limite de requisições do Gemini foi atingido. Aguarde e tente novamente."
        )
    if code in (401, 403):
        return "Não foi possível autenticar no Gemini. Verifique a chave e as permissões no Google AI Studio."
    if code == 404:
        return "O modelo Gemini configurado não está disponível para esta chave. Verifique GEMINI_MODEL."
    if code == 400:
        return "O Gemini recusou a solicitação. Verifique a chave, o modelo e a configuração da integração."
    return "O serviço Gemini está temporariamente indisponível. Tente novamente mais tarde."


def provider_error_category(error):
    """Classificação indicativa: retorna apenas rótulos fixos, nunca texto do provedor."""
    message = getattr(error, "message", "")
    text = message.casefold() if isinstance(message, str) else ""
    if any(marker in text for marker in ("thought_signature", "thought signature")):
        return "thought_signature_validation"
    if any(
        marker in text for marker in ("function_response", "function response", "functionresponse")
    ):
        return "function_response_validation"
    return "unclassified"


def clarify(plan: dict, messages: list) -> str | None:
    queries = plan.get("queries")
    if not isinstance(queries, list) or not queries:
        return METRIC_QUESTION
    if len(queries) > 4:
        return "Consulte até quatro métricas ou medidas por pergunta. Quais deseja priorizar?"
    for query in queries:
        if not isinstance(query, dict):
            return METRIC_QUESTION
        question = clarify_query(query, messages)
        if question:
            return question
    return None


def clarify_query(plan: dict, messages: list) -> str | None:
    if plan.get("operation") not in {"total", "analysis"}:
        raise ValueError("Operação de consulta inválida.")
    if plan.get("metric") not in METRICS:
        return METRIC_QUESTION
    compatible = {
        "faturamento": {"valor"},
        "recebimentos": {"valor"},
        "pedidos": {"valor", "quantidade"},
        "contratos": {"valor", "quantidade"},
        "clientes": {"quantidade"},
        "horas": {"horas_previstas", "horas_realizadas"},
        "chamados": {"chamados_abertos", "chamados_resolvidos", "taxa_resolucao"},
    }
    if plan.get("measure") not in compatible[plan["metric"]]:
        questions = {
            "pedidos": "você deseja o valor ou a quantidade? Pode pedir ambos.",
            "contratos": "você deseja o valor ou a quantidade? Pode pedir ambos.",
            "horas": "deseja horas previstas, realizadas ou ambas?",
            "chamados": "deseja chamados abertos, resolvidos ou a taxa de resolução?",
            "clientes": "deseja a quantidade de clientes?",
            "faturamento": "deseja o valor total emitido?",
            "recebimentos": "deseja o valor total recebido?",
        }
        return f"Para {METRICS[plan['metric']]}, {questions[plan['metric']]}"
    period = plan.get("period")
    if not isinstance(period, dict):
        return PERIOD_QUESTION
    try:
        if date.fromisoformat(period["start"]) >= date.fromisoformat(period["end"]):
            return PERIOD_QUESTION
        evidence = period["evidence"]
        # Só aceita evidência literal de mensagem do gestor, não de tool ou modelo.
        if (
            not isinstance(evidence, str)
            or not evidence.strip()
            or not any(
                m["role"] == "user"
                and isinstance(m["content"], str)
                and evidence.casefold() in m["content"].casefold()
                for m in messages
            )
        ):
            return PERIOD_QUESTION
    except (KeyError, ValueError, TypeError):
        return PERIOD_QUESTION
    return None


class BIAgent:
    def __init__(self, settings: Settings, client=None, database=None):
        self.settings = settings
        self.client = client
        self.database = database or DatabaseTools(settings)

    async def close(self):
        if self.client:
            if hasattr(self.client.aio, "aclose"):
                await self.client.aio.aclose()
            if hasattr(self.client, "close"):
                self.client.close()

    async def answer(
        self, question: str, history: list, *, trace: dict | None = None
    ) -> tuple[str, list]:
        # Evidência opcional pertence à chamada, nunca ao estado compartilhado do bot.
        trace = trace if trace is not None else {}
        trace.clear()
        trace.update(status="error", queries=[], requests=[])
        if not question.strip() or len(question) > 4000:
            text = "Envie uma pergunta de negócio mais curta e não vazia."
            return text, []
        turn = [{"role": "user", "content": question}]
        if self.client is None:
            key = self.settings.gemini_api_key.get_secret_value()
            if not key:
                text = "O serviço de IA ainda não foi configurado. Avise o responsável pelo assistente."
                return text, turn + [{"role": "assistant", "content": text}]
            self.client = genai.Client(
                api_key=key,
                vertexai=False,
                http_options=types.HttpOptions(
                    api_version="v1beta",
                    timeout=30000,
                    retry_options=types.HttpRetryOptions(attempts=1),
                ),
            )
        try:
            async with asyncio.timeout(100):
                return await self._answer(question, history, turn, trace)
        except APIError as exc:
            trace.update(status="provider_error", provider_code=exc.code)
            text = api_error_message(exc.code)
            return text, turn + [{"role": "assistant", "content": text}]
        except (httpx.HTTPError, TimeoutError):
            trace.update(status="transport_error")
            return FAILURE, turn + [{"role": "assistant", "content": FAILURE}]
        except (ValueError, TypeError, KeyError):
            # Nenhuma exceção externa, credencial ou SQL chega ao Telegram.
            return FAILURE, turn + [{"role": "assistant", "content": FAILURE}]

    async def _generate(self, trace, **kwargs):
        record = {"model": self.settings.gemini_model}
        trace["requests"].append(record)
        try:
            response = await self.client.aio.models.generate_content(**kwargs)
        except APIError as exc:
            category = provider_error_category(exc)
            record.update(provider_code=exc.code, provider_category=category)
            trace["provider_category"] = category
            raise
        record["resolved_model"] = response.model_version
        if response.usage_metadata:
            record["usage"] = response.usage_metadata.model_dump(exclude_none=True)
        return response

    async def _answer(self, question, history, turn, trace):
        messages = copy.deepcopy(history + turn)
        # O planejador não declara tools: não envie blocos tool_use/tool_result
        # históricos à API sem as respectivas definições. Mantém pedido e resposta.
        planning_messages = [m for m in messages if isinstance(m["content"], str)]
        today = datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()
        response = await self._generate(
            trace,
            model=self.settings.gemini_model,
            contents=gemini_contents(planning_messages),
            config=types.GenerateContentConfig(
                system_instruction=PLANNER_PROMPT + "\nData atual: " + today,
                max_output_tokens=4096,
                response_mime_type="application/json",
                response_json_schema=PLANNER_SCHEMA,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        plan = parse_json(response)
        trace["plan"] = copy.deepcopy(plan)
        clarification = clarify(plan, messages)
        if clarification:
            trace["status"] = (
                "clarification_period"
                if clarification == PERIOD_QUESTION
                else "clarification_metric"
                if clarification == METRIC_QUESTION
                else "clarification_measure"
                if clarification.startswith("Para ")
                else "clarification_limit"
            )
            return clarification, turn + [{"role": "assistant", "content": clarification}]
        answers = []
        for query in plan["queries"]:
            # Cada métrica tem resultados próprios: q1 de pedidos não pode ser
            # reutilizado como faturamento. Mantém só o contexto textual entre consultas.
            evidence = {"plan": copy.deepcopy(query), "attempts": []}
            trace["queries"].append(evidence)
            answers.append(
                await self._query(query, copy.deepcopy(planning_messages), trace, evidence)
            )
        text = "\n\n".join(answers)
        trace["status"] = "answer"
        # Guarda só o pedido real e a resposta visível. Tools/assinaturas permanecem
        # no loop que as originou, sem contaminar esclarecimentos ou outras métricas.
        return text, turn + [{"role": "assistant", "content": text}]

    async def _query(self, plan, messages, trace, evidence):
        if plan["operation"] == "total":
            schema = await asyncio.to_thread(self.database.get_schema)
            if "error" in schema:
                raise ValueError("Não foi possível consultar o schema.")
            sql = total_query(plan)
            result = await asyncio.to_thread(self.database.execute_sql, sql)
            evidence["attempts"].append({"sql": sql, "result": copy.deepcopy(result)})
            if "error" in result:
                raise ValueError("Não foi possível executar o total planejado.")
            text = render_answer(
                {"kind": "answer", "result_id": "q1"},
                {"q1": result},
                plan["metric"],
                plan["period"],
                plan["measure"],
            )
            evidence.update(selected=copy.deepcopy(result), selected_id="q1", template=True)
            return text
        system = SYSTEM_PROMPT + "\nPlano confirmado: " + json.dumps(plan, ensure_ascii=False)
        results, sql_errors, schema_seen = {}, 0, False
        for _ in range(self.settings.max_tool_rounds):
            response = await self._generate(
                trace,
                model=self.settings.gemini_model,
                contents=gemini_contents(messages),
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=8192,
                    tools=[types.Tool(function_declarations=TOOLS)],
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            )
            content = response_content(response)
            assistant = {"role": "assistant", "content": content.model_dump(exclude_none=True)}
            calls = [part.function_call for part in content.parts or [] if part.function_call]
            if calls:
                if len(calls) > 4:
                    break
                messages.append(assistant)
                tool_results = []
                for call in calls:
                    name, inputs = call.name, call.args or {}
                    if name == "get_schema" and inputs == {}:
                        result = await asyncio.to_thread(self.database.get_schema)
                        schema_seen = "error" not in result
                    elif (
                        name == "execute_sql"
                        and isinstance(inputs, dict)
                        and set(inputs) == {"sql"}
                        and isinstance(inputs["sql"], str)
                    ):
                        if not schema_seen:
                            result = {"error": "Consulte get_schema antes de executar SQL."}
                        elif sql_errors >= self.settings.max_sql_errors:
                            result = {"error": "O limite de correções foi atingido."}
                        else:
                            result = await asyncio.to_thread(
                                self.database.execute_sql, inputs["sql"]
                            )
                            evidence["attempts"].append(
                                {"sql": inputs["sql"], "result": copy.deepcopy(result)}
                            )
                            if "error" in result:
                                sql_errors += 1
                            else:
                                result_id = f"q{len(results) + 1}"
                                results[result_id] = result
                                result = {**result, "result_id": result_id}
                    else:
                        result = {"error": "Tool ou argumentos não permitidos."}
                    tool_results.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                id=call.id,
                                name=name,
                                response=result,
                            )
                        )
                    )
                messages.append(
                    {
                        "role": "user",
                        "content": types.Content(
                            role="user",
                            parts=tool_results,
                        ).model_dump(exclude_none=True),
                    }
                )
                if sql_errors >= self.settings.max_sql_errors:
                    break
                continue
            try:
                payload = parse_json(response)
                text = render_answer(
                    payload, results, plan["metric"], plan["period"], plan["measure"]
                )
                evidence.update(
                    selected=copy.deepcopy(results[payload["result_id"]]),
                    selected_id=payload["result_id"],
                    template=False,
                )
                return text
            except (InvalidAnswer, ValueError, TypeError):
                messages.append(
                    {"role": "assistant", "content": "Não foi possível validar a resposta."}
                )
                messages.append(
                    {
                        "role": "user",
                        "content": "Retorne somente o objeto kind/result_id de uma consulta desta pergunta. "
                        "Se ainda não consultou, use as tools.",
                    }
                )
        # Uma pergunta composta só é concluída quando todas as métricas são válidas.
        raise ValueError("Não foi possível concluir uma das consultas planejadas.")
