"""Phase 4 Independent QA and Adversarial Verification Test Suite.

Audits:
1. Existence and integrity of report/Final_Report.md, report/Final_Report.tex, and report/Final_Report.pdf.
2. PDF page count equals exactly 7 pages, with a separate 1-page poster.
3. Page-by-page mapping to rubric sections:
   - Page 1: Section 1 (The Question)
   - Page 2: Section 2 (The Model)
   - Page 3: Section 3 (The Method)
   - Page 4: Section 4 (The Answer)
   - Page 5: Section 5 (One Sensitivity Check)
   - Page 6: Section 6 (What the Model Cannot Say)
   - Page 7: References Page
4. Exact Sentence Constraint: Section 6 must contain EXACTLY THREE sentences.
5. Numerical consistency between LaTeX/Markdown reports and Phase 3 solver outputs:
   - Z* = 56,982,720.00 INR
   - Average cost = 431.69 INR/MT
   - Tonne-km = 17,513,100
   - Reported pivots match the executed solver diagnostics
   - Chhani shadow price = 1022.90 INR/MT
   - Saturation breakpoint = 34,000 MT
"""

import json
import os
import re
import unittest
import pypdf
import pandas as pd


class TestPhase4Deliverables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.md_path = "report/Final_Report.md"
        cls.tex_path = "report/Final_Report.tex"
        cls.pdf_path = "report/Final_Report.pdf"
        cls.diag_path = "outputs/tables/solver_diagnostics.json"

        with open(cls.diag_path, "r", encoding="utf-8") as f:
            cls.diagnostics = json.load(f)

        with open(cls.md_path, "r", encoding="utf-8") as f:
            cls.md_content = f.read()

        with open(cls.tex_path, "r", encoding="utf-8") as f:
            cls.tex_content = f.read()

        cls.pdf_reader = pypdf.PdfReader(cls.pdf_path)
        cls.poster_pdf_path = "report/Poster.pdf"
        cls.poster_reader = pypdf.PdfReader(cls.poster_pdf_path)

    def test_01_files_exist_and_non_empty(self):
        self.assertTrue(os.path.exists(self.md_path))
        self.assertTrue(os.path.exists(self.tex_path))
        self.assertTrue(os.path.exists(self.pdf_path))
        self.assertTrue(os.path.exists(self.poster_pdf_path))
        self.assertGreater(os.path.getsize(self.md_path), 5000)
        self.assertGreater(os.path.getsize(self.tex_path), 5000)
        self.assertGreater(os.path.getsize(self.pdf_path), 500000)
        self.assertGreater(os.path.getsize(self.poster_pdf_path), 500000)

    def test_02_pdf_page_count_exactly_seven(self):
        self.assertEqual(len(self.pdf_reader.pages), 7, "Final_Report.pdf must have strictly 7 pages (6 sections + references).")
        self.assertEqual(len(self.poster_reader.pages), 1, "Poster.pdf must have strictly 1 page.")

    def test_03_page_by_page_rubric_sections(self):
        expected_sections = [
            (0, "Section 1: The Question"),
            (1, "Section 2: The Model"),
            (2, "Section 3: The Method"),
            (3, "Section 4: The Answer"),
            (4, "Section 5: One Sensitivity Check"),
            (5, "Section 6: What the Model Cannot Say"),
            (6, "References"),
        ]
        for page_idx, expected_header in expected_sections:
            page_text = self.pdf_reader.pages[page_idx].extract_text()
            self.assertIn(
                expected_header.lower(),
                page_text.lower(),
                f"Page {page_idx + 1} does not contain '{expected_header}'",
            )

    def test_04_section_6_sentence_count_exact(self):
        """Rubric requirement: Section 6 must have EXACTLY THREE sentences."""
        page_6_text = self.pdf_reader.pages[5].extract_text()

        # Find items 1., 2., 3.
        pattern = r"\d\.\s+([A-Z].*?)(?=(?:\d\.\s+[A-Z]|\Z|Page\s+6))"
        matches = re.findall(pattern, page_6_text, re.DOTALL)
        self.assertEqual(len(matches), 3, f"Expected exactly 3 numbered entries in Section 6, found {len(matches)}")

        for idx, item in enumerate(matches, 1):
            clean_item = " ".join(item.strip().split())
            # Each entry must end with a period and represent a single complete sentence
            self.assertTrue(clean_item.endswith("."), f"Sentence {idx} does not end with period: {clean_item}")
            # Count internal sentence terminators (. ! ?)
            internal_terminators = re.findall(r"\w+[.!?]\s+[A-Z]", clean_item)
            self.assertEqual(
                len(internal_terminators),
                0,
                f"Entry {idx} contains multiple sentences: {clean_item}",
            )

    def test_05_numerical_consistency_with_solver_telemetry(self):
        z_opt = self.diagnostics["total_system_cost_inr"]
        piv_1 = self.diagnostics["simplex_pivots_phase1"]
        piv_2 = self.diagnostics["simplex_pivots_phase2"]
        total_piv = self.diagnostics["simplex_total_pivots"]
        avg_cost = self.diagnostics["average_cost_per_mt_inr"]
        tonne_km = self.diagnostics["total_tonne_km"]

        self.assertEqual(z_opt, 56982720.0)
        self.assertGreater(piv_1, 0)
        self.assertGreater(piv_2, 0)
        self.assertEqual(total_piv, piv_1 + piv_2)
        self.assertAlmostEqual(avg_cost, 431.69, places=2)
        self.assertEqual(tonne_km, 17513100.0)

        # Check in LaTeX content
        self.assertIn("56,982,720.00", self.tex_content)
        self.assertIn("431.69", self.tex_content)
        self.assertIn("17.51 Million Tonne-km", self.tex_content)
        self.assertIn(f"{piv_1} steps (pivots)", self.tex_content)
        self.assertIn(f"another {piv_2} steps", self.tex_content)
        self.assertIn(f"{total_piv} pivots in total", self.tex_content)

        # Check in Markdown content
        self.assertIn("56,982,720.00", self.md_content)
        self.assertIn("431.69", self.md_content)
        self.assertIn("17,513,100", self.md_content)

    def test_06_sensitivity_numbers_consistent(self):
        # Chhani shadow price 1022.90 and breakpoint at 34,000 MT
        self.assertIn("1,022.90", self.tex_content)
        self.assertIn("706.55", self.tex_content)
        self.assertIn("34,000", self.tex_content)
        self.assertIn("5,504,700.00", self.tex_content)
        self.assertIn("6.61 Crore", self.tex_content)

    def test_07_images_exist_and_embedded(self):
        fig1 = "outputs/figures/fig1_network_flow_map.png"
        fig2 = "outputs/figures/fig2_depot_utilization.png"
        fig3 = "outputs/figures/fig3_sensitivity_curve_shadow_price.png"

        self.assertTrue(os.path.exists(fig1))
        self.assertTrue(os.path.exists(fig2))
        self.assertTrue(os.path.exists(fig3))

        self.assertIn("fig1_network_flow_map.png", self.tex_content)
        self.assertIn("fig2_depot_utilization.png", self.tex_content)
        self.assertIn("fig3_sensitivity_curve_shadow_price.png", self.tex_content)


    def test_08_source_section6_exactly_three_sentences(self):
        md_section = self.md_content.split('Section 6: What the Model Cannot Say', 1)[1].split('# Page 7', 1)[0]
        tex_section = self.tex_content.split(r'\section*{Section 6: What the Model Cannot Say}', 1)[1].split(r'\end{enumerate}', 1)[0]
        md_items = re.findall(r'^\d+\.\s+(.+)$', md_section, re.MULTILINE)
        tex_items = re.findall(r'\\item\s+(.+)$', tex_section, re.MULTILINE)
        for items in (md_items, tex_items):
            self.assertEqual(len(items), 3)
            for item in items:
                self.assertTrue(item.endswith('.'))
                self.assertEqual(len(re.findall(r'[.!?](?:\s|$)', item)), 1, item)

    def test_09_poster_a3_landscape_and_author_metadata(self):
        page = self.poster_reader.pages[0]
        self.assertAlmostEqual(float(page.mediabox.width), 1190.55, delta=1)
        self.assertAlmostEqual(float(page.mediabox.height), 841.89, delta=1)
        for reader in (self.pdf_reader, self.poster_reader):
            text = ' '.join(page.extract_text() for page in reader.pages)
            compact = re.sub(r'\s+', '', text)
            for required in ('AbhitejSinghBhullar', 'RadhikaPurohit', '23110009', '24110280', 'CE637'):
                self.assertIn(required, compact)
            self.assertTrue('IITGandhinagar' in compact or 'IndianInstituteofTechnologyGandhinagar' in compact)
            self.assertNotIn('TeamGujarat', compact)
            self.assertNotIn('TechnicalWorkingPaper', compact)

    def test_10_report_active_route_table_values_match_csv(self):
        shipments = pd.read_csv('outputs/tables/optimal_shipments_wheat_rice.csv')
        fields = ['distance_km', 'wheat_shipped_mt', 'rice_shipped_mt', 'total_shipped_mt', 'unit_cost_inr_per_mt', 'total_cost_inr', 'tonne_km']
        for content, delimiter, marker in ((self.md_content, '|', '# Page 4'), (self.tex_content, '&', r'\section*{Section 4: The Answer}')):
            section = content.split(marker, 1)[1]
            for _, shipment in shipments[shipments.total_shipped_mt > 0].iterrows():
                rows = [line for line in section.splitlines() if f"{shipment.depot_id}:" in line and f"{shipment.warehouse_id}:" in line and delimiter in line]
                self.assertEqual(len(rows), 1, (shipment.depot_id, shipment.warehouse_id))
                cells = [cell for cell in rows[0].split(delimiter) if cell.strip()]
                values = [float(re.search(r'[0-9][0-9,]*(?:\.[0-9]+)?', cell).group().replace(',', '')) for cell in cells[2:9]]
                self.assertEqual(len(values), len(fields))
                for value, field in zip(values, fields):
                    self.assertAlmostEqual(value, shipment[field], places=2, msg=f'{shipment.depot_id}->{shipment.warehouse_id}: {field}')

    def test_11_poster_showcase_standalone(self):
        self.assertEqual(len(self.poster_reader.pages), 1)
        page = self.poster_reader.pages[0]
        poster_text = re.sub(r'\s+', '', page.extract_text()).lower()
        self.assertIn('132,000', poster_text)
        self.assertIn('56,982,720', poster_text)
        self.assertIn('surat', poster_text)
        self.assertIn('chhani', poster_text)

    def test_12_report_prose_matches_source(self):
        tex_section = self.tex_content.split(r'\section*{Section 6: What the Model Cannot Say}', 1)[1].split(r'\end{enumerate}', 1)[0]
        source_sentences = re.findall(r'\\item\s+(.+)$', tex_section, re.MULTILINE)
        pdf_text = re.sub(r'[\s\-–—]+', '', self.pdf_reader.pages[5].extract_text())
        for sentence in source_sentences:
            self.assertIn(re.sub(r'[\s\-–—]+', '', sentence), pdf_text)
        for heading in ('Linear Transport Cost', 'Single Average Month', 'How the Solver Reached the Optimal Answer'):
            self.assertIn(heading, self.tex_content)
        for obsolete_heading in ('Algorithmic Convergence Telemetry', 'Stationary Monthly Planning', 'Affine Haulage Cost \\& Fleet Homogeneity'):
            self.assertNotIn(obsolete_heading, self.tex_content)

if __name__ == "__main__":
    unittest.main()
