"""
Aetheon Cartography Builder

Genera un GeoJSON unificado a partir de las capas
cartográficas canónicas almacenadas en codex.

Fuentes:
    codex/03_Cartografia/*.geojson

Salida:
    docs/03_Cartografia/AETHEON.geojson

Principios:
- codex es la fuente de verdad.
- docs contiene el producto publicable.
- AETHEON.geojson es un artefacto generado.
- No se modifican geometrías ni propiedades.
- Se detectan IDs duplicados.
"""

from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parent.parent

SOURCE_DIR = (
    ROOT
    / "codex"
    / "03_Cartografia"
)

OUTPUT_DIR = (
    ROOT
    / "docs"
    / "03_Cartografia"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "AETHEON.geojson"
)


SOURCE_FILES = [
    "parcela.geojson",
    "bancales.geojson",
    "zonas.geojson",
    "construcciones.geojson",
    "estructuras.geojson",
    "accesos.geojson",
    "guardianes.geojson",
]


def load_geojson(path):
    """
    Carga y valida mínimamente un GeoJSON.
    """

    print(f"[CARTOGRAPHY] Reading {path.name}...")

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as exc:
        print()
        print(f"[ERROR] Invalid JSON: {path}")
        print(f"        {exc}")
        sys.exit(1)

    except OSError as exc:
        print()
        print(f"[ERROR] Unable to read: {path}")
        print(f"        {exc}")
        sys.exit(1)

    if data.get("type") != "FeatureCollection":
        print()
        print(
            f"[ERROR] {path.name} is not "
            "a GeoJSON FeatureCollection."
        )
        sys.exit(1)

    features = data.get("features")

    if not isinstance(features, list):
        print()
        print(
            f"[ERROR] {path.name} does not contain "
            "a valid 'features' array."
        )
        sys.exit(1)

    print(
        f"[OK] {path.name}: "
        f"{len(features)} feature(s)."
    )

    return data


def get_feature_id(feature):
    """
    Obtiene el ID de una feature.

    Soporta tanto:

        feature["id"]

    como:

        feature["properties"]["id"]
    """

    feature_id = feature.get("id")

    if feature_id:
        return str(feature_id)

    properties = feature.get("properties", {})

    if isinstance(properties, dict):
        feature_id = properties.get("id")

        if feature_id:
            return str(feature_id)

    return None


def check_duplicate_ids(features):
    """
    Comprueba que no existan IDs repetidos
    entre las distintas capas.
    """

    seen = {}
    duplicates = []

    for source_name, feature in features:

        feature_id = get_feature_id(feature)

        if not feature_id:
            continue

        if feature_id in seen:
            duplicates.append(
                (
                    feature_id,
                    seen[feature_id],
                    source_name,
                )
            )
        else:
            seen[feature_id] = source_name

    if duplicates:
        print()
        print("[ERROR] Duplicate feature IDs detected:")

        for feature_id, first_source, second_source in duplicates:
            print(
                f"  - {feature_id}"
                f" ({first_source} / {second_source})"
            )

        print()
        print(
            "Cartography merge aborted. "
            "Resolve duplicate IDs first."
        )

        sys.exit(1)

    print(
        f"[OK] {len(seen)} unique feature ID(s)."
    )


def merge_geojson():
    """
    Fusiona todas las capas cartográficas canónicas.
    """

    if not SOURCE_DIR.exists():
        print()
        print("[ERROR] Cartography source directory not found:")
        print(f"        {SOURCE_DIR}")
        sys.exit(1)

    collected_features = []

    print()
    print("[CARTOGRAPHY] Collecting layers...")

    for filename in SOURCE_FILES:

        path = SOURCE_DIR / filename

        if not path.exists():
            print()
            print("[ERROR] Required cartography layer not found:")
            print(f"        {path}")
            sys.exit(1)

        data = load_geojson(path)

        for feature in data["features"]:
            collected_features.append(
                (
                    filename,
                    feature,
                )
            )

    print()
    print(
        "[CARTOGRAPHY] Checking "
        "feature identifiers..."
    )

    check_duplicate_ids(
        collected_features
    )

    merged_features = [
        feature
        for _, feature in collected_features
    ]

    return {
        "type": "FeatureCollection",
        "name": "AETHEON",
        "features": merged_features,
    }


def write_geojson(data):
    """
    Escribe el GeoJSON unificado en docs.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        f"[CARTOGRAPHY] Writing "
        f"{OUTPUT_FILE.name}..."
    )

    try:
        with OUTPUT_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4,
            )

            file.write("\n")

    except OSError as exc:
        print()
        print(
            f"[ERROR] Unable to write "
            f"{OUTPUT_FILE}"
        )
        print(f"        {exc}")
        sys.exit(1)

    print(
        f"[OK] Generated: {OUTPUT_FILE}"
    )


def run():
    """
    Ejecuta la construcción cartográfica completa.
    """

    print()
    print("======================================")
    print(" AETHEON CARTOGRAPHY")
    print("======================================")

    print()
    print(
        f"[CARTOGRAPHY] Source: "
        f"{SOURCE_DIR}"
    )

    merged = merge_geojson()

    write_geojson(
        merged
    )

    print()
    print(
        f"[CARTOGRAPHY] "
        f"{len(merged['features'])} "
        f"feature(s) merged."
    )

    print(
        f"[CARTOGRAPHY] Output: "
        f"{OUTPUT_FILE}"
    )

    print()
    print(
        "Cartography build completed "
        "successfully."
    )


if __name__ == "__main__":
    run()