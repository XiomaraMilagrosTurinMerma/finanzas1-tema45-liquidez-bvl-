# Incidencias de las fuentes de datos

Registro de los problemas que aparecieron al extraer y limpiar los datos, y cómo se resolvieron. Todo se puede verificar en `log_ejecucion.txt` (extracción del 24/09/2026).

| N.º | Fuente | Qué pasó | Cómo se resolvió | Efecto en la muestra |
|---|---|---|---|---|
| 1 | Yahoo Finance (API) | De los 32 tickers consultados, 8 no devolvieron datos: CASAGRC1, ENDISPC1, ENGEPEC1, POMALCC1, AENZAC1, BROCALC1, LAREDOC1 y CARTAVC1 (0 filas). | Se repitió la consulta y el resultado fue el mismo, así que se excluyeron. | La muestra final queda en 24 emisoras. |
| 2 | BVL (dataondemand) | En la primera prueba (modo prueba, ALICORC1 2025, 24/09/2026 12:19), la BVL respondió HTTP 200, pero el contenido no era JSON. | Se volvió a ejecutar la prueba a las 12:24 y respondió bien (248 filas); luego se descargaron las 24 emisoras. | Ninguno: se descargaron 48 024 filas. |
| 3 | BVL | 10 610 días tenían precio de cierre igual a 0 porque en esos días la acción no se negoció. | Esos precios se cambiaron a vacío (no son precios reales) y se marcó `negociado = 0`. | Se usan para medir la frecuencia de negociación. |
| 4 | Yahoo + BVL | Las dos fuentes no tienen exactamente los mismos días (48 067 filas en Yahoo y 48 024 en la BVL). | Se unieron por `ticker` + `fecha` y se conservaron solo los días comunes. | Quedan 46 625 filas. |
| 5 | Yahoo Finance | 3 rendimientos diarios mayores a ±50 %, que parecen errores de dato. | Se reemplazaron por vacío. | No afectan los resultados de forma relevante. |

Los datos crudos no se editaron a mano; todas las correcciones se hacen en `03_limpieza_datos.py`.
