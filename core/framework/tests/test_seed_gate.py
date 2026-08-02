"""Regression: entrega gobernada del gate al consumer (specs/016, ADR-0020)."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from edaios_sdd_adapter.spec_kit import GATE_REL, GATE_SIDECAR_REL, seed_gate

ROOT = Path(__file__).resolve().parents[3]


class SeedGateTests(unittest.TestCase):
    def _core_root(self) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="edaios-seed-core-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        gate = tmp / GATE_REL
        gate.parent.mkdir(parents=True)
        gate.write_text("print('gate v1')\n", encoding="utf-8")
        (tmp / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        return tmp

    def _consumer(self) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="edaios-seed-consumer-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        return tmp

    def test_siembra_fresca_crea_gate_y_sidecar(self) -> None:
        core, consumer = self._core_root(), self._consumer()
        dest = seed_gate(core, consumer)
        self.assertTrue(dest.is_file())
        sidecar = (consumer / GATE_SIDECAR_REL).read_text(encoding="utf-8")
        digest = hashlib.sha256((core / GATE_REL).read_bytes()).hexdigest()
        self.assertIn(digest, sidecar)
        self.assertIn("edaios-core v9.9.9", sidecar)
        self.assertIn("seed_gate", sidecar)

    def test_siembra_identica_es_idempotente(self) -> None:
        core, consumer = self._core_root(), self._consumer()
        seed_gate(core, consumer)
        sidecar_before = (consumer / GATE_SIDECAR_REL).read_text(encoding="utf-8")
        seed_gate(core, consumer)
        self.assertEqual(
            sidecar_before,
            (consumer / GATE_SIDECAR_REL).read_text(encoding="utf-8"),
        )

    def test_divergencia_sin_force_falla_con_digests(self) -> None:
        core, consumer = self._core_root(), self._consumer()
        seed_gate(core, consumer)
        (consumer / GATE_REL).write_text("print('editado a mano')\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "divergente.*sha256:.*sha256:.*force=True"):
            seed_gate(core, consumer)

    def test_force_re_siembra_gate_y_sidecar(self) -> None:
        core, consumer = self._core_root(), self._consumer()
        seed_gate(core, consumer)
        (consumer / GATE_REL).write_text("print('editado a mano')\n", encoding="utf-8")
        dest = seed_gate(core, consumer, force=True)
        self.assertEqual(dest.read_text(encoding="utf-8"), "print('gate v1')\n")
        digest = hashlib.sha256((core / GATE_REL).read_bytes()).hexdigest()
        self.assertIn(digest, (consumer / GATE_SIDECAR_REL).read_text(encoding="utf-8"))

    def test_fuente_ausente_falla_cerrado(self) -> None:
        consumer = self._consumer()
        with self.assertRaises(FileNotFoundError):
            seed_gate(self._consumer(), consumer)

    def test_sidecar_ausente_con_gate_identico_se_repara(self) -> None:
        # RA-001: reintentar tras una escritura parcial converge.
        core, consumer = self._core_root(), self._consumer()
        seed_gate(core, consumer)
        (consumer / GATE_SIDECAR_REL).unlink()
        seed_gate(core, consumer)
        sidecar = (consumer / GATE_SIDECAR_REL).read_text(encoding="utf-8")
        digest = hashlib.sha256((core / GATE_REL).read_bytes()).hexdigest()
        self.assertIn(digest, sidecar)

    def test_sidecar_manchado_con_gate_identico_se_repara(self) -> None:
        core, consumer = self._core_root(), self._consumer()
        seed_gate(core, consumer)
        (consumer / GATE_SIDECAR_REL).write_text(
            "procedencia manual vieja\n", encoding="utf-8"
        )
        seed_gate(core, consumer)
        self.assertIn(
            "seed_gate", (consumer / GATE_SIDECAR_REL).read_text(encoding="utf-8")
        )

    def test_sidecar_previo_sin_gate_no_se_pisa_sin_force(self) -> None:
        # RA-004: el registro de procedencia anterior es evidencia.
        core, consumer = self._core_root(), self._consumer()
        sidecar = consumer / GATE_SIDECAR_REL
        sidecar.parent.mkdir(parents=True)
        sidecar.write_text("registro previo\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "sin gate acompañante"):
            seed_gate(core, consumer)
        seed_gate(core, consumer, force=True)
        self.assertIn("seed_gate", sidecar.read_text(encoding="utf-8"))

    def test_symlink_en_tools_validation_falla_cerrado(self) -> None:
        # RA-003: contención física; la siembra no atraviesa symlinks.
        core, consumer = self._core_root(), self._consumer()
        fuera = Path(tempfile.mkdtemp(prefix="edaios-fuera-"))
        self.addCleanup(shutil.rmtree, fuera, ignore_errors=True)
        (consumer / "tools").mkdir()
        (consumer / "tools/validation").symlink_to(fuera, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "contención física"):
            seed_gate(core, consumer)
        self.assertEqual(list(fuera.iterdir()), [])

    def test_plb_005_es_ko_playbook(self) -> None:
        playbook = ROOT / "core/framework/docs/playbooks/PLB-005-onboarding-de-consumer.md"
        text = playbook.read_text(encoding="utf-8")
        self.assertIn("id: PLB-005", text)
        self.assertIn("tipo: Playbook", text)
        self.assertIn("deriva_de: ADR-0020", text)
        self.assertIn("seed_gate", text)


if __name__ == "__main__":
    unittest.main()
