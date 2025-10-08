from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
import pandas as pd
from app.repositories.database_repository import Database
from app.core.container import container
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Rotas relacionadas a pedidos
@router.get("/orders")
def listar_orders(database: Database = Depends(lambda: container.database())):
    logger.info("Listando todos os pedidos da tabela orders")
    try:
        db = database
        assert db.conn is not None
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM orders")
        linhas = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]

        df = pd.DataFrame(linhas, columns=colunas)
        # Limpeza básica para evitar problemas de serialização
        df = df.fillna(0).replace({pd.NA: 0}).astype(object)

        logger.info(f"{len(df)} pedidos encontrados")
        return {"total_pedidos": len(df), "pedidos": df.to_dict(orient="records")}
    except Exception as e:
        logger.exception("Erro ao listar pedidos")
        return JSONResponse(status_code=500, content={"erro": str(e)})


@router.get("/orders/periodo")
def listar_orders_periodo(
    database: Database = Depends(lambda: container.database())
):
    logger.info(f"Listando pedidos entre {data_inicio} e {data_fim}")
    try:
        # Validar formato
        try:
            inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            fim = datetime.strptime(data_fim, "%Y-%m-%d")
        except ValueError:
            logger.warning("Datas inválidas fornecidas")
            return JSONResponse(
                status_code=400,
                content={"erro": "Datas inválidas, use formato YYYY-MM-DD"},
            )

        db = database
        assert db.conn is not None
        cursor = db.conn.cursor()
        query = """
            SELECT * FROM orders
            WHERE date(payment_date) BETWEEN ? AND ?
        """
        cursor.execute(query, (data_inicio, data_fim))
        linhas = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]

        df = pd.DataFrame(linhas, columns=colunas)
        df = df.fillna(0).replace({pd.NA: 0}).astype(object)

        logger.info(f"{len(df)} pedidos encontrados no período")
        return {
            "periodo": {"inicio": data_inicio, "fim": data_fim},
            "total_pedidos": len(df),
            "pedidos": df.to_dict(orient="records"),
        }
    except Exception as e:
        logger.exception("Erro ao listar pedidos por período")
        return JSONResponse(status_code=500, content={"erro": str(e)})
