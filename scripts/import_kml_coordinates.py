"""Traslada geometrías corregidas desde un KML a las capas GeoJSON canónicas."""

from argparse import ArgumentParser
from pathlib import Path
import json
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "codex" / "05_Cartografia"
RESOURCE_DIR = ROOT / "recursos"
DEFAULT_KML = RESOURCE_DIR / "Aetheon_revisado.kml"
SOURCE_FILES = (
    "parcela.geojson",
    "bancales.geojson",
    "zonas.geojson",
    "construcciones.geojson",
    "estructuras.geojson",
    "accesos.geojson",
    "guardianes.geojson",
)
KML_NAMESPACE = {"kml": "http://www.opengis.net/kml/2.2"}


def coordinates(text):
    """Convierte coordenadas KML a coordenadas GeoJSON bidimensionales."""

    result = []
    for token in (text or "").split():
        values = token.split(",")
        if len(values) < 2:
            raise ValueError(f"Coordenada KML inválida: {token}")
        result.append([float(values[0]), float(values[1])])
    return result


def placemark_geometry(placemark):
    point = placemark.find("kml:Point/kml:coordinates", KML_NAMESPACE)
    if point is not None:
        values = coordinates(point.text)
        return {"type": "Point", "coordinates": values[0]}

    line = placemark.find("kml:LineString/kml:coordinates", KML_NAMESPACE)
    if line is not None:
        return {"type": "LineString", "coordinates": coordinates(line.text)}

    polygon = placemark.find("kml:Polygon", KML_NAMESPACE)
    if polygon is not None:
        rings = []
        outer = polygon.find(
            "kml:outerBoundaryIs/kml:LinearRing/kml:coordinates",
            KML_NAMESPACE,
        )
        if outer is None:
            raise ValueError("Polígono KML sin anillo exterior")
        rings.append(coordinates(outer.text))
        for inner in polygon.findall(
            "kml:innerBoundaryIs/kml:LinearRing/kml:coordinates",
            KML_NAMESPACE,
        ):
            rings.append(coordinates(inner.text))
        return {"type": "Polygon", "coordinates": rings}

    return None


def load_kml(path):
    root = ET.parse(path).getroot()
    geometries = {}

    for placemark in root.findall(".//kml:Placemark", KML_NAMESPACE):
        name_element = placemark.find("kml:name", KML_NAMESPACE)
        name = (name_element.text or "").strip() if name_element is not None else ""
        geometry = placemark_geometry(placemark)
        if not name or geometry is None:
            continue
        if name in geometries:
            raise ValueError(f"Nombre KML duplicado: {name}")
        geometries[name] = geometry

    return geometries


def feature_keys(feature):
    properties = feature.get("properties") or {}
    values = (
        feature.get("id"),
        feature.get("name"),
        properties.get("id"),
        properties.get("name"),
        properties.get("nombre"),
    )
    return [str(value).strip() for value in values if value]


def main():
    parser = ArgumentParser()
    parser.add_argument("kml", nargs="?", type=Path, default=DEFAULT_KML)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    try:
        kml_geometries = load_kml(args.kml)
    except (OSError, ET.ParseError, ValueError) as exc:
        print(f"[ERROR] No se pudo leer el KML: {exc}")
        return 1

    matched_kml = set()
    changes = []
    unmatched_geojson = []

    for filename in SOURCE_FILES:
        path = SOURCE_DIR / filename
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        file_changed = False

        for feature in data.get("features", []):
            matches = [key for key in feature_keys(feature) if key in kml_geometries]
            if not matches:
                unmatched_geojson.append((filename, feature_keys(feature)))
                continue

            key = matches[0]
            incoming = kml_geometries[key]
            current = feature.get("geometry") or {}
            if current.get("type") != incoming["type"]:
                print(
                    f"[ERROR] Geometría incompatible para {key}: "
                    f"{current.get('type')} / {incoming['type']}"
                )
                return 1

            matched_kml.add(key)
            if current.get("coordinates") != incoming["coordinates"]:
                feature["geometry"]["coordinates"] = incoming["coordinates"]
                changes.append((filename, key, incoming["type"]))
                file_changed = True

        if args.apply and file_changed:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=4) + "\n",
                encoding="utf-8",
            )

    print(f"[KML] {len(kml_geometries)} geometrías encontradas.")
    print(f"[MATCH] {len(matched_kml)} elementos relacionados.")
    print(f"[CHANGE] {len(changes)} geometrías diferentes.")
    for filename, key, geometry_type in changes:
        print(f"  - {filename}: {key} ({geometry_type})")

    unused = sorted(set(kml_geometries) - matched_kml)
    if unused:
        print(f"[KML ONLY] {len(unused)} elementos sin correspondencia:")
        for key in unused:
            print(f"  - {key}")

    if unmatched_geojson:
        print(f"[GEOJSON ONLY] {len(unmatched_geojson)} elementos sin correspondencia:")
        for filename, keys in unmatched_geojson:
            print(f"  - {filename}: {', '.join(keys) or '(sin identificador)'}")

    print("[OK] Cambios aplicados." if args.apply else "[DRY RUN] No se modificaron archivos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
