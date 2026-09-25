# Nombres y apellidos: Turin Merma Xiomara Milagros
# Codigo de matricula: 2024200535B
# Tema 45 - Liquidez bursatil y rendimiento de las acciones en la Bolsa de Valores de Lima
# Fecha de extraccion: 2026-09-25

"""
03_limpieza_datos.py
Limpia los dos archivos crudos, los une por la llave común (ticker + fecha)
y calcula las variables del estudio. Genera datos_procesados_<codigo>.csv.
Los archivos crudos NO se modifican: solo se leen.
"""

# ============================================================
# BLOQUE 1. Librerías y rutas relativas
# ============================================================
import hashlib
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

CODIGO = "2024200535B"
RAIZ = Path(__file__).resolve().parent.parent
CRUDO_YAHOO = RAIZ / "datos_crudos" / f"datos_crudos_{CODIGO}_yahoo.csv"
CRUDO_BVL = RAIZ / "datos_crudos" / f"datos_crudos_{CODIGO}_bvl.csv"
CARPETA_PROC = RAIZ / "datos_procesados"
ARCHIVO_PROC = CARPETA_PROC / f"datos_procesados_{CODIGO}.csv"
ARCHIVO_LOG = RAIZ / "log_ejecucion.txt"
CARPETA_PROC.mkdir(exist_ok=True)

LIMITE_RETORNO = 0.50   # retornos diarios mayores a ±50 % se tratan como error de dato
PERCENTIL_WINSOR = 0.01 # la iliquidez de Amihud se recorta al 1 % y 99 %


def escribir_log(mensaje):
    """Escribe una línea con fecha y hora en log_ejecucion.txt y en la consola."""
    linea = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")


escribir_log("INICIO limpieza de datos")

# ============================================================
# BLOQUE 2. Fuente 1: Yahoo Finance (de aquí sale el RETORNO)
# ============================================================
yahoo = pd.read_csv(CRUDO_YAHOO)
col_precio = "Adj Close" if "Adj Close" in yahoo.columns else "Close"
yahoo = yahoo.rename(columns={"Date": "fecha", col_precio: "precio_ajustado_yahoo",
                              "Volume": "volumen_yahoo"})
yahoo["ticker"] = yahoo["ticker"].str.replace(".LM", "", regex=False)  # BAP.LM -> BAP
yahoo["fecha"] = pd.to_datetime(yahoo["fecha"])
yahoo = yahoo[["ticker", "fecha", "precio_ajustado_yahoo", "volumen_yahoo"]]

# Retorno diario simple con el precio ajustado (incluye dividendos)
yahoo = yahoo.sort_values(["ticker", "fecha"]).drop_duplicates(["ticker", "fecha"])
yahoo["retorno"] = yahoo.groupby("ticker")["precio_ajustado_yahoo"].pct_change(fill_method=None)

# ============================================================
# BLOQUE 3. Fuente 2: BVL (de aquí salen VOLUMEN, MONTO y NEGOCIACIÓN)
# ============================================================
bvl = pd.read_csv(CRUDO_BVL)
bvl = bvl.rename(columns={
    "nemonico": "ticker", "date": "fecha", "close": "precio_cierre_bvl",
    "quantityNegotiated": "acciones_negociadas",
    "solAmountNegotiated": "monto_negociado_soles",
})
bvl["fecha"] = pd.to_datetime(bvl["fecha"])
bvl = bvl[["ticker", "fecha", "precio_cierre_bvl", "acciones_negociadas", "monto_negociado_soles"]]
bvl = bvl.drop_duplicates(["ticker", "fecha"])

# En los días sin negociación la BVL registra precio 0: no es un precio real
ceros = (bvl["precio_cierre_bvl"] == 0).sum()
bvl["precio_cierre_bvl"] = bvl["precio_cierre_bvl"].replace(0, np.nan)
escribir_log(f"BVL: {ceros} precios de cierre en 0 (dias sin negociacion) convertidos a vacio")

# Variable binaria: 1 si la acción se negoció ese día, 0 si no
bvl["negociado"] = (bvl["acciones_negociadas"] > 0).astype(int)

# ============================================================
# BLOQUE 4. Unión de las dos fuentes por la llave ticker + fecha
# ============================================================
datos = pd.merge(yahoo, bvl, on=["ticker", "fecha"], how="inner")
escribir_log(f"Union: Yahoo {len(yahoo)} filas + BVL {len(bvl)} filas -> {len(datos)} filas comunes")

# ============================================================
# BLOQUE 5. Tratamiento de outliers y cálculo de la iliquidez de Amihud
# ============================================================
extremos = (datos["retorno"].abs() > LIMITE_RETORNO).sum()
datos.loc[datos["retorno"].abs() > LIMITE_RETORNO, "retorno"] = np.nan
escribir_log(f"Retornos mayores a +/-{LIMITE_RETORNO:.0%} tratados como error: {extremos}")

# Amihud = |retorno| / monto negociado (en millones de soles). Solo días con negociación.
con_monto = datos["monto_negociado_soles"] > 0
datos["amihud"] = np.nan
datos.loc[con_monto, "amihud"] = (datos.loc[con_monto, "retorno"].abs()
                                  / (datos.loc[con_monto, "monto_negociado_soles"] / 1e6))
inf, sup = datos["amihud"].quantile([PERCENTIL_WINSOR, 1 - PERCENTIL_WINSOR])
datos["amihud"] = datos["amihud"].clip(inf, sup)

# ============================================================
# BLOQUE 6. Orden final, guardado y hash SHA-256
# ============================================================
datos["fecha"] = datos["fecha"].dt.strftime("%Y-%m-%d")
columnas = ["ticker", "fecha", "retorno", "precio_ajustado_yahoo", "volumen_yahoo",
            "precio_cierre_bvl", "acciones_negociadas", "monto_negociado_soles",
            "negociado", "amihud"]
datos = datos[columnas].sort_values(["ticker", "fecha"]).reset_index(drop=True)
datos.to_csv(ARCHIVO_PROC, index=False, encoding="utf-8")

sha256 = hashlib.sha256(ARCHIVO_PROC.read_bytes()).hexdigest()
escribir_log(f"FIN | {ARCHIVO_PROC.name} | {len(datos)} filas | {datos['ticker'].nunique()} tickers "
             f"| {len(columnas)} columnas | SHA-256: {sha256}")

# ============================================================
# BLOQUE 7. Resumen en consola
# ============================================================
print("\n===== RESUMEN DE LA BASE PROCESADA =====")
print(f"Periodo: {datos['fecha'].min()} a {datos['fecha'].max()}")
print(f"Filas: {len(datos)} | Tickers: {datos['ticker'].nunique()}")
print("\nDatos vacíos por columna:")
print(datos.isna().sum().to_string())
print("\nEstadísticas principales:")
print(datos[["retorno", "monto_negociado_soles", "negociado", "amihud"]].describe().round(4).to_string())
print(f"\nHash SHA-256 (copiar al README):\n{sha256}")
