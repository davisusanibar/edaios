import tempfile
import unittest
import sqlite3
from contextlib import closing
from pathlib import Path

from edaios_sdk_consumption import (
    DerivedKnowledgeIndex,
    IndexContractError,
    IndexIntegrityError,
    IndexStaleError,
    KnowledgeClient,
)


def _ko(ko_id: str, title: str, state: str, body: str) -> str:
    return f"""---
id: {ko_id}
tipo: Article
titulo: {title}
version: 1.0.0
estado: {state}
autoridad: Foundation
idioma: es
owner: OWNER-CORE
deriva_de: Foundation
---

{body}
"""


class DerivedKnowledgeIndexTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "core/foundation/knowledge").mkdir(parents=True)
        (self.root / "governance").mkdir()
        (self.root / "README.md").write_text("# Fixture\n", encoding="utf-8")
        (self.root / "governance/ADR_CATALOG.md").write_text("# ADR Catalog\n", encoding="utf-8")
        self.canonical = self.root / "core/foundation/knowledge/canonical.md"
        self.review = self.root / "core/foundation/knowledge/review.md"
        self.canonical.write_text(
            _ko("KO-CANONICAL", "Canonical search", "Ratificado", "Authoritative index contract."),
            encoding="utf-8",
        )
        self.review.write_text(
            _ko("KO-REVIEW", "Draft search", "Propuesto", "Experimental draft token."),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_index_is_derived_canonical_by_default_and_stale_fail_closed(self):
        index = DerivedKnowledgeIndex(KnowledgeClient(self.root), index_root=self.root)
        report = index.rebuild()
        self.assertEqual(report["channels"], ["normative"])
        self.assertFalse(report["authoritative"])
        hits = index.search("Authoritative")
        self.assertEqual([hit.ko_id for hit in hits], ["KO-CANONICAL"])
        self.assertFalse(hits[0].authoritative)
        self.assertTrue(hits[0].source_authoritative)
        self.assertEqual(hits[0].representation, "derived-index-hit")
        self.assertEqual(index.search("draft"), [])
        with self.assertRaises(IndexContractError):
            index.search("draft", include_channels=["review"])

        self.canonical.write_text(
            _ko("KO-CANONICAL", "Canonical search", "Ratificado", "Changed authoritative contract."),
            encoding="utf-8",
        )
        self.assertEqual(index.status()["status"], "stale")
        with self.assertRaises(IndexStaleError):
            index.search("Changed")
        index.rebuild()
        self.assertEqual([hit.ko_id for hit in index.search("Changed")], ["KO-CANONICAL"])

    def test_noncanonical_channel_requires_build_and_query_opt_in(self):
        index = DerivedKnowledgeIndex(
            KnowledgeClient(self.root), index_root=self.root, force_fallback=True
        )
        report = index.rebuild(include_channels=["normative", "review"])
        self.assertEqual(report["search_mode"], "fallback-like")
        self.assertEqual(index.search("draft"), [])
        hits = index.search("draft", include_channels=["review"])
        self.assertEqual([hit.ko_id for hit in hits], ["KO-REVIEW"])
        self.assertEqual(hits[0].channel, "review")

    def test_index_path_cannot_escape_workspace(self):
        with self.assertRaises(IndexContractError):
            DerivedKnowledgeIndex(
                KnowledgeClient(self.root), index_root=self.root, database="../index.sqlite3"
            )

    def test_tampered_sqlite_rows_or_fts_fail_closed(self):
        index = DerivedKnowledgeIndex(KnowledgeClient(self.root), index_root=self.root)
        report = index.rebuild()
        with closing(sqlite3.connect(index.database)) as connection:
            connection.execute(
                "UPDATE documents SET content='Injected memory' WHERE ko_id='KO-CANONICAL'"
            )
            connection.commit()
        with self.assertRaises(IndexIntegrityError):
            index.status()

        if report["search_mode"] == "fts5":
            index.rebuild()
            with closing(sqlite3.connect(index.database)) as connection:
                connection.execute(
                    "UPDATE documents_fts SET content='Injected FTS' "
                    "WHERE ko_id='KO-CANONICAL'"
                )
                connection.commit()
            with self.assertRaises(IndexIntegrityError):
                index.search("Injected")


if __name__ == "__main__":
    unittest.main()
