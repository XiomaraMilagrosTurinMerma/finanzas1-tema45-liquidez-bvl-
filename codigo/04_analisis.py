# Nombres y apellidos: Turin Merma Xiomara Milagros
# Codigo de matricula: 2024200535B
# Tema 45 - Liquidez bursatil y rendimiento de las acciones en la Bolsa de Valores de Lima
# Fecha de extraccion: 2026-09-25

"""
04_analisis.py
Responde la pregunta: ¿la iliquidez es un factor de riesgo remunerado en la BVL?
Pasos: (1) datos diarios -> mensuales; (2) estadística descriptiva por emisora;
(3) carteras por terciles de iliquidez (Amihud, 2002); (4) regresiones de
Fama-MacBeth y panel con errores agrupados; (5) figuras.
Todo se genera desde datos_procesados y se guarda en /salidas (CSV + LaTeX + PNG).
"""

# ============================================================
# BLOQUE 1. Librerías, rutas y parámetros
# ============================================================
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

CODIGO = "2024200535B"
RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_PROC = RAIZ / "datos_procesados" / f"datos_procesados_{CODIGO}.csv"
SALIDAS = RAIZ / "salidas"
ARCHIVO_LOG = RAIZ / "log_ejecucion.txt"
SALIDAS.mkdir(exist_ok=True)

N_GRUPOS = 3          # terciles de iliquidez
MIN_ACCIONES_MES = 9  # mínimo de emisoras por mes para armar carteras
plt.rcParams.update({"font.size": 10, "figure.dpi": 110})


def escribir_log(mensaje):
    """Escribe una línea con fecha y hora en log_ejecucion.txt y en la consola."""
    linea = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")


def guardar_tabla(df, nombre, decimales=4):
    """Guarda una tabla en CSV y en LaTeX (booktabs) para insertarla en el artículo."""
    df.to_csv(SALIDAS / f"{nombre}.csv", encoding="utf-8")
    df_tex = df.copy()
    for c in df_tex.columns:
        if pd.api.types.is_float_dtype(df_tex[c]):
            df_tex[c] = df_tex[c].map(lambda x: "" if pd.isna(x) else f"{x:,.{decimales}f}")
    encabezado = [df_tex.index.name or ""] + [str(c) for c in df_tex.columns]
    lineas = ["\\begin{tabular}{l" + "r" * len(df_tex.columns) + "}", "\\toprule",
              " & ".join(encabezado) + " \\\\", "\\midrule"]
    for idx, fila in df_tex.iterrows():
        lineas.append(" & ".join([str(idx)] + [str(v) for v in fila.values]) + " \\\\")
    lineas += ["\\bottomrule", "\\end{tabular}"]
    texto = "\n".join(lineas).replace("%", "\\%").replace("_", "\\_")
    (SALIDAS / f"{nombre}.tex").write_text(texto, encoding="utf-8")


def t_estadistico(serie):
    """t de Student de la media de una serie de tiempo."""
    serie = serie.dropna()
    return serie.mean() / (serie.std(ddof=1) / np.sqrt(len(serie)))


escribir_log("INICIO analisis")

# ============================================================
# BLOQUE 2. De datos diarios a mensuales
# ============================================================
d = pd.read_csv(ARCHIVO_PROC, parse_dates=["fecha"])
d["mes"] = d["fecha"].dt.to_period("M")

mensual = d.groupby(["ticker", "mes"]).agg(
    retorno_mes=("retorno", lambda r: (1 + r.dropna()).prod() - 1),
    amihud_mes=("amihud", "mean"),
    frec_negociacion=("negociado", "mean"),
    monto_mes_millones=("monto_negociado_soles", lambda m: m.sum() / 1e6),
    dias=("fecha", "count"),
).reset_index().sort_values(["ticker", "mes"])

# Características del mes anterior (para predecir el retorno del mes siguiente)
grupo = mensual.groupby("ticker")
mensual["amihud_lag"] = grupo["amihud_mes"].shift(1)
mensual["frec_lag"] = grupo["frec_negociacion"].shift(1)
mensual.to_csv(SALIDAS / "panel_mensual.csv", index=False, encoding="utf-8")
escribir_log(f"Panel mensual: {len(mensual)} observaciones empresa-mes")

# ============================================================
# BLOQUE 3. Tabla 1: estadística descriptiva por emisora
# ============================================================
tabla1 = d.groupby("ticker").agg(
    dias=("fecha", "count"),
    pct_dias_negociados=("negociado", lambda x: 100 * x.mean()),
    monto_diario_prom_mill=("monto_negociado_soles", lambda m: m.mean() / 1e6),
    amihud_prom=("amihud", "mean"),
)
tabla1["retorno_mensual_prom_pct"] = 100 * mensual.groupby("ticker")["retorno_mes"].mean()
tabla1 = tabla1.sort_values("amihud_prom")
tabla1.index.name = "Emisora"
guardar_tabla(tabla1, "tabla1_descriptiva_emisoras", decimales=3)

# ============================================================
# BLOQUE 4. Tabla 2: carteras por terciles de iliquidez
# Cada mes se ordenan las emisoras por su Amihud del mes anterior.
# ============================================================
m = mensual.dropna(subset=["amihud_lag", "retorno_mes"]).copy()
m = m[m.groupby("mes")["ticker"].transform("count") >= MIN_ACCIONES_MES]
m["cartera"] = m.groupby("mes")["amihud_lag"].transform(
    lambda x: pd.qcut(x.rank(method="first"), N_GRUPOS, labels=False) + 1)

carteras = m.groupby(["mes", "cartera"])["retorno_mes"].mean().unstack()
carteras.columns = ["C1_liquida", "C2_intermedia", "C3_iliquida"]
carteras["C3_menos_C1"] = carteras["C3_iliquida"] - carteras["C1_liquida"]
carteras.to_csv(SALIDAS / "retornos_carteras_mensuales.csv", encoding="utf-8")

tabla2 = pd.DataFrame({
    "Retorno mensual promedio (%)": 100 * carteras.mean(),
    "Estadistico t": carteras.apply(t_estadistico),
    "Meses": carteras.count(),
})
carac = m.groupby("cartera")[["amihud_lag", "frec_lag"]].mean()
tabla2.loc[carteras.columns[:3], "Amihud promedio"] = carac["amihud_lag"].values
tabla2.loc[carteras.columns[:3], "Frec. negociacion (%)"] = 100 * carac["frec_lag"].values
tabla2.index.name = "Cartera"
guardar_tabla(tabla2, "tabla2_carteras_iliquidez", decimales=3)

# ============================================================
# BLOQUE 5. Tabla 3: regresiones
# (a) Fama-MacBeth: una regresión de corte transversal por mes y promedio
# (b) Panel MCO con errores estándar agrupados por emisora (robustez)
# ============================================================
m["retorno_pct"] = 100 * m["retorno_mes"]
m["frec_lag_pct"] = 100 * m["frec_lag"]
formula = "retorno_pct ~ amihud_lag + frec_lag_pct"

coefs = []
for mes, corte in m.groupby("mes"):
    if len(corte) >= MIN_ACCIONES_MES:
        coefs.append(smf.ols(formula, data=corte).fit().params.rename(str(mes)))
coefs = pd.DataFrame(coefs)
fm = pd.DataFrame({"Coef. Fama-MacBeth": coefs.mean(), "t (FM)": coefs.apply(t_estadistico)})

panel = smf.ols(formula, data=m).fit(cov_type="cluster", cov_kwds={"groups": m["ticker"]})
fm["Coef. panel MCO"] = panel.params
fm["t (panel, cluster)"] = panel.tvalues
fm.index = ["Constante", "Iliquidez de Amihud (t-1)", "Frec. de negociacion % (t-1)"]
fm.index.name = "Variable"
guardar_tabla(fm, "tabla3_regresiones", decimales=4)
(SALIDAS / "tabla3_panel_detalle.txt").write_text(panel.summary().as_text(), encoding="utf-8")

# ============================================================
# BLOQUE 6. Figuras
# ============================================================
# Figura 1: iliquidez promedio del mercado en el tiempo
fig, ax = plt.subplots(figsize=(8, 3.5))
serie = mensual.groupby("mes")["amihud_mes"].mean()
ax.plot(serie.index.to_timestamp(), serie.values, color="#1f4e79")
ax.set_ylabel("Amihud promedio")
ax.set_xlabel("Mes")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(SALIDAS / "fig1_amihud_tiempo.png", dpi=300)
plt.close(fig)

# Figura 2: porcentaje de días negociados por emisora
fig, ax = plt.subplots(figsize=(8, 5))
frec = tabla1["pct_dias_negociados"].sort_values()
ax.barh(frec.index, frec.values, color="#2e75b6")
ax.set_xlabel("Días con negociación (%)")
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig(SALIDAS / "fig2_frecuencia_negociacion.png", dpi=300)
plt.close(fig)

# Figura 3: valor acumulado de S/ 1 invertido en cada cartera
fig, ax = plt.subplots(figsize=(8, 3.5))
acum = (1 + carteras[["C1_liquida", "C2_intermedia", "C3_iliquida"]].fillna(0)).cumprod()
for col, color in zip(acum.columns, ["#1f4e79", "#7f7f7f", "#c00000"]):
    ax.plot(acum.index.to_timestamp(), acum[col], label=col.replace("_", " "), color=color)
ax.set_ylabel("Valor de S/ 1 invertido")
ax.legend(frameon=False)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(SALIDAS / "fig3_carteras_acumulado.png", dpi=300)
plt.close(fig)

# Figura 4: iliquidez frente a retorno promedio por emisora (eje X logarítmico)
fig, ax = plt.subplots(figsize=(7, 5))
ax.scatter(tabla1["amihud_prom"], tabla1["retorno_mensual_prom_pct"], color="#1f4e79", s=25)
ax.set_xscale("log")
ax.set_xticks([0.02, 0.05, 0.1, 0.2, 0.5])
ax.set_xticklabels(["0.02", "0.05", "0.1", "0.2", "0.5"])
# Posición de cada etiqueta (desplazamiento x, desplazamiento y, alineación) para que no se enciman
ajustes = {"FERREYC1": (5, 4, "left"), "BAP": (-5, -3, "right"), "ALICORC1": (-5, -3, "right"),
           "INRETC1": (-5, -3, "right"), "VOLCABC1": (5, -3, "left"), "BBVAC1": (-5, -3, "right"),
           "CPACASC1": (5, 2, "left"), "CVERDEC1": (-5, -3, "right"), "IFS": (5, 2, "left"),
           "BACKUSI1": (-5, -10, "right"), "LUSURC1": (5, -3, "left"), "CREDITC1": (-5, 3, "right"),
           "SCOTIAC1": (-5, -3, "right"), "NEXAPEC1": (5, 3, "left"), "INTERBC1": (0, -11, "center"),
           "AUSTRAC1": (-5, -3, "right"), "ATACOBC1": (-5, -3, "right")}
for tk, fila in tabla1.iterrows():
    dx, dy, ha = ajustes.get(tk, (5, -3, "left"))
    ax.annotate(tk, (fila["amihud_prom"], fila["retorno_mensual_prom_pct"]), xytext=(dx, dy),
                textcoords="offset points", fontsize=7, ha=ha)
ax.set_xlabel("Amihud promedio (escala logarítmica)")
ax.set_ylabel("Retorno mensual promedio (%)")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(SALIDAS / "fig4_amihud_vs_retorno.png", dpi=300)
plt.close(fig)

# ============================================================
# BLOQUE 7. Resumen
# ============================================================
escribir_log(f"FIN analisis | {len(list(SALIDAS.iterdir()))} archivos en /salidas")
pd.set_option("display.width", 140)
print("\n===== TABLA 1: DESCRIPTIVA POR EMISORA =====")
print(tabla1.round(3).to_string())
print("\n===== TABLA 2: CARTERAS POR ILIQUIDEZ =====")
print(tabla2.round(3).to_string())
print("\n===== TABLA 3: REGRESIONES =====")
print(fm.round(4).to_string())