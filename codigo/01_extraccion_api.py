# Nombres y apellidos: Turin Merma Xiomara Milagros
# Codigo de matricula: 2024200535B
# Tema 45 - Liquidez bursatil y rendimiento de las acciones en la Bolsa de Valores de Lima
# Fecha de extraccion: 2026-09-24

"""
01_extraccion_api.py
Vía API: Yahoo Finance mediante la librería yfinance.
Endpoint que consulta yfinance por dentro:
    https://query1.finance.yahoo.com/v8/finance/chart/{ticker}
Descarga precios diarios y volumen negociado de emisoras de la BVL (sufijo .LM)
y guarda el archivo crudo, sin editar, en /datos_crudos.
"""

# ============================================================
# BLOQUE 1. Librerías
# ============================================================
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

# ============================================================
# BLOQUE 2. Parámetros congelados de la consulta (numeral 2.4.5)
# Son constantes, NO fechas dinámicas tipo "hoy".
# ============================================================
FECHA_INICIO = "2018-01-01"
FECHA_CORTE = "2025-12-31"
CODIGO = "2024200535B"
PAUSA_SEGUNDOS = 1.5      # pausa entre solicitudes (mínimo exigido: 1 s)
REINTENTOS = 3            # intentos por ticker si falla la conexión

# Emisoras candidatas de la BVL en Yahoo Finance.
# Se prueban todas y se conservan las que devuelven datos (meta: al menos 20).
TICKERS = [
    "ALICORC1.LM", "BACKUSI1.LM", "BAP.LM", "BBVAC1.LM", "BVN.LM",
    "CASAGRC1.LM", "CORAREI1.LM", "CPACASC1.LM", "CREDITC1.LM", "CVERDEC1.LM",
    "ENDISPC1.LM", "ENGEPEC1.LM", "ENGIEC1.LM", "FERREYC1.LM", "IFS.LM",
    "INRETC1.LM", "INTERBC1.LM", "LUSURC1.LM", "MINSURI1.LM", "NEXAPEC1.LM",
    "POMALCC1.LM", "SCCO.LM", "SCOTIAC1.LM", "SIDERC1.LM", "UNACEMC1.LM",
    "VOLCABC1.LM", "AENZAC1.LM", "ATACOBC1.LM", "BROCALC1.LM", "LAREDOC1.LM",
    "CARTAVC1.LM", "AUSTRAC1.LM",
]

# ============================================================
# BLOQUE 3. Rutas relativas a la carpeta del proyecto (sin C:\Users\...)
# Este archivo está en /codigo, así que la raíz es la carpeta de arriba.
# ============================================================
RAIZ = Path(__file__).resolve().parent.parent
CARPETA_CRUDOS = RAIZ / "datos_crudos"
ARCHIVO_CRUDO = CARPETA_CRUDOS / f"datos_crudos_{CODIGO}_yahoo.csv"
ARCHIVO_LOG = RAIZ / "log_ejecucion.txt"
CARPETA_CRUDOS.mkdir(exist_ok=True)


def escribir_log(mensaje):
    """Escribe una línea con fecha y hora en log_ejecucion.txt y en la consola."""
    linea = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")


# ============================================================
# BLOQUE 4. Descarga de cada ticker con manejo de errores
# yfinance no entrega el código HTTP directamente: si devuelve datos,
# la respuesta del servidor fue 200; si falla, se registra el error.
# ============================================================
# yfinance toma la fecha final como "exclusiva", por eso se suma un día.
fin_exclusivo = (datetime.strptime(FECHA_CORTE, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

escribir_log(f"INICIO extraccion API Yahoo Finance | periodo {FECHA_INICIO} a {FECHA_CORTE} | {len(TICKERS)} tickers")

tablas = []
for ticker in TICKERS:
    datos = pd.DataFrame()
    error = ""
    for intento in range(1, REINTENTOS + 1):
        try:
            datos = yf.Ticker(ticker).history(
                start=FECHA_INICIO, end=fin_exclusivo,
                interval="1d", auto_adjust=False, actions=False,
            )
            break
        except Exception as e:  # error de conexión u otro problema
            error = str(e)
            time.sleep(PAUSA_SEGUNDOS * intento)

    if datos.empty:
        escribir_log(f"{ticker}: 0 filas | respuesta: ERROR/sin datos {error}")
    else:
        datos = datos.reset_index()
        datos["Date"] = datos["Date"].dt.strftime("%Y-%m-%d")  # solo la fecha
        datos.insert(0, "ticker", ticker)
        tablas.append(datos)
        escribir_log(f"{ticker}: {len(datos)} filas | respuesta HTTP 200")

    time.sleep(PAUSA_SEGUNDOS)  # pausa entre solicitudes

# ============================================================
# BLOQUE 5. Guardado del archivo crudo y resumen
# ============================================================
if tablas:
    crudo = pd.concat(tablas, ignore_index=True)
    crudo.to_csv(ARCHIVO_CRUDO, index=False, encoding="utf-8")
    n_tickers = crudo["ticker"].nunique()
    escribir_log(f"FIN | archivo: {ARCHIVO_CRUDO.name} | {len(crudo)} filas | {n_tickers} tickers con datos")

    print("\n===== RESUMEN =====")
    print(crudo.groupby("ticker").size().sort_values(ascending=False).to_string())
    print(f"\nTickers con datos: {n_tickers} (meta: 20)")
    print(f"Observaciones totales: {len(crudo)} (meta: 30 000)")
else:
    escribir_log("FIN | ningun ticker devolvio datos: revisar conexion a internet") 