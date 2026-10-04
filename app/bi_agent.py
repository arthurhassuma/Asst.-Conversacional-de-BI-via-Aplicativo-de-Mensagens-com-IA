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
from app.rendering import METRICS, InvalidAnswer, render_answer

FAILURE = "Não consegui concluir a consulta com segurança. Reformule a pergunta ou tente novamente."
PERIOD_QUESTION = "Qual período deseja consultar? Informe as datas ou o mês e o ano."
METRIC_QUESTION = (
    "Qual métrica deseja consultar: faturamento emitido, recebimentos, "
    "pedidos, contratos, clientes, horas ou chamados?"
)
MEASURE_QUESTION = (
    "Você deseja o valor ou a quantidade? Para indicadores operacionais, "
    "especifique horas previstas, horas realizadas ou a medida de chamados."
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


def clarify(plan: dict, messages: list) -> str | None:
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
        return MEASURE_QUESTION
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

    async def answer(self, question: str, history: list) -> tuple[str, list]:
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
                return await self._answer(question, history, turn)
        except APIError as exc:
            text = api_error_message(exc.code)
            return text, turn + [{"role": "assistant", "content": text}]
        except (httpx.HTTPError, TimeoutError, ValueError, TypeError, KeyError):
            # Nenhuma exceção externa, credencial ou SQL chega ao Telegram.
            return FAILURE, turn + [{"role": "assistant", "content": FAILURE}]

    async def _answer(self, question, history, turn):
        messages = copy.deepcopy(history + turn)
        # O planejador não declara tools: não envie blocos tool_use/tool_result
        # históricos à API sem as respectivas definições. Mantém pedido e resposta.
        planning_messages = [m for m in messages if isinstance(m["content"], str)]
        today = datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()
        response = await self.client.aio.models.generate_content(
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
        clarification = clarify(plan, messages)
        if clarification:
            return clarification, turn + [{"role": "assistant", "content": clarification}]
        system = SYSTEM_PROMPT + "\nPlano confirmado: " + json.dumps(plan, ensure_ascii=False)
        results, sql_errors, schema_seen = {}, 0, False
        for _ in range(self.settings.max_tool_rounds):
            response = await self.client.aio.models.generate_content(
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
                text = render_answer(parse_json(response), results, plan["metric"])
                # Histórico recebe a resposta de fato vista pelo gestor.
                messages.append({"role": "assistant", "content": text})
                return text, messages[len(history) :]
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
        # Descarta chamadas incompletas no histórico em caso de falha.
        return FAILURE, turn + [{"role": "assistant", "content": FAILURE}]
