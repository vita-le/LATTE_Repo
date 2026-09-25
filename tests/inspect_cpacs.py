from pathlib import Path

from src.core.cpacs_config import get_cpacs_configurations


CPACS_FILE = Path("examples/DLH_CPACS.xml")


def main():

    configurations = get_cpacs_configurations(CPACS_FILE)

    print("CPACS:", CPACS_FILE)
    print()
    print("Available configurations:")

    for configuration in configurations:
        print(
            f"- {configuration['type']}: "
            f"{configuration['uid']}"
        )


if __name__ == "__main__":
    main()