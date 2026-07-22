 ### 📸 Checklist de Evidencias (Final)                                                                                                
                                                                                                                                        
  1. Análisis Estático, CI/CD y Backend (Responsable: Julio)                                                                            
                                                                                                                                        
  [ ] Imagen: Captura del dashboard de SonarCloud mostrando la Deuda Técnica Inicial (antes de corregir el código).                     
  [ ] Imagen: Captura del dashboard de SonarCloud mostrando la mejora y la Deuda Técnica Final.                                         
  [ ] Código: Fragmento o captura de pantalla de su archivo YAML de Integración Continua (ej. .github/workflows/sonar.yml o el pipeline 
  de tests) para demostrar que automatizaron el proceso en GitHub.                                                                      
  [ ] Código: Un pequeño bloque (4-8 líneas) de un script de pytest que haya creado para testear el backend (ej. una prueba del endpoint
  de audio).                                                                                                                            
  [ ] Imagen: Captura de la terminal mostrando las pruebas de pytest terminando con éxito (en verde).                                   
                                                                                                                                        
  2. Pruebas Automatizadas Frontend (Responsable: Mesias)                                                                               
                                                                                                                                        
  [ ] Código: Un pequeño bloque de código de uno de los scripts de automatización E2E que haya hecho en Cypress (o Jest) validando      
  flujos de Next.js.                                                                                                                    
  [ ] Imagen: Captura de pantalla de la interfaz de Cypress corriendo los tests (o el log de la terminal) demostrando que los flujos    
  pasaron con éxito.                                                                                                                    
                                                                                                                                        
  3. Pruebas Manuales, Diseño y Rastreo (Responsable: Gabriel)                                                                          
                                                                                                                                        
  [ ] Documento: La Matriz de Rastreabilidad completamente llena (mapeando los casos CP-01 a CP-10 con los requerimientos).             
  [ ] Imagen: Por cada caso manual exitoso, una captura de pantalla de la aplicación web demostrando que el flujo funcionó (ej.         
  mostrando una transcripción completada en la interfaz).                                                                               
  [ ] Imagen: Capturas de pantalla de los tickets tipo "Bug" creados en Jira. Se debe ver claramente su descripción, severidad y la     
  imagen adjunta del fallo original.                                                                                                    
  [ ] Imagen (Re-testing): Capturas de pantalla de los comentarios en los tickets de Jira, donde Gabriel confirma que volvió a probar el
  bug (después de que Julio o Mesias lo arreglaran) y autoriza pasarlo a Done.                                                          
                                                                                                                                        
  4. Gestión, Métricas Consolidadas y Demostración (Responsable: Denise)                                                                
                                                                                                                                        
  [ ] Imagen: Captura panorámica del tablero Kanban de Jira, evidenciando cómo fluyeron las historias y los bugs desde To Do hasta Done.
  [ ] Métricas Documentadas: En el texto del informe, un pequeño resumen de Denise calculando la Densidad de Defectos (cuántos bugs     
  hallaron por cada historia de usuario probada) y el Test Pass Rate (qué porcentaje de casos pasaron frente a los fallidos).           
  [ ] Video Demostrativo: El enlace al video final (5-7 mins) mostrando al profesor todo funcionando en conjunto: el tablero de Jira,   
  las pruebas automáticas corriendo en la terminal, y la plataforma web en uso.                                                         
                                                                                                                                        
  Con este balance entre capturas de gestión (Jira/SonarCloud) y fragmentos de código de pruebas reales (pytest/Cypress), su documento  
  será irrefutable.                                                                                                                     

────────────────────────────────────────────────────────────
> ahh, y cierto, verás hay mas casos de prueba en @[docs/sqa/zephyr.csv]

▸ Thought for 6s, 406 tokens
  Prioritizing Tool Usage

● Read(D:/SpeechNotes/docs/sqa/zephyr.csv) (ctrl+o to expand)

▸ Thought for 1s, 521 tokens
  Prioritizing Tool Usage

● Bash(python -c "import sys; content = open('SQA_Plan_Template.tex', 'r', encoding='utf-8').read(); content = content...) (ctrl+o to
expand)

▸ Thought for 5s, 277 tokens
  Prioritizing Tool Usage
● Schedule(120s: Check task 193 status) (ctrl+o to expand)

▸ Thought Process
  Prioritizing Tool Usage
  ¡Muy buena observación! No me había percatado de que la base de datos de Zephyr tenía un total de 17 casos de prueba (CP-01 al CP-17),
  que incluyen validaciones más profundas como "Login con credenciales incorrectas", "Bloqueo de rutas administrativas", etc.           
                                                                                                                                        
  Ya actualicé todos los lugares en el documento PDF donde antes decía "CP-01 al CP-10", "10 Casos" o "10 flujos" para que ahora refleje
  correctamente que la cobertura es de 17 casos de prueba. El PDF actualizado está en la misma ubicación:                               
  SQA_Plan_Template.pdf                                                                                                                 
                                                                                                                                        
  Aquí tienes la lista de evidencias final ajustada para Gabriel con los 17 casos:                                                      
                                                                                                                                        
  ### 📸 Checklist de Evidencias (Ajustado)                                                                                             
                                                                                                                                        
  1. Análisis Estático, CI/CD y Backend (Responsable: Julio)                                                                            
                                                                                                                                        
  [ ] Imagen: Captura de SonarCloud con la Deuda Técnica Inicial.                                                                       
  [ ] Imagen: Captura de SonarCloud con la Deuda Técnica Final (mejorada).                                                              
  [ ] Código: Fragmento del YAML de Integración Continua (GitHub Actions).                                                              
  [ ] Código: Un pequeño bloque de un script de pytest validando algo del backend.                                                      
  [ ] Imagen: Captura de la terminal con las pruebas de pytest en verde.                                                                
                                                                                                                                        
  2. Pruebas Automatizadas Frontend (Responsable: Mesias)                                                                               
                                                                                                                                        
  [ ] Código: Bloque de código E2E en Cypress probando Next.js.                                                                         
  [ ] Imagen: Pantallazo de Cypress/terminal ejecutando exitosamente los tests.                                                         
                                                                                                                                        
  3. Pruebas Manuales, Diseño y Rastreo (Responsable: Gabriel)                                                                          
                                                                                                                                        
  [ ] Documento: Matriz de Rastreabilidad mapeando los 17 casos (CP-01 a CP-17) con los requerimientos originales.                      
  [ ] Imagen: Por cada caso manual de los 17 que pase con éxito, foto de la aplicación demostrando el flujo operando bien.              
  [ ] Imagen: Capturas de los tickets tipo "Bug" en Jira (si falló alguno de los 17 casos).                                             
  [ ] Imagen: Capturas de Re-testing en los comentarios de Jira, aprobando el pase a Done de los bugs solucionados.                     
                                                                                                                                        
  4. Gestión, Métricas Consolidadas y Demostración (Responsable: Denise)                                                                
                                                                                                                                        
  [ ] Imagen: Tablero Kanban de Jira mostrando todas las historias de los 17 casos moviéndose hasta Done.                               
  [ ] Métricas Documentadas: Cálculo de la Densidad de Defectos y el Test Pass Rate (basado en los 17 casos).                           
  [ ] Video Demostrativo: Enlace al video final exhibiendo todo operando.                            