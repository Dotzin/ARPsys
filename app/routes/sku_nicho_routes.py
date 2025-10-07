from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import JSONResponse
from app.services.sku_nicho_service import SkuNichoInserter
import logging
import pandas as pd

router = APIRouter()
logger = logging.getLogger(__name__)


# Dependency injection for services
def get_sku_nicho_inserter(request: Request) -> SkuNichoInserter:
    return request.app.state.sku_nicho_inserter


# Rotas relacionadas a SKU/Nicho
@router.post("/sku_nicho/inserir")
def inserir_sku_nicho(
    sku: str, nicho: str, inserter: SkuNichoInserter = Depends(get_sku_nicho_inserter)
):
    logger.info(f"Inserindo SKU {sku} no nicho {nicho}")
    inserter.insert_one(sku, nicho)
    logger.info(f"SKU {sku} inserido com sucesso")
    return {"mensagem": f"SKU {sku} inserido no nicho {nicho} com sucesso."}


@router.post("/sku_nicho/inserir_varios")
def inserir_varios_sku_nicho(
    sku_nicho_lista: list[dict],
    inserter: SkuNichoInserter = Depends(get_sku_nicho_inserter),
):
    logger.info(f"Inserindo {len(sku_nicho_lista)} registros de SKU/nicho")
    for item in sku_nicho_lista:
        if "sku" not in item or "nicho" not in item:
            logger.warning(f"Registro inválido: {item}")
            return JSONResponse(
                status_code=400,
                content={"erro": "Cada item deve conter 'sku' e 'nicho'"},
            )
    inserter.insert_many(sku_nicho_lista)
    logger.info("Inserção múltipla concluída")
    return {"mensagem": f"{len(sku_nicho_lista)} registros inseridos com sucesso."}


@router.post("/sku_nicho/inserir_xlsx")
async def inserir_xlsx(
    file: UploadFile = File(...),
    inserter: SkuNichoInserter = Depends(get_sku_nicho_inserter),
):
    logger.info(f"Inserindo SKUs de XLSX: {file.filename}")
    try:
        df = pd.read_excel(file.file)
        sku_nicho_lista = df.to_dict(orient="records")
        for item in sku_nicho_lista:
            if "sku" not in item or "nicho" not in item:
                logger.warning(f"Registro inválido no XLSX: {item}")
                return JSONResponse(
                    status_code=400,
                    content={"erro": "Cada linha deve conter colunas 'sku' e 'nicho'"},
                )
        inserter.insert_many(sku_nicho_lista)
        logger.info(f"Inserção de XLSX concluída: {len(sku_nicho_lista)} registros")
        return {
            "mensagem": f"{len(sku_nicho_lista)} registros inseridos com sucesso do XLSX."
        }
    except Exception as e:
        logger.exception("Erro ao processar XLSX")
        return JSONResponse(status_code=500, content={"erro": str(e)})


@router.put("/sku_nicho/atualizar")
def atualizar_sku_nicho(
    sku: str,
    novo_nicho: str,
    inserter: SkuNichoInserter = Depends(get_sku_nicho_inserter),
):
    logger.info(f"Atualizando SKU {sku} para nicho {novo_nicho}")
    atualizados = inserter.update_nicho(sku, novo_nicho)
    logger.info(f"{atualizados} registros atualizados")
    return {"mensagem": f"{atualizados} registro(s) atualizado(s)."}


@router.delete("/sku_nicho/deletar")
def deletar_sku_nicho(
    sku: str, inserter: SkuNichoInserter = Depends(get_sku_nicho_inserter)
):
    logger.info(f"Deletando SKU {sku}")
    deletados = inserter.delete_sku(sku)
    logger.info(f"{deletados} registros deletados")
    return {"mensagem": f"{deletados} registro(s) apagado(s)."}


@router.get("/sku_nicho/listar")
def listar_sku_nicho(inserter: SkuNichoInserter = Depends(get_sku_nicho_inserter)):
    logger.info("Listando todos os SKU/nichos")
    rows = inserter.list_all()
    logger.info(f"{len(rows)} registros retornados")
    return {"dados": rows}
