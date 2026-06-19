# Carteras Rodrigo Miguel

Primera app Streamlit basada en `Portfolio Rodrigo Miguel.xlsx`.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estructura

- `app.py`: interfaz y cálculos.
- `portfolio_data.py`: posiciones extraídas del Excel.
- `market_data.py`: consultas a Yahoo Finance mediante `yfinance`.

## Métodos de valuación

- `local`: ticker argentino con sufijo `.BA`.
- `underlying_ratio_ccl`: precio del subyacente en USD dividido por ratio y convertido con CCL.
- `return_on_invested`: aplica la variación del subyacente al monto originalmente invertido, replicando la lógica usada para GOOGL en el Excel.
