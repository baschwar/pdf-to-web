import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pdf_to_web.normalize import apply_readiness, apply_source_title, extraction_summary, normalize_document


class NormalizeTests(unittest.TestCase):
    @mock.patch(
        "pdf_to_web.normalize.recover_source_title_region",
        return_value=("Recovered title", [100.0, 700.0, 300.0, 720.0]),
    )
    def test_recovered_title_retains_and_backfills_source_region(self, _recover):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "project.json").write_text(
                json.dumps({"schema_version": "pdf-to-web-project-v1", "title": "Project", "source": {}})
            )
            document = {"metadata": {"title": "Project"}, "blocks": []}
            self.assertTrue(apply_source_title(document, project))
            title = document["blocks"][0]
            self.assertEqual(title["provenance"]["bounding_box"], [100.0, 700.0, 300.0, 720.0])

            del title["provenance"]["bounding_box"]
            self.assertTrue(apply_source_title(document, project))
            self.assertEqual(title["provenance"]["bounding_box"], [100.0, 700.0, 300.0, 720.0])

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
        self.assertEqual(nested["children"][0]["content"], "Child")

    def test_hard_list_markers_are_removed_and_flat_subitems_are_nested(self):
        document = normalize_document(
            {
                "kids": [
                    {
                        "type": "list",
                        "numbering style": "unordered",
                        "list items": [
                            {"type": "list item", "id": 1, "content": "• COVID-19 o Boosters may be required."},
                            {"type": "list item", "id": 2, "content": "• Influenza"},
                        ],
                    }
                ]
            }
        )
        first, second = document["blocks"][0]["children"]
        self.assertEqual(first["content"], "COVID-19")
        self.assertEqual(first["children"][0]["children"][0]["content"], "Boosters may be required.")
        self.assertEqual(second["content"], "Influenza")

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
        self.assertIn("auto_excluded_page_artifacts", codes)
        self.assertEqual(document["blocks"][0]["role"], "page_header")
        self.assertEqual(document["blocks"][0]["review"]["status"], "excluded")

    def test_page_number_footer_is_excluded_without_excluding_footnote_content(self):
        document = normalize_document(
            {
                "number of pages": 2,
                "kids": [
                    {"type": "paragraph", "page number": 1, "bounding box": [40, 40, 560, 52], "content": "Updated 03/2023 Page | 1"},
                    {"type": "list", "page number": 1, "bounding box": [40, 90, 560, 150], "content": "1 See supporting regulation."},
                ],
            }
        )
        footer, footnote = document["blocks"]
        self.assertEqual(footer["review"]["status"], "excluded")
        self.assertNotEqual(footnote.get("review", {}).get("status"), "excluded")

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

    def test_explicit_footnote_moves_to_document_model(self):
        document = normalize_document(
            {
                "number of pages": 1,
                "kids": [
                    {
                        "type": "paragraph",
                        "id": 1,
                        "page number": 1,
                        "content": "This statement includes a footnote 1.",
                    },
                    {
                        "type": "footnote",
                        "id": 2,
                        "page number": 1,
                        "content": "1. Footnote text.",
                    },
                ],
            }
        )
        self.assertEqual(document["footnotes"][0]["marker"], "1")
        self.assertEqual(document["footnotes"][0]["text"], "Footnote text.")
        self.assertTrue(document["blocks"][1]["export_as_footnote_body"])
        self.assertNotEqual(document["blocks"][1].get("review", {}).get("status"), "excluded")
        reference = document["blocks"][0]["footnote_references"][0]
        self.assertEqual(reference["footnote_id"], document["footnotes"][0]["id"])
        self.assertEqual(reference["source_block"], "odl-1")

    def test_numbered_footnote_list_moves_to_document_model(self):
        document = normalize_document(
            {
                "number of pages": 1,
                "kids": [
                    {"type": "paragraph", "id": 1, "page number": 1, "content": "Claims one 1 and two 2."},
                    {
                        "type": "list",
                        "id": 2,
                        "page number": 1,
                        "numbering style": "arabic numbers",
                        "list items": [
                            {"type": "list item", "id": 11, "page number": 1, "content": "1 First note."},
                            {"type": "list item", "id": 12, "page number": 1, "content": "2 Second note."},
                        ],
                    },
                ],
            }
        )
        self.assertEqual([note["text"] for note in document["footnotes"]], ["First note.", "Second note."])
        self.assertTrue(document["blocks"][1]["export_as_footnote_body"])

    def test_unmatched_note_is_preserved_for_review(self):
        document = normalize_document(
            {
                "number of pages": 1,
                "kids": [
                    {"type": "paragraph", "page number": 1, "content": "Body text."},
                    {"type": "footnote", "page number": 1, "content": "1. Maybe a note."},
                    {
                        "type": "list",
                        "numbering style": "decimal",
                        "list items": [{"type": "list item", "content": "1. Ordinary item"}],
                    },
                ],
            }
        )
        self.assertNotIn("footnotes", document)
        self.assertFalse(document["blocks"][1].get("export_as_footnote_body", False))
        self.assertEqual(document["blocks"][1]["review"]["status"], "needs_review")
        self.assertIn(
            "block_review_required",
            {issue["code"] for issue in apply_readiness(document)["issues"]},
        )
        self.assertEqual(document["blocks"][2]["type"], "list")


if __name__ == "__main__":
    unittest.main()
