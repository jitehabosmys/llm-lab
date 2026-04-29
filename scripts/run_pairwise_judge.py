from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_ROOT = Path("/hy-tmp/outputs/llm-lab-pairwise-judge")
DEFAULT_ENV_FILE = REPO_ROOT / ".env"
WINNER_VALUES = {"A", "B", "tie"}
DIMENSIONS = [
    "evidence_groundedness",
    "root_cause_quality",
    "actionability",
    "missing_info_quality",
    "overall_engineering_quality",
]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or key in os.environ:
            continue

        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        os.environ[key] = value


load_env_file(DEFAULT_ENV_FILE)
DEFAULT_MODEL = os.getenv("OPENAI_JUDGE_MODEL", "gpt-5.3-codex")
DEFAULT_BASE_URL = os.getenv("OPENAI_BASE_URL")


@dataclass
class CandidateResult:
    sample_id: str
    prompt: str
    system: str | None
    raw_output: str
    reference_output: dict[str, Any] | None
    metrics: dict[str, Any]
    record: dict[str, Any]


@dataclass
class PairInputs:
    sample_id: str
    prompt: str
    system: str | None
    reference_output: dict[str, Any] | None
    a: CandidateResult
    b: CandidateResult


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run pairwise LLM-as-a-judge comparisons on two inference-result files "
            "and export DPO candidate pairs."
        )
    )
    parser.add_argument("--candidate-a", type=Path, required=True, help="Path to candidate A results jsonl.")
    parser.add_argument("--candidate-b", type=Path, required=True, help="Path to candidate B results jsonl.")
    parser.add_argument("--label-a", type=str, default=None, help="Human-readable label for candidate A.")
    parser.add_argument("--label-b", type=str, default=None, help="Human-readable label for candidate B.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Judge model. Default: {DEFAULT_MODEL}")
    parser.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_BASE_URL,
        help="Optional OpenAI-compatible API base URL. Defaults to OPENAI_BASE_URL env var.",
    )
    parser.add_argument("--concurrency", type=int, default=4, help="Concurrent judge requests. Default: 4")
    parser.add_argument("--max-samples", type=int, default=0, help="Limit number of comparable pairs. 0 means all.")
    parser.add_argument("--seed", type=int, default=42, help="Seed for A/B order randomization. Default: 42")
    parser.add_argument("--use-reference", action="store_true", help="Include reference output in the judge prompt.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Default: /hy-tmp/outputs/llm-lab-pairwise-judge/<timestamp>",
    )
    return parser.parse_args()


def make_output_dir(explicit: Path | None) -> Path:
    if explicit is not None:
        path = explicit
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = DEFAULT_OUTPUT_ROOT / timestamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def derive_label(path: Path) -> str:
    name = path.name
    suffix = "_results.jsonl"
    if name.endswith(suffix):
        return name[: -len(suffix)]
    return path.stem


def load_results(path: Path) -> dict[str, CandidateResult]:
    rows: dict[str, CandidateResult] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        sample_id = record["sample_id"]
        rows[sample_id] = CandidateResult(
            sample_id=sample_id,
            prompt=record["prompt"],
            system=record.get("system"),
            raw_output=record["raw_output"],
            reference_output=record.get("reference_output"),
            metrics=record["metrics"],
            record=record,
        )
    return rows


def build_pairs(results_a: dict[str, CandidateResult], results_b: dict[str, CandidateResult]) -> list[PairInputs]:
    common_ids = sorted(set(results_a) & set(results_b))
    pairs: list[PairInputs] = []
    for sample_id in common_ids:
        a = results_a[sample_id]
        b = results_b[sample_id]
        pairs.append(
            PairInputs(
                sample_id=sample_id,
                prompt=a.prompt,
                system=a.system,
                reference_output=a.reference_output,
                a=a,
                b=b,
            )
        )
    return pairs


def schema_valid(candidate: CandidateResult) -> bool:
    return bool(candidate.metrics.get("schema_valid", False))


def make_gate_result(
    pair: PairInputs,
    label_a: str,
    label_b: str,
    use_reference: bool,
) -> dict[str, Any] | None:
    a_valid = schema_valid(pair.a)
    b_valid = schema_valid(pair.b)

    if a_valid and not b_valid:
        winner = "A"
        confidence = "high"
        source = "gate_schema_validity"
        reason = f"{label_a} passes schema validation while {label_b} does not."
    elif b_valid and not a_valid:
        winner = "B"
        confidence = "high"
        source = "gate_schema_validity"
        reason = f"{label_b} passes schema validation while {label_a} does not."
    elif not a_valid and not b_valid:
        winner = "tie"
        confidence = "high"
        source = "gate_both_schema_invalid"
        reason = "Both candidates fail schema validation, so the pair is skipped from content judging."
    else:
        return None

    return {
        "sample_id": pair.sample_id,
        "judge_source": source,
        "winner": winner,
        "winner_confidence": confidence,
        "dimension_winners": {dimension: "tie" for dimension in DIMENSIONS},
        "reason": reason,
        "used_reference": use_reference,
        "candidate_a_label": label_a,
        "candidate_b_label": label_b,
        "candidate_a_metrics": pair.a.metrics,
        "candidate_b_metrics": pair.b.metrics,
        "candidate_a_output": pair.a.raw_output,
        "candidate_b_output": pair.b.raw_output,
        "reference_output": pair.reference_output if use_reference else None,
        "usable_for_dpo": winner in {"A", "B"},
        "high_confidence_for_dpo": winner in {"A", "B"},
    }


def build_judge_instructions() -> str:
    return (
        "You are an impartial evaluator for a Chinese training/deployment diagnosis assistant. "
        "Compare candidate A and candidate B for the same input. "
        "Judge only by the provided input, environment, command, and log. "
        "Prefer answers that are evidence-grounded, conservative, actionable, and helpful for engineering diagnosis. "
        "Do not reward verbosity. "
        "If both are similarly good or similarly bad, return tie. "
        "Return structured JSON only."
    )


def build_judge_input(
    pair: PairInputs,
    a_label: str,
    b_label: str,
    use_reference: bool,
) -> list[dict[str, Any]]:
    content_parts: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": "\n".join(
                [
                    f"Sample ID: {pair.sample_id}",
                    f"System prompt: {pair.system or '(none)'}",
                    "Task input:",
                    pair.prompt,
                    "",
                    f"Candidate A ({a_label}):",
                    pair.a.raw_output,
                    "",
                    f"Candidate B ({b_label}):",
                    pair.b.raw_output,
                ]
            ),
        }
    ]
    if use_reference and pair.reference_output is not None:
        content_parts.append(
            {
                "type": "input_text",
                "text": "Reference output (for calibration only, do not require exact wording match):\n"
                + json.dumps(pair.reference_output, ensure_ascii=False, indent=2),
            }
        )

    return [{"role": "user", "content": content_parts}]


def judge_response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "winner": {"type": "string", "enum": ["A", "B", "tie"]},
            "winner_confidence": {"type": "string", "enum": ["low", "medium", "high"]},
            "dimension_winners": {
                "type": "object",
                "additionalProperties": False,
                "properties": {dimension: {"type": "string", "enum": ["A", "B", "tie"]} for dimension in DIMENSIONS},
                "required": DIMENSIONS,
            },
            "reason": {"type": "string"},
        },
        "required": ["winner", "winner_confidence", "dimension_winners", "reason"],
    }


async def judge_one(
    client: AsyncOpenAI,
    pair: PairInputs,
    label_a: str,
    label_b: str,
    model: str,
    use_reference: bool,
    rng: random.Random,
) -> dict[str, Any]:
    # Randomize candidate order to reduce position bias.
    if rng.random() < 0.5:
        display_a, display_b = pair.a, pair.b
        display_a_label, display_b_label = label_a, label_b
        swap_back = False
    else:
        display_a, display_b = pair.b, pair.a
        display_a_label, display_b_label = label_b, label_a
        swap_back = True

    response = await client.responses.create(
        model=model,
        temperature=0,
        instructions=build_judge_instructions(),
        input=build_judge_input(
            PairInputs(
                sample_id=pair.sample_id,
                prompt=pair.prompt,
                system=pair.system,
                reference_output=pair.reference_output,
                a=display_a,
                b=display_b,
            ),
            display_a_label,
            display_b_label,
            use_reference,
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "pairwise_diagnosis_judge",
                "schema": judge_response_schema(),
                "strict": True,
            }
        },
        max_output_tokens=400,
    )
    parsed = json.loads(response.output_text)
    if swap_back:
        parsed["winner"] = {"A": "B", "B": "A", "tie": "tie"}[parsed["winner"]]
        parsed["dimension_winners"] = {
            key: {"A": "B", "B": "A", "tie": "tie"}[value] for key, value in parsed["dimension_winners"].items()
        }

    return {
        "sample_id": pair.sample_id,
        "judge_source": "openai_pairwise_judge",
        "winner": parsed["winner"],
        "winner_confidence": parsed["winner_confidence"],
        "dimension_winners": parsed["dimension_winners"],
        "reason": parsed["reason"],
        "used_reference": use_reference,
        "candidate_a_label": label_a,
        "candidate_b_label": label_b,
        "candidate_a_metrics": pair.a.metrics,
        "candidate_b_metrics": pair.b.metrics,
        "candidate_a_output": pair.a.raw_output,
        "candidate_b_output": pair.b.raw_output,
        "reference_output": pair.reference_output if use_reference else None,
        "raw_response_id": getattr(response, "id", None),
        "usable_for_dpo": parsed["winner"] in {"A", "B"},
        "high_confidence_for_dpo": parsed["winner"] in {"A", "B"} and parsed["winner_confidence"] == "high",
    }


async def judge_pairs(
    client: AsyncOpenAI,
    pairs: list[PairInputs],
    label_a: str,
    label_b: str,
    model: str,
    concurrency: int,
    use_reference: bool,
    seed: int,
) -> list[dict[str, Any]]:
    semaphore = asyncio.Semaphore(concurrency)
    rng = random.Random(seed)
    lock = asyncio.Lock()

    async def worker(index: int, pair: PairInputs) -> dict[str, Any]:
        gate_result = make_gate_result(pair, label_a, label_b, use_reference)
        if gate_result is not None:
            log(
                f"[{index}/{len(pairs)}] {pair.sample_id} resolved by gate: "
                f"{gate_result['judge_source']} winner={gate_result['winner']}"
            )
            return gate_result

        async with semaphore:
            async with lock:
                local_seed = rng.randint(0, 10**9)
            local_rng = random.Random(local_seed)
            result = await judge_one(client, pair, label_a, label_b, model, use_reference, local_rng)
            log(
                f"[{index}/{len(pairs)}] {pair.sample_id} judged by model: "
                f"winner={result['winner']} confidence={result['winner_confidence']}"
            )
            return result

    tasks = [worker(index, pair) for index, pair in enumerate(pairs, start=1)]
    return await asyncio.gather(*tasks)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")


def summarize_results(results: list[dict[str, Any]], label_a: str, label_b: str) -> dict[str, Any]:
    total = len(results)
    source_counts = Counter(result["judge_source"] for result in results)
    winner_counts = Counter(result["winner"] for result in results)

    summary: dict[str, Any] = {
        "total_pairs": total,
        "judge_source_counts": dict(source_counts),
        "winner_counts": dict(winner_counts),
        "usable_for_dpo_count": sum(1 for result in results if result["usable_for_dpo"]),
        "high_confidence_for_dpo_count": sum(1 for result in results if result["high_confidence_for_dpo"]),
    }

    comparable = winner_counts[label_a] if label_a in winner_counts else 0
    comparable += winner_counts[label_b] if label_b in winner_counts else 0
    if comparable > 0:
        pass

    variant_wins = {
        label_a: sum(1 for result in results if result["winner"] == "A"),
        label_b: sum(1 for result in results if result["winner"] == "B"),
        "tie": sum(1 for result in results if result["winner"] == "tie"),
    }
    summary["variant_wins"] = variant_wins

    decided_total = variant_wins[label_a] + variant_wins[label_b]
    if decided_total > 0:
        summary["variant_win_rates_excluding_ties"] = {
            label_a: round(variant_wins[label_a] / decided_total, 4),
            label_b: round(variant_wins[label_b] / decided_total, 4),
        }

    dimension_counts: dict[str, dict[str, int]] = {}
    for dimension in DIMENSIONS:
        counts = Counter(result["dimension_winners"][dimension] for result in results)
        dimension_counts[dimension] = {
            label_a: counts["A"],
            label_b: counts["B"],
            "tie": counts["tie"],
        }
    summary["dimension_winner_counts"] = dimension_counts

    summary["failed_or_tied_sample_ids"] = {
        "tie": [result["sample_id"] for result in results if result["winner"] == "tie"],
        "not_high_confidence_for_dpo": [
            result["sample_id"] for result in results if not result["high_confidence_for_dpo"]
        ],
    }
    return summary


def build_dpo_rows(results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_pairs: list[dict[str, Any]] = []
    high_conf_pairs: list[dict[str, Any]] = []

    for result in results:
        if result["winner"] not in {"A", "B"}:
            continue
        if result["winner"] == "A":
            chosen_output = result["candidate_a_output"]
            rejected_output = result["candidate_b_output"]
            chosen_label = result["candidate_a_label"]
            rejected_label = result["candidate_b_label"]
        else:
            chosen_output = result["candidate_b_output"]
            rejected_output = result["candidate_a_output"]
            chosen_label = result["candidate_b_label"]
            rejected_label = result["candidate_a_label"]

        row = {
            "sample_id": result["sample_id"],
            "chosen_variant": chosen_label,
            "rejected_variant": rejected_label,
            "chosen_output": chosen_output,
            "rejected_output": rejected_output,
            "judge_source": result["judge_source"],
            "winner_confidence": result["winner_confidence"],
            "dimension_winners": result["dimension_winners"],
            "judge_reason": result["reason"],
            "used_reference": result["used_reference"],
        }
        all_pairs.append(row)
        if result["high_confidence_for_dpo"]:
            high_conf_pairs.append(row)

    return all_pairs, high_conf_pairs


async def async_main() -> None:
    args = parse_args()
    output_dir = make_output_dir(args.output_dir)
    label_a = args.label_a or derive_label(args.candidate_a)
    label_b = args.label_b or derive_label(args.candidate_b)

    results_a = load_results(args.candidate_a)
    results_b = load_results(args.candidate_b)
    pairs = build_pairs(results_a, results_b)
    if args.max_samples > 0:
        pairs = pairs[: args.max_samples]

    manifest = {
        "candidate_a": str(args.candidate_a),
        "candidate_b": str(args.candidate_b),
        "label_a": label_a,
        "label_b": label_b,
        "model": args.model,
        "base_url": args.base_url,
        "concurrency": args.concurrency,
        "max_samples": args.max_samples,
        "seed": args.seed,
        "use_reference": args.use_reference,
        "pair_count": len(pairs),
    }
    write_json(output_dir / "run_manifest.json", manifest)
    log(f"Output directory: {output_dir}")
    log(f"Comparing `{label_a}` vs `{label_b}` across {len(pairs)} pair(s)")

    client_kwargs: dict[str, Any] = {}
    if args.base_url:
        client_kwargs["base_url"] = args.base_url
    client = AsyncOpenAI(**client_kwargs)
    results = await judge_pairs(
        client=client,
        pairs=pairs,
        label_a=label_a,
        label_b=label_b,
        model=args.model,
        concurrency=args.concurrency,
        use_reference=args.use_reference,
        seed=args.seed,
    )
    write_jsonl(output_dir / "judge_results.jsonl", results)

    summary = summarize_results(results, label_a, label_b)
    write_json(output_dir / "judge_summary.json", summary)

    dpo_pairs, dpo_pairs_high_conf = build_dpo_rows(results)
    write_jsonl(output_dir / "dpo_pairs.jsonl", dpo_pairs)
    write_jsonl(output_dir / "dpo_pairs_high_confidence.jsonl", dpo_pairs_high_conf)

    log("Wrote judge_results.jsonl, judge_summary.json, and DPO pair exports")
    print(json.dumps({"output_dir": str(output_dir), "summary": summary}, ensure_ascii=False, indent=2))


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
