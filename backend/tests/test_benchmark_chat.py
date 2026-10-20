from scripts.benchmark_chat import summarize


def test_summarize_reports_percentiles_and_range():
    assert summarize([4.0, 1.0, 3.0, 2.0]) == "n=4 median=2.500s p95=4.000s min=1.000s max=4.000s"
