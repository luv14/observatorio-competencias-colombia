# Guía de mantenimiento

## Propósito

Identificar necesidades expresadas por el mercado laboral para orientar cursos y sus temáticas por zona UNAD y municipio. Las publicaciones son la fuente de análisis. Las menciones no prueban por sí mismas una brecha de formación ni distinguen completamente lo obligatorio de lo deseable.

## Dónde hacer cada cambio

| Necesidad | Archivo | Precaución |
|---|---|---|
| Añadir conceptos o sinónimos | `skill-catalog.json` | Respetar estructura y categorías; validar ejemplos positivos y negativos. |
| Ajustar normalización o contexto | `skills.py` | Revisar falsos positivos y negativos en `test_skills.py`. |
| Cambiar descarga | `descargar_ofertas.py` | Comprobar endpoint y cobertura; mantener TLS y validación completa. |
| Cambiar columnas o identidad | `procesar_ofertas.py` | Los índices de filas son un contrato compartido con `app.js`. |
| Cambiar controles de salida | `preparar_publicacion.py` | Al ampliar 188 conceptos, actualizar este control y la versión del diccionario del procesador. |
| Cambiar cálculo, filtros o top 10 | `plantilla/app.js` | Mantener denominador de publicaciones únicas y dos decimales. |
| Cambiar diseño, textos o colores | `plantilla/index.html` | Conservar identificadores de controles y del mapa. |
| Modificar agrupación territorial | `plantilla/zones.js` | Coordinar cambios con SVG y botones en `index.html`. |
| Cambiar horario o publicación | `.github/workflows/actualizar.yml` | Cron en UTC: hora de Colombia + 5. Verificar proyecto y rama de producción. |

## Lectura de un concepto del diccionario

Cada entrada contiene un término visible, una categoría y un patrón de búsqueda. Los patrones se aplican a texto normalizado: minúsculas, sin tildes y con espacios unificados. Consultar una entrada existente antes de crear otra. JSON no acepta comentarios: documentar decisiones sobre nuevos conceptos en esta guía o en un archivo Markdown aparte. No introducir campos sin revisar cómo los utiliza el detector.

## Cálculos que debemos conservar

- Una competencia cuenta una vez por publicación identificada, aunque se repita en el texto o en variantes de la misma publicación dentro de la selección.
- Denominador: todas las publicaciones únicas de la selección con fecha de vencimiento presente y mayor o igual al corte. Incluye publicaciones sin competencias detectadas.
- El navegador excluye registros sin fecha de vencimiento. Revisar esta política explícitamente si se decide cambiarla.
- Porcentaje = publicaciones con mención / publicaciones de la selección × 100.
- Una publicación puede mencionar varias competencias: los porcentajes no tienen que sumar 100 %.
- El corte usa la fecha de Colombia; no demuestra que la fuente esté actualizada ese día.
- Identidad por prestador y URL, con respaldos documentados. Aún no elimina duplicados entre portales distintos.

## Actualización del diccionario

1. Revisar ejemplos reales que no se estén detectando o que se detecten fuera de contexto.
2. Agregar o ajustar término, categoría y sinónimos sin duplicar conceptos existentes.
3. Crear ejemplos de prueba positivos y negativos cuando se añada una regla o cambie su interpretación.
4. Ejecutar `python -m unittest discover -p 'test_*.py'`.
5. Si cambia el número de conceptos, actualizar el control de `preparar_publicacion.py` y el prefijo de `dictionary_version` en el procesador. El hash distingue versiones del catálogo.
6. Ejecutar el workflow manualmente sin publicar; revisar resultado antes de desplegar.
7. Registrar fecha y motivo del cambio. Para comparar períodos con catálogos diferentes se necesita reprocesar con una versión común o explicar la diferencia.

## Cómo verificar cambios

Pruebas Python: `python -m unittest discover -p 'test_*.py'`.

Sintaxis del navegador (con Node disponible): `node --check plantilla/app.js` y `node --check plantilla/zones.js`.

La prueba del descargador simula respuestas sin conexión; no demuestra que el portal esté disponible. Confirmar la ejecución real en GitHub Actions. Para probar localmente el sitio, procesar un CSV y servir la carpeta `public` con `python -m http.server 8080 --bind 127.0.0.1 --directory public`.

No editar `public` ni `resultados`: se generan de nuevo. Editar las fuentes y regenerar. Nunca incluir secretos, tokens ni contraseñas. Revisar un cambio pequeño por vez y conservar el historial en GitHub.

## Límites conocidos

La exportación sin filtros reproduce la solicitud observada, pero su equivalencia con «Todos» debe comprobarse. Las validaciones actuales detectan archivos malformados o vacíos; no detectan todas las reducciones inesperadas de cobertura ni errores semánticos. La revisión de datos y del diccionario sigue siendo necesaria.

La programación diaria está comentada hasta validar la primera publicación. Los cambios de este paquete son documentación y formato: no activan la programación ni publican el sitio.
