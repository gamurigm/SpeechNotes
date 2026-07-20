# Suite frontend de QA (Persona C)

La carpeta contiene dos niveles de prueba:

- `unit/`: pruebas Jest + Testing Library de los controles de grabación y de la vista de transcripción.
- `e2e/`: Cypress recorre el dashboard real con autenticación demo, micrófono de navegador simulado y un backend Socket.IO local controlado por la prueba.

## Ejecución

Desde `web/`:

```powershell
npm ci
npm run test:unit
npm run test:e2e
```

Para ejecutar ambas suites en orden:

```powershell
npm run test:frontend
```

Las capturas de Cypress se guardan en `tests/evidence/screenshots/`. El backend simulado escucha únicamente durante Cypress en `127.0.0.1:9443`; por ello el puerto debe estar libre y no hace falta iniciar la API Python real. La autenticación usa una base temporal en `.next/e2e.db`, por lo que `web/dev.db` no se modifica.
