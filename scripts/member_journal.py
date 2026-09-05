"""Genera en docs el índice inverso de Bitácora para cada Miembro."""

from pathlib import Path
import re
import unicodedata

try:
    from book import extract_event_time, extract_title, present_event_time
except ModuleNotFoundError:
    from scripts.book import extract_event_time, extract_title, present_event_time


ROOT = Path(__file__).resolve().parent.parent
CODEX_MEMBERS_DIR = ROOT / "codex" / "02_Miembros"
CODEX_JOURNAL_DIR = ROOT / "codex" / "04_Bitacora"
DOCS_MEMBERS_DIR = ROOT / "docs" / "02_Miembros"
DOCS_JOURNAL_DIR = ROOT / "docs" / "04_Bitacora"

GENERATED_START = "<!-- BEGIN GENERATED MEMBER JOURNAL -->"
GENERATED_END = "<!-- END GENERATED MEMBER JOURNAL -->"
GENERATED_PATTERN = re.compile(
    rf"\n*{re.escape(GENERATED_START)}.*?{re.escape(GENERATED_END)}\n*",
    re.DOTALL,
)


def normalize(value):
    """Normaliza identificadores sin interpretar su significado."""

    decomposed = unicodedata.normalize("NFKD", value)
    plain = "".join(character for character in decomposed if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "", plain.casefold())


def extract_section(text, heading):
    match = re.search(
        rf"^##[ \t]+{re.escape(heading)}[ \t]*$(.*?)(?=^##(?:[ \t]|$)|\Z)",
        text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def extract_member_name(text, fallback):
    match = re.search(r"^Nombre:[ \t]*(.+?)[ \t]*$", text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else fallback


def extract_references(text):
    """Extrae exclusivamente las referencias declaradas mediante **Miembros:**."""

    section = extract_section(text, "Referencias")
    if section is None:
        return []

    lines = section.splitlines()
    member_field = re.compile(r"^\*\*Miembros:\*\*[ \t]*(.*)$", re.IGNORECASE)
    if not any(member_field.match(line.strip()) for line in lines):
        raise ValueError(
            "La sección Referencias debe declarar el campo **Miembros:**."
        )

    references = []
    in_members = False
    for line in lines:
        value = line.strip()
        if not value:
            continue

        value = re.sub(r"^[-*][ \t]+", "", value)
        field = member_field.match(value)
        if field:
            in_members = True
            values = field.group(1).split(",")
        elif re.match(r"^\*\*[^*]+:\*\*", value):
            in_members = False
            continue
        elif in_members:
            values = value.split(",")
        else:
            continue

        references.extend(item.strip() for item in values if item.strip())

    return references


def load_members():
    aliases = {}
    members = {}

    for path in sorted(CODEX_MEMBERS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8-sig")
        name = extract_member_name(text, path.stem)
        member = {"path": path, "name": name, "entries": []}
        members[path.stem] = member

        for alias in (path.stem, name):
            key = normalize(alias)
            existing = aliases.get(key)
            if existing is not None and existing is not member:
                raise ValueError(f"Alias de Miembro duplicado: {alias}")
            aliases[key] = member

    return members, aliases


def load_journal_entries(aliases):
    unresolved = {}

    for path in sorted(CODEX_JOURNAL_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8-sig")
        entry = {
            "path": path,
            "title": extract_title(text, path.stem),
            "time": extract_event_time(text),
        }

        linked = set()
        for reference in extract_references(text):
            member = aliases.get(normalize(reference))
            if member is None:
                unresolved.setdefault(normalize(reference), reference)
                continue
            identity = member["path"].stem
            if identity not in linked:
                member["entries"].append(entry)
                linked.add(identity)

    return set(unresolved.values())


def member_link(reference, aliases):
    """Enlaza una referencia si existe una ficha de Miembro."""

    member = aliases.get(normalize(reference))
    if member is None:
        return reference
    target = f"../02_Miembros/{member['path'].name}"
    return f"[{reference}]({target})"


def materialize_member_references(text, aliases):
    """Materializa en una Bitácora los enlaces declarados bajo **Miembros:**."""

    section_pattern = re.compile(
        r"(^##[ \t]+Referencias[ \t]*$)(.*?)(?=^##(?:[ \t]|$)|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = section_pattern.search(text)
    if match is None:
        return text

    lines = match.group(2).splitlines()
    in_members = False
    rendered = []

    for line in lines:
        field = re.match(
            r"^(?P<indent>[ \t]*)\*\*Miembros:\*\*[ \t]*(?P<values>.*)$",
            line,
            re.IGNORECASE,
        )
        if field:
            in_members = True
            values = field.group("values")
            if values:
                linked = ", ".join(
                    member_link(item.strip(), aliases)
                    for item in values.split(",")
                    if item.strip()
                )
                rendered.append(f"{field.group('indent')}**Miembros:** {linked}")
            else:
                rendered.append(line)
            continue

        if re.match(r"^[ \t]*\*\*[^*]+:\*\*", line):
            in_members = False
            rendered.append(line)
            continue

        if in_members and line.strip():
            prefix = re.match(r"^(?P<indent>[ \t]*)(?P<bullet>[-*][ \t]+)?", line)
            value = line[prefix.end():]
            linked = ", ".join(
                member_link(item.strip(), aliases)
                for item in value.split(",")
                if item.strip()
            )
            bullet = prefix.group("bullet") or ""
            rendered.append(f"{prefix.group('indent')}{bullet}{linked}")
        else:
            rendered.append(line)

    body = "\n".join(rendered)
    if match.group(2).endswith("\n"):
        body += "\n"
    replacement = match.group(1) + body
    return text[:match.start()] + replacement + text[match.end():]


def materialize_journal_member_links(aliases):
    linked_entries = 0

    for destination in sorted(DOCS_JOURNAL_DIR.glob("*.md")):
        text = destination.read_text(encoding="utf-8-sig")
        rendered = materialize_member_references(text, aliases)
        if rendered != text:
            destination.write_text(rendered, encoding="utf-8")
            linked_entries += 1

    return linked_entries


def materialize_member_composition(text, aliases):
    """Enlaza los integrantes declarados en la sección opcional ## Miembros."""

    section_pattern = re.compile(
        r"(^##[ \t]+Miembros[ \t]*$)(.*?)(?=^##(?:[ \t]|$)|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = section_pattern.search(text)
    if match is None:
        return text

    rendered = []
    for line in match.group(2).splitlines():
        if not line.strip() or line.lstrip().startswith("<!--"):
            rendered.append(line)
            continue

        prefix = re.match(r"^(?P<indent>[ \t]*)(?P<bullet>[-*][ \t]+)?", line)
        value = line[prefix.end():]
        linked = ", ".join(
            member_link(item.strip(), aliases)
            for item in value.split(",")
            if item.strip()
        )
        bullet = prefix.group("bullet") or ""
        rendered.append(f"{prefix.group('indent')}{bullet}{linked}")

    body = "\n".join(rendered)
    if match.group(2).endswith("\n"):
        body += "\n"
    replacement = match.group(1) + body
    return text[:match.start()] + replacement + text[match.end():]


def materialize_member_composition_links(aliases):
    linked_pages = 0

    for destination in sorted(DOCS_MEMBERS_DIR.glob("*.md")):
        text = destination.read_text(encoding="utf-8-sig")
        rendered = materialize_member_composition(text, aliases)
        if rendered != text:
            destination.write_text(rendered, encoding="utf-8")
            linked_pages += 1

    return linked_pages


def generated_block(entries):
    lines = [GENERATED_START, "### Entradas relacionadas", ""]

    for entry in sorted(entries, key=lambda item: item["path"].name):
        temporal = present_event_time(entry["time"]) if entry["time"] is not None else None
        label = f"*{temporal}* — " if temporal else ""
        target = f"../04_Bitacora/{entry['path'].name}"
        lines.append(f"- {label}[{entry['title']}]({target})")

    lines.append(GENERATED_END)
    return "\n".join(lines)


def materialize(text, entries):
    """Inserta un bloque derivado preservando cualquier contenido autoral."""

    text = GENERATED_PATTERN.sub("\n", text)
    block = generated_block(entries)
    section_pattern = re.compile(
        r"(^##[ \t]+Bitácora[ \t]*$)(.*?)(?=^##(?:[ \t]|$)|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = section_pattern.search(text)

    if match:
        authored = match.group(2).strip()
        body = f"\n{authored}\n\n" if authored else "\n\n"
        replacement = f"{match.group(1)}{body}{block}\n\n"
        return text[:match.start()] + replacement + text[match.end():]

    insertion = re.search(
        r"^##[ \t]+(?:Recursos|Media|Croquis|Referencias)[ \t]*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    section = f"## Bitácora\n\n{block}\n\n"
    if insertion:
        return text[:insertion.start()] + section + text[insertion.start():]
    return text.rstrip() + "\n\n" + section


def run():
    print("[MEMBER JOURNAL] Building reverse journal index...")
    members, aliases = load_members()
    unresolved = load_journal_entries(aliases)
    journal_entries = materialize_journal_member_links(aliases)
    composition_pages = materialize_member_composition_links(aliases)
    linked_members = 0
    linked_entries = 0

    for member in members.values():
        if not member["entries"]:
            continue

        destination = DOCS_MEMBERS_DIR / member["path"].name
        text = destination.read_text(encoding="utf-8-sig")
        destination.write_text(materialize(text, member["entries"]), encoding="utf-8")
        linked_members += 1
        linked_entries += len(member["entries"])
        count = len(member["entries"])
        label = "entry" if count == 1 else "entries"
        print(f"[MEMBER JOURNAL] {member['name']}: {count} {label}.")

    print(f"[MEMBER JOURNAL] Done. {linked_entries} link(s) across {linked_members} member(s).")
    print(f"[MEMBER JOURNAL] Linked member references in {journal_entries} journal entry/entries.")
    print(f"[MEMBER JOURNAL] Linked compositions in {composition_pages} member page(s).")
    if unresolved:
        print(
            f"[MEMBER JOURNAL] {len(unresolved)} reference name(s) "
            "do not currently have a member page; ignored."
        )


if __name__ == "__main__":
    run()
