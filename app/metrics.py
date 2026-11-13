import os
import threading
import time

CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"
DURATION_BUCKETS = (0.1, 0.25, 0.5, 1, 2, 3, 5, 8, 13, 20, 40, 100)


def _escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _labels(names: tuple, values: tuple) -> str:
    if not names:
        return ""
    return "{" + ",".join(f'{n}="{_escape(v)}"' for n, v in zip(names, values, strict=True)) + "}"


class Counter:
    def __init__(self, name: str, help_text: str, label_names: tuple = ()):
        self.name, self.help, self.label_names = name, help_text, label_names
        self._values: dict[tuple, float] = {}
        self._lock = threading.Lock()

    def inc(self, *label_values, amount: float = 1):
        with self._lock:
            self._values[label_values] = self._values.get(label_values, 0) + amount

    def render(self) -> list[str]:
        lines = [f"# HELP {self.name} {self.help}", f"# TYPE {self.name} counter"]
        with self._lock:
            items = sorted(self._values.items())
        for values, number in items:
            lines.append(f"{self.name}{_labels(self.label_names, values)} {number:g}")
        return lines


class Histogram:
    def __init__(
        self, name: str, help_text: str, label_names: tuple = (), buckets=DURATION_BUCKETS
    ):
        self.name, self.help, self.label_names = name, help_text, label_names
        self.buckets = tuple(buckets)
        self._series: dict[tuple, list] = {}
        self._lock = threading.Lock()

    def observe(self, *label_values, value: float):
        with self._lock:
            counts, total = self._series.setdefault(
                label_values, [[0] * len(self.buckets), [0.0, 0]]
            )
            for index, bound in enumerate(self.buckets):
                if value <= bound:
                    counts[index] += 1
            total[0] += value
            total[1] += 1

    def render(self) -> list[str]:
        lines = [f"# HELP {self.name} {self.help}", f"# TYPE {self.name} histogram"]
        with self._lock:
            items = sorted((k, list(v[0]), list(v[1])) for k, v in self._series.items())
        for values, counts, (total, count) in items:
            for bound, number in zip(self.buckets, counts, strict=True):
                names = (*self.label_names, "le")
                lines.append(
                    f"{self.name}_bucket{_labels(names, (*values, f'{bound:g}'))} {number}"
                )
            lines.append(
                f"{self.name}_bucket{_labels((*self.label_names, 'le'), (*values, '+Inf'))} {count}"
            )
            lines.append(f"{self.name}_sum{_labels(self.label_names, values)} {total:g}")
            lines.append(f"{self.name}_count{_labels(self.label_names, values)} {count}")
        return lines


UPDATES = Counter(
    "bi_updates_total",
    "Updates do Telegram recebidos no webhook, por resultado.",
    ("result",),
)
QUESTIONS = Counter(
    "bi_questions_total",
    "Perguntas processadas pelo agente, por desfecho.",
    ("status",),
)
QUESTION_SECONDS = Histogram(
    "bi_question_duration_seconds",
    "Duração do processamento de uma pergunta pelo agente.",
)
GEMINI_REQUESTS = Counter(
    "bi_gemini_requests_total", "Chamadas ao Gemini feitas para responder perguntas."
)
PROVIDER_ERRORS = Counter(
    "bi_provider_errors_total",
    "Erros do provedor de IA, por código HTTP.",
    ("code",),
)
QUERY_PATHS = Counter(
    "bi_queries_total",
    "Consultas respondidas, por caminho (modelo fixo ou SQL livre).",
    ("path",),
)
SQL_EXECUTIONS = Counter(
    "bi_sql_executions_total",
    "Execuções de SQL no banco, por resultado.",
    ("outcome",),
)
SQL_SECONDS = Histogram(
    "bi_sql_duration_seconds",
    "Duração da execução de SQL no banco, por resultado.",
    ("outcome",),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 3),
)

_METRICS = (
    UPDATES,
    QUESTIONS,
    QUESTION_SECONDS,
    GEMINI_REQUESTS,
    PROVIDER_ERRORS,
    QUERY_PATHS,
    SQL_EXECUTIONS,
    SQL_SECONDS,
)
_STARTED = time.time()
KNOWN_STATUSES = {
    "answer",
    "error",
    "invalid_question",
    "provider_error",
    "transport_error",
    "unsupported_request",
    "clarification_period",
    "clarification_metric",
    "clarification_measure",
    "clarification_limit",
}


def record_question(trace: dict, seconds: float):
    status = trace.get("status", "error")
    QUESTIONS.inc(status if status in KNOWN_STATUSES else "other")
    QUESTION_SECONDS.observe(value=seconds)
    GEMINI_REQUESTS.inc(amount=len(trace.get("requests", [])))
    code = trace.get("provider_code")
    if status == "provider_error":
        PROVIDER_ERRORS.inc(str(code) if isinstance(code, int) else "desconhecido")
    for query in trace.get("queries", []):
        if "template" in query:
            QUERY_PATHS.inc("modelo_fixo" if query["template"] else "sql_livre")


def render() -> str:
    lines = []
    for metric in _METRICS:
        lines.extend(metric.render())
    revision = os.getenv("PAC_REVISION", "desconhecida")
    lines += [
        "# HELP bi_build_info Revisão do código em execução.",
        "# TYPE bi_build_info gauge",
        f'bi_build_info{{revision="{_escape(revision)}"}} 1',
        "# HELP bi_process_start_time_seconds Início do processo (epoch).",
        "# TYPE bi_process_start_time_seconds gauge",
        f"bi_process_start_time_seconds {_STARTED:.0f}",
    ]
    return "\n".join(lines) + "\n"
