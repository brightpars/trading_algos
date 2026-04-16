import os

import matplotlib.pyplot as plt


class PLOT:
    PLOT = "plot"
    SEGMENTED = "segmented"
    HORIZONTAL_DASHED = "horizontal_dashed"


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def _x_values(data_list):
    return list(range(len(data_list)))


def add_normal_graph(data_list, spec, title=""):
    if not data_list:
        return

    x_values = _x_values(data_list)
    if isinstance(spec, tuple) and len(spec) == 2 and spec[1] == PLOT.PLOT:
        key = spec[0]
        y_values = [item.get(key) for item in data_list]
        plt.plot(x_values, y_values, label=str(key))
    elif isinstance(spec, tuple) and len(spec) == 3 and spec[1] == PLOT.SEGMENTED:
        keys, _, colours = spec
        close_values = [item.get("Close") for item in data_list]
        for key, colour in zip(keys, colours):
            y_values = [
                close if item.get(key) else None
                for item, close in zip(data_list, close_values)
            ]
            plt.scatter(x_values, y_values, color=colour, label=str(key), s=10)
    plt.title(title)
    plt.grid(True, alpha=0.2)


def add_special_graph(spec, title=""):
    if not spec:
        return
    kind = spec[0]
    if kind != PLOT.HORIZONTAL_DASHED:
        return
    _, horizontal_line_list, colour_list = spec
    for y_value, colour in zip(horizontal_line_list, colour_list):
        plt.axhline(y=y_value, color=colour, linestyle="--", alpha=0.5)
    plt.title(title)


def save_figure(path, filename, overwrite=True):
    _ensure_dir(path)
    target = os.path.join(path, f"{filename}.png")
    if not overwrite and os.path.exists(target):
        return target
    plt.tight_layout()
    plt.savefig(target)
    plt.close()
    return target
