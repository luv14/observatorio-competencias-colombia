// Catálogo territorial analítico UNAD: identificador, nombre, color y departamentos.
// La pertenencia se compara por texto exacto con el CSV. No equivale a límites de centros.
// Si cambia una zona, revisar departamentos, botones y geometría SVG en index.html.
const UNAD_ZONES = [
  {
    id: "ZCAR",
    name: "Zona Caribe",
    color: "#005883",
    deps: [
      "ATLÁNTICO",
      "BOLÍVAR",
      "CESAR",
      "CÓRDOBA",
      "LA GUAJIRA",
      "MAGDALENA",
      "SUCRE",
      "ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA",
    ],
    source: "https://caribe.unad.edu.co/",
  },
  {
    id: "ZOCC",
    name: "Zona Occidente",
    color: "#F0B429",
    deps: ["ANTIOQUIA", "CALDAS", "CHOCÓ", "QUINDIO", "RISARALDA"],
    source: "https://occidente.unad.edu.co/",
  },
  {
    id: "ZCORI",
    name: "Zona Centro Oriente",
    color: "#F47920",
    deps: ["SANTANDER", "NORTE DE SANTANDER", "ARAUCA"],
    source: "https://centroriente.unad.edu.co/",
  },
  {
    id: "ZCBOY",
    name: "Zona Centro Boyacá",
    color: "#50B748",
    deps: ["BOYACÁ"],
    source: "https://boyaca.unad.edu.co/",
  },
  {
    id: "ZCBC",
    name: "Zona Centro Bogotá - Cundinamarca",
    color: "#A54686",
    deps: ["BOGOTÁ, D.C.", "CUNDINAMARCA"],
    source: "https://bogota.unad.edu.co/",
  },
  {
    id: "ZCSUR",
    name: "Zona Centro Sur",
    color: "#43C7F4",
    deps: ["VALLE DEL CAUCA", "CAUCA", "NARIÑO"],
    source: "https://centrosur.unad.edu.co/",
  },
  {
    id: "ZSUR",
    name: "Zona Sur",
    color: "#668DA4",
    deps: ["TOLIMA", "HUILA", "CAQUETÁ", "PUTUMAYO"],
    source: "https://sur.unad.edu.co/",
  },
  {
    id: "ZAO",
    name: "Zona Amazonia y Orinoquia",
    color: "#F8D27F",
    deps: [
      "AMAZONAS",
      "META",
      "CASANARE",
      "GUAVIARE",
      "GUAINÍA",
      "VAUPÉS",
      "VICHADA",
    ],
    source: "https://amazonia.unad.edu.co/",
  },
];
