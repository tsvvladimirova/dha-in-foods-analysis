from pathlib import Path
import json
import pandas as pd


# Define project directories
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "useable_data"

NORWAY_DIR = DATA_DIR / "Matvaretabellen — Norway"

# Define Norway source file paths
NORWAY_FOODS_FILE = NORWAY_DIR / "foods.json"
NORWAY_FOOD_GROUPS_FILE = NORWAY_DIR / "food-groups.json"

# Define New Zealand source file paths
NEW_ZEALAND_DIR = DATA_DIR / "FOODfiles 2024 — New Zealand"

NZ_DATA_FILE = NEW_ZEALAND_DIR / "Unabridged DATA.FT.xlsx"
NZ_NAME_FILE = NEW_ZEALAND_DIR / "NAME.FT.xlsx"

# Define output directory
PROCESSED_DATA_DIR = PROJECT_DIR / "processed_data"


def load_json(file_path):
    """Load a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def extract_norway_dha(norway_foods, norway_food_groups):
    """Extract DHA values and food group information."""

    dha_records = []

    for food in norway_foods["foods"]:
        for constituent in food["constituents"]:

            if constituent["nutrientId"].startswith("C22:6n-3"):
                dha_records.append({
                    "foodName": food["foodName"],
                    "foodId": food["foodId"],
                    "foodGroupId": str(food["foodGroupId"]),
                    "quantity": constituent.get("quantity"),
                    "unit": constituent.get("unit"),
                    "sourceId": constituent["sourceId"],
                })

    norway_dha_df = pd.DataFrame(dha_records)

    # Create a lookup dictionary for food group names
    food_group_lookup = {
        str(group["foodGroupId"]): group["name"]
        for group in norway_food_groups["foodGroups"]
    }

    # Add food group names
    norway_dha_df["foodGroupName"] = (
        norway_dha_df["foodGroupId"].map(food_group_lookup)
    )

    return norway_dha_df

def extract_new_zealand_dha(nz_data, nz_names):
    """Extract DHA values and food information from FOODfiles."""

    # Select the DHA component
    dha_data = nz_data[
        nz_data["Component Identifier"] == "F22D6CN3"
    ].copy()

    # Select relevant food information
    food_info = nz_names[
        [
            "FoodID",
            "Food Name",
            "Short Food Name",
            "Edible portion (%)",
            "Generic Name",
            "Kind",
            "State",
        ]
    ].copy()

    # Merge DHA data with food information
    nz_dha_df = dha_data.merge(
        food_info,
        on="FoodID",
        how="left",
        validate="one_to_one"
    )

    # Rename columns to make them easier to use
    nz_dha_df = nz_dha_df.rename(
        columns={
            "FoodID": "foodId",
            "Food Name": "foodName",
            "Short Food Name": "shortFoodName",
            "Value": "quantity",
            "Unit Code": "unit",
            "Matrix Unit Code": "matrixUnitCode",
            "Source Code": "sourceCode",
            "Value Type Code": "valueTypeCode",
            "Acquisition Type Code": "acquisitionTypeCode",
            "Method Type Code": "methodTypeCode",
            "Method Indicator Code": "methodIndicatorCode",
            "Edible portion (%)": "ediblePortionPercent",
            "Generic Name": "genericName",
        }
    )

    # Keep the relevant columns
    nz_dha_df = nz_dha_df[
        [
            "foodName",
            "shortFoodName",
            "foodId",
            "quantity",
            "unit",
            "matrixUnitCode",
            "ediblePortionPercent",
            "genericName",
            "Kind",
            "State",
            "sourceCode",
            "valueTypeCode",
            "acquisitionTypeCode",
            "methodTypeCode",
            "methodIndicatorCode",
        ]
    ]

    # Rename remaining columns
    nz_dha_df = nz_dha_df.rename(
        columns={
            "Kind": "kind",
            "State": "state",
        }
    )

    return nz_dha_df

def main():

    # Load Norway source data
    norway_foods = load_json(NORWAY_FOODS_FILE)
    norway_food_groups = load_json(NORWAY_FOOD_GROUPS_FILE)

    # Extract DHA data
    norway_dha_df = extract_norway_dha(
        norway_foods,
        norway_food_groups
    )

    # Create output directory if it does not exist
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save extracted data
    output_file = PROCESSED_DATA_DIR / "norway_dha.csv"

    norway_dha_df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    # Basic loading checks
    print("Norway DHA data loaded successfully.")
    print(f"Number of records: {len(norway_dha_df)}")
    print(f"Missing DHA values: {norway_dha_df['quantity'].isna().sum()}")
    print(
        "Missing food group names:",
        norway_dha_df["foodGroupName"].isna().sum()
    )
    print(f"Saved to: {output_file}")

    # Load New Zealand source data
    nz_data = pd.read_excel(
        NZ_DATA_FILE,
        header=1,
        dtype={"FoodID": "string"}
    )

    nz_names = pd.read_excel(
        NZ_NAME_FILE,
        header=1,
        dtype={"FoodID": "string"}
    )

    # Extract DHA data
    nz_dha_df = extract_new_zealand_dha(
        nz_data,
        nz_names
    )

    # Save extracted data
    nz_output_file = PROCESSED_DATA_DIR / "new_zealand_dha.csv"

    nz_dha_df.to_csv(
        nz_output_file,
        index=False,
        encoding="utf-8-sig"
    )

    # Basic loading checks
    print("\nNew Zealand DHA data loaded successfully.")
    print(f"Number of records: {len(nz_dha_df)}")
    print(f"Missing DHA values: {nz_dha_df['quantity'].isna().sum()}")
    print(f"Missing food names: {nz_dha_df['foodName'].isna().sum()}")
    print(f"Saved to: {nz_output_file}")

if __name__ == "__main__":
    main()
