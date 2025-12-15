Changelog
=========


1.7 (2025-12-15)
----------------

* [DOC] Memoize [Pilar Marinas]
* [FIX] Mode presetació obrir enllaç en finestra nova [Pilar Marinas]
* feat(tinymce): habilitar paste de imágenes desde clipboard [Pilar Marinas]

1.6 (2025-12-09)
----------------

* [FIX] Disable viewGDoc [Pilar Marinas]
* [ADD] Añadir los futuros en el filtro del año actual [Pilar Marinas]
* [DEL] Quitar purge_cache_varnish [Iago López]
* [FIX] Descargar gdoc [Iago López]
* Merge remote-tracking branch 'origin/develop' into rendimiento [Iago López]
* Merge remote-tracking branch 'origin/develop' into cancelar_firma [Iago López]
* [UPD] Limpieza [Iago López]
* [UDP] Avances cancelacion firma [Iago López]
* [UPD] Avances cancelacion [Iago López]
* [RENDIMIENTO] En las vistas filtradas solo calcular los elementos a mostrar por pagina y arreglar literal estado en sessiones [Pilar Marinas]
* [ADD] Aviso cuando se modifica o añade contenido en una session ya enviada a firmar o firmada [Iago López]
* [RENDIMIENTO] allOrgansEstatsLlista eliminar un getObject() 2 veces en la misma linea [Pilar Marinas]
* [UPD] Avances cancelacion firma [Iago López]
* [RENDIMIENTO] Optimizar ActaPrintView (Evitar getObject en bucles) [Pilar Marinas]
* [FIX] Para que los js cargen en la raiz y no den error [Pilar Marinas]
* [FIX] Para que los js cargen en la raiz y no den error [Pilar Marinas]
* [TESTING] test_filesinsidepunt_visibility [Pilar Marinas]
* [FIX] Controlar la prioridad de roles [Iago López]
* [RENDIMIENTO] Hacer hasdcode el filtro por años empieza 2016 [Pilar Marinas]
* [RENDIMIENTO] Filtrar vista actas por años [Pilar Marinas]
* [UPD] Añadir boton de cancelacion en estado realizada tambien [Iago López]
* [RENDIMIENTO] Filtrar vista sessiones por años [Pilar Marinas]
* [RENDIMIENTO] Filtrar vista acords por años [Pilar Marinas]
* [ADD] Cancelar firma [Iago López]

1.5 (2025-12-01)
----------------

* [RENDIMIENTO] Imagenes lazy y async [Pilar Marinas]
* [ADD] Si tenemos unidaddocumental no mostramos vista presentacion [Iago López]
* [RENDIMIENTO] Comentar los subcribers de purge_cache_varnish_organs [Pilar Marinas]
* [RENDIMIENTO] Añadido defer a todos los scripts para no bloquear rendering [Pilar Marinas]
* [UPD] Añadir nuevos estados de la firma y mejora de los estilos de estos [Iago López]
* [FIX] signSessio target [Iago López]
* [UPD] Cambiar visibilidad documentacion y ficheros en la session [Iago López]
* [FIX] Corregir visibilidad ficheros y documentos (falta arreglar session) [Iago López]
* [FIX] Presentation - ficheros sin fichero se les mostraba el boton de abrir el modal del fichero publico, se ha quitado porque no hay contenido [Iago López]
* [FIX] Badge estado firma no se veia bien [Iago López]
* [UPD] Print CSS no mostrar usercentrics [Iago López]
* [UPD] Path TMP_FOLDER añadir / al final [Iago López]
* [UPD] Quitar data-bs-backdrop y data-bs-keyboard de modales [Iago López]
* [FIX / RENDIMIENTO] Quitar atributos new_tab y utilizar directamente target [Iago López]
* [RENDIMIENTO - TEST] portlet la meva vinculacio [Pilar Marinas]
* [TESTING] Añadir test para ver que search muestra la meva vinculacio [Pilar Marinas]
* [RENDIMIENTO]Solucionar error search la meva vinculació [Pilar Marinas]
* [FIX] Visualizacion iconos dobles, no se veian juntos [Iago López]
* [UPD] Quitar python pt session [Iago López]
* [RENDIMIENTO] Mejorar carga browser search optimization [Pilar Marinas]
* [UPD] Solo mantejar pdf en el contenido file [Iago López]
* [RENDIMIENTO] Mejorar carga portlet_calendar optimization [Pilar Marinas]
* [UPD] Ruta TMDIR [Iago López]
* [RENDIMIENTO] Solucionar error si no hay acta actaData/isSigned [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga votacion en acord [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga votacio_acord [Pilar Marinas]
* [FIX] no se podia votar [Iago López]
* [RENDIMIENTO] Mejorar carga sessio manual_import optimization [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga sessio mail_message quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga sessio mail_informar quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga sessio mail_convocar quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga sessio excusar_assist quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga sessio butlleti quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga punt/subpunt quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga file quitando python del template PDT revisar quitar ficheros que no sean PDF [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga audio quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga annex quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga acta quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga acord quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga firma session quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga presentation quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Mejorar carga session quitando python del template [Pilar Marinas]
* [RENDIMIENTO] Quitar llamadas duplicadas [Iago López]
* [RENDIMIENTO] Quitar doble comprobacion del rol en lamevavinculacio [Iago López]
* [UPD] Estilos print tablas [Iago López]

1.4 (2025-11-24)
----------------

* Merge remote-tracking branch 'origin/rendimiento' [Iago López]
* [UPD] Evitar error merge [Iago López]

1.3 (2025-11-24)
----------------

* [UPD] Reducir texto print [Iago López]
* [FIX] Visualizacion composicion govern [Iago López]
* [UPD] Cambiar variable entorno TMPFOLDER a TMPDIR [Iago López]
* [UPD] organType solo modificable por webmaster o manager [Iago López]
* [FIX] Votaciones listado ver mensaje de acord sin numeracio si no tiene [Iago López]
* [UPD] Presentation flex [Iago López]

1.2 (2025-11-18)
----------------

* [FIX] Accion creacion punto [Iago López]

1.1 (2025-11-18)
----------------

* [UPD] Mejora visualizacion errores signSessio [Iago López]
* [UPD] Mejoras pt [Iago López]
* [FIX] Secretario le salia el enlace a la configuracion del sitio pero no tiene permisos [Iago López]
* [FIX] Traducciones workflows [Iago López]
* [FIX] No mostrar organs no publicos en el portlet de navegacion si no tienes permisos [Iago López]

0.1 (2025-10-23)
----------------

- Initial release
