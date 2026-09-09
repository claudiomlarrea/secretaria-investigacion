/**
 * Cifras verificables de la Secretaría (actualizar cuando cambien).
 * sistemas / equipo se cuentan desde el HTML.
 * publicaciones, visitas y el índice abierto se completan en runtime.
 */
window.SEC_NUMEROS = {
  items: [
    {
      id: "equipo",
      value: 5,
      labelEs: "Personas en el equipo",
      labelEn: "Team members",
      href: "#equipo",
      fromEquipo: true
    },
    {
      id: "sistemas",
      value: 11,
      labelEs: "Aplicaciones IA",
      labelEn: "AI apps",
      href: "#herramientas",
      fromHerramientas: true
    },
    {
      id: "publicaciones",
      value: null,
      labelEs: "Publicaciones registradas",
      labelEn: "Recorded publications",
      href: "#publicaciones",
      fromPublicaciones: true
    },
    {
      id: "publicaciones-mundo",
      value: null,
      labelEs: "Publicaciones científicas en el mundo",
      labelEn: "Scientific publications worldwide",
      href: "#publicaciones-uccuyo",
      fromOpenAlex: true
    },
    {
      id: "visitas",
      value: null,
      labelEs: "Visitas con origen",
      labelEn: "Visits with origin",
      href: "#visitas",
      fromVisitas: true
    },
    {
      id: "paises",
      value: null,
      labelEs: "Países",
      labelEn: "Countries",
      href: "#visitas",
      fromPaises: true
    },
    {
      id: "provincias",
      value: null,
      labelEs: "Provincias / regiones",
      labelEn: "Provinces / regions",
      href: "#visitas",
      fromRegiones: true
    },
    {
      id: "uvt",
      value: 1,
      labelEs: "Unidad de Vinculación Tecnológica",
      labelEn: "Technology Transfer Unit",
      href: "#uvt"
    }
  ],
  editorialEs:
    "Indicadores del portal institucional: se actualizan con el equipo, las aplicaciones, la Biblioteca y las visitas.",
  editorialEn:
    "Institutional portal indicators: they update from the team, the apps, the Library, and visits."
};
