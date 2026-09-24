# Nombres y apellidos: Turin Merma Xiomara Milagros
# Codigo de matricula: 2024200535B
# Tema 45 - Liquidez bursatil y rendimiento de las acciones en la Bolsa de Valores de Lima
# Fecha de extraccion: 2026-09-24

"""
02_scraping_web.py
Vía 2: descarga programática desde el portal de la Bolsa de Valores de Lima (BVL).
El portal www.bvl.com.pe carga sus cotizaciones históricas desde este servicio:
    https://dataondemand.bvl.com.pe/v1/issuers/stock/{nemonico}?startDate=AAAA-MM-DD&endDate=AAAA-MM-DD
Reglas éticas (numeral 2.4.8): se revisa robots.txt, se usa un User-Agent
identificable y una pausa mínima entre solicitudes.
Las respuestas se guardan SIN EDITAR en /datos_crudos/bvl como evidencia.
"""

# ============================================================
# BLOQUE 1. Librerías
# ============================================================
import time
from datetime import datetime
from pathlib import Path
from urllib import robotparser

import pandas as pd
import requests

# ============================================================
# BLOQUE 2. Parámetros congelados de la consulta
# ============================================================
FECHA_INICIO = "2018-01-01"
FECHA_CORTE = "2025-12-31"
CODIGO = "2024200535B"
PAUSA_SEGUNDOS = 1.5
MODO_PRUEBA = False   # True: prueba con 1 empresa y 1 año. Si funciona, cambiar a False.

URL_BASE = "https://dataondemand.bvl.com.pe/v1/issuers/stock/{nemonico}"
USER_AGENT = "Mozilla/5.0 (compatible; ProyectoAcademicoUNCP/1.0; contacto: e_2024200535B@uncp.edu.pe)"
CABECERAS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Origin": "https://www.bvl.com.pe",
    "Referer": "https://www.bvl.com.pe/",
}

# Mismas 24 emisoras que devolvieron datos en 01_extraccion_api.py (sin el sufijo .LM)
NEMONICOS = [
    "ALICORC1", "BACKUSI1", "BAP", "BBVAC1", "BVN", "CORAREI1", "CPACASC1",
    "CREDITC1", "CVERDEC1", "ENGIEC1", "FERREYC1", "IFS", "INRETC1", "INTERBC1",
    "LUSURC1", "MINSURI1", "NEXAPEC1", "SCCO", "SCOTIAC1", "SIDERC1",
    "UNACEMC1", "VOLCABC1", "ATACOBC1", "AUSTRAC1",
]

# ============================================================
# BLOQUE 3. Rutas relativas a la carpeta del proyecto
# ============================================================
RAIZ = Path(__file__).resolve().parent.parent
CARPETA_BVL = RAIZ / "datos_crudos" / "bvl"
ARCHIVO_CRUDO = RAIZ / "datos_crudos" / f"datos_crudos_{CODIGO}_bvl.csv"
ARCHIVO_LOG = RAIZ / "log_ejecucion.txt"
ARCHIVO_INCIDENCIAS = RAIZ / "incidencias_fuente.md"
CARPETA_BVL.mkdir(parents=True, exist_ok=True)


def ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def escribir_log(mensaje):
    """Escribe una línea con fecha y hora en log_ejecucion.txt y en la consola."""
    linea = f"[{ahora()}] {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")


# ============================================================
# BLOQUE 4. Revisión de robots.txt antes de descargar
# ============================================================
def revisar_robots(url):
    """Devuelve True si robots.txt permite consultar la URL."""
    dominio = "/".join(url.split("/")[:3])
    rp = robotparser.RobotFileParser()
    rp.set_url(dominio + "/robots.txt")
    try:
        rp.read()
    except Exception:
        return True  # si no existe robots.txt, no hay restricción declarada
    return rp.can_fetch(USER_AGENT, url)


# ============================================================
# BLOQUE 5. Descarga por empresa y por año
# Se pide un año a la vez para no sobrecargar el portal.
# ============================================================
anios = list(range(int(FECHA_INICIO[:4]), int(FECHA_CORTE[:4]) + 1))
nemonicos = NEMONICOS
if MODO_PRUEBA:
    nemonicos, anios = NEMONICOS[:1], [2025]

escribir_log(f"INICIO descarga BVL | periodo {FECHA_INICIO} a {FECHA_CORTE} | "
             f"{len(nemonicos)} emisoras | modo prueba: {MODO_PRUEBA}")

tablas, incidencias = [], []
url_ejemplo = URL_BASE.format(nemonico=nemonicos[0])

if not revisar_robots(url_ejemplo):
    escribir_log("robots.txt NO permite esta ruta: se detiene la descarga")
    incidencias.append((url_ejemplo, ahora(), "robots.txt", "Ruta no permitida por robots.txt"))
else:
    for nem in nemonicos:
        for anio in anios:
            inicio = max(f"{anio}-01-01", FECHA_INICIO)
            fin = min(f"{anio}-12-31", FECHA_CORTE)
            url = URL_BASE.format(nemonico=nem)
            try:
                r = requests.get(url, params={"startDate": inicio, "endDate": fin},
                                 headers=CABECERAS, timeout=30)
            except requests.RequestException as e:
                escribir_log(f"{nem} {anio}: ERROR de conexion | {e}")
                incidencias.append((url, ahora(), "sin respuesta", str(e)[:200]))
                time.sleep(PAUSA_SEGUNDOS)
                continue

            if MODO_PRUEBA:
                print("\n--- Primeros caracteres de la respuesta ---")
                print(r.text[:600])
                print("-------------------------------------------\n")

            if r.status_code == 200:
                # Evidencia primaria: la respuesta tal como llegó, sin editar
                (CARPETA_BVL / f"{nem}_{anio}.json").write_text(r.text, encoding="utf-8")
                try:
                    datos = r.json()
                    if isinstance(datos, dict):
                        datos = datos.get("content") or datos.get("data") or [datos]
                    tabla = pd.json_normalize(datos)
                    tabla["nemonico"] = nem
                    tablas.append(tabla)
                    escribir_log(f"{nem} {anio}: {len(tabla)} filas | respuesta HTTP {r.status_code}")
                except ValueError:
                    escribir_log(f"{nem} {anio}: respuesta HTTP 200 pero no es JSON")
                    incidencias.append((url, ahora(), 200, "La respuesta no es JSON"))
            else:
                escribir_log(f"{nem} {anio}: 0 filas | respuesta HTTP {r.status_code}")
                incidencias.append((url, ahora(), r.status_code, r.text[:200]))

            time.sleep(PAUSA_SEGUNDOS)  # pausa entre solicitudes

# ============================================================
# BLOQUE 6. Guardado del crudo y registro de incidencias
# ============================================================
if tablas:
    crudo = pd.concat(tablas, ignore_index=True)
    crudo.to_csv(ARCHIVO_CRUDO, index=False, encoding="utf-8")
    escribir_log(f"FIN | archivo: {ARCHIVO_CRUDO.name} | {len(crudo)} filas | "
                 f"{crudo['nemonico'].nunique()} emisoras")
    print("\nColumnas recibidas:", list(crudo.columns))
else:
    escribir_log("FIN | la BVL no devolvio datos")

if incidencias:
    with open(ARCHIVO_INCIDENCIAS, "w", encoding="utf-8") as f:
        f.write("# Incidencias de la fuente: Bolsa de Valores de Lima\n\n")
        f.write("| URL | Fecha y hora | Codigo HTTP | Mensaje del portal |\n|---|---|---|---|\n")
        for url, fecha, codigo_http, msg in incidencias:
            msg = str(msg).replace("\n", " ").replace("|", "/")
            f.write(f"| {url} | {fecha} | {codigo_http} | {msg} |\n")
        f.write("\nCaptura de pantalla: (agregar)\n")
    print(f"\nSe registraron {len(incidencias)} incidencias en {ARCHIVO_INCIDENCIAS.name}")