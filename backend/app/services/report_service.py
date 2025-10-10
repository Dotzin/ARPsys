import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import pandas as pd
import pytz
from app.repositories.database_repository import Database

from app.config.constants import (
    TOP_NICHOS_LIMIT,
    TOP_SKUS_LIMIT,
    TOP_ADS_LIMIT,
    TOP_PER_NICHO_LIMIT,
    LAST_SALES_LIMIT,
)

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self.db = database  # For backward compatibility
        self.logger = logging.getLogger(__name__)

    def get_daily_report_data(self, user_id: int = 1) -> Optional[Dict[str, Any]]:
        """Calcula e retorna apenas o relatório do dia atual."""
        sao_paulo = pytz.timezone('America/Sao_Paulo')
        hoje = datetime.now(pytz.utc).astimezone(sao_paulo).strftime("%Y-%m-%d")
        self.logger.info(f"Calculando relatório diário para {hoje}")

        try:
            db = self.database
            assert db.conn is not None
            cursor = db.conn.cursor()

            query = """ SELECT o.*, n.nicho FROM orders o LEFT JOIN sku_nichos n ON o.sku = n.sku AND o.user_id = n.user_id
                        WHERE date(o.payment_date) = ? AND o.user_id = ? """
            linhas = cursor.execute(query, (hoje, user_id)).fetchall()
            colunas = [desc[0] for desc in cursor.description]

            df = pd.DataFrame(linhas, columns=colunas)
            if df.empty:
                self.logger.info("Nenhum pedido encontrado para o relatório diário")
                return {"dia": hoje, "status": "sem_dados", "kpis_diarios": {}}

            # Add date fields
            df["data"] = pd.to_datetime(df["payment_date"], errors="coerce")
            if not df.empty and "data" in df.columns:
                df["hour"] = df["data"].dt.hour
                df["weekday"] = df["data"].dt.weekday
                df["month"] = df["data"].dt.month
                df["payment_date_brt"] = df["payment_date"]
            else:
                df["hour"] = 0
                df["weekday"] = 0
                df["month"] = 0
                df["payment_date_brt"] = df["payment_date"]

            # Generate KPIs for the current day
            kpis_diarios = self._calculate_daily_kpis(df)

            # Analysis by niche for the day
            por_nicho_dia = self._calculate_niche_analysis(df)

            # Analysis by SKU for the day
            por_sku_dia = (
                df.groupby(["sku", "nicho"])
                .agg({"profit": "sum", "total_value": "sum", "order_id": "count", "quantity": "sum"})
                .reset_index()
                .rename(columns={"profit": "lucro_liquido", "total_value": "faturamento_total", "order_id": "total_pedidos", "quantity": "total_unidades"})
            )
            por_sku_dia = self._clean_df_for_json(por_sku_dia)

            # Daily rankings
            rankings_diarios = self._calculate_daily_rankings(df, por_nicho_dia)

            # Última venda
            ultima_venda_df = df.sort_values("payment_date", ascending=False).head(1)[
                [
                    "payment_date_brt",
                    "order_id",
                    "cart_id",
                    "sku",
                    "title",
                    "quantity",
                    "total_value",
                    "profit",
                    "nicho",
                ]
            ].rename(columns={"payment_date_brt": "payment_date"})
            ultima_venda = (
                ultima_venda_df.to_dict(orient="records")[0]
                if not ultima_venda_df.empty
                else None
            )

            # Melhor produto
            melhor_produto_df = (
                df.groupby("sku")
                .agg({"profit": "sum", "total_value": "sum", "quantity": "sum"})
                .sort_values("profit", ascending=False)
                .head(1)
                .reset_index()
            )
            melhor_produto = (
                melhor_produto_df.to_dict(orient="records")[0]
                if not melhor_produto_df.empty
                else None
            )

            # Melhor anúncio
            melhor_anuncio_df = (
                df.groupby("ad")
                .agg({"profit": "sum", "total_value": "sum", "quantity": "sum"})
                .sort_values("profit", ascending=False)
                .head(1)
                .reset_index()
            )
            melhor_anuncio = (
                melhor_anuncio_df.to_dict(orient="records")[0]
                if not melhor_anuncio_df.empty
                else None
            )

            # Last 15 sales
            ultimas_15_vendas = (
                df.sort_values("payment_date", ascending=False)
                .head(LAST_SALES_LIMIT)[
                    [
                        "payment_date_brt",
                        "order_id",
                        "cart_id",
                        "sku",
                        "title",
                        "quantity",
                        "total_value",
                        "profit",
                        "nicho",
                    ]
                ]
                .rename(columns={"payment_date_brt": "payment_date"})
                .to_dict(orient="records")
            )

            # Vendas negativas
            vendas_negativas = df[df["profit"] < 0][
                [
                    "payment_date_brt",
                    "order_id",
                    "cart_id",
                    "sku",
                    "title",
                    "quantity",
                    "total_value",
                    "profit",
                    "nicho",
                ]
            ].rename(columns={"payment_date_brt": "payment_date"}).to_dict(orient="records")

            # Por hora
            por_hora = (
                df.groupby("hour")
                .agg({"profit": "sum", "total_value": "sum", "order_id": "count"})
                .reset_index()
                .rename(
                    columns={
                        "profit": "lucro_liquido",
                        "total_value": "faturamento",
                        "order_id": "total_pedidos",
                    }
                )
            )
            por_hora = self._clean_df_for_json(por_hora)

            relatorio_final = {
                "dia": hoje,
                "status": "sucesso",
                "kpis_diarios": kpis_diarios,
                "analise_por_nicho_dia": por_nicho_dia.to_dict(orient="records"),
                "por_sku_dia": por_sku_dia.to_dict(orient="records"),
                "por_hora": por_hora.to_dict(orient="records"),
                "rankings_diarios": rankings_diarios,
                "timestamp_atualizacao": datetime.now().isoformat(),
                "ultima_venda": ultima_venda,
                "melhor_produto": melhor_produto,
                "melhor_anuncio": melhor_anuncio,
                "ultimas_15_vendas": ultimas_15_vendas,
                "vendas_negativas": vendas_negativas,
            }

            return relatorio_final

        except Exception as e:
            self.logger.exception("Erro ao calcular o relatório diário")
            return {"dia": hoje, "status": "erro", "erro": str(e), "kpis_diarios": {}}

    def _calculate_daily_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate daily KPIs from the dataframe."""
        total_pedidos = len(df)
        total_unidades = int(df["quantity"].fillna(0).sum())
        faturamento = float(df["total_value"].fillna(0).sum())
        lucro_liquido = float(df["profit"].fillna(0).sum())

        ticket_medio = {
            "pedido": faturamento / total_pedidos if total_pedidos > 0 else 0,
            "unidade": faturamento / total_unidades if total_unidades > 0 else 0,
        }

        custos = {
            "custo_total": float(df["cost"].fillna(0).sum()) if not df.empty else 0,
            "frete_total": float(df["freight"].fillna(0).sum()) if not df.empty else 0,
            "impostos_total": float(df["taxes"].fillna(0).sum()) if not df.empty else 0,
        }

        return {
            "lucro_liquido": lucro_liquido,
            "faturamento": faturamento,
            "total_pedidos": total_pedidos,
            "total_unidades": total_unidades,
            "ticket_medio": ticket_medio,
            "custos": custos,
        }

    def _calculate_niche_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate analysis by niche for the day."""
        por_nicho_dia = (
            df.groupby("nicho")
            .agg({"profit": "sum", "total_value": "sum", "order_id": "count"})
            .reset_index()
            .rename(
                columns={
                    "profit": "lucro_liquido",
                    "total_value": "faturamento",
                    "order_id": "total_pedidos",
                }
            )
        )

        # Clean and convert to JSON
        por_nicho_dia = self._clean_df_for_json(por_nicho_dia)
        return por_nicho_dia

    def _clean_df_for_json(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame for JSON serialization."""
        return df.fillna(0).replace({pd.NA: 0}).astype(object)

    def _calculate_daily_rankings(
        self, df: pd.DataFrame, por_nicho_dia: pd.DataFrame
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate daily rankings."""
        top_nichos_dia = (
            por_nicho_dia.sort_values("lucro_liquido", ascending=False)
            .head(TOP_NICHOS_LIMIT)
            .to_dict(orient="records")
        )
        top_skus_dia = (
            df.groupby("sku")
            .agg({"profit": "sum", "gross_profit": "sum"})
            .sort_values("profit", ascending=False)
            .head(TOP_SKUS_LIMIT)
            .reset_index()
            .rename(columns={"profit": "lucro_liquido", "gross_profit": "lucro_bruto"})
            .to_dict(orient="records")
        )
        top_ads_dia = (
            df.groupby("ad")
            .agg({"profit": "sum", "gross_profit": "sum"})
            .sort_values("profit", ascending=False)
            .head(TOP_ADS_LIMIT)
            .reset_index()
            .rename(columns={"profit": "lucro_liquido", "gross_profit": "lucro_bruto"})
            .to_dict(orient="records")
        )

        return {
            "top_nichos": top_nichos_dia,
            "top_skus": top_skus_dia,
            "top_ads": top_ads_dia,
        }

    def _validate_dates(
        self, data_inicio: Optional[str], data_fim: Optional[str]
    ) -> Tuple[datetime, datetime, int]:
        """Validate and parse start and end dates."""
        if not data_inicio or not data_fim:
            hoje = datetime.today().strftime("%Y-%m-%d")
            data_inicio = data_fim = hoje

        start = datetime.strptime(data_inicio, "%Y-%m-%d")
        end = datetime.strptime(data_fim, "%Y-%m-%d")
        dias_totais = (end - start).days + 1
        return start, end, dias_totais

    def _fetch_data_from_db(self, start: datetime, end: datetime, user_id: int = 1) -> pd.DataFrame:
        """Fetch orders data from database for the given period."""
        db = self.database
        assert db.conn is not None
        cursor = db.conn.cursor()

        query = """
            SELECT o.*, n.nicho
            FROM orders o
            LEFT JOIN sku_nichos n ON o.sku = n.sku AND o.user_id = n.user_id
            WHERE date(o.payment_date) >= ? AND date(o.payment_date) <= ? AND o.user_id = ?
        """
        linhas = cursor.execute(
            query, (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), user_id)
        ).fetchall()
        colunas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(linhas, columns=colunas)

        if df.empty:
            self.logger.warning(
                f"Nenhum pedido encontrado para o período {start.date()} a {end.date()}"
            )
            raise ValueError("Nenhum pedido encontrado neste período")

        self.logger.info(
            f"DataFrame carregado com {len(df)} pedidos para o período {start.date()} a {end.date()}"
        )

        df["data"] = pd.to_datetime(df["payment_date"], errors="coerce")

        # Extrair campos de data
        if not df.empty and "data" in df.columns:
            df["hour"] = df["data"].dt.hour
            df["weekday"] = df["data"].dt.weekday
            df["month"] = df["data"].dt.month
        else:
            df["hour"] = 0
            df["weekday"] = 0
            df["month"] = 0

        self.logger.info("Campos de data extraídos (hora, dia da semana, mês)")
        return df

    def generate_relatorio_flex(
        self, data_inicio: Optional[str] = None, data_fim: Optional[str] = None, user_id: int = 1
    ) -> Dict[str, Any]:
        """Gera o relatório flexível com KPIs, relatórios diários, análises por nicho/SKU e rankings."""
        self.logger.info(
            f"Gerando relatório flex com data_inicio={data_inicio}, data_fim={data_fim}"
        )
        try:
            start, end, dias_totais = self._validate_dates(data_inicio, data_fim)
        except Exception:
            self.logger.warning("Datas inválidas fornecidas")
            raise ValueError("Datas inválidas, use formato YYYY-MM-DD")

        try:
            df = self._fetch_data_from_db(start, end, user_id)

            # ================================
            # 1️⃣ KPIs GERAIS
            # ================================
            skus_sem_nicho = df[df["nicho"].isna()]["sku"].unique().tolist()
            kpis_gerais = {
                "faturamento_total": float(df["total_value"].sum()),
                "lucro_bruto_total": float(df["gross_profit"].sum()),
                "lucro_liquido_total": float(df["profit"].sum()),
                "total_pedidos": int(len(df)),
                "total_unidades": int(df["quantity"].sum()),
                "ticket_medio": {
                    "pedido": (
                        float(df["total_value"].sum() / len(df)) if len(df) > 0 else 0
                    ),
                    "unidade": (
                        float(df["total_value"].sum() / df["quantity"].sum())
                        if df["quantity"].sum() > 0
                        else 0
                    ),
                },
                "custos": {
                    "custo_total": float(df["cost"].sum()),
                    "frete_total": float(df["freight"].sum()),
                    "impostos_total": float(df["taxes"].sum()),
                },
                "skus_sem_nicho": skus_sem_nicho,
            }

            # Add indices after kpis_gerais is defined
            kpis_gerais["indices"] = {
                "rentabilidade_media": float(
                    (kpis_gerais["lucro_liquido_total"] / kpis_gerais["faturamento_total"]) * 100
                    if kpis_gerais["faturamento_total"] > 0
                    else 0
                ),
                "profitabilidade_media": float(
                    df["profitability"].fillna(0).mean()
                    if not df["profitability"].isna().all()
                    else 0
                ),
            }

            self.logger.info(
                f"KPIs gerais calculados: faturamento R$ {kpis_gerais['faturamento_total']:.2f}, lucro R$ {kpis_gerais['lucro_liquido_total']:.2f}, {kpis_gerais['total_pedidos']} pedidos"
            )

            # ================================
            # 2️⃣ RELATÓRIOS DIÁRIOS
            # ================================
            relatorios_diarios = []

            for dia, grupo_dia in df.groupby(df["data"].dt.date):
                resumo = {
                    "faturamento": float(grupo_dia["total_value"].sum()),
                    "lucro_bruto": float(grupo_dia["gross_profit"].sum()),
                    "lucro_liquido": float(grupo_dia["profit"].sum()),
                    "total_pedidos": int(len(grupo_dia)),
                    "total_unidades": int(grupo_dia["quantity"].sum()),
                    "ticket_medio": {
                        "pedido": (
                            float(grupo_dia["total_value"].sum() / len(grupo_dia))
                            if len(grupo_dia) > 0
                            else 0
                        ),
                        "unidade": (
                            float(
                                grupo_dia["total_value"].sum()
                                / grupo_dia["quantity"].sum()
                            )
                            if grupo_dia["quantity"].sum() > 0
                            else 0
                        ),
                    },
                }

                # nichos dentro do dia
                nichos = []
                for nicho, grupo_nicho in grupo_dia.groupby("nicho"):
                    nichos.append(
                        {
                            "nicho": nicho if nicho else "Sem nicho",
                            "faturamento": float(grupo_nicho["total_value"].sum()),
                            "lucro_bruto": float(grupo_nicho["gross_profit"].sum()),
                            "profit": float(grupo_nicho["profit"].sum()),
                            "total_pedidos": int(len(grupo_nicho)),
                            "total_unidades": int(grupo_nicho["quantity"].sum()),
                        }
                    )

                relatorios_diarios.append(
                    {"data": str(dia), "resumo": resumo, "nichos": nichos}
                )

            self.logger.info(
                f"Relatórios diários gerados para {len(relatorios_diarios)} dias"
            )

            # ================================
            # 3️⃣ RELATÓRIO POR NICHO GERAL
            # ================================
            por_nicho = (
                df.groupby("nicho")
                .agg(
                    {
                        "profit": "sum",
                        "gross_profit": "sum",
                        "order_id": "count",
                        "quantity": "sum",
                        "total_value": "sum",
                        "freight": "sum",
                        "taxes": "sum",
                        "cost": "sum",
                        "rentability": "mean",
                        "profitability": "mean",
                    }
                )
                .reset_index()
                .rename(
                    columns={
                        "profit": "lucro_liquido",
                        "gross_profit": "lucro_bruto",
                        "order_id": "total_pedidos",
                        "quantity": "total_unidades",
                        "total_value": "faturamento_total",
                    }
                )
            )

            por_nicho["participacao_faturamento"] = (
                por_nicho["faturamento_total"] / kpis_gerais["faturamento_total"]
                if kpis_gerais["faturamento_total"] != 0
                else 0
            )
            por_nicho["participacao_lucro"] = (
                por_nicho["lucro_liquido"] / kpis_gerais["lucro_liquido_total"]
                if kpis_gerais["lucro_liquido_total"] != 0
                else 0
            )
            por_nicho["media_dia_valor"] = por_nicho["faturamento_total"] / dias_totais
            por_nicho["media_dia_unidades"] = por_nicho["total_unidades"] / dias_totais
            por_nicho = self._clean_df_for_json(por_nicho)

            self.logger.info(
                f"Análise por nicho concluída para {len(por_nicho)} nichos"
            )

            # ================================
            # 4️⃣ RELATÓRIO POR SKU
            # ================================
            por_sku = (
                df.groupby(["sku", "nicho"])
                .agg(
                    {
                        "profit": "sum",
                        "gross_profit": "sum",
                        "order_id": "count",
                        "quantity": "sum",
                        "total_value": "sum",
                    }
                )
                .reset_index()
                .rename(
                    columns={
                        "profit": "lucro_liquido",
                        "gross_profit": "lucro_bruto",
                        "order_id": "total_pedidos",
                        "quantity": "total_unidades",
                        "total_value": "faturamento_total",
                    }
                )
            )
            por_sku = self._clean_df_for_json(por_sku)

            self.logger.info(f"Análise por SKU concluída para {len(por_sku)} SKUs")

            # ================================
            # 4.5️⃣ AGREGADOS POR HORA E DIA DA SEMANA
            # ================================
            por_hora = (
                df.groupby("hour")
                .agg({"profit": "sum", "total_value": "sum", "order_id": "count"})
                .reset_index()
                .rename(
                    columns={
                        "profit": "lucro_liquido",
                        "total_value": "faturamento",
                        "order_id": "total_pedidos",
                    }
                )
            )
            por_hora = self._clean_df_for_json(por_hora)

            por_dia_semana = (
                df.groupby("weekday")
                .agg({"profit": "sum", "total_value": "sum", "order_id": "count"})
                .reset_index()
                .rename(
                    columns={
                        "profit": "lucro_liquido",
                        "total_value": "faturamento",
                        "order_id": "total_pedidos",
                    }
                )
            )
            por_dia_semana = self._clean_df_for_json(por_dia_semana)

            self.logger.info("Agregados por hora e dia da semana calculados")

            # ================================
            # 4.6️⃣ LISTA DE PEDIDOS
            # ================================
            pedidos_lista = df.sort_values("data", ascending=False)[
                [
                    "data",
                    "order_id",
                    "cart_id",
                    "sku",
                    "title",
                    "quantity",
                    "total_value",
                    "profit",
                    "nicho",
                    "hour",
                ]
            ].to_dict(orient="records")

            self.logger.info(
                f"Lista de pedidos gerada com {len(pedidos_lista)} entradas"
            )



            # ================================
            # 6️⃣ RANKINGS
            # ================================
            top_ads = (
                df.groupby("ad")
                .agg({"profit": "sum", "gross_profit": "sum"})
                .sort_values("profit", ascending=False)
                .head(TOP_ADS_LIMIT)
                .reset_index()
            )
            top_skus = (
                df.groupby("sku")
                .agg({"profit": "sum", "gross_profit": "sum"})
                .sort_values("profit", ascending=False)
                .head(TOP_SKUS_LIMIT)
                .reset_index()
            )
            top_por_nicho = (
                df.groupby(["nicho", "sku"])
                .agg({"profit": "sum", "gross_profit": "sum"})
                .sort_values(["nicho", "profit"], ascending=[True, False])
                .groupby(level=0)
                .head(TOP_PER_NICHO_LIMIT)
                .reset_index()
            )

            # Top SKUs per niche
            top_skus_per_nicho = {}
            for nicho in top_por_nicho["nicho"].unique():
                nicho_skus = top_por_nicho[top_por_nicho["nicho"] == nicho].to_dict(
                    orient="records"
                )
                top_skus_per_nicho[nicho] = nicho_skus

            self.logger.info(
                f"Rankings calculados: {len(top_skus)} top SKUs, {len(top_ads)} top anúncios, {len(top_por_nicho)} por nicho, top skus per nicho: {len(top_skus_per_nicho)}"
            )

            self.logger.info("Relatório flex gerado com sucesso")

            return {
                "periodo": {
                    "inicio": start.strftime("%Y-%m-%d"),
                    "fim": end.strftime("%Y-%m-%d"),
                    "dias_totais": dias_totais,
                },
                "kpis_gerais": kpis_gerais,
                "relatorios": {
                    "diario": relatorios_diarios,
                    "por_nicho": por_nicho.to_dict(orient="records"),
                    "por_sku": por_sku.to_dict(orient="records"),
                    "por_hora": por_hora.to_dict(orient="records"),
                    "por_dia_semana": por_dia_semana.to_dict(orient="records"),
                    "pedidos_lista": pedidos_lista,
                },
                "rankings": {
                    "top_ads": top_ads.to_dict(orient="records"),
                    "top_skus": top_skus.to_dict(orient="records"),
                    "top_por_nicho": top_por_nicho.to_dict(orient="records"),
                    "top_skus_per_nicho": top_skus_per_nicho,
                },
            }

        except Exception as e:
            self.logger.exception("Erro ao gerar relatório flex")
            raise
