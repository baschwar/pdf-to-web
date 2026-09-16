import unittest

from pdf_to_web.normalize import apply_readiness, extraction_summary, normalize_document


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
        review = apply_readiness(document)
        self.assertEqual(review["status"], "needs_review")
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

    def test_readiness_distinguishes_review_and_blocked(self):
        document = normalize_document(
            {
                "number of pages": 1,
                "kids": [{"type": "paragraph", "page number": 1, "content": "Short"}],
            }
        )
        document["metadata"]["source_embedded_text_character_count"] = 100
        self.assertEqual(apply_readiness(document)["status"], "conversion_blocked")
        document["blocks"][0]["content"] = "x" * 70
        self.assertEqual(apply_readiness(document)["status"], "needs_review")
        document["blocks"][0]["content"] = "x" * 95
        self.assertEqual(apply_readiness(document)["status"], "review_ready")

    def test_complex_visual_retains_assets_text_and_page(self):
        document = normalize_document(
            {
                "number of pages": 1,
                "kids": [
                    {"type": "heading", "heading level": 1, "page number": 1, "content": "Heart Failure"},
                    {"type": "paragraph", "page number": 1, "content": "Recovered instructions"},
                ],
            }
        )
        document["metadata"]["source_embedded_text_character_count"] = 100
        document["metadata"]["source_embedded_text_characters_by_page"] = [100]
        assets = {
            "assets": [
                {"source_page": 1, "filename": f"asset-{number}.png"}
                for number in range(1, 6)
            ]
        }
        review = apply_readiness(document, assets)
        visual = review["complex_visuals"][0]
        self.assertEqual(review["status"], "needs_review")
        self.assertEqual(visual["type"], "infographic")
        self.assertEqual(visual["source_page"], 1)
        self.assertEqual(len(visual["asset_references"]), 5)
        self.assertIn("Recovered instructions", visual["recovered_text"])
        self.assertTrue(visual["human_review_required"])

    def test_missing_heading_level_and_page_furniture_are_explicit(self):
        document = normalize_document(
            {
                "number of pages": 1,
                "kids": [
                    {"type": "header", "page number": 1, "content": "Repeated"},
                    {"type": "heading", "page number": 1, "content": "Provisional"},
                ],
            }
        )
        review = apply_readiness(document)
        codes = {issue["code"] for issue in review["issues"]}
        self.assertIn("missing_heading_levels", codes)
        self.assertIn("repeated_page_furniture", codes)
        self.assertEqual(document["blocks"][0]["role"], "page_header")

    def test_image_caption_association_is_not_exported_twice(self):
        document = normalize_document(
            {
                "kids": [
                    {"type": "image", "id": 1, "page number": 1, "source": "figure.png"},
                    {"type": "caption", "id": 2, "page number": 1, "content": "Figure caption"},
                ]
            }
        )
        image, caption = document["blocks"]
        self.assertEqual(image["caption"], "Figure caption")
        self.assertEqual(caption["associated_image_id"], image["id"])
        self.assertTrue(caption["export_as_part_of_image"])

    def test_source_reading_order_is_preserved_for_columns(self):
        document = normalize_document(
            {
                "kids": [
                    {"type": "paragraph", "page number": 1, "bounding box": [300, 700, 500, 720], "content": "Right first"},
                    {"type": "paragraph", "page number": 1, "bounding box": [40, 650, 250, 670], "content": "Left second"},
                ]
            }
        )
        self.assertEqual(
            [block["content"] for block in document["blocks"]],
            ["Right first", "Left second"],
        )


if __name__ == "__main__":
    unittest.main()
