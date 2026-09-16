import unittest

from pdf_to_web.normalize import extraction_summary, normalize_document


class NormalizeTests(unittest.TestCase):
    def test_known_and_unknown_elements_preserve_provenance(self):
        raw = {
            "file name": "sample.pdf",
            "number of pages": 2,
            "title": "Sample",
            "author": "A. Author",
            "kids": [
                {
                    "type": "heading",
                    "id": 7,
                    "page number": 1,
                    "bounding box": [1, 2, 3, 4],
                    "heading level": 1,
                    "content": "Sample",
                },
                {
                    "type": "regionlist",
                    "id": 8,
                    "page number": 2,
                    "content": "Unclassified layout region",
                    "custom field": True,
                },
            ],
        }
        document = normalize_document(raw)
        self.assertEqual(document["blocks"][0]["type"], "heading")
        self.assertEqual(document["blocks"][0]["provenance"]["source_page"], 1)
        unknown = document["blocks"][1]
        self.assertEqual(unknown["type"], "unknown")
        self.assertEqual(unknown["review_status"], "review_required")
        self.assertTrue(unknown["provenance"]["raw"]["custom field"])

    def test_nested_list_is_retained(self):
        raw = {
            "kids": [
                {
                    "type": "list",
                    "numbering style": "decimal",
                    "list items": [
                        {
                            "type": "list item",
                            "content": "Parent",
                            "kids": [
                                {
                                    "type": "list",
                                    "numbering style": "bullet",
                                    "list items": [{"type": "list item", "content": "Child"}],
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        document = normalize_document(raw)
        self.assertTrue(document["blocks"][0]["ordered"])
        nested = document["blocks"][0]["children"][0]["children"][0]
        self.assertEqual(nested["type"], "list")
        self.assertFalse(nested["ordered"])

    def test_summary_flags_incomplete_page_coverage(self):
        document = normalize_document(
            {
                "number of pages": 2,
                "kids": [
                    {"type": "paragraph", "page number": 1, "content": "Clean text"}
                ],
            }
        )
        summary = extraction_summary(document)
        self.assertEqual(summary["status"], "TEXT EXTRACTION REVIEW REQUIRED")
        self.assertEqual(summary["represented_pages"], [1])
        self.assertEqual(summary["page_coverage_ratio"], 0.5)

    def test_table_cells_keep_text_spans_and_geometry(self):
        document = normalize_document(
            {
                "number of pages": 1,
                "kids": [
                    {
                        "type": "table",
                        "page number": 1,
                        "rows": [
                            {
                                "type": "table row",
                                "cells": [
                                    {
                                        "type": "table cell",
                                        "page number": 1,
                                        "bounding box": [1, 2, 3, 4],
                                        "row span": 2,
                                        "column span": 1,
                                        "kids": [
                                            {"type": "paragraph", "content": "Program"},
                                            {"type": "paragraph", "content": "BSN"},
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )
        cell = document["blocks"][0]["rows"][0][0]
        self.assertEqual(cell["content"], "Program BSN")
        self.assertEqual(cell["row_span"], 2)
        self.assertEqual(cell["provenance"]["bounding_box"], [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
