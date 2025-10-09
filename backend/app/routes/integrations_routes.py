from fastapi import APIRouter, Depends, HTTPException
from app.models import IntegrationCreate, TokenRequest, ArpTokenRequest, BearerTokenRequest, User
from app.services.integrations_service import IntegrationsService
from app.services.data_service import Data
from app.services.data_parser_service import DataParser
from app.services.order_service import OrderInserter
from app.core.dependencies import get_current_user
from app.core.container import container
from datetime import datetime
import logging

router = APIRouter()


def get_integrations_service() -> IntegrationsService:
    return container.integrations_service()


@router.get("/tokens")
async def get_integration_tokens(
    current_user: User = Depends(get_current_user),
    service: IntegrationsService = Depends(get_integrations_service)
):
    try:
        tokens = service.get_user_integrations(current_user.id)
        return {
            "arp_session_cookie": tokens.get("arpcommerce", ""),
            "auth_bearer_token": tokens.get("bearer", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/arpcommerce")
async def save_arpcommerce_token(
    token_request: ArpTokenRequest,
    current_user: User = Depends(get_current_user),
    service: IntegrationsService = Depends(get_integrations_service),
    inserter: OrderInserter = Depends(lambda: container.order_inserter())
):
    try:
        if not token_request.token_value.strip():
            raise HTTPException(status_code=400, detail="Session cookie is required")

        integration = IntegrationCreate(
            integration_type="arpcommerce",
            token_value=token_request.token_value
        )
        service.save_integration(current_user.id, integration)

        # Fetch orders from 01/09/2025 to current date
        data_inicio = "2025-09-01"
        data_fim = datetime.now().strftime("%Y-%m-%d")
        url = f"https://app.arpcommerce.com.br/sells?r={data_inicio}/{data_fim}"
        logger = logging.getLogger(__name__)
        logger.info(f"Fetching orders from {data_inicio} to {data_fim}")

        data_obj = Data(url, {"session": token_request.token_value})
        raw_json = data_obj.get_data()
        logger.info(f"Raw data obtained: {len(raw_json)} records")

        parser = DataParser(raw_json)
        pedidos = parser.parse_orders()
        logger.info(f"Parsed orders: {len(pedidos)} orders")

        inserter.insert_orders(pedidos, current_user.id)
        logger.info(f"{len(pedidos)} orders inserted into DB successfully")

        return {"message": "ARPCommerce session cookie saved successfully and orders fetched"}
    except HTTPException:
        raise
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Error saving ARPCommerce token and fetching orders")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bearer")
async def save_bearer_token(
    token_request: BearerTokenRequest,
    current_user: User = Depends(get_current_user),
    service: IntegrationsService = Depends(get_integrations_service)
):
    try:
        if not token_request.token_value.strip():
            raise HTTPException(status_code=400, detail="Bearer token is required")

        integration = IntegrationCreate(
            integration_type="bearer",
            token_value=token_request.token_value
        )
        service.save_integration(current_user.id, integration)
        return {"message": "Bearer token saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
