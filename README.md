# Observatorio de competencias del mercado laboral colombiano

Herramienta para identificar habilidades, conocimientos y requisitos mencionados en publicaciones de empleo y orientar cursos pertinentes por zona UNAD y municipio. No es un portal de vacantes. Las menciones no demuestran por sí mismas una brecha de formación.

## Proceso

1. `python descargar_ofertas.py`: solicita la exportación pública CSV y valida descarga y estructura antes de sustituir el archivo.
2. `python preparar_publicacion.py`: elimina duplicados exactos, detecta conceptos con el diccionario de 188 términos y crea `public/` tras validar los resultados.
3. GitHub Actions publica esa carpeta en el proyecto existente de Cloudflare Pages.

Se requieren Python 3.13 y, solo para publicar, Node 22 y Wrangler 4. Python utiliza su biblioteca estándar. No se debe desactivar la verificación TLS. En un equipo institucional Windows que requiera la confianza del sistema se puede configurar truststore; el runner Linux usa sus certificados predeterminados.

## Primera ejecución

El workflow se instala en `.github/workflows/actualizar.yml`. En Actions, elegir **Actualizar observatorio → Run workflow**. Dejar **publicar** sin marcar para comprobar descarga y procesamiento. No cambia el sitio. La primera conexión real desde GitHub todavía debe verificarse.

Para publicar, configurar en Settings → Secrets and variables → Actions los secretos `CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_API_TOKEN`. El token necesita permiso Account / Cloudflare Pages / Edit limitado a la cuenta correspondiente. Nunca subir el token a archivos o compartirlo en el chat.

Ejecutar de nuevo con **publicar** marcado. Usa el proyecto existente `observatorio-competencias-colombia` y la rama de producción `main`; comprobarla en Cloudflare antes de la primera publicación. No crea otro proyecto ni necesita dominio propio.

Tras verificar el sitio, descomentar `schedule:` y la línea `cron` del workflow. Programación propuesta: diaria a las 06:23 de Colombia (11:23 UTC). GitHub puede retrasar ejecuciones y puede desactivar programaciones en repositorios públicos sin actividad durante 60 días; revisar Actions periódicamente. Se puede ejecutar manualmente en cualquier momento.

## Costos y límites

Usar repositorio público y runner estándar `ubuntu-latest`. No activar runners grandes ni funciones, R2, bases de datos o complementos de pago. No se almacenan CSV ni artefactos de Actions. Cada archivo publicado se comprueba por debajo de 25 MiB. Revisar los límites vigentes de GitHub y Cloudflare antes de aumentar frecuencia o volumen. Un error de descarga, procesamiento o validación impide el paso de publicación: el sitio anterior permanece disponible.

## Metodología y mantenimiento

Se conserva la identidad por prestador y URL (con código como respaldo); no se resuelven aún duplicados entre portales distintos. El diccionario se carga en UTF-8. Porcentajes: publicaciones únicas con mención / publicaciones únicas vigentes de la selección; una publicación puede mencionar varias competencias. El diccionario requiere revisión humana periódica de ejemplos y términos nuevos. El corte se calcula con fecha de Colombia, que no garantiza que la fuente haya actualizado sus datos ese día.

La exportación reproduce el endpoint observado con `page=1` y sin filtros adicionales; aún debe contrastarse su cobertura con la selección «Todos» en la interfaz. No se afirma cobertura total del mercado. Si cambia el endpoint o el esquema, la ejecución se detiene. Se respeta TLS; no se eluden autenticación ni bloqueos.

## Carga desde el navegador

Descomprimir el ZIP. En GitHub, Add file → Upload files y cargar los archivos visibles, incluidas la carpeta `plantilla` y las pruebas. Para el workflow, Add file → Create new file; escribir `.github/workflows/actualizar.yml` y pegar el contenido del archivo incluido. Crear también `.gitignore` con su contenido si el navegador no permite seleccionarlo. El ZIP incluye una copia visible `actualizar-workflow.txt` para facilitar copiar el workflow; esta copia no ejecuta nada.

Documentación: https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/ y https://docs.github.com/en/billing/concepts/product-billing/github-actions
