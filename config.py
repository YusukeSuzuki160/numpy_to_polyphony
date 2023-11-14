import json
from typing import Any


class Config:
    def __init__(self, config_file: str = "") -> None:
        if config_file == "":
            self.config = {}
        else:
            with open(config_file) as f:
                config = json.load(f)
            self.config = config
        self.PREPROCESS_CONFIGS = ["fixed_point_style"]

    def is_config(self) -> bool:
        return bool(self.config)

    def get_preprocess_config(self) -> dict[str, Any]:
        config = {}
        for key in self.PREPROCESS_CONFIGS:
            if key in self.config:
                config[key] = self.config[key]
        return config

    def get_polyphony_config(self) -> dict[str, Any]:
        config = {}
        for key in self.config:
            if key not in self.PREPROCESS_CONFIGS and key in self.config:
                config[key] = self.config[key]
        return config

    def has_key(self, key: str) -> bool:
        return key in self.config

    def gen_config_json(self) -> str:
        content = self.get_polyphony_config()
        file_name = "./configs/config_temp.json"
        with open(file_name, "w") as f:
            json.dump(content, f, indent=4)
        return file_name
