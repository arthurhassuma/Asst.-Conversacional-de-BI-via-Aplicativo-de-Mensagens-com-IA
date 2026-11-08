"""CLI de treino local, sem chamadas externas e sem utilizar dados de sessões."""

import json
from pathlib import Path

from app.cli_support import PortugueseArgumentParser
from training.corpus import load_corpus, validate_corpus

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = PortugueseArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "train", "test"])
    parser.add_argument("--corpus", type=Path, default=ROOT / "training/questions-v1.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--thresholds",
        default="0.5,0.6,0.7",
        help="Limiares de confiança testados, escolhidos só pela validação.",
    )
    parser.add_argument(
        "--joint-selection",
        action="store_true",
        help="Escolhe C e limiar juntos pelo macro-F1 com abstenção (protocolo v2).",
    )
    parser.add_argument(
        "--c-grid",
        default="0.5,1,2",
        help="Valores de C da regressão logística, escolhidos só pela validação.",
    )
    parser.add_argument("--model", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        rows = load_corpus(args.corpus)
        if args.command == "validate":
            print(json.dumps(validate_corpus(rows), ensure_ascii=False))
            return
        from training.fit import evaluate_model, fit_model

        if args.output is None or args.output.exists():
            raise ValueError(
                "Informe uma pasta de saída nova; resultados existentes são preservados."
            )
        if args.command == "train":
            c_grid = tuple(float(value) for value in args.c_grid.split(","))
            thresholds = tuple(float(value) for value in args.thresholds.split(","))
            artifact, report = fit_model(
                rows, args.seed, c_grid, thresholds, joint=args.joint_selection
            )
        else:
            if args.model is None:
                raise ValueError("Informe --model com o artefato congelado.")
            artifact = json.loads(args.model.read_text(encoding="utf-8"))
            report = evaluate_model(artifact, rows, "test")
        args.output.mkdir(parents=True)
        if args.command == "train":
            (args.output / "model.json").write_text(
                json.dumps(artifact, ensure_ascii=False, sort_keys=True), encoding="utf-8"
            )
        (args.output / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary = report.get("validation", report.get("classifier"))
        print(
            json.dumps(
                {"etapa": args.command, "metricas": summary, "saida": str(args.output)},
                ensure_ascii=False,
            )
        )
    except (ValueError, OSError, ImportError) as exc:
        message = (
            'Instale as dependências de treinamento: pip install -e ".[training]".'
            if isinstance(exc, ImportError)
            else str(exc)
        )
        parser.exit(1, message + "\n")


if __name__ == "__main__":
    main()
