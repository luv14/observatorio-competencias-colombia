"""Regression checks for normalization and ambiguous dictionary mentions."""
"""Ejemplos de regresión: verificar detección y exclusiones al editar reglas."""
import unittest
from skills import detect,skills,norm

def terms(s):return {skills[i] for i in detect(s)}
class DictionaryTests(unittest.TestCase):
 def test_unicode_spaces(self):
  self.assertIn('Servicio al cliente',terms('Habilidades de atención\u00a0al\u00a0cliente.'))
  self.assertEqual(norm('Trabajo\n en\t equipo'),'trabajo en equipo')
 def test_mojibake(self):
  self.assertIn('Conducción',terms('Requiere licencia de conducciÃ³n.'))
  self.assertIn('Trabajo en equipo',terms('trabajo\u00a0en\u00a0equipo'))
  self.assertIn('Limpieza y desinfección',terms('Funciones de desinfecciÃ³n.'))
 def test_sales_context(self):
  self.assertNotIn('Ventas',terms('Empresa dedicada a ventas de productos.'))
  self.assertNotIn('Ventas',terms('Ofrecemos comisiones por ventas.'))
  self.assertNotIn('Ventas',terms('Trabajará en el departamento de ventas.'))
  self.assertIn('Ventas',terms('Empresa del sector financiero buscando asesor con experiencia en ventas.'))
  self.assertIn('Ventas',terms('Funciones: realizar ventas y atender clientes.'))
 def test_negation(self):
  self.assertNotIn('Alemán',terms('No se requiere conocimiento previo de alemán.'))
  self.assertIn('Alemán',terms('Se requiere dominio de alemán.'))
 def test_company_activity(self):
  self.assertNotIn('Limpieza y desinfección',terms('Quick es una plataforma de soluciones de limpieza y mantenimiento. Buscamos auxiliar de bodega.'))
  self.assertIn('Limpieza y desinfección',terms('Funciones: realizar limpieza y desinfección de equipos.'))
 def test_sectors(self):
  for label,text in [('Picking','Funciones: picking y packing de productos.'),('Confección','Requisitos: experiencia en máquinas de confección.'),('Toma de muestras','Experiencia en toma de muestras.'),('Siembra y cosecha','Funciones: siembra y cosecha.'),('Power Automate','Conocimientos de Power Automate.'),('Conducción','Licencia C2 vigente.')]:self.assertIn(label,terms(text))
 def test_ambiguous_acronym(self):
  self.assertNotIn('Buenas prácticas de manufactura',terms('Conocimientos en BPM para modelar procesos de software.'))
  self.assertIn('Buenas prácticas de manufactura',terms('Producción de alimentos. Requisitos: conocimientos de BPM.'))
 def test_word_boundaries(self):
  self.assertNotIn('Java',terms('Conocimientos de JavaScript.'))
  self.assertNotIn('SQL',terms('Manejo de MySQL.'))
  self.assertEqual(terms('Manejo de C# y C++'),{'C#','C++'})
if __name__=='__main__':unittest.main()
