import json
from typing import Optional

def replace_property_value(
    input_file: str,
    output_file: str,
    property_name: str,
    new_value,
    old_value: Optional[str] = None
) -> None:
    """
    Reads a JSON file (list of objects), replaces a property value,
    and writes the updated content to a new file.

    :param input_file: Path to input JSON file
    :param output_file: Path to output JSON file
    :param property_name: Property to update (e.g., "category")
    :param new_value: New value to assign
    :param old_value: If provided, only replace when current value matches this
    """

    # Read JSON file
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON root must be a list of objects")

    # Update values
    for item in data:
        if not isinstance(item, dict):
            continue

        if property_name in item:
            if old_value is None or item[property_name] == old_value:
                item[property_name] = new_value

    # Write updated JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    replace_property_value(
        input_file="mercado_livre_fone_20260212.json",
        output_file="mercado_livre_fone_20260212.json",
        property_name="CATEGORY",
        new_value="fone",
        old_value=None  # Set to None to replace all values
    )