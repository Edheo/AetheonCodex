import unittest

from scripts.member_journal import extract_references, materialize


class MemberJournalTests(unittest.TestCase):
    def test_extracts_plain_and_inline_member_references(self):
        self.assertEqual(
            ["TITAN", "VETUSTA"],
            extract_references("## Referencias\nTITAN\nVETUSTA\n"),
        )
        self.assertEqual(
            ["Aetheon", "Edheo", "Logos"],
            extract_references("## Referencias\n**Miembros:** Aetheon, Edheo, Logos\n"),
        )

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


if __name__ == "__main__":
    unittest.main()
