"""Exportación CSV pública; TLS verificado y sustitución atómica tras validar."""
# Usar los certificados del sistema operativo para verificar HTTPS.
import truststore
truststore.inject_into_ssl()
import csv
import json
import os
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen

# Endpoint observado en la exportación del portal. Si cambia, revisar la solicitud
# real del navegador; no sustituirlo por una URL de descarga temporal de otro trabajo.
BASE = 'https://www.buscadordeempleo.gov.co/backbue/v1/vacantes/export/csv/async'
REQUIRED = {'CODIGO_VACANTE', 'DESCRIPCION_VACANTE', 'DEPARTAMENTO', 'MUNICIPIO'}


def request_json(url, method='GET'):
    # urllib conserva la verificación TLS; no se omiten errores de certificado.
    req = Request(url, method=method, headers={'Accept': 'application/json', 'User-Agent': 'ObservatorioCompetencias/1.0'})
    with urlopen(req, timeout=60) as response:
        return json.load(response)


def validate_csv(path):
    """Lee todo el CSV: detecta esquema incorrecto, filas truncadas y archivo vacío."""
    csv.field_size_limit(10_000_000)
    with path.open(encoding='utf-8-sig', newline='') as stream:
        sample = stream.read(65536)
        stream.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=';,\t')
        reader = csv.DictReader(stream, dialect=dialect, strict=True)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError('El archivo no tiene las columnas esperadas')
        count = 0
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError('CSV incompleto o con columnas inconsistentes')
            count += 1
        if not count:
            raise ValueError('CSV sin registros')
    return count


def download(destination=Path('ofertas.csv')):
    destination = Path(destination)
    part = destination.with_suffix(destination.suffix + '.part')
    try:
        print('Solicitando la exportación…', flush=True)
        # El POST crea un trabajo; el identificador permite consultar su estado.
        job = request_json(BASE + '?page=1', 'POST')
        job_id = str(job['jobId'])
        if not job_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in job_id):
            raise ValueError('Identificador de exportación no válido')
        # Espera limitada y consultas espaciadas para no saturar el portal.
        deadline = time.monotonic() + 900
        print('Esperando la generación del CSV…', flush=True)
        while True:
            status = request_json(BASE + '/' + job_id + '/status')
            state = status.get('status')
            if state == 'completed':
                break
            if state in {'failed', 'error', 'cancelled'}:
                raise RuntimeError('La exportación falló en el portal')
            if time.monotonic() >= deadline:
                raise TimeoutError('El portal no completó la exportación en 15 minutos')
            time.sleep(10)
        print('Descargando el archivo…', flush=True)
        req = Request(BASE + '/' + job_id + '/download', headers={'Accept': 'text/csv'})
        # Descarga por bloques: evita cargar cientos de MB en memoria de una vez.
        with urlopen(req, timeout=120) as response, part.open('wb') as stream:
            content_type = response.headers.get('Content-Type', '').lower()
            if not any(t in content_type for t in ('csv', 'octet-stream', 'text/plain')):
                raise ValueError('El portal no devolvió un archivo CSV')
            expected = response.headers.get('Content-Length')
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                stream.write(chunk)
            if expected and total != int(expected):
                raise ValueError('Descarga incompleta')
        print('Validando el CSV…', flush=True)
        count = validate_csv(part)
        # Solo sustituir el archivo anterior después de validar todos los registros.
        os.replace(part, destination)
        print(f'Descarga correcta: {count:,} registros; {total / 1024**2:.2f} MiB', flush=True)
    finally:
        part.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        download(Path(sys.argv[1]) if len(sys.argv) > 1 else Path('ofertas.csv'))
    except Exception as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
