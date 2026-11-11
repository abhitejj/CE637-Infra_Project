"""Independent checks of actual solver execution and reproducible input handling."""
import copy
import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestIndependentOptimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solver = load_module('audit_solver', '03_solve_optimization.py')
        cls.lp = cls.solver.build_lp_matrices()
        cls.custom = cls.solver.solve_custom_two_phase_simplex(cls.lp)
        cls.highs, cls.a, cls.b = cls.solver.solve_scipy_highs_verification(cls.lp)

    def test_solver_objective_and_all_primal_constraints(self):
        for x in (self.custom['x_solution'], self.highs.x):
            self.assertGreaterEqual(float(np.min(x)), -1e-7)
            self.assertLessEqual(float(np.max(self.a @ x - self.b)), 1e-7)
            self.assertAlmostEqual(float(self.lp['c_cost'] @ x), self.highs.fun, places=5)
        np.testing.assert_allclose(self.a[12:] @ self.custom['x_solution'], self.b[12:], atol=1e-7)

    def test_signed_dual_feasibility_and_strong_duality(self):
        y = self.highs.ineqlin.marginals
        slack = self.b - self.a @ self.highs.x
        reduced = self.lp['c_cost'] - self.a.T @ y
        self.assertLessEqual(float(y.max()), 1e-7)
        self.assertGreaterEqual(float(reduced.min()), -1e-7)
        np.testing.assert_allclose(y * slack, 0, atol=1e-5)
        np.testing.assert_allclose(reduced * self.highs.x, 0, atol=1e-5)
        self.assertAlmostEqual(float(self.b @ y), self.highs.fun, places=5)

    def test_infeasible_instance_rejected_explicitly(self):
        lp = copy.deepcopy(self.lp)
        lp['b'][:12] = 0
        with self.assertRaisesRegex(ValueError, '(?i)infeasib'):
            self.solver.solve_custom_two_phase_simplex(lp)

    def test_perturbed_rhs_feasibility_and_objectives_match_highs(self):
        rng = np.random.default_rng(637)
        for case in range(30):
            with self.subTest(case=case):
                lp = copy.deepcopy(self.lp)
                lp['b'] = lp['b'] * rng.uniform(.3, 1.8, 24)
                b = lp['b'].copy()
                b[12:] *= -1
                reference = linprog(lp['c_cost'], A_ub=self.a, b_ub=b, method='highs-ds')
                if reference.status == 2:
                    with self.assertRaisesRegex(ValueError, '(?i)infeasib'):
                        self.solver.solve_custom_two_phase_simplex(lp)
                else:
                    self.assertTrue(reference.success, reference.message)
                    result = self.solver.solve_custom_two_phase_simplex(lp)
                    self.assertAlmostEqual(result['Z_star'], reference.fun, places=4)
                    self.assertLessEqual(float(np.max(self.a @ result['x_solution'] - b)), 1e-5)

    def test_zero_rhs_feasible_degenerate_instance(self):
        lp = copy.deepcopy(self.lp)
        lp['b'][:] = 0
        result = self.solver.solve_custom_two_phase_simplex(lp)
        np.testing.assert_allclose(result['x_solution'], 0, atol=1e-7)
        self.assertAlmostEqual(result['Z_star'], 0)

    def solve_capacity(self, capacity):
        b = self.b.copy()
        b[9] = capacity
        result = linprog(self.lp['c_cost'], A_ub=self.a, b_ub=b, method='highs-ds')
        self.assertTrue(result.success, result.message)
        return result

    def test_sensitivity_breakpoint_uses_one_sided_differences(self):
        z = {v: self.solve_capacity(v).fun for v in (28000, 31999, 32000, 32001, 33999, 34000, 34001, 35000)}
        self.assertAlmostEqual(z[31999] - z[32000], 1022.90, places=4)
        self.assertAlmostEqual(z[32000] - z[32001], 706.55, places=4)
        self.assertAlmostEqual(z[33999] - z[34000], 706.55, places=4)
        self.assertAlmostEqual(z[34000], z[34001], places=4)
        self.assertAlmostEqual(z[34000], z[35000], places=4)
        self.assertAlmostEqual(z[28000] - z[34000], 5504700, places=4)

    def test_rounded_costs_have_bounded_affine_residual(self):
        distance = self.lp['df_dist'].to_numpy()
        ideal_cost = np.repeat((100 + 2.5 * distance).reshape(-1), 2)
        x = self.custom['x_solution']
        residual = float((self.lp['c_cost'] - ideal_cost) @ x)
        self.assertLessEqual(abs(residual), 0.0050001 * x.sum())
        self.assertGreater(abs(residual), 1, 'Baseline rounded rates are not an exact affine objective')

    def test_exported_flows_recompute_objective_and_constraints(self):
        shipments = pd.read_csv(ROOT / 'outputs/tables/optimal_shipments_wheat_rice.csv')
        x = shipments[['wheat_shipped_mt', 'rice_shipped_mt']].to_numpy().reshape(-1)
        self.assertLessEqual(float(np.max(self.a @ x - self.b)), 1e-7)
        self.assertAlmostEqual(float(self.lp['c_cost'] @ x), self.highs.fun, places=5)
        np.testing.assert_allclose(shipments.total_cost_inr, shipments.total_shipped_mt * shipments.unit_cost_inr_per_mt, atol=.01)


class TestOfflineDatasetReplay(unittest.TestCase):
    def replay(self, invalid=False):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / 'data/raw').mkdir(parents=True)
            raw = directory / 'data/raw/osrm_response.json'
            if invalid:
                raw.write_text(json.dumps({'code': 'NoTable', 'distances': []}))
            else:
                shutil.copyfile(ROOT / 'data/raw/osrm_response.json', raw)
            before = raw.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/01_build_dataset.py')], cwd=directory, capture_output=True, text=True, timeout=30)
            self.assertEqual(raw.read_bytes(), before, 'Raw routing evidence must never be overwritten by replay')
            if invalid:
                self.assertNotEqual(result.returncode, 0, 'Invalid routing payload must fail without a fabricated fallback')
                return
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(before)
            for file, key, divisor in [('distance_matrix_km.csv', 'distances', 1000), ('duration_matrix_hr.csv', 'durations', 3600)]:
                actual = pd.read_csv(directory / 'data/processed' / file, index_col='depot_id').to_numpy()
                np.testing.assert_allclose(actual, np.round(np.array(payload[key]) / divisor, 2), atol=1e-9)
            for file in ('distance_matrix_km.csv', 'duration_matrix_hr.csv', 'cost_matrix_inr_per_mt.csv'):
                a = pd.read_csv(directory / 'data/processed' / file, index_col='depot_id')
                b = pd.read_csv(ROOT / 'data/processed' / file, index_col='depot_id')
                pd.testing.assert_frame_equal(a, b)

    def test_source_register_categories_and_raw_fingerprint(self):
        register = pd.read_csv(ROOT / 'data/source_register.csv')
        self.assertTrue(set(register.Category).issubset({'OFFICIAL', 'RETRIEVED', 'CALCULATED', 'ASSUMPTION'}))
        self.assertTrue(set(register.Verification_Status).issubset({'VERIFIED', 'PROVISIONAL', 'ASSUMED'}))
        assumed = register[register.Category == 'ASSUMPTION']
        self.assertTrue((assumed.Verification_Status == 'ASSUMED').all())
        self.assertGreaterEqual(len(assumed), 3)
        fingerprint = hashlib.sha256((ROOT / 'data/raw/osrm_response.json').read_bytes()).hexdigest()
        retrieved = register[register.Category == 'RETRIEVED']
        self.assertIn(fingerprint, ' '.join(retrieved.Specific_Data_Fields))

    def test_default_replay_immutable_and_reproducible(self):
        self.replay()

    def test_invalid_osrm_payload_fails_without_fallback(self):
        self.replay(invalid=True)


if __name__ == '__main__':
    unittest.main()
