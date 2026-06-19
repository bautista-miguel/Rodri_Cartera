from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from market_data import Quote, get_history, get_quote
from portfolio_data import PORTFOLIOS

st.set_page_config(page_title="Carteras Rodrigo Miguel", page_icon="📈", layout="wide")


@st.cache_data(ttl=900, show_spinner=False)
def cached_quote(symbol: str) -> Quote:
    return get_quote(symbol)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_history(symbol: str, start: str) -> pd.Series:
    return get_history(symbol, start)


def money(value: float) -> str:
    return f"${value:,.0f}".replace(",", ".")


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value:.2%}"


def colored_metric(container, label: str, value: float | None) -> None:
    if value is None or pd.isna(value):
        color = "#6b7280"
        formatted = "—"
    elif value > 0:
        color = "#16a34a"
        formatted = f"{value:.2%}"
    elif value < 0:
        color = "#dc2626"
        formatted = f"{value:.2%}"
    else:
        color = "#374151"
        formatted = f"{value:.2%}"

    html = (
        '<div style="padding-top: 0.1rem;">'
        f'<div style="font-size: 1rem; color: #4b5563; margin-bottom: 0.35rem;">{label}</div>'
        f'<div style="font-size: 2.55rem; line-height: 1.15; color: {color}; font-weight: 500;">{formatted}</div>'
        '</div>'
    )
    container.markdown(html, unsafe_allow_html=True)


def benchmark_return_from_start(symbol: str, start_date: str) -> tuple[float | None, float | None, pd.Timestamp | None]:
    start = pd.Timestamp(start_date)
    history_start = (start - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
    history = cached_history(symbol, history_start)
    if history.empty:
        return None, None, None

    history = history.sort_index()
    tz = getattr(history.index, "tz", None)
    comparison_start = start.tz_localize(tz) if tz is not None and start.tzinfo is None else start
    eligible = history.loc[history.index >= comparison_start]
    if eligible.empty:
        return None, None, None

    initial_price = float(eligible.iloc[0])
    current_price = float(history.iloc[-1])
    if initial_price == 0:
        return None, initial_price, pd.Timestamp(eligible.index[0])
    return current_price / initial_price - 1, initial_price, pd.Timestamp(eligible.index[0])


def calculate_position(position: dict[str, Any], ccl: float) -> dict[str, Any]:
    method = position["method"]
    qty = float(position["quantity"])
    buy_price = float(position["buy_price"])
    source_symbol = position.get("yf_local") or position.get("yf_underlying")
    quote = cached_quote(source_symbol)

    invested = float(position.get("invested_ars", 0.0))
    current_value = None
    current_unit_price = None
    total_return = None

    if method == "local":
        invested = invested or qty * buy_price
        current_unit_price = quote.price
        if quote.price is not None:
            current_value = qty * quote.price
            total_return = current_value / invested - 1 if invested else None
        method_label = "Precio local Yahoo (.BA)"

    elif method == "underlying_ratio_ccl":
        ratio = float(position["ratio"])
        invested = invested or qty * buy_price * ccl
        if quote.price is not None:
            current_unit_price = quote.price / ratio
            current_value = qty * current_unit_price * ccl
            total_return = current_value / invested - 1 if invested else None
        method_label = "Subyacente USD ÷ ratio × CCL"

    elif method == "return_on_invested":
        invested = float(position["invested_ars"])
        current_unit_price = quote.price
        if quote.price is not None:
            total_return = quote.price / buy_price - 1
            current_value = invested * (1 + total_return)
        method_label = "Variación del subyacente sobre monto invertido"

    else:
        raise ValueError(f"Método desconocido: {method}")

    return {
        "Ticker": position["ticker"],
        "Instrumento": position["name"],
        "Cantidad": qty,
        "Fecha compra": pd.to_datetime(position["buy_date"]).date(),
        "Precio compra": buy_price,
        "Precio actual": current_unit_price,
        "Invertido ARS": invested,
        "Valor actual ARS": current_value,
        "Resultado ARS": None if current_value is None else current_value - invested,
        "Resultado %": total_return,
        "Variación diaria": quote.daily_change,
        "Método": method_label,
        "Fuente": source_symbol,
        "Último dato": quote.timestamp,
        "Error": quote.error,
    }


def portfolio_frame(config: dict[str, Any], ccl: float) -> pd.DataFrame:
    return pd.DataFrame([calculate_position(p, ccl) for p in config["positions"]])


def render_portfolio(config: dict[str, Any], ccl: float) -> None:
    with st.spinner("Consultando precios..."):
        df = portfolio_frame(config, ccl)

    valid = df["Valor actual ARS"].notna()
    invested_positions = float(df["Invertido ARS"].sum())
    current_positions = float(df.loc[valid, "Valor actual ARS"].sum())
    cash = float(config.get("cash_ars", 0.0))
    invested_total = invested_positions + cash
    current_total = current_positions + cash
    return_total = current_total / invested_total - 1 if invested_total else 0.0

    df["Peso actual"] = df["Valor actual ARS"] / current_total
    df["Aporte diario"] = df["Peso actual"] * df["Variación diaria"]
    daily_return = df["Aporte diario"].sum(min_count=1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Invertido", money(invested_total))
    c2.metric("Valor actual", money(current_total), money(current_total - invested_total))
    colored_metric(c3, "Rendimiento total", return_total)
    colored_metric(c4, "Variación diaria", None if pd.isna(daily_return) else float(daily_return))

    if (~valid).any():
        missing = ", ".join(df.loc[~valid, "Ticker"].astype(str))
        st.warning(f"No se pudieron obtener precios para: {missing}. No están incluidos en el valor actual mostrado.")

    summary_tab, charts_tab, detail_tab, diagnostics_tab = st.tabs(
        ["Resumen", "Gráficos de precios", "Posiciones", "Diagnóstico de precios"]
    )

    with summary_tab:
        st.subheader("Composición actual")
        composition = df.loc[valid, ["Ticker", "Valor actual ARS"]].copy()
        if cash > 0:
            composition = pd.concat([
                composition,
                pd.DataFrame([{"Ticker": "Efectivo", "Valor actual ARS": cash}]),
            ], ignore_index=True)
        fig_pie = px.pie(
            composition,
            names="Ticker",
            values="Valor actual ARS",
            hole=0.35,
        )
        fig_pie.update_traces(
            textposition="inside",
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Valor: $%{value:,.0f}<br>Peso: %{percent}<extra></extra>",
        )
        fig_pie.update_layout(
            height=520,
            margin=dict(l=20, r=20, t=20, b=20),
            legend_title_text="Posiciones",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        benchmark_symbol = config["benchmark"]["symbol"]
        benchmark_return, benchmark_start_price, benchmark_start_date = benchmark_return_from_start(
            benchmark_symbol, config["start_date"]
        )
        st.subheader("Comparación")
        b1, b2 = st.columns(2)
        colored_metric(b1, "Cartera desde inicio", return_total)
        colored_metric(b2, f"{benchmark_symbol} desde inicio", benchmark_return)
        if benchmark_start_price is None:
            st.caption(f"No se pudo obtener el histórico de {benchmark_symbol} desde {config['start_date']}.")
        else:
            st.caption(
                f"Benchmark calculado desde el primer cierre disponible de {benchmark_symbol} "
                f"a partir del {pd.Timestamp(config['start_date']).strftime('%d/%m/%Y')}: "
                f"${benchmark_start_price:,.2f} ({benchmark_start_date.strftime('%d/%m/%Y')})."
            )

    with charts_tab:
        st.subheader("Evolución del precio y punto de entrada")
        selected_ticker = st.selectbox(
            "Elegí una posición",
            options=[p["ticker"] for p in config["positions"]],
            key=f"chart_selector_{config['start_date']}",
        )
        position = next(p for p in config["positions"] if p["ticker"] == selected_ticker)
        symbol = position.get("yf_local") or position.get("yf_underlying")
        buy_date = pd.Timestamp(position["buy_date"])
        history_start = (buy_date - pd.Timedelta(days=45)).strftime("%Y-%m-%d")
        history = cached_history(symbol, history_start)

        if history.empty:
            st.warning(f"Yahoo Finance no devolvió historial para {symbol}.")
        else:
            plotted = history.copy()
            unit_label = "ARS por unidad"
            if position["method"] == "underlying_ratio_ccl":
                plotted = plotted / float(position["ratio"])
                unit_label = "USD por CEDEAR equivalente"
            elif position["method"] == "return_on_invested":
                unit_label = "USD del subyacente"

            chart_df = plotted.rename("Precio").reset_index()
            date_col = chart_df.columns[0]
            chart_df = chart_df.rename(columns={date_col: "Fecha"})
            entry_price = float(position["buy_price"])

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=chart_df["Fecha"],
                y=chart_df["Precio"],
                mode="lines",
                name="Precio",
                line=dict(width=2.5),
                hovertemplate="%{x|%d/%m/%Y}<br>Precio: %{y:,.2f}<extra></extra>",
            ))
            fig.add_hline(
                y=entry_price,
                line_dash="dash",
                annotation_text=f"Precio de entrada: {entry_price:,.2f}",
                annotation_position="top left",
            )
            fig.add_vline(
                x=buy_date.timestamp() * 1000,
                line_dash="dot",
                annotation_text=f"Compra: {buy_date.strftime('%d/%m/%Y')}",
                annotation_position="top right",
            )
            fig.add_trace(go.Scatter(
                x=[buy_date],
                y=[entry_price],
                mode="markers",
                name="Entrada",
                marker=dict(size=12, symbol="diamond"),
                hovertemplate=(
                    f"Entrada<br>{buy_date.strftime('%d/%m/%Y')}<br>"
                    f"Precio: {entry_price:,.2f}<extra></extra>"
                ),
            ))
            fig.update_layout(
                title=f"{position['name']} ({symbol})",
                xaxis_title="Fecha",
                yaxis_title=unit_label,
                height=560,
                hovermode="x unified",
                margin=dict(l=20, r=20, t=60, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "La línea horizontal marca el precio registrado de compra y la línea vertical la fecha de entrada."
            )

    with detail_tab:
        display = df.copy()
        for col in ["Precio compra", "Precio actual", "Invertido ARS", "Valor actual ARS", "Resultado ARS"]:
            display[col] = display[col].map(lambda x: "—" if pd.isna(x) else f"{x:,.2f}")
        for col in ["Resultado %", "Variación diaria", "Peso actual"]:
            display[col] = display[col].map(lambda x: "—" if pd.isna(x) else f"{x:.2%}")
        st.dataframe(
            display[[
                "Ticker", "Instrumento", "Cantidad", "Fecha compra", "Precio compra",
                "Precio actual", "Invertido ARS", "Valor actual ARS", "Resultado ARS",
                "Resultado %", "Variación diaria", "Peso actual"
            ]],
            hide_index=True,
            use_container_width=True,
        )

    with diagnostics_tab:
        st.caption("Esta tabla permite verificar de dónde sale cada precio y detectar fallas de Yahoo Finance.")
        diag = df[["Ticker", "Método", "Fuente", "Último dato", "Error"]].copy()
        diag["Estado"] = diag["Error"].apply(lambda x: "OK" if not x else "Error")
        st.dataframe(
            diag[["Ticker", "Método", "Fuente", "Último dato", "Estado", "Error"]],
            hide_index=True,
            use_container_width=True,
        )


st.title("Carteras de Rodrigo Miguel")
st.caption("Primera versión basada en el Excel original. Los métodos de valuación se mantienen explícitos.")

with st.sidebar:
    ccl = st.number_input("CCL utilizado", min_value=1.0, value=1480.0, step=10.0)
    st.caption("El CCL solo afecta las posiciones valuadas en USD/ratio.")
    if st.button("Actualizar precios"):
        st.cache_data.clear()
        st.rerun()

principal_tab, chica_tab = st.tabs(["Cartera principal", "Cartera chica"])

with principal_tab:
    render_portfolio(PORTFOLIOS["Cartera principal"], ccl)

with chica_tab:
    render_portfolio(PORTFOLIOS["Cartera chica"], ccl)

st.divider()
st.caption("Pendiente para la siguiente iteración: persistencia de históricos, autenticación y actualización automática del CCL.")
