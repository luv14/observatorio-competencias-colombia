"""Convierte el CSV en datos compactos para el navegador.

Uso: python procesar_ofertas.py ofertas.csv [fecha_de_corte_YYYY-MM-DD]
Preserva ubicaciones y variantes; solo elimina filas exactamente iguales.
La salida definitiva se crea al completar todo el procesamiento.
"""
import shutil,tempfile,functools,csv,json,gzip,hashlib,re,unicodedata,sys,collections,datetime,pathlib
# Rutas relativas al script: permite ejecutarlo desde cualquier carpeta.
base=pathlib.Path(__file__).parent
src=sys.argv[1] if len(sys.argv)>1 else str(base/'ofertas.csv')
# Colombia usa UTC-5. El corte determina qué publicaciones muestra el dashboard.
cutoff=sys.argv[2] if len(sys.argv)>2 else (datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(hours=5)).date().isoformat()
datetime.date.fromisoformat(cutoff)
print('Procesando:',src,flush=True)
resultados=base/'resultados';resultados.mkdir(exist_ok=True)
# Carpeta temporal: nunca se sobrescribe una actualización anterior.
out=pathlib.Path(tempfile.mkdtemp(prefix='.procesando-',dir=resultados))
from skills import detect,skills,catalog,categories,METHOD
# seen detecta filas idénticas; offers identifica publicaciones únicas.
# records conserva las variantes territoriales y groups reúne sus índices.
seen=set();offers={};records=[];raw=dups=blank=0;groups=collections.defaultdict(set)
@functools.lru_cache(maxsize=10000)
def date(s):
 """Normaliza fechas a ISO; rechaza datos no interpretables en vez de adivinarlos."""
 if not s.strip():return ''
 for formato in ('%d/%m/%Y %H:%M','%d/%m/%Y %H:%M:%S','%d/%m/%Y','%Y-%m-%d'):
  try:return datetime.datetime.strptime(s.strip(),formato).date().isoformat()
  except ValueError:pass
 try:return datetime.datetime.fromisoformat(s.strip().replace('Z','+00:00')).date().isoformat()
 except ValueError:raise ValueError('Formato de fecha no reconocido: '+repr(s))
# utf-8-sig acepta CSV con o sin BOM y conserva las tildes.
with open(src,encoding='utf-8-sig',newline='') as f:
 csv.field_size_limit(10000000)
 sample=f.read(65536);f.seek(0)
 dialect=csv.Sniffer().sniff(sample,delimiters=';,\t')
 reader=csv.DictReader(f,dialect=dialect,strict=True)
 # El esquema es un contrato: si la fuente cambia, detener la publicación.
 required={'CODIGO_VACANTE','TITULO_VACANTE','DESCRIPCION_VACANTE','NIVEL_ESTUDIOS','RANGO_SALARIAL','NOMBRE_PRESTADOR','DEPARTAMENTO','MUNICIPIO','TIPO_CONTRATO','URL_DETALLE_VACANTE','CANTIDAD_VACANTES','FECHA_PUBLICACION','FECHA_VENCIMIENTO','SECTOR_ECONOMICO','TELETRABAJO','MESES_EXPERIENCIA_CARGO'}
 if not required.issubset(reader.fieldnames or []):raise ValueError('Faltan columnas necesarias: '+str(sorted(required-set(reader.fieldnames or []))))
 for r in reader:
  if None in r or any(v is None for v in r.values()):raise ValueError('CSV incompleto: fila con columnas faltantes; no se publica un conjunto parcial')
  raw+=1
  if raw%10000==0:print(f'Revisadas {raw:,} filas...',flush=True)
  # No confundir duplicado exacto con una oferta repetida en otra ciudad.
  h=hashlib.sha256(json.dumps(r,ensure_ascii=False,sort_keys=True).encode()).digest()
  if h in seen:dups+=1;continue
  seen.add(h);blank+=not bool(r['CODIGO_VACANTE'])
  # Prioridad de identidad: URL, código y finalmente contenido de respaldo.
  # El prestador forma parte de la clave: aún no hay deduplicación entre portales.
  identity=r['URL_DETALLE_VACANTE'].strip() or r['CODIGO_VACANTE'].strip() or '|'.join(r[k] for k in ['TITULO_VACANTE','DESCRIPCION_VACANTE','FECHA_PUBLICACION'])
  key=hashlib.sha256((r['NOMBRE_PRESTADOR']+'|'+identity).encode()).hexdigest()[:20]
  ss=detect(r['DESCRIPCION_VACANTE'])
  if key not in offers:
   offers[key]=len(offers)
  # Contrato de filas usado también por plantilla/app.js (no reordenar).
  # 0 clave; 1 departamento; 2 municipio; 3 título; 4 educación; 5 salario;
  # 6 contrato; 7 sector; 8 puestos; 9 publicación; 10 vencimiento;
  # 11 experiencia; 12 teletrabajo; 13 índices de competencias; 14 prestador.
  rec=[key,r['DEPARTAMENTO'],r['MUNICIPIO'],r['TITULO_VACANTE'],r['NIVEL_ESTUDIOS'],r['RANGO_SALARIAL'],r['TIPO_CONTRATO'],r['SECTOR_ECONOMICO'],int(r['CANTIDAD_VACANTES']),date(r['FECHA_PUBLICACION']),date(r['FECHA_VENCIMIENTO']),r['MESES_EXPERIENCIA_CARGO'],r['TELETRABAJO']=='1',ss,r['NOMBRE_PRESTADOR']]
  groups[key].add(len(records));records.append(rec)
# Metadatos de trazabilidad y catálogo que consume el dashboard.
# Al ampliar el catálogo, actualizar también el control de preparar_publicacion.py.
meta={'raw':raw,'duplicates':dups,'clean':len(records),'offers':len(offers),'blank_clean':blank,'cutoff':cutoff,'dictionary_version':'188-'+hashlib.sha256((base/'skill-catalog.json').read_bytes()).hexdigest()[:12],'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'skill_method':METHOD,'skills':skills,'skill_categories':categories(),'multi_location':sum(len({(records[i][1],records[i][2]) for i in v})>1 for v in groups.values()),'method':'Identidad por prestador + URL; si falta URL, código; si faltan ambos, título, descripción y publicación. Se preservan variantes y ubicaciones. Los puestos se suman una vez por oferta usando el máximo declarado entre sus registros; no son aditivos entre territorios.'}
# Comprimir reduce transferencia; el navegador descomprime data.json.gz.
with gzip.open(out/'data.json.gz','wt',encoding='utf-8',compresslevel=9) as f:json.dump({'meta':meta,'rows':records},f,ensure_ascii=False,separators=(',',':'))
(out/'quality.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
if raw==0:raise ValueError('El CSV no contiene registros')
# Se publican solo los datos procesados y los tres archivos estáticos.
for name in ('index.html','app.js','zones.js'):shutil.copy2(base/'plantilla'/name,out/name)
final=resultados/('actualizacion_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
# Renombrar al final hace visible únicamente una actualización completa.
out.rename(final)
print('PROCESAMIENTO CORRECTO')
print('Filas originales:',raw)
print('Duplicados exactos eliminados:',dups)
print('Registros conservados:',len(records))
print('Ofertas identificadas:',len(offers))
print('Conceptos del diccionario:',len(skills))
print('Fecha de corte:',cutoff)
print('Carpeta generada:',final.resolve())
