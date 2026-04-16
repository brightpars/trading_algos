from __future__ import annotations

import copy
import json
import os

import matplotlib.pyplot as plt

from trading_algos.alertgen.shared_utils.models import AnalysisReportData
from trading_algos.alertgen.shared_utils.plotting import save_figure


def serialize_analysis_report(path, filename, data_list, eval_dict):
    report_path = os.path.join(path, filename + ".dict")
    data_list_copy = copy.deepcopy(data_list)
    for data in data_list_copy:
        data.pop("_id", None)
        data["ts"] = str(data["ts"])
    payload = AnalysisReportData(data=data_list_copy, eval_dict=eval_dict)
    with open(report_path, "w") as fp:
        json.dump({"data": payload.data, "eval_dict": payload.eval_dict}, fp)
    return report_path


def write_analysis_report_bundle(
    *,
    report_path,
    data_name,
    data_list,
    eval_dict,
    make_standard_figure,
    make_ground_truth_figure,
    alg_specific_report,
    figure_w,
    figure_l,
):
    fig, axes = plt.subplots(ncols=1, nrows=2, gridspec_kw={"height_ratios": [2, 1]})

    plt.sca(axes[0])
    make_standard_figure(save=False)
    fig.add_subplot(axes[0])

    plt.sca(axes[1])
    make_ground_truth_figure(save=False)
    fig.add_subplot(axes[1])

    fig.set_size_inches(figure_w, 3 * figure_l)
    plt.tight_layout()

    save_figure(path=report_path, filename=data_name)
    serialize_analysis_report(
        path=report_path,
        filename=data_name,
        data_list=data_list,
        eval_dict=eval_dict,
    )
    alg_specific_report()
