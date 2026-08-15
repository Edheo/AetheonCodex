"""
Aetheon Cartography Builder

Genera un GeoJSON unificado a partir de las capas
cartográficas canónicas almacenadas en codex.

Fuentes:
    codex/03_Cartografia/*.geojson

Salida:
    docs/03_Cartografia/AETHEON.geojson
    docs/03_Cartografia/MAPA.md
    docs/assets/stylesheets/cartography.css
    docs/assets/javascripts/cartography.js

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

MAP_FILE = OUTPUT_DIR / "MAPA.md"

STYLESHEET_FILE = (
    ROOT
    / "docs"
    / "assets"
    / "stylesheets"
    / "cartography.css"
)

JAVASCRIPT_FILE = (
    ROOT
    / "docs"
    / "assets"
    / "javascripts"
    / "cartography.js"
)

MAP_MARKDOWN = """# Mapa de Aetheon

<div
    id="aetheon-map"
    data-geojson="../AETHEON.geojson"
    aria-label="Mapa interactivo de Aetheon">
</div>

<p id="aetheon-map-status" role="status"></p>
"""

MAP_STYLESHEET = """.md-main__inner:has(#aetheon-map) {
    max-width: 90rem;
}

#aetheon-map {
    width: 100%;
    height: clamp(520px, 78vh, 900px);
    background: var(--md-default-bg-color);
}

#aetheon-map-status {
    margin-top: 0.75rem;
}

@media screen and (max-width: 44.984375em) {
    #aetheon-map {
        height: 65vh;
        min-height: 420px;
    }
}
"""

MAP_JAVASCRIPT = r"""(() => {
    "use strict";

    const mapElement = document.getElementById("aetheon-map");

    if (!mapElement || typeof L === "undefined") {
        return;
    }

    const statusElement = document.getElementById(
        "aetheon-map-status"
    );

    const setStatus = (message) => {
        if (statusElement) {
            statusElement.textContent = message;
        }
    };

    const valueFromFeature = (feature, key) => {
        const properties = feature.properties || {};
        return feature[key] ?? properties[key];
    };

    const buildPopup = (feature) => {
        const fields = [
            ["Nombre", valueFromFeature(feature, "name")],
            ["Tipo", valueFromFeature(feature, "kind")],
            ["ID", valueFromFeature(feature, "id")],
        ].filter(([, value]) => value !== undefined && value !== null && value !== "");

        if (!fields.length) {
            return null;
        }

        const container = document.createElement("dl");

        fields.forEach(([label, value]) => {
            const term = document.createElement("dt");
            const description = document.createElement("dd");

            term.textContent = label;
            description.textContent = String(value);
            container.append(term, description);
        });

        return container;
    };

    const map = L.map(mapElement);

    L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        {
            maxNativeZoom: 19,
            maxZoom: 22,
            attribution: "Tiles &copy; Esri &mdash; Source: Esri and contributors",
        }
    ).addTo(map);

    fetch(mapElement.dataset.geojson)
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return response.json();
        })
        .then((data) => {
            const geojsonLayer = L.geoJSON(data, {
                onEachFeature(feature, layer) {
                    const popup = buildPopup(feature);

                    if (popup) {
                        layer.bindPopup(popup);
                    }
                },
            }).addTo(map);

            const bounds = geojsonLayer.getBounds();

            if (!bounds.isValid()) {
                throw new Error("El GeoJSON no contiene geometrías válidas.");
            }

            map.fitBounds(bounds, { padding: [20, 20] });
            setStatus("");
        })
        .catch((error) => {
            console.error("Unable to load AETHEON.geojson:", error);
            setStatus("No se ha podido cargar la cartografía de Aetheon.");
        });
})();
"""


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


def write_text_file(path, content):
    """
    Escribe un artefacto textual generado en UTF-8.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        path.write_text(
            content,
            encoding="utf-8",
        )

    except OSError as exc:
        print()
        print(f"[ERROR] Unable to write {path}")
        print(f"        {exc}")
        sys.exit(1)

    print(f"[OK] Generated: {path}")


def generate_map():
    """
    Genera la página y los recursos del visor cartográfico.
    """

    print()
    print("[CARTOGRAPHY] Generating interactive map...")

    write_text_file(MAP_FILE, MAP_MARKDOWN)
    write_text_file(STYLESHEET_FILE, MAP_STYLESHEET)
    write_text_file(JAVASCRIPT_FILE, MAP_JAVASCRIPT)


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

    generate_map()

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
