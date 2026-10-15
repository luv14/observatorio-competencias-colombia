"""Detector de menciones explícitas: catálogo, normalización y reglas de contexto.

Editar conceptos en skill-catalog.json; mantener identificadores/orden coherentes
con los datos generados. Las reglas reducen ambigüedades, pero no sustituyen
la validación humana ni detectan todas las competencias implícitas.
"""
import functools,json,pathlib,re,unicodedata
# UTF-8 explícito evita etiquetas dañadas en equipos Windows.
catalog=json.loads((pathlib.Path(__file__).parent/'skill-catalog.json').read_text(encoding='utf-8'))
skills=[e['term'] for e in catalog];rx=[re.compile(e['pattern']) for e in catalog]
# Triggers are a speed hint only. Empty literal alternatives disable the hint.
triggers=[re.findall('[a-z]{3,}',e['pattern'].replace(r'\b','').replace(r'\w','')) for e in catalog]
for i,e in enumerate(catalog):
 if e['term'] in {'C#','Conducción'}:triggers[i]=[]
def repair_token(token):
 """Intenta reparar caracteres mal decodificados solo si la conversión es válida."""
 for _ in range(2):
  before=token
  for enc in ('cp1252','latin1'):
   try:
    candidate=token.encode(enc).decode('utf-8')
    if candidate!=token:token=candidate;break
   except (UnicodeEncodeError,UnicodeDecodeError):pass
  if token==before:break
 return token
def norm(raw):
 """Unifica tildes, mayúsculas y espacios antes de aplicar expresiones regulares."""
 raw=re.sub(r'\S*[ÃÂâ][^\s]*',lambda m:repair_token(m.group()),raw)
 text=''.join(c for c in unicodedata.normalize('NFD',raw.lower()) if unicodedata.category(c)!='Mn')
 return re.sub(r'\s+',' ',text).strip()
# Señales para distinguir el perfil solicitado de la descripción de la empresa.
PROFILE=re.compile(r'buscamos|buscando|busca(?:mos)?\b|busqueda|solicita|necesita|contrata|convoca|requerimos|requiere|requisitos|experiencia|conocimientos|habilidades|funciones|responsabilidades|perfil|debe|debera|necesitas|tu mision')
BUSINESS=re.compile(r'(?:empresa|compania|plataforma|organizacion).{0,110}?(?:dedicad[oa]|especializad[oa]|soluciones de|sector(?: de)?|ofrece)')
NEGATIVE=re.compile(r'(?:no (?:se requiere|requiere|es necesario|es indispensable|necesita)|sin necesidad de)(?: tener)?(?: conocimientos?| dominio| manejo| hablar| saber)?(?: previo)?(?: de| en| del idioma)?\s*$')
def accepted(term,text,m):
 """Decide si una coincidencia corresponde al perfil y no a un contexto excluido."""
 prefix=text[max(0,m.start()-220):m.start()]
 if term=='Buenas prácticas de manufactura' and m.group().strip()=='bpm':
  if not re.search(r'alimentos|manufactura|farmaceut|produccion|higiene|inocuidad',text):return False
 # Company activity is not a competence of the candidate.
 business=list(BUSINESS.finditer(prefix))
 if business and not PROFILE.search(prefix[business[-1].end():]):return False
 if NEGATIVE.search(prefix):return False
 if term in {'Inglés','Francés','Portugués','Alemán','Italiano','Catalán'}:
  if re.search(r'(?:oferta|ofrece|programas|cursos) (?:para incluir |de |en )?$',prefix):return False
 # A sales bonus or a company's sales department alone is not a skill.
 if term=='Ventas':
  if re.search(r'(?:bono|bonificacion|comisiones?) (?:por |sobre |de )?$',prefix):return False
  if re.search(r'(?:departamento|area|sector) de\s*$',prefix):return False
 return True
@functools.lru_cache(maxsize=50000)
# Un concepto cuenta como presente una sola vez en cada descripción.
def detect(raw):
 text=norm(raw);found=[]
 for i,(r,ts) in enumerate(zip(rx,triggers)):
  if ts and not any(t in text for t in ts):continue
  if any(accepted(skills[i],text,m) for m in r.finditer(text)):found.append(i)
 return found
# El frontend usa estas categorías para construir las cinco tarjetas.
def categories():return [{'id':c,'terms':[e['term'] for e in catalog if e['category']==c]} for c in ['transversales','tecnicas','conocimientos','herramientas','idiomas']]

METHOD="Menciones explícitas con normalización de espacios, reparación conservadora de caracteres y exclusiones parciales de contexto. No distingue de forma completa requisitos obligatorios y deseables; las coincidencias requieren revisión humana para validación semántica."
