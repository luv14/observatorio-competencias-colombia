"""Procesa y valida; crea public/ únicamente con una ejecución correcta."""
import datetime
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys

base = Path(__file__).resolve().parent
# Registrar las salidas existentes permite distinguir la carpeta de esta ejecución.
before = set((base / 'resultados').glob('actualizacion_*'))
# check=True aborta el workflow si el procesador devuelve un error.
subprocess.run([sys.executable, str(base / 'procesar_ofertas.py'), str(base / 'ofertas.csv')], check=True)
created = set((base / 'resultados').glob('actualizacion_*')) - before
if len(created) != 1:
    raise RuntimeError('No se identificó una única carpeta nueva')
source = created.pop()
with gzip.open(source / 'data.json.gz', 'rt', encoding='utf-8') as stream:
    data = json.load(stream)
meta, rows = data['meta'], data['rows']
cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)).date().isoformat()
if not rows or meta['cutoff'] != cutoff or meta['clean'] != len(rows):
    raise ValueError('Metadatos o registros inconsistentes')
# Control de catálogo: cambiar 188 al ampliar deliberadamente el diccionario.
# Exigir datos vigentes evita publicar accidentalmente un archivo histórico vacío.
if len(meta['skills']) != 188 or not any(not r[10] or r[10] >= cutoff for r in rows):
    raise ValueError('Diccionario inesperado o ninguna publicación vigente')
# Cloudflare Pages limita cada archivo a 25 MiB; no publicar si se supera.
for name in ('index.html', 'app.js', 'zones.js', 'quality.json', 'data.json.gz'):
    file = source / name
    if not file.is_file() or file.stat().st_size == 0 or file.stat().st_size >= 25 * 1024**2:
        raise ValueError('Archivo ausente, vacío o excede límite de Pages: ' + name)
# public/ es una carpeta de salida desechable, nunca una fuente editable.
public = base / 'public'
if public.exists():
    shutil.rmtree(public)
shutil.copytree(source, public)
print('Publicación validada en public/')
