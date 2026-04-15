from trading_algos.alertgen.alg100_variants import alg100, alg101, alg102
from trading_algos.alertgen.alg200_variants import alg200, alg201
from trading_algos.alertgen.alg_aggregate import agreegate_algs


def create_alertgen_algorithm(sensor_config, report_base_path):
    symbol = sensor_config["symbol"]
    alg_code = sensor_config["alg_code"]
    alg_param_for_logging = sensor_config["alg_param"]

    if alg_code == 100:
        alg_inst = alg100(symbol, report_base_path=report_base_path)
    elif alg_code == 101:
        alg_inst = alg101(symbol, report_base_path=report_base_path)
    elif alg_code == 102:
        alg_inst = alg102(symbol, report_base_path=report_base_path)
    elif alg_code == 200:
        alg_inst = alg200(
            symbol, report_base_path=report_base_path, wlen=sensor_config["alg_param"]
        )
    elif alg_code == 201:
        alg_inst = alg201(
            symbol, report_base_path=report_base_path, wlen=sensor_config["alg_param"]
        )
    elif alg_code == 901:
        wlen = sensor_config["alg_param"]
        alg_inst = agreegate_algs(
            symbol,
            report_base_path=report_base_path,
            buy_algs_obj_list=[alg102(symbol, report_base_path=report_base_path)],
            sell_algs_obj_list=[
                alg201(symbol, report_base_path=report_base_path, wlen=wlen),
                alg102(symbol, report_base_path=report_base_path),
            ],
        )
    elif alg_code == 902:
        wlen_list = sensor_config["alg_param"]
        alg_inst = agreegate_algs(
            symbol,
            report_base_path=report_base_path,
            buy_algs_obj_list=[
                alg201(symbol, report_base_path=report_base_path, wlen=wlen_list[0])
            ],
            sell_algs_obj_list=[
                alg201(symbol, report_base_path=report_base_path, wlen=wlen_list[1])
            ],
        )
    else:
        raise ValueError(f"unsupported alg_code={alg_code}")

    return alg_inst, alg_param_for_logging
