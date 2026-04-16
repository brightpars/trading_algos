from __future__ import annotations

from typing import Any

from scipy import stats

from trading_algos.alertgen.common import TREND
from trading_algos.alertgen.models import EvaluationSummary


def _linregress_slope_and_rvalue(x: list[float], y: list[float]) -> tuple[float, float]:
    result: Any = stats.linregress(x, y)
    return float(result.slope), float(result.rvalue)


def set_gt_in_data(data_list, idx, gt):
    data_list[idx]["gt_up"] = gt == TREND.UP
    data_list[idx]["gt_down"] = gt == TREND.DOWN
    data_list[idx]["gt_nn"] = gt not in [TREND.UP, TREND.DOWN]
    data_list[idx]["gt_trend"] = gt


def calculate_ground_truth(data_list, evaluate_window_len):
    last_idx = len(data_list) - 1
    first_colourful_idx = last_idx - evaluate_window_len

    for idx in range(last_idx, first_colourful_idx - 1, -1):
        set_gt_in_data(data_list, idx, TREND.UNKNOWN)

    for idx in range(first_colourful_idx - 1, -1, -1):
        y = [
            data_list[idx]["Close"],
            data_list[idx + evaluate_window_len - 1]["Close"],
        ]
        x = [1, evaluate_window_len]
        slope, r = _linregress_slope_and_rvalue(x, y)
        if abs(r) < 0.7:
            gt = data_list[idx + 1]["gt_trend"]
        else:
            threshold = 0.001
            if slope > threshold:
                gt = TREND.UP
            elif slope < -threshold:
                gt = TREND.DOWN
            else:
                gt = data_list[idx + 1]["gt_trend"]
        set_gt_in_data(data_list, idx, gt)

    while True:
        do_changed = False
        for idx in range(first_colourful_idx - 3, -1, -1):
            begin_idx = idx
            mid_idx = idx + 1
            end_idx = idx + 2
            if data_list[begin_idx]["gt_trend"] == data_list[end_idx]["gt_trend"]:
                if data_list[begin_idx]["gt_trend"] != data_list[mid_idx]["gt_trend"]:
                    gt = data_list[begin_idx]["gt_trend"]
                    set_gt_in_data(data_list, mid_idx, gt)
                    do_changed = True
        if do_changed is False:
            break

    while True:
        do_changed = False
        for idx in range(first_colourful_idx - 4, -1, -1):
            begin_idx = idx
            mid_idx = idx + 1
            end_idx = idx + 3
            if data_list[begin_idx]["gt_trend"] == data_list[end_idx]["gt_trend"]:
                if data_list[begin_idx]["gt_trend"] != data_list[mid_idx]["gt_trend"]:
                    gt = data_list[begin_idx]["gt_trend"]
                    set_gt_in_data(data_list, mid_idx, gt)
                    set_gt_in_data(data_list, mid_idx + 1, gt)
                    do_changed = True
        if do_changed is False:
            break


def evaluate_predictions(data_list, predicted_trend_list):
    correct_prediction_no = 0
    absolute_wrong_no = 0
    correct_buy_signal_no = 0
    correct_sell_signal_no = 0
    buy_signals = 0
    sell_signals = 0

    for idx, predicted_trend in enumerate(predicted_trend_list):
        ground_truth_trend = data_list[idx]["gt_trend"]
        if predicted_trend == ground_truth_trend:
            correct_prediction_no += 1
        if ground_truth_trend == TREND.UP and predicted_trend == TREND.DOWN:
            absolute_wrong_no += 1
        if ground_truth_trend == TREND.DOWN and predicted_trend == TREND.UP:
            absolute_wrong_no += 1
        if predicted_trend == TREND.UP:
            buy_signals += 1
            if ground_truth_trend == TREND.UP:
                correct_buy_signal_no += 1
        if predicted_trend == TREND.DOWN:
            sell_signals += 1
            if ground_truth_trend == TREND.DOWN:
                correct_sell_signal_no += 1

    return EvaluationSummary(
        metrics={
            "B~": buy_signals,
            "B+": correct_buy_signal_no,
            "S~": sell_signals,
            "S+": correct_sell_signal_no,
            "!!": absolute_wrong_no,
            "correct_predictions": correct_prediction_no,
        }
    )
