from trading_algos.alertgen.alg100_variants import alg102
from trading_algos.alertgen.alg200_variants import alg201
from trading_algos.alertgen.alg_aggregate import agreegate_algs


def test_aggregate_alert_algorithm_produces_interactive_payloads(tmp_path):
    aggregate = agreegate_algs(
        "AAPL",
        report_base_path=str(tmp_path),
        buy_algs_obj_list=[alg102("AAPL", report_base_path=str(tmp_path))],
        sell_algs_obj_list=[alg201("AAPL", report_base_path=str(tmp_path), wlen=2)],
    )

    sample_rows = [
        {
            "ts": f"2025-01-01 10:00:0{i}",
            "Open": 10 + i,
            "High": 11 + i,
            "Low": 9 + i,
            "Close": 10.5 + i,
        }
        for i in range(4)
    ]
    aggregate.process_list(sample_rows)

    payloads = aggregate.interactive_report_payloads()

    assert len(payloads) >= 1
    assert all(payload for payload, _description in payloads)
