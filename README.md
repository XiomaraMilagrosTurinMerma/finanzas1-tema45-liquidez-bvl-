# Liquidez bursátil y rendimiento de las acciones en la Bolsa de Valores de Lima

- **Autora:** Turín Merma Xiomara Milagros
- **Código de matrícula:** 2024200535B
- **Curso:** Finanzas I (055D) · Escuela Profesional de Economía · UNCP · 2026-II · Unidad I
- **Tema del temario:** n.º 45 — Liquidez bursátil y rendimiento de las acciones en la BVL
- **Repositorio:** https://github.com/XiomaraMilagrosTurinMerma/finanzas1-tema45-liquidez-bvl-

## Fuentes y endpoints
| Vía | Fuente | Endpoint | Script |
|---|---|---|---|
| API | Yahoo Finance (librería yfinance) | https://query1.finance.yahoo.com/v8/finance/chart/{ticker} | codigo/01_extraccion_api.py |
| Descarga programática | Bolsa de Valores de Lima | https://dataondemand.bvl.com.pe/v1/issuers/stock/{nemonico}?startDate=&endDate= | codigo/02_scraping_web.py |

Muestra: 24 emisoras de la BVL. Frecuencia diaria. Llave de unión: ticker + fecha.

## Parámetros de la consulta (congelados)
- FECHA_INICIO = 2018-01-01
- FECHA_CORTE = 2025-12-31
- Fecha de extracción: 2026-09-24 (ver log_ejecucion.txt)

## Orden de ejecución
1. `codigo/01_extraccion_api.py` → datos_crudos/datos_crudos_2024200535B_yahoo.csv
2. `codigo/02_scraping_web.py` → datos_crudos/datos_crudos_2024200535B_bvl.csv y datos_crudos/bvl/*.json
3. `codigo/03_limpieza_datos.py` → datos_procesados/datos_procesados_2024200535B.csv
4. `codigo/04_analisis.py` → tablas (CSV y LaTeX) y figuras (PNG) en /salidas

Instalación: `pip install -r requirements.txt`

## Versiones
- Python 3.12.11
- pandas 3.0.5
- numpy 2.5.2
- requests 2.34.2
- yfinance 1.7.0
- statsmodels 0.15.0
- matplotlib 3.10.9

## Clave de API
Ninguna de las dos fuentes requiere clave. El archivo `.env.example` se incluye vacío por exigencia de la consigna.

## Hash SHA-256 del archivo procesado
`datos_procesados/datos_procesados_2024200535B.csv`

`085a7c9af9c76c210f187f360a318285be47f01c97669ff8eeff20b839ee8aba`

## Reproducibilidad
Las fechas de consulta son constantes. Si una fuente revisa sus series después de la extracción, la reejecución puede diferir levemente; el log acredita la fecha y hora de la extracción original. Los datos crudos no se editan.

## Ética
Se revisó robots.txt, se usó un User-Agent identificable y una pausa de 1.5 s entre solicitudes. Solo se extrajo información pública. Se usó IA como apoyo para escribir y depurar el código; la autora revisó y comprende cada bloque.
