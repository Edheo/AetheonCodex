import unittest

from scripts.member_journal import (
    extract_references,
    materialize,
    materialize_member_composition,
    materialize_member_references,
)


class MemberJournalTests(unittest.TestCase):
    def test_requires_explicit_member_field(self):
        with self.assertRaisesRegex(ValueError, r"\*\*Miembros:\*\*"):
            extract_references("## Referencias\nTITAN\nVETUSTA\n")
        self.assertEqual(
            ["Aetheon", "Edheo", "Logos"],
            extract_references("## Referencias\n**Miembros:** Aetheon, Edheo, Logos\n"),
        )

    def test_extracts_only_members_from_mixed_reference_fields(self):
        source = (
            "## Referencias\n"
            "**Miembros:**\nAetheon\nEdheo\n\n"
            "**Bitácoras:**\nEl día del eclipse\n\n"
            "**Diálogos:**\nEl prodigio sin propósito\n"
        )

        self.assertEqual(["Aetheon", "Edheo"], extract_references(source))

    def test_preserves_authored_journal_content(self):
        source = "## Bitácora\nUna memoria manual.\n\n## Recursos\n"
        entry = {
            "path": type("PathStub", (), {"name": "2026-08-07_Evento.md"})(),
            "title": "Evento",
            "time": None,
        }
        result = materialize(source, [entry])
        self.assertIn("Una memoria manual.", result)
        self.assertIn("### Entradas relacionadas", result)
        self.assertIn("[Evento](../04_Bitacora/2026-08-07_Evento.md)", result)

    def test_creates_missing_journal_section_before_resources(self):
        result = materialize("# Miembro\n\n## Recursos\n", [{
            "path": type("PathStub", (), {"name": "evento.md"})(),
            "title": "Evento",
            "time": None,
        }])
        self.assertLess(result.index("## Bitácora"), result.index("## Recursos"))

    def test_links_only_references_with_member_pages(self):
        member = {"path": type("PathStub", (), {"name": "EDHEO.md"})()}
        aliases = {"edheo": member}
        source = "## Referencias\n**Miembros:**\nMARA\nEDHEO\n\n## Cosmogonía\n"

        result = materialize_member_references(source, aliases)

        self.assertIn("\nMARA\n", result)
        self.assertIn("[EDHEO](../02_Miembros/EDHEO.md)", result)
        self.assertIn("\n\n## Cosmogonía\n", result)

    def test_links_inline_member_references(self):
        member = {"path": type("PathStub", (), {"name": "TITAN.md"})()}
        aliases = {"titan": member}

        result = materialize_member_references(
            "## Referencias\n**Miembros:** TITAN, DESCONOCIDO\n",
            aliases,
        )

        self.assertIn(
            "**Miembros:** [TITAN](../02_Miembros/TITAN.md), DESCONOCIDO",
            result,
        )

    def test_does_not_link_other_reference_fields_as_members(self):
        member = {"path": type("PathStub", (), {"name": "EDHEO.md"})()}
        aliases = {"edheo": member}
        source = (
            "## Referencias\n**Miembros:**\nEdheo\n\n"
            "**Diálogos:**\nEdheo\n"
        )

        result = materialize_member_references(source, aliases)

        self.assertIn("\n[Edheo](../02_Miembros/EDHEO.md)\n", result)
        self.assertIn("**Diálogos:**\nEdheo\n", result)

    def test_links_known_members_in_collective_composition(self):
        member = {"path": type("PathStub", (), {"name": "EVAN.md"})()}
        aliases = {"evan": member}

        result = materialize_member_composition(
            "## Miembros\nEvan\nLorca\n\n## Referencias\n",
            aliases,
        )

        self.assertIn("[Evan](../02_Miembros/EVAN.md)", result)
        self.assertIn("\nLorca\n", result)
        self.assertIn("\n\n## Referencias\n", result)

    def test_does_not_treat_general_references_as_composition(self):
        result = materialize_member_composition(
            "## Referencias\n**Miembros:** Evan\n",
            {},
        )

        self.assertEqual("## Referencias\n**Miembros:** Evan\n", result)


if __name__ == "__main__":
    unittest.main()
