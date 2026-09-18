import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pdf_to_web.normalize import (
    _apply_link_annotations,
    _clean_list_markers,
    _normalize_heading_hierarchy,
    _select_source_title,
    apply_readiness,
    apply_source_title,
    apply_source_supplemental_regions,
    extraction_summary,
    normalize_document,
    reconcile_visual_reading_order,
    repair_interleaved_images,
)


class NormalizeTests(unittest.TestCase):
    def test_interleaved_image_splits_list_and_removes_empty_wrapper(self):
        def provenance(bbox):
            return {"source_page": 1, "bounding_box": bbox}

        nested = {"id": "nested", "type": "list", "ordered": True, "marker_style": "lower-alpha", "children": [{"id": "a", "type": "list_item", "content": "Nested", "provenance": provenance([90, 610, 300, 622])}], "provenance": provenance([90, 610, 300, 622])}
        document = {"blocks": [
            {"id": "steps", "type": "list", "ordered": True, "marker_style": "decimal", "children": [
                {"id": "one", "type": "list_item", "content": "One", "children": [nested], "provenance": provenance([54, 640, 400, 675])},
                {"id": "two", "type": "list_item", "content": "Two", "provenance": provenance([54, 500, 400, 512])},
                {"id": "three", "type": "list_item", "content": "Three", "provenance": provenance([54, 240, 300, 252])},
            ], "provenance": provenance([54, 240, 500, 675])},
            {"id": "wrapper", "type": "paragraph", "content": "", "provenance": provenance([53, 268, 343, 491])},
            {"id": "screen", "type": "image", "src": "images/screen.png", "provenance": provenance([54, 269, 342, 490])},
        ]}
        self.assertTrue(repair_interleaved_images(document))
        self.assertEqual([block["id"] for block in document["blocks"]], ["steps", "screen", "steps-continuation-3"])
        self.assertEqual([item["id"] for item in document["blocks"][0]["children"]], ["one", "two"])
        self.assertEqual(document["blocks"][2]["start"], 3)
        self.assertFalse(repair_interleaved_images(document))

    def test_indented_following_list_is_associated_with_parent_item(self):
        def provenance(bbox):
            return {"source_page": 1, "bounding_box": bbox}

        document = {"blocks": [
            {"id": "step-three", "type": "list", "ordered": True, "start": 3, "children": [
                {"id": "three", "type": "list_item", "content": "Step three", "provenance": provenance([54, 240, 303, 251])}
            ], "provenance": provenance([54, 240, 303, 251])},
            {"id": "details", "type": "list", "ordered": True, "marker_style": "lower-alpha", "children": [
                {"id": "a", "type": "list_item", "content": "Detail A", "provenance": provenance([90, 220, 350, 236])},
                {"id": "b", "type": "list_item", "content": "Detail B", "provenance": provenance([90, 200, 350, 216])},
            ], "provenance": provenance([90, 200, 350, 236])},
        ]}
        self.assertTrue(repair_interleaved_images(document))
        self.assertEqual(len(document["blocks"]), 1)
        self.assertEqual(document["blocks"][0]["children"][0]["children"][0]["id"], "details")

    @mock.patch(
        "pdf_to_web.normalize.recover_source_supplemental_regions",
        return_value={
            "subtitle": ("Post-Baccalaureate 4-Year Sample Program Fall 2026 Cohort", [300, 690, 570, 730]),
            "footer_note": ("*Please note this is a sample plan.", [36, 45, 440, 56]),
            "revision": ("Revised 09/25", [490, 45, 576, 56]),
        },
    )
    def test_supplemental_header_and_footer_regions_are_recovered_once(self, _recover):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            document = {"blocks": [{"id": "recovered-document-title", "type": "heading", "level": 1, "content": "Title"}]}
            self.assertTrue(apply_source_supplemental_regions(document, project))
            self.assertFalse(apply_source_supplemental_regions(document, project))
            self.assertEqual([block["id"] for block in document["blocks"]], [
                "recovered-document-title", "recovered-document-subtitle",
                "recovered-document-note", "recovered-document-revision",
            ])
            self.assertEqual(document["blocks"][1]["level"], 2)
            self.assertEqual(document["blocks"][2]["runs"][0]["type"], "emphasis")
            self.assertEqual(document["blocks"][-1]["content"], "Revised 09/25")

    def _program_plan_document(self):
        def provenance(order, bbox):
            return {"source_page": 1, "bounding_box": bbox, "source_order": order, "raw": {"id": order}}

        tables = [
            {"id": f"t{year}", "type": "table", "rows": [[{"content": f"Year {year} course"}]], "provenance": provenance(year + 10, [36, 600 - year * 120, 576, 690 - year * 120])}
            for year in range(1, 5)
        ]
        labels = [
            {"id": f"y{year}", "type": "list_item", "content": f"YEAR {year}", "children": [tables[year - 1]] if year == 3 else [], "provenance": provenance(year, [36, 692 - year * 120, 82, 706 - year * 120])}
            for year in range(1, 5)
        ]
        return {
            "metadata": {"title": "Program"},
            "blocks": [
                {"id": "title", "type": "heading", "level": 1, "content": "Program", "provenance": provenance(0, [100, 730, 400, 750])},
                {"id": "years", "type": "list", "ordered": False, "children": labels, "provenance": provenance(1, [36, 90, 82, 706])},
                tables[0], tables[1], tables[3],
            ],
        }

    def test_visual_order_restores_multiple_scrambled_heading_table_pairs(self):
        document = self._program_plan_document()
        self.assertTrue(reconcile_visual_reading_order(document))
        self.assertEqual([block["id"] for block in document["blocks"]], ["title", "y1", "t1", "y2", "t2", "y3", "t3", "y4", "t4"])
        self.assertEqual([block["type"] for block in document["blocks"][1::2]], ["heading"] * 4)
        self.assertEqual(document["blocks"][1]["provenance"]["source_order"], 1)
        self.assertEqual(document["blocks"][1]["provenance"]["visual_order_reason"], "heading_table_association")
        self.assertEqual(document["blocks"][6]["rows"][0][0]["content"], "Year 3 course")

    def test_visual_order_is_idempotent_and_keeps_title_first(self):
        document = self._program_plan_document()
        reconcile_visual_reading_order(document)
        first_order = [block["id"] for block in document["blocks"]]
        self.assertFalse(reconcile_visual_reading_order(document))
        self.assertEqual([block["id"] for block in document["blocks"]], first_order)
        self.assertEqual(document["blocks"][0]["id"], "title")

    def test_ambiguous_heading_table_layout_is_flagged_not_reordered(self):
        document = self._program_plan_document()
        duplicate = json.loads(json.dumps(document["blocks"][2]))
        duplicate["id"] = "t1-duplicate"
        duplicate["provenance"]["bounding_box"] = [36, 479, 576, 569]
        document["blocks"].append(duplicate)
        original = [block["id"] for block in document["blocks"]]
        self.assertFalse(reconcile_visual_reading_order(document))
        self.assertEqual([block["id"] for block in document["blocks"]], original)
        issues = document["blocks"][1]["children"][0]["review"]["issues"]
        self.assertEqual(issues[0]["code"], "reading_order_needs_review")

    def test_column_misalignment_prevents_global_y_sort(self):
        document = self._program_plan_document()
        document["blocks"][3]["provenance"]["bounding_box"] = [320, 360, 860, 450]
        original = [block["id"] for block in document["blocks"]]
        self.assertFalse(reconcile_visual_reading_order(document))
        self.assertEqual([block["id"] for block in document["blocks"]], original)

    def test_heading_hierarchy_demotes_extra_h1_and_clamps_jumps(self):
        document = {
            "blocks": [
                {"id": "title", "type": "heading", "level": 1, "content": "Title"},
                {"id": "jump", "type": "heading", "level": 3, "content": "Section"},
                {"id": "extra", "type": "heading", "level": 1, "content": "Appendix"},
            ]
        }
        _normalize_heading_hierarchy(document)
        self.assertEqual([block["level"] for block in document["blocks"]], [1, 2, 2])
        self.assertEqual(document["blocks"][1]["review"]["issues"][0]["code"], "heading_level_jump_corrected")
        self.assertEqual(document["blocks"][2]["review"]["issues"][0]["code"], "additional_h1_demoted")

    def test_title_selection_skips_page_number_and_joins_title_lines(self):
        text = "1\nRegistering for Your CITI Account and\nEnrolling in CITI Trainings\n1. First step"
        regions = [
            ("1", [550, 50, 560, 61], 11),
            ("Registering for", [198, 708, 286, 726], 14),
            ("Your CITI Account and", [286, 708, 414, 726], 14),
            ("Enrolling in CITI Trainings", [233, 691, 380, 709], 14),
            ("First step", [72, 650, 130, 664], 11),
        ]
        title, bbox = _select_source_title(text, regions)
        self.assertEqual(title, "Registering for Your CITI Account and Enrolling in CITI Trainings")
        self.assertEqual(bbox, [198, 691, 414, 726])

    def test_title_selection_collapses_repeated_designed_text(self):
        text = "Body copy first.\nHeart Failure ManagementHeart Failure ManagementHeart Failure Management"
        regions = [
            ("Body copy first.", [0, 20, 200, 40], 20),
            ("Heart Failure Management", [7, 35, 630, 100], 52),
            ("rt", [100, 35, 130, 100], 52),
        ]
        title, _ = _select_source_title(text, regions)
        self.assertEqual(title, "Heart Failure Management")

    def test_pdf_link_annotation_becomes_inline_link_run(self):
        document = {
            "blocks": [
                {
                    "id": "p1",
                    "type": "paragraph",
                    "content": "Visit https://example.edu/help for assistance.",
                    "provenance": {"source_page": 2, "bounding_box": [20, 100, 500, 140]},
                }
            ]
        }
        _apply_link_annotations(
            document,
            [{"url": "https://example.edu/help", "source_page": 2, "bounding_box": [50, 105, 220, 130]}],
        )
        block = document["blocks"][0]
        self.assertEqual([run["type"] for run in block["runs"]], ["text", "link", "text"])
        self.assertEqual(block["runs"][1]["url"], "https://example.edu/help")
        self.assertTrue(document["source_links"][0]["inline_preserved"])

    def test_unmatched_pdf_link_is_reported_without_inventing_visible_text(self):
        document = {
            "blocks": [
                {
                    "id": "p1",
                    "type": "paragraph",
                    "content": "Read the policy.",
                    "provenance": {"source_page": 1, "bounding_box": [20, 100, 500, 140]},
                }
            ]
        }
        _apply_link_annotations(
            document,
            [{"url": "https://example.edu/policy", "source_page": 1, "bounding_box": [50, 105, 220, 130]}],
        )
        self.assertNotIn("runs", document["blocks"][0])
        self.assertFalse(document["source_links"][0]["inline_preserved"])

    def test_link_prefers_nested_block_containing_visible_url(self):
        url = "https://example.edu/help"
        child = {
            "id": "li1",
            "type": "list_item",
            "content": f"Help: {url}",
            "provenance": {"source_page": 1, "bounding_box": [40, 110, 300, 130]},
        }
        document = {
            "blocks": [
                {
                    "id": "list1",
                    "type": "list",
                    "content": "",
                    "children": [child],
                    "provenance": {"source_page": 1, "bounding_box": [20, 80, 500, 160]},
                }
            ]
        }
        _apply_link_annotations(
            document,
            [{"url": url, "source_page": 1, "bounding_box": [50, 112, 220, 128]}],
        )
        self.assertEqual(document["source_links"][0]["source_block"], "li1")
        self.assertEqual(child["runs"][1]["type"], "link")

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

    @mock.patch(
        "pdf_to_web.normalize.recover_source_title_region",
        return_value=("Metadata title", [100.0, 700.0, 300.0, 720.0]),
    )
    def test_recovered_title_adds_matching_h1_when_metadata_already_matches(self, _recover):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "project.json").write_text(
                json.dumps({"schema_version": "pdf-to-web-project-v1", "title": "Project", "source": {}})
            )
            document = {
                "metadata": {"title": "Metadata title"},
                "blocks": [{"id": "section", "type": "heading", "level": 1, "content": "Section"}],
            }
            self.assertTrue(apply_source_title(document, project))
            self.assertEqual(document["blocks"][0]["content"], "Metadata title")

    @mock.patch(
        "pdf_to_web.normalize.recover_source_title_region",
        return_value=("A sufficiently long recovered title", [100.0, 700.0, 300.0, 720.0]),
    )
    def test_recovered_title_does_not_duplicate_longer_matching_h1(self, _recover):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "project.json").write_text(
                json.dumps({"schema_version": "pdf-to-web-project-v1", "title": "Project", "source": {}})
            )
            document = {
                "metadata": {"title": "Project"},
                "blocks": [
                    {
                        "id": "title",
                        "type": "heading",
                        "level": 1,
                        "content": "A sufficiently long recovered title with its final words",
                    }
                ],
            }
            self.assertTrue(apply_source_title(document, project))
            self.assertEqual(len(document["blocks"]), 1)

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

    def test_ordered_markers_are_removed_only_from_matching_semantic_lists(self):
        raw = {
            "kids": [
                {"type": "list", "numbering style": "arabic numbers", "list items": [{"type": "list item", "content": "1. Main"}, {"type": "list item", "content": "2) Next"}]},
                {"type": "list", "numbering style": "english letters", "list items": [{"type": "list item", "content": "a. Alpha"}, {"type": "list item", "content": "B) Upper"}]},
                {"type": "list", "numbering style": "roman numbers", "list items": [{"type": "list item", "content": "i. Roman"}, {"type": "list item", "content": "II) Upper Roman"}]},
                {"type": "paragraph", "content": "1. Ordinary numbered paragraph"},
                {"type": "paragraph", "content": "A. Ordinary lettered paragraph"},
            ]
        }
        document = normalize_document(raw)
        self.assertEqual([item["content"] for item in document["blocks"][0]["children"]], ["Main", "Next"])
        self.assertEqual([item["content"] for item in document["blocks"][1]["children"]], ["Alpha", "Upper"])
        self.assertEqual([item["content"] for item in document["blocks"][2]["children"]], ["Roman", "Upper Roman"])
        self.assertEqual(document["blocks"][0]["marker_style"], "decimal")
        self.assertEqual(document["blocks"][1]["marker_style"], "upper-alpha")
        self.assertEqual(document["blocks"][2]["marker_style"], "upper-roman")
        self.assertEqual(document["blocks"][3]["content"], "1. Ordinary numbered paragraph")
        self.assertEqual(document["blocks"][4]["content"], "A. Ordinary lettered paragraph")

    def test_nested_ordered_lists_keep_style_paragraphs_and_links(self):
        blocks = [{"type": "list", "ordered": True, "marker_style": "decimal", "children": [{"type": "list_item", "content": "1. Main", "runs": [{"type": "text", "text": "1. Visit "}, {"type": "link", "text": "WSU", "url": "https://wsu.edu"}], "children": [{"type": "paragraph", "content": "Explanation"}, {"type": "list", "ordered": True, "marker_style": "lower-alpha", "children": [{"type": "list_item", "content": "a. Substep", "children": [{"type": "list", "ordered": True, "marker_style": "lower-roman", "children": [{"type": "list_item", "content": "i. Detail", "children": []}]}]}]}]}]}]
        _clean_list_markers(blocks)
        main = blocks[0]["children"][0]
        nested = main["children"][1]
        roman = nested["children"][0]["children"][0]
        self.assertEqual(main["content"], "Main")
        self.assertEqual(main["runs"][0]["text"], "Visit ")
        self.assertEqual(main["runs"][1], {"type": "link", "text": "WSU", "url": "https://wsu.edu"})
        self.assertEqual(main["children"][0]["content"], "Explanation")
        self.assertEqual(nested["children"][0]["content"], "Substep")
        self.assertEqual(roman["children"][0]["content"], "Detail")

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
