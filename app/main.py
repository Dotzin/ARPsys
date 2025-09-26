from fastapi import FastAPI, Query
from contextlib import asynccontextmanager
from utils.get_data import Data
from utils.data_parser import DataParser
from utils.database import Database, TableCreator
from utils.order_inserter import OrderInserter
import os
from datetime import datetime

# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.db")

# ------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    database = Database(db_path)
    database.connect()
    app.state.database = database

    table_creator = TableCreator(database)
    table_creator.create_orders_table()

    app.state.order_inserter = OrderInserter(database)
    yield
    database.close()


app = FastAPI(lifespan=lifespan)

# ------------------------------
@app.post("/update_orders")
def update_orders(date: str = Query(None, description="Data única DD/MM/YYYY ou intervalo DD/MM/YYYY/DD/MM/YYYY")):
    """
    Atualiza pedidos da API.
    
    :param date: Data única ou intervalo separadas por '/'.
    """
    if not date:
        date_start = date_end = datetime.today().strftime("%Y-%m-%d")
    else:
        parts = date.split("/")
        if len(parts) == 3:
            # Data única
            day, month, year = parts
            date_start = date_end = f"{year}-{month}-{day}"
        elif len(parts) == 6:
            # Intervalo
            day1, month1, year1, day2, month2, year2 = parts
            date_start = f"{year1}-{month1}-{day1}"
            date_end = f"{year2}-{month2}-{day2}"
        else:
            return {"error": "Formato de data inválido. Use DD/MM/YYYY ou DD/MM/YYYY/DD/MM/YYYY."}

    # 2️⃣ Pegar dados da API (com a data no query param)
    cookies = {'session': '.eJwVir0KwjAURt_l0rGU5j_tpLg4Oam4leR6UwqmLUnrIr678YMDh8P3gWGlFN1M8wb9lnaqgaKbXtCDS-uhgEuMlJCaIo1PUMOeKQ2Zcp6Wufx0-1_1OB2v7zHfs7-o8y3KqkQUilsflO245UFoRYS2C8wK9ZSuVYZ59Fy2xmjjAyomrDaSDDpkAr4_KMQwig.aMxLsg.3D5e5s_a96H1mPB_uHM7CySJ7n8'}
    url = f'https://app.arpcommerce.com.br/sells?r={date_start}'
    if date_start != date_end:
        # Se intervalo, API pode aceitar algo como ?start=YYYY-MM-DD&end=YYYY-MM-DD
        url = f'https://app.arpcommerce.com.br/sells?r={date_start}/{date_end}'

    data = Data(url, cookies)
    raw_json = data.get_data()

    # 3️⃣ Estruturar os dados
    parser = DataParser(raw_json)
    orders = parser.parse_orders()

    # 4️⃣ Inserir no banco
    order_inserter = app.state.order_inserter
    order_inserter.insert_orders(orders)
    print(url)

    return {"message": f"{len(orders)} orders updated successfully.", "date_start": date_start, "date_end": date_end}
