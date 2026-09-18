from __future__ import annotations

import unittest

from pdf_to_web.doctor import node_version_supported


class DoctorTests(unittest.TestCase):
    def test_node_version_supports_current_preview_minimum(self) -> None:
        self.assertFalse(node_version_supported(None))
        self.assertFalse(node_version_supported("20.18.9"))
        self.assertTrue(node_version_supported("20.19.0"))
        self.assertTrue(node_version_supported("22.0.0"))

    def test_node_version_rejects_unparseable_values(self) -> None:
        self.assertFalse(node_version_supported("unknown"))
        self.assertFalse(node_version_supported("20"))


if __name__ == "__main__":
    unittest.main()
