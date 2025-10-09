from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from app.services.sku_nicho_service import SkuNichoInserter
from app.core.container import container
from app.models import User, SkuNichoInsert, SkuNichoUpdate, SkuNichoDelete
from app.routes.auth_routes import get_current_active_user
import logging
import pandas as pd
import io

router = APIRouter()
logger = logging.getLogger(__name__)


# Rotas relacionadas a SKU/Nicho
@router.get("/sku_nicho/template_xlsx")
def download_template_xlsx(
    current_user: User = Depends(get_current_active_user),
):
    logger.info(f"Download template requested by user: {current_user.username}")
    # Create a sample DataFrame with the expected columns
    df = pd.DataFrame({
        "sku": ["exemplo_sku_1", "exemplo_sku_2"],
        "nicho": ["exemplo_nicho_1", "exemplo_nicho_2"]
    })

    # Save DataFrame to an in-memory bytes buffer as XLSX
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    output.seek(0)

    headers = {
        "Content-Disposition": "attachment; filename=template_sku_nicho.xlsx"
    }
    response = StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)
    response.status_code = 200
    return response


@router.post("/sku_nicho/inserir")
def inserir_sku_nicho(
    sku_nicho: SkuNichoInsert,
    current_user: User = Depends(get_current_active_user),
    inserter: SkuNichoInserter = Depends(lambda: container.sku_nicho_inserter())
):
    logger.info(f"Inserindo SKU {sku_nicho.sku} no nicho {sku_nicho.nicho}")
    inserter.insert_one(sku_nicho.sku, sku_nicho.nicho, current_user.id)
    logger.info(f"SKU {sku_nicho.sku} inserido com sucesso")
    return {"mensagem": f"SKU {sku_nicho.sku} inserido no nicho {sku_nicho.nicho} com sucesso."}


@router.post("/sku_nicho/inserir_varios")
def inserir_varios_sku_nicho(
    sku_nicho_lista: list[dict],
    current_user: User = Depends(get_current_active_user),
    inserter: SkuNichoInserter = Depends(lambda: container.sku_nicho_inserter()),
):
    logger.info(f"Inserindo {len(sku_nicho_lista)} registros de SKU/nicho")
    for item in sku_nicho_lista:
        if "sku" not in item or "nicho" not in item:
            logger.warning(f"Registro inválido: {item}")
            return JSONResponse(
                status_code=400,
                content={"erro": "Cada item deve conter 'sku' e 'nicho'"},
            )
    inserter.insert_many(sku_nicho_lista, current_user.id)
    logger.info("Inserção múltipla concluída")
    return {"mensagem": f"{len(sku_nicho_lista)} registros inseridos com sucesso."}


@router.post("/sku_nicho/inserir_xlsx")
async def inserir_xlsx(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    inserter: SkuNichoInserter = Depends(lambda: container.sku_nicho_inserter()),
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
        inserter.insert_many(sku_nicho_lista, current_user.id)
        logger.info(f"Inserção de XLSX concluída: {len(sku_nicho_lista)} registros")
        return {
            "mensagem": f"{len(sku_nicho_lista)} registros inseridos com sucesso do XLSX."
        }
    except Exception as e:
        logger.exception("Erro ao processar XLSX")
        return JSONResponse(status_code=500, content={"erro": str(e)})


@router.put("/sku_nicho/atualizar")
def atualizar_sku_nicho(
    sku_update: SkuNichoUpdate,
    current_user: User = Depends(get_current_active_user),
    inserter: SkuNichoInserter = Depends(lambda: container.sku_nicho_inserter()),
):
    logger.info(f"Atualizando SKU {sku_update.sku} para nicho {sku_update.novo_nicho}")
    atualizados = inserter.update_nicho(sku_update.sku, sku_update.novo_nicho, current_user.id)
    logger.info(f"{atualizados} registros atualizados")
    return {"mensagem": f"{atualizados} registro(s) atualizado(s)."}


@router.delete("/sku_nicho/deletar")
def deletar_sku_nicho(
    sku_delete: SkuNichoDelete,
    current_user: User = Depends(get_current_active_user),
    inserter: SkuNichoInserter = Depends(lambda: container.sku_nicho_inserter())
):
    logger.info(f"Deletando SKU {sku_delete.sku}")
    deletados = inserter.delete_sku(sku_delete.sku, current_user.id)
    logger.info(f"{deletados} registros deletados")
    return {"mensagem": f"{deletados} registro(s) apagado(s)."}


@router.get("/sku_nicho/listar")
def listar_sku_nicho(
    current_user: User = Depends(get_current_active_user),
    inserter: SkuNichoInserter = Depends(lambda: container.sku_nicho_inserter())
):
    logger.info("Listando todos os SKU/nichos")
    rows = inserter.list_all(current_user.id)
    logger.info(f"{len(rows)} registros retornados")
    return {"dados": rows}
