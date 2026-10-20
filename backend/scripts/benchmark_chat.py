import argparse
import math
import statistics
import sys
import time

from app.core.config import settings
from app.services.chat import LLMError, call_llm, stream_llm

PROMPTS = [
    "Suggest one small way to make a morning walk a consistent habit.",
    "How can I get back on track after missing a day of journaling?",
    "Suggest a simple cue for remembering to stretch.",
    "How can I make a new reading habit easier to maintain?",
    "Give me one practical tip for building a daily exercise routine.",
    "What is a small reward I could use for completing a habit?",
    "How can I track progress on drinking more water?",
    "Suggest a gentle way to restart meditation after a break.",
    "How can I make meal planning feel less overwhelming?",
    "What is one way to build consistency with practicing guitar?",
    "How should I adjust a habit that feels too ambitious?",
    "Suggest a useful reminder for taking a short walk.",
    "How can I make evening reflection a regular habit?",
    "Give me one tip for sticking with a daily language lesson.",
    "How can I celebrate small wins while building a habit?",
    "What can I do when my usual habit cue is unavailable?",
    "Suggest a simple way to create a bedtime routine.",
    "How can I fit a quick strength workout into a busy day?",
    "What is a good first step for tidying my desk daily?",
    "How can I make a habit more enjoyable?",
]


def summarize(samples: list[float]) -> str:
    ordered = sorted(samples)
    p95 = ordered[math.ceil(0.95 * len(ordered)) - 1]
    return (
        f"n={len(ordered)} median={statistics.median(ordered):.3f}s "
        f"p95={p95:.3f}s min={ordered[0]:.3f}s max={ordered[-1]:.3f}s"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark non-streaming AI coach response time.")
    parser.add_argument("--requests", type=int, default=20, help="Number of sequential prompts to send (default: 20).")
    parser.add_argument("--stream", action="store_true", help="Use the streaming path and report TTFT as well as total time.")
    args = parser.parse_args()
    if args.requests < 1:
        parser.error("--requests must be at least 1")

    samples = []
    ttfts = []
    print(f"Model: {settings.llm_model}; requests: {args.requests}")
    print("The first request is reported as cold; remaining requests are reported as warm.")
    try:
        for index in range(args.requests):
            messages = [
                {"role": "system", "content": "You are a concise, supportive habit coach."},
                {"role": "user", "content": PROMPTS[index % len(PROMPTS)]},
            ]
            started_at = time.perf_counter()
            if args.stream:
                first = None
                for _ in stream_llm(messages):
                    if first is None:
                        first = time.perf_counter() - started_at
                ttfts.append(first)
            else:
                call_llm(messages)
            samples.append(time.perf_counter() - started_at)
    except LLMError as exc:
        print(f"Benchmark failed: {exc.message}", file=sys.stderr)
        return 1

    if ttfts:
        print(f"Cold TTFT: {summarize(ttfts[:1])}")
        if len(ttfts) > 1:
            print(f"Warm TTFT: {summarize(ttfts[1:])}")
    print(f"Cold total: {summarize(samples[:1])}")
    if len(samples) > 1:
        print(f"Warm total: {summarize(samples[1:])}")
    else:
        print("Warm: not measured (only one request)")
    if not args.stream:
        print("Non-streaming TTFT equals total response time: text is shown only after the full reply arrives.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
