import pandas as pd
import json

# Caminho do seu arquivo XLSX
file_path = "arquivo.xlsx"

# Lê o Excel
df = pd.read_excel(file_path)

# Converte para lista de dicionários com chaves em minúsculo
resultado = [{"nicho": row["NICHO"], "sku": row["SKU"]} for _, row in df.iterrows()]

# Exibe o resultado
print(resultado)

# Salva como JSON
with open("resultado.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=4)
