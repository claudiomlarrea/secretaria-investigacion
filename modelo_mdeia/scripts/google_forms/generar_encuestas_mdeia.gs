/**
 * MDeIA UCCuyo — Generador de encuestas Google Forms
 * Uso: script.google.com → Nuevo proyecto → pegar → ejecutar crearTodasLasEncuestasMDeIA
 * Requiere autorizar Google Forms. Al final verás en Registro los enlaces para compartir.
 */

var UNIDADES_MDEIA = ["Departamento Administrativo Sede San Juan", "Departamento Administrativo Sede San Luis", "ECRyPSJ- Escuela de Cultura Religiosa y Pastoral Sede San Juan", "ESEGSJ- Escuela de Seguridad Sede San Juan", "FBOSCO- Facultad Don Bosco Sede Mendoza", "FCEESJ- Facultad de Ciencias Económicas y Empresariales Sede San Juan", "FCEESL- Facultad de Ciencias Económicas y Empresariales Sede San Luis", "FCMSJ- Facultad de Ciencias Médicas Sede San Juan", "FCMSL- Facultad de Ciencias Médicas Sede San Luis", "FCQyTSJ- Facultad de Ciencias Químicas y Tecnológicas Sede San Juan", "FCVSL- Facultad de Ciencias Veterinarias Sede San Luis", "FDCSSJ- Facultad de Derecho y Ciencias Sociales Sede San Juan", "FDCSSL- Facultad de Derecho y Ciencias Sociales Sede San Luis", "FFyHSJ- Facultad de Filosofía y Humanidades Sede San Juan", "ISB- Instituto de Formación Docente San Buenaventura Sede San Juan", "ISDSM- Instituto de Formación Docente Santa María Sede San Juan", "OIA- Observatorio de Inteligencia Artificial", "Secretaría de Extensión", "Secretaría de Investigación", "UCCuyo — Universidad Católica de Cuyo (institución completa)"];

function crearTodasLasEncuestasMDeIA() {
  var enlaces = [];
  enlaces.push(crearFormulario_estudiante());
  enlaces.push(crearFormulario_docente());
  enlaces.push(crearFormulario_autoridad());
  enlaces.push(crearFormulario_administracion());
  Logger.log(enlaces.join('\n'));
  return enlaces;
}

function crearFormulario_estudiante() {
  var form = FormApp.create("MDeIA UCCuyo — Encuesta Estudiantes");
  form.setDescription("Uso de IA, servicios digitales y satisfacción con plataformas institucionales.");
  form.setIsQuiz(false);
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.setConfirmationMessage('Gracias. Sus respuestas alimentan el diagnóstico MDeIA UCCuyo.');
  var item = form.addListItem().setTitle("META_SEDE").setHelpText("¿En qué sede cursás principalmente?");
  item.setChoices(["San Juan", "San Luis", "Mendoza", "Otra / no aplica"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("META_UNIDAD").setHelpText("Facultad o unidad académica (lista oficial MDeIA UCCuyo)");
  item.setChoices(UNIDADES_MDEIA.map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_IA_USO__chatgpt").setHelpText("¿Con qué frecuencia usás herramientas de IA generativa (ChatGPT, Gemini, Copilot, etc.) para tus estudios?");
  item.setChoices(["Nunca", "Rara vez", "A veces", "Frecuentemente", "Siempre"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_IA_USO__traduccion").setHelpText("¿Con qué frecuencia usás IA para traducir o mejorar textos académicos?");
  item.setChoices(["Nunca", "Rara vez", "A veces", "Frecuentemente", "Siempre"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_IA_USO__resumenes").setHelpText("¿Con qué frecuencia usás IA para resumir bibliografía o apuntes?");
  item.setChoices(["Nunca", "Rara vez", "A veces", "Frecuentemente", "Siempre"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_IA_USO__codigo").setHelpText("¿Con qué frecuencia usás IA para programación o análisis de datos en tus materias?");
  item.setChoices(["Nunca", "Rara vez", "A veces", "Frecuentemente", "Siempre"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(false);
  var item = form.addListItem().setTitle("IND_GUIA_IA__conocimiento").setHelpText("¿Conocés la guía o normativa institucional sobre uso responsable de IA?");
  item.setChoices(["No", "Sí", "No sé"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_APP_INST__uso").setHelpText("¿Con qué frecuencia usás la app o portal institucional de la universidad (campus, SIU, etc.)?");
  item.setChoices(["Nunca", "Rara vez", "A veces", "Frecuentemente", "Siempre"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_CAU__conoce").setHelpText("¿Sabés cómo contactar al Centro de Atención al Usuario / mesa de ayuda TI?");
  item.setChoices(["No", "Sí"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_CAU__satisfaccion").setHelpText("Si contactaste soporte TI, ¿qué tan satisfecho/a quedaste con la respuesta?");
  item.setChoices(["Totalmente en desacuerdo", "En desacuerdo", "Ni de acuerdo ni en desacuerdo", "De acuerdo", "Totalmente de acuerdo"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(false);
  var item = form.addListItem().setTitle("IND_LMS__satisfaccion").setHelpText("¿Qué tan satisfecho/a estás con el aula virtual / LMS de la universidad?");
  item.setChoices(["Totalmente en desacuerdo", "En desacuerdo", "Ni de acuerdo ni en desacuerdo", "De acuerdo", "Totalmente de acuerdo"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_WIFI__satisfaccion").setHelpText("¿Qué tan satisfecho/a estás con la conectividad WiFi en la sede?");
  item.setChoices(["Totalmente en desacuerdo", "En desacuerdo", "Ni de acuerdo ni en desacuerdo", "De acuerdo", "Totalmente de acuerdo"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_TRAMITES__satisfaccion").setHelpText("¿Qué tan satisfecho/a estás con los trámites online disponibles (inscripciones, certificados, etc.)?");
  item.setChoices(["Totalmente en desacuerdo", "En desacuerdo", "Ni de acuerdo ni en desacuerdo", "De acuerdo", "Totalmente de acuerdo"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var url = form.getPublishedUrl();
  Logger.log('Formulario Estudiantes: ' + url);
  return url;
}

function crearFormulario_docente() {
  var form = FormApp.create("MDeIA UCCuyo — Encuesta Docentes");
  form.setDescription("Formación en IA, integridad académica, LMS y evaluación auténtica.");
  form.setIsQuiz(false);
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.setConfirmationMessage('Gracias. Sus respuestas alimentan el diagnóstico MDeIA UCCuyo.');
  var item = form.addListItem().setTitle("META_SEDE").setHelpText("¿En qué sede desarrollás principalmente tu actividad docente?");
  item.setChoices(["San Juan", "San Luis", "Mendoza", "Otra / no aplica"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("META_UNIDAD").setHelpText("Facultad o departamento académico (lista oficial MDeIA UCCuyo)");
  item.setChoices(UNIDADES_MDEIA.map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_FORM_IA__recibida").setHelpText("¿Qué nivel de formación formal recibiste sobre IA aplicada a la docencia?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_IA_USO__planificacion").setHelpText("¿Con qué frecuencia usás IA para planificar clases, materiales o rúbricas?");
  item.setChoices(["Nunca", "Rara vez", "A veces", "Frecuentemente", "Siempre"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_IA_USO__evaluacion").setHelpText("¿Con qué frecuencia usás IA en el diseño o corrección de evaluaciones?");
  item.setChoices(["Nunca", "Rara vez", "A veces", "Frecuentemente", "Siempre"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_INTEGRIDAD__guia_catedra").setHelpText("¿Tu cátedra cuenta con guía explícita de integridad académica que contempla el uso de IA?");
  item.setChoices(["No", "En elaboración", "Sí"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_EVAL_AUTENTICA__practicas").setHelpText("¿En qué nivel implementás evaluaciones auténticas que reducen la dependencia de IA no declarada?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_GUIA_ETICA__conocimiento").setHelpText("¿Conocés y aplicás la guía institucional de uso responsable de IA generativa?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_LMS__uso_avanzado").setHelpText("¿En qué nivel usás funcionalidades avanzadas del LMS (foros, entregas, videoclase, analítica)?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_ALFABETIZACION__aplicacion").setHelpText("¿En qué nivel incorporás alfabetización algorítmica y pedagogía con IA en tu práctica docente?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_COMINNOVA__conocimiento").setHelpText("¿Conocés las recomendaciones de la Comisión de Innovación Docente sobre nuevas tecnologías?");
  item.setChoices(["No", "Sí"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(false);
  var url = form.getPublishedUrl();
  Logger.log('Formulario Docentes: ' + url);
  return url;
}

function crearFormulario_autoridad() {
  var form = FormApp.create("MDeIA UCCuyo — Encuesta Autoridades");
  form.setDescription("Estrategia digital, gobierno TI, financiación y gobernanza de IA (rectorado, decanato, secretarías).");
  form.setIsQuiz(false);
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.setConfirmationMessage('Gracias. Sus respuestas alimentan el diagnóstico MDeIA UCCuyo.');
  var item = form.addTextItem().setTitle("META_CARGO").setHelpText("Cargo o rol institucional");
  item.setRequired(false);
  var item = form.addListItem().setTitle("META_SEDE").setHelpText("Ámbito de evaluación");
  item.setChoices(["Institución completa", "Sede San Juan", "Sede San Luis", "Sede Mendoza"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_ESTRATEGIA_DIGITAL").setHelpText("¿En qué nivel la institución dispone de estrategia digital alineada con la estrategia institucional?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_ESTRATEGIA_UNI").setHelpText("¿En qué nivel existe estrategia de negocio institucional formalmente definida?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_LIDERAZGO_RECTOR").setHelpText("¿En qué nivel el Rectorado y equipo de gestión lideran la planificación estratégica de TI y transformación digital?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_PLAN_TD").setHelpText("¿En qué nivel existe un Plan de Transformación Digital aprobado por el equipo de gestión?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_MODELO_GOBIERNO_TI").setHelpText("¿En qué nivel está implementado el modelo de gobierno de TI (roles, comités, políticas)?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_COMISION_ESTRATEGIA_TI").setHelpText("¿En qué nivel funciona un comité de estrategia y gobierno de TI?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_PLAN_FINANCIACION_TI").setHelpText("¿En qué nivel existe plan de financiación plurianual de TI alineado con la estrategia?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_GUIA_ETICA_IA").setHelpText("¿En qué nivel está aprobada e implementada la guía de uso responsable de IA generativa?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_ENCUESTA_IA_PERIODICA").setHelpText("¿En qué nivel la institución realiza encuestas periódicas sobre uso de IA en la comunidad?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_OBSERVATORIO_IA").setHelpText("¿En qué nivel está activo un observatorio o instancia de monitoreo de IA institucional?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var url = form.getPublishedUrl();
  Logger.log('Formulario Autoridades: ' + url);
  return url;
}

function crearFormulario_administracion() {
  var form = FormApp.create("MDeIA UCCuyo — Encuesta Personal administrativo");
  form.setDescription("Uso y satisfacción con sistemas de gestión, CAU y trámites digitalizados (depto. administrativo, secretarías).");
  form.setIsQuiz(false);
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.setConfirmationMessage('Gracias. Sus respuestas alimentan el diagnóstico MDeIA UCCuyo.');
  var item = form.addListItem().setTitle("META_SEDE").setHelpText("¿En qué sede trabajás?");
  item.setChoices(["San Juan", "San Luis", "Mendoza", "Otra / no aplica"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("META_AREA").setHelpText("Área o unidad institucional (lista oficial MDeIA UCCuyo)");
  item.setChoices(UNIDADES_MDEIA.map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_SIU__uso_diario").setHelpText("¿Con qué frecuencia usás SIU-Guaraní u otros sistemas de gestión académica en tu trabajo diario?");
  item.setChoices(["Nunca", "Rara vez", "A veces", "Frecuentemente", "Siempre"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_SIU__satisfaccion").setHelpText("¿Qué tan satisfecho/a estás con los sistemas de gestión académica (SIU, etc.)?");
  item.setChoices(["Totalmente en desacuerdo", "En desacuerdo", "Ni de acuerdo ni en desacuerdo", "De acuerdo", "Totalmente de acuerdo"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_CAU__contacto").setHelpText("¿Contactaste al CAU / mesa de ayuda TI en los últimos 12 meses?");
  item.setChoices(["No", "Sí"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_CAU__resolvio").setHelpText("Si contactaste, ¿el problema quedó resuelto satisfactoriamente?");
  item.setChoices(["No", "Sí"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(false);
  var item = form.addListItem().setTitle("IND_CAU__satisfaccion").setHelpText("¿Qué tan satisfecho/a estás con el soporte TI recibido?");
  item.setChoices(["Totalmente en desacuerdo", "En desacuerdo", "Ni de acuerdo ni en desacuerdo", "De acuerdo", "Totalmente de acuerdo"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(false);
  var item = form.addListItem().setTitle("IND_TRAMITES__digitalizados").setHelpText("¿En qué nivel los trámites de tu área están digitalizados y son usables sin papel?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_CAPACITACION_DIGITAL").setHelpText("¿En qué nivel recibís capacitación en herramientas digitales para tu puesto?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_PSERVTI__calidad").setHelpText("¿En qué nivel los servicios TI que usás son confiables, oportunos y adecuados a tu trabajo?");
  item.setChoices(["0 — No implementado", "1 — Inicial / ad hoc", "2 — En desarrollo", "3 — Implementado", "4 — Optimizado / referente"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var item = form.addListItem().setTitle("IND_GESTION__satisfaccion").setHelpText("¿Qué tan satisfecho/a estás con las herramientas de gestión administrativa (compras, mesa de entrada, etc.)?");
  item.setChoices(["Totalmente en desacuerdo", "En desacuerdo", "Ni de acuerdo ni en desacuerdo", "De acuerdo", "Totalmente de acuerdo"].map(function(o) { return item.createChoice(o); }));
  item.setRequired(true);
  var url = form.getPublishedUrl();
  Logger.log('Formulario Personal administrativo: ' + url);
  return url;
}
