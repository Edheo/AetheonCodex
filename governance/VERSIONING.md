# Versionado de Aetheon

Esta guía describe el flujo que implementan actualmente los scripts del repositorio. La versión canónica se guarda en `VERSION` y usa el formato `X.Y.Z`; las releases nuevas se etiquetan sin prefijo `v`.

## Ramas

- `master`: historial publicado. Recibe cada `release/X.Y.Z` mediante un merge `--no-ff`.
- `develop`: integración del trabajo futuro. Es el único punto de partida admitido por `start-release.ps1` y, tras cerrar una release, recibe `master` y queda como rama activa.
- `feature/*`: trabajo aislado. No hay scripts específicos para crear o cerrar features.
- `release/X.Y.Z`: preparación de una versión concreta. `start-release.ps1` la crea y `finish-release.ps1` exige este nombre exacto.

No se trabaja directamente en `master`. Durante la preparación de una release, las correcciones destinadas a esa versión se hacen y se commitean en su rama `release/*`.

## Features

Los scripts no automatizan este flujo. Una feature se crea desde `develop` actualizado y limpio:

```powershell
git switch develop
git pull --ff-only
git switch -c feature/nombre
```

Trabaja, revisa y commitea normalmente. Para compartir la rama puede usarse:

```powershell
.\publish-release.ps1
```

Aunque conserva ese nombre, este script admite cualquier rama activa: construye el proyecto, comprueba el estado remoto y ejecuta `git push -u origin <rama>` tras pedir confirmación.

Cuando la feature esté terminada, intégrala en `develop` y publica `develop`:

```powershell
git switch develop
git pull --ff-only
git merge --no-ff feature/nombre
.\publish-release.ps1
git branch -d feature/nombre
```

Si la rama remota ya no es necesaria, su eliminación es una operación manual. Antes del merge deben ejecutarse las revisiones adecuadas al cambio; los scripts no imponen pruebas específicas para features.

## Preparar una release

Precondiciones de `start-release.ps1`:

- estar en `develop`, con una rama activa y el working tree completamente limpio;
- disponer de `origin/develop` y poder hacer `fetch`;
- poder actualizar `develop` por fast-forward; el script aborta si la historia ha divergido;
- tener un runtime Python operativo (`.venv`, `py` o `python`);
- que `VERSION` coincida con el tag semántico más reciente alcanzable desde `origin/develop`;
- que no existan ya la rama local o remota `release/X.Y.Z` ni el tag calculado.

El script calcula la siguiente versión desde el tag más reciente. Debe indicarse exactamente un incremento:

```powershell
.\start-release.ps1 -Patch
.\start-release.ps1 -Minor
.\start-release.ps1 -Major
```

Tras confirmar, el script:

1. crea y activa `release/X.Y.Z`;
2. actualiza `VERSION`;
3. ejecuta `scripts/build.py`;
4. muestra los cambios pendientes.

El script no hace commit ni push. Revisa el build y el contenido generado; después deja la preparación guardada y sincronizada:

```powershell
git status
git diff
git add <archivos revisados>
git commit -m "Prepare release X.Y.Z"
.\publish-release.ps1
```

Ese push de la rama de release es necesario: `finish-release.ps1` exige que `release/X.Y.Z` y `origin/release/X.Y.Z` apunten al mismo commit.

## Cerrar y publicar una release

Ejecuta desde la propia rama `release/X.Y.Z`, limpia y ya publicada:

```powershell
.\finish-release.ps1
```

Antes de pedir confirmación, el script:

- comprueba que `VERSION` coincide con `X.Y.Z`;
- hace `fetch --prune --tags`;
- exige que la rama local y la remota de release estén sincronizadas;
- actualiza `master` y `develop` desde sus ramas remotas, solo mediante fast-forward;
- comprueba que el tag no exista;
- ejecuta `python -m unittest discover tests` y `scripts/build.py`;
- exige que el build no haya modificado el working tree;
- muestra los commits que entrarán respecto de `master`.

Tras la confirmación, realiza esta secuencia exacta:

1. cambia a `master` y fusiona `release/X.Y.Z` con `--no-ff`;
2. crea el tag anotado `X.Y.Z` sobre ese nuevo commit de `master`;
3. cambia a `develop` y fusiona `master` con `--no-ff`;
4. hace un único `git push --atomic` de `master`, `develop` y el tag, eliminando también la rama remota de release si existía;
5. elimina la rama local de release;
6. deja activa `develop`.

Por tanto, el tag se crea durante `finish-release.ps1`, después del merge en `master` y antes del push. La publicación Git de la release ocurre con el push atómico del propio script: no hay que ejecutar después `tag-release.ps1` ni `publish-release.ps1`.

## Qué hace cada script

| Script | Rama de ejecución | Función |
|---|---|---|
| `start-release.ps1` | `develop` | Calcula la siguiente versión, crea `release/X.Y.Z`, actualiza `VERSION` y construye. No commitea ni publica. |
| `finish-release.ps1` | `release/X.Y.Z` | Prueba, construye, fusiona en `master`, crea el tag, sincroniza `develop`, publica todo atómicamente y elimina la rama de release. |
| `release-tools.ps1` | No se ejecuta directamente | Funciones compartidas de Git, versión, sincronización y selección de Python. |
| `tag-release.ps1` | Ninguna | Retirado. Siempre termina con error y remite al flujo `start-release`/`finish-release`. |
| `publish-release.ps1` | Cualquier rama activa | Activa `.venv` y ejecuta `scripts/publish.py`: exige limpieza, hace fetch, evita publicar si la rama local va por detrás, construye y hace push de la rama activa. No crea tags, merges ni despliegues. |

## Si algo falla

Los scripts abortan al primer error. `finish-release.ps1` no intenta rollback automático, así que antes de repetirlo inspecciona:

```powershell
git status
git branch --show-current
git log --oneline --decorate -10
git tag --list
git branch -vv
```

- **Working tree sucio:** revisa el build o los cambios pendientes y commitea o descarta únicamente lo que corresponda.
- **Rama local por detrás:** sincronízala mediante fast-forward y vuelve a ejecutar. Si hay divergencia, resuélvela manualmente; los scripts no fuerzan ni reescriben historia.
- **Release local y remota no sincronizadas:** publica la rama de release o integra primero los commits remotos.
- **Fallo antes de la confirmación:** no se han hecho merges, tags ni pushes; corrige la causa y reintenta.
- **Fallo durante el cierre:** determina qué pasos llegaron a completarse antes de borrar ramas o tags. Si el push atómico falló, el remoto no debería contener una publicación parcial, pero pueden existir localmente el merge en `master`, el tag y el merge en `develop`.
- **Conflicto de merge:** resuélvelo o aborta el merge con `git merge --abort`; no vuelvas a ejecutar hasta recuperar un estado limpio y coherente.
- **Tag ya existente:** no lo reemplaces automáticamente. Comprueba a qué commit apunta y resuelve la discrepancia antes de continuar.

No borres una rama de release ni recrees un tag como medida de recuperación hasta confirmar el estado local y remoto.
