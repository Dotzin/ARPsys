"""Constants used throughout the application."""

# Report limits
TOP_NICHOS_LIMIT = 10
TOP_SKUS_LIMIT = 10
TOP_ADS_LIMIT = 30
TOP_PER_NICHO_LIMIT = 15
LAST_SALES_LIMIT = 15

# API settings
API_BASE_URL = "https://app.arpcommerce.com.br"
API_SELLS_ENDPOINT = "/sells"

# Timezone adjustment (hours)
API_TIMEZONE_OFFSET = 3  # BRT is UTC-3

# Update intervals (seconds)
REPORT_UPDATE_INTERVAL = 3600  # 1 hour

# File paths
DATABASE_PATH = "database.db"
ML_MODEL_PATH = "models/profit_forecast_model.pkl"
