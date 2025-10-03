import pandas as pd
import json

def excel_to_json(file_path: str, output_path: str = None):
    df = pd.read_excel(file_path)

    df.columns = df.columns.str.strip().str.lower()

    if "sku" not in df.columns or "nicho" not in df.columns:
        raise ValueError("O Excel precisa ter colunas: sku e nicho")

    df = df.drop_duplicates(subset=["sku"]).reset_index(drop=True)

    payload = [
        {"sku": str(row["sku"]).strip(), "nicho": str(row["nicho"]).strip()}
        for _, row in df.iterrows()
    ]

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


if __name__ == "__main__":
    data = excel_to_json("arquivo.xlsx", "sku_nichos.json")
    print(json.dumps(data, ensure_ascii=False, indent=2))
