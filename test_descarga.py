"""Pruebas sin red: descarga válida y protección ante archivos incompletos."""
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import descargar_ofertas as module


class Response(io.BytesIO):
    def __init__(self, content, length=None):
        super().__init__(content)
        self.headers = {'Content-Type': 'text/csv', 'Content-Length': str(len(content) if length is None else length)}


class DownloadTests(unittest.TestCase):
    csv = 'CODIGO_VACANTE;DESCRIPCION_VACANTE;DEPARTAMENTO;MUNICIPIO\n1;"Comunicación\ny Excel";VALLE;CALI\n'.encode('utf-8-sig')

    def test_success(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'ofertas.csv'
            with patch.object(module, 'request_json', side_effect=[{'jobId': 'abc-123'}, {'status': 'completed'}]), patch.object(module, 'urlopen', return_value=Response(self.csv)):
                module.download(target)
            self.assertEqual(target.read_bytes(), self.csv)
            self.assertFalse(target.with_suffix('.csv.part').exists())

    def test_incomplete_preserves_existing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'ofertas.csv'
            target.write_bytes(b'previous')
            with patch.object(module, 'request_json', side_effect=[{'jobId': 'abc'}, {'status': 'completed'}]), patch.object(module, 'urlopen', return_value=Response(self.csv, len(self.csv) + 1)):
                with self.assertRaises(ValueError):
                    module.download(target)
            self.assertEqual(target.read_bytes(), b'previous')
            self.assertFalse(target.with_suffix('.csv.part').exists())

    def test_rejects_empty_or_invalid_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'ofertas.csv'
            for content in ('incorrecto\n1\n', self.csv.decode('utf-8-sig').split('\n')[0] + '\n'):
                target.write_text(content, encoding='utf-8')
                with self.assertRaises((ValueError, module.csv.Error)):
                    module.validate_csv(target)
