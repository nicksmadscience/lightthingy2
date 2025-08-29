import yaml


class LightThingy:
    def __init__(self):
        self.data = []

        with open("presets.yaml") as stream:
            try:
                presets = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)


if __name__ == "__main__":
    lt = LightThingy()