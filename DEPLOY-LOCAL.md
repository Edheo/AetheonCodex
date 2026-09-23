# Publicacion local en IIS

Desde PowerShell, en la raiz del repositorio:

```powershell
.\deploy-local.ps1 -WhatIf    # Describe la operacion sin construir ni escribir.
.\deploy-local.ps1 -BuildOnly # Ejecuta el build completo sin tocar IIS.
.\deploy-local.ps1            # Construye y publica en C:\inetpub\AetheonCodex.
```

Tambien se puede invocar el script por su ruta completa desde otra carpeta.
Reutiliza `Invoke-AetheonPython` de `release-tools.ps1` y `scripts/build.py`,
incluidas todas sus etapas y MkDocs. Como cualquier build del proyecto,
regenera `docs/` y `site/`. No requiere commits ni cambia versiones, ramas o tags.
`start-release.ps1`, `finish-release.ps1` y GitHub Pages siguen disponibles.

## Requisitos

- Windows, PowerShell, Robocopy y las dependencias de `requirements.txt` instaladas
  preferiblemente en `.venv` (se usa la misma seleccion de Python que las releases).
- IIS configurado para contenido estatico, con `index.html` como documento
  predeterminado y ruta fisica `C:\inetpub\AetheonCodex`.
- Permisos para crear y renombrar carpetas en `C:\inetpub`, leer el sitio actual
  y aplicar sus permisos al staging. Puede ser necesario ejecutar PowerShell
  como administrador. El script no se eleva ni cambia la configuracion de IIS.
- La identidad que sirve el sitio debe tener lectura y ejecucion. Si el destino
  existe, se copia su ACL raiz; los nuevos archivos heredan esa ACL. Si no existe,
  se heredan los permisos de `C:\inetpub`. Los permisos particulares de archivos
  o subcarpetas anteriores no se trasladan: usa permisos heredables en la raiz.

## Actualizacion y recuperacion

El destino debe dedicarse al sitio generado. Tras un build correcto y un
`index.html` no vacio, se prepara una carpeta hermana nueva y se copia `site/`.
Se conserva el `web.config` raiz del destino si existe (tiene prioridad sobre
el generado). Otros archivos manuales quedan solo en la copia anterior.
Se rechazan enlaces y junctions en origen, destino y sus ancestros.

Solo al terminar la copia se renombra el destino como
`C:\inetpub\AetheonCodex-backup-FECHA-ID` y se coloca el staging en su lugar.
Asi desaparecen del sitio los archivos obsoletos sin borrar la version anterior.
Hay un breve intervalo entre los dos renombrados: no es un cambio atomico ni
una garantia de disponibilidad continua. Si IIS u otro proceso bloquea el
renombrado, la operacion falla; puede ser necesario parar el sitio antes de repetir.
Si falla el segundo renombrado se intenta restaurar el anterior automaticamente.
Un fallo devuelve codigo 1; Robocopy considera correctos los codigos 0 a 7.

Las copias y los staging fallidos se conservan, consumen espacio y deben retirarse
manualmente tras comprobar el resultado. No configures IIS para servir las
carpetas hermanas de respaldo. Para recuperar una copia manualmente, detén el
sitio, aparta el destino actual y devuelve la copia a `AetheonCodex`; después
reinicia el sitio. Los mensajes indican la ubicacion conservada si falla la
restauracion automatica. Evita modificar las carpetas durante la publicacion.
