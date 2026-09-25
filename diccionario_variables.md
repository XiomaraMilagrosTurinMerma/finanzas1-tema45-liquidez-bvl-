# Diccionario de variables: datos_procesados_2024200535B.csv

| Variable | Definición | Unidad | Frecuencia | Fuente | URL o endpoint |
|---|---|---|---|---|---|
| ticker | Nemónico de la emisora en la BVL | Texto | — | Yahoo Finance / BVL | Llave de unión |
| fecha | Día de negociación | AAAA-MM-DD | Diaria | Yahoo Finance / BVL | Llave de unión |
| retorno | Retorno diario simple del precio ajustado | Proporción | Diaria | Yahoo Finance | https://query1.finance.yahoo.com/v8/finance/chart/{ticker} |
| precio_ajustado_yahoo | Precio de cierre ajustado por dividendos | Moneda de negociación | Diaria | Yahoo Finance | https://query1.finance.yahoo.com/v8/finance/chart/{ticker} |
| volumen_yahoo | Acciones negociadas según Yahoo | Número de acciones | Diaria | Yahoo Finance | https://query1.finance.yahoo.com/v8/finance/chart/{ticker} |
| precio_cierre_bvl | Precio de cierre (vacío si no hubo negociación) | Moneda de negociación | Diaria | BVL | https://dataondemand.bvl.com.pe/v1/issuers/stock/{nemonico} |
| acciones_negociadas | Cantidad de acciones negociadas | Número de acciones | Diaria | BVL | https://dataondemand.bvl.com.pe/v1/issuers/stock/{nemonico} |
| monto_negociado_soles | Monto negociado | Soles (S/) | Diaria | BVL | https://dataondemand.bvl.com.pe/v1/issuers/stock/{nemonico} |
| negociado | 1 si la acción se negoció ese día, 0 si no | Binaria (0/1) | Diaria | BVL | Calculada en 03_limpieza_datos.py |
| amihud | Iliquidez de Amihud: |retorno| / monto negociado en millones de S/ (winsorizada 1 %-99 %) | Proporción por millón de S/ | Diaria | Yahoo Finance + BVL | Calculada en 03_limpieza_datos.py |
