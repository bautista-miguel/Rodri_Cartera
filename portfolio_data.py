from __future__ import annotations

PORTFOLIOS = {
    "Cartera chica": {
        "initial_capital_ars": 2_000_000.0,
        "cash_ars": 8_650.0,
        "start_date": "2026-04-23",
        "benchmark": {"symbol": "SPY.BA", "start_price": 7138.0},
        "positions": [
            {"ticker": "NOW", "name": "ServiceNow", "quantity": 460, "buy_price": 868.5, "buy_date": "2026-05-21", "method": "local", "yf_local": "NOW.BA"},
            {"ticker": "MELI", "name": "MercadoLibre", "quantity": 25, "buy_price": 19480.0, "buy_date": "2026-05-19", "method": "local", "yf_local": "MELI.BA"},
            {"ticker": "AMAT", "name": "Applied Materials", "quantity": 3, "buy_price": 126375.0, "buy_date": "2026-05-13", "method": "local", "yf_local": "AMAT.BA"},
            {"ticker": "MRVL", "name": "Marvell Technology", "quantity": 6, "buy_price": 19890.0, "buy_date": "2026-05-15", "method": "local", "yf_local": "MRVL.BA"},
            {"ticker": "PAMP", "name": "Pampa Energía", "quantity": 100, "buy_price": 4970.0, "buy_date": "2026-04-29", "method": "local", "yf_local": "PAMP.BA"},
            {"ticker": "GGAL", "name": "Grupo Financiero Galicia", "quantity": 11, "buy_price": 6450.0, "buy_date": "2026-04-23", "method": "local", "yf_local": "GGAL.BA"},
        ],
    },
    "Cartera principal": {
        "initial_capital_ars": None,
        "cash_ars": 0.0,
        "start_date": "2026-06-02",
        "benchmark": {"symbol": "SPY.BA", "start_price": 7615.0},
        "positions": [
            {"ticker": "MELI", "name": "MercadoLibre CEDEAR", "quantity": 846, "buy_price": 21260.0, "buy_date": "2026-06-02", "method": "local", "yf_local": "MELI.BA"},
            {"ticker": "ASML", "name": "ASML CEDEAR", "quantity": 1155, "buy_price": 17320.0, "buy_date": "2026-06-02", "method": "local", "yf_local": "ASML.BA", "ratio": 146.0},
            {"ticker": "GOOGL", "name": "Alphabet — retorno del subyacente", "quantity": 2259, "buy_price": 363.5, "invested_ars": 21_528_000.0, "buy_date": "2026-06-02", "method": "return_on_invested", "yf_underlying": "GOOGL", "ratio": 58.0},
            {"ticker": "NU", "name": "Nu Holdings CEDEAR", "quantity": 570, "buy_price": 8735.0, "buy_date": "2026-06-02", "method": "local", "yf_local": "NU.BA", "ratio": 2.0},
            {"ticker": "ASML USD", "name": "ASML valuado en USD/ratio", "quantity": 247, "buy_price": 12.11, "buy_date": "2026-06-05", "method": "underlying_ratio_ccl", "yf_underlying": "ASML", "ratio": 146.0},
            {"ticker": "IBIT", "name": "iShares Bitcoin Trust / ratio", "quantity": 5361, "buy_price": 3.735, "buy_date": "2026-06-12", "method": "underlying_ratio_ccl", "yf_underlying": "IBIT", "ratio": 9.68},
        ],
    },
}
