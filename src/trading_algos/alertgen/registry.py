def get_default_alertgen_sensor_config(name="sensor_0"):
    return {
        "name": name,
        "sensor_config": {
            "alg_code": 901,
            "alg_param": 30,
            "symbol": "EVGO",
            "buy": True,
            "sell": False,
        },
        "enable": True,
    }


def get_default_alertgen_engine_config(name="alertgen_0"):
    return {
        "name": name,
        "engine_config": {"interval_secs": 60, "type": "gen1"},
        "enable": True,
        "sensors": [get_default_alertgen_sensor_config()],
    }
