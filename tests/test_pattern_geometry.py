import unittest
from src.chart_data import detect_chart_patterns, compute_fibo_and_indicators

# Fixture candles copied from real VRT and NOW historical data (35 bars) so tests are 100% self-contained
# and never read or touch data/candles_cache.json.
VRT_FIXTURE_CANDLES = [
    {"time": "2026-09-10", "open": 259.1, "high": 262.0, "low": 244.77, "close": 248.13, "volume": 10055200},
    {"time": "2026-09-11", "open": 252.5, "high": 258.78, "low": 251.84, "close": 257.06, "volume": 4767600},
    {"time": "2026-09-14", "open": 228.0, "high": 241.3, "low": 226.94, "close": 237.39, "volume": 10905000},
    {"time": "2026-09-15", "open": 243.02, "high": 245.41, "low": 233.9, "close": 234.61, "volume": 5728200},
    {"time": "2026-09-16", "open": 240.0, "high": 244.76, "low": 237.64, "close": 239.41, "volume": 5514600},
    {"time": "2026-09-17", "open": 249.75, "high": 252.34, "low": 241.25, "close": 241.49, "volume": 4967200},
    {"time": "2026-09-18", "open": 246.19, "high": 250.15, "low": 242.43, "close": 249.39, "volume": 7837100},
    {"time": "2026-09-21", "open": 254.67, "high": 254.88, "low": 247.61, "close": 250.86, "volume": 4867500},
    {"time": "2026-09-22", "open": 250.3, "high": 255.4, "low": 249.14, "close": 253.46, "volume": 3518200},
    {"time": "2026-09-23", "open": 253.68, "high": 255.02, "low": 248.51, "close": 248.78, "volume": 3549000},
    {"time": "2026-09-24", "open": 240.47, "high": 246.9, "low": 239.0, "close": 245.3, "volume": 4122500},
    {"time": "2026-09-25", "open": 249.18, "high": 254.5, "low": 248.0, "close": 253.28, "volume": 4127100},
    {"time": "2026-09-28", "open": 253.23, "high": 254.2, "low": 242.52, "close": 244.04, "volume": 4274800},
    {"time": "2026-09-29", "open": 251.38, "high": 254.13, "low": 246.84, "close": 248.34, "volume": 3289900},
    {"time": "2026-09-30", "open": 249.48, "high": 250.82, "low": 241.27, "close": 241.31, "volume": 4176500},
    {"time": "2026-10-01", "open": 242.92, "high": 249.53, "low": 238.3, "close": 246.12, "volume": 3469200},
    {"time": "2026-10-02", "open": 250.64, "high": 254.8, "low": 248.54, "close": 252.18, "volume": 3344900},
    {"time": "2026-10-05", "open": 254.34, "high": 258.1, "low": 250.06, "close": 253.62, "volume": 4352200},
    {"time": "2026-10-06", "open": 253.2, "high": 256.5, "low": 249.1, "close": 253.14, "volume": 4238300},
    {"time": "2026-10-07", "open": 244.02, "high": 246.87, "low": 239.64, "close": 246.49, "volume": 5491400},
    {"time": "2026-10-08", "open": 242.2, "high": 252.1, "low": 239.76, "close": 243.73, "volume": 5873500},
    {"time": "2026-10-09", "open": 246.47, "high": 248.49, "low": 239.89, "close": 242.78, "volume": 3421900},
    {"time": "2026-10-12", "open": 239.66, "high": 242.82, "low": 237.4, "close": 239.36, "volume": 3530700},
    {"time": "2026-10-13", "open": 234.26, "high": 238.55, "low": 230.68, "close": 237.29, "volume": 4801500},
    {"time": "2026-10-14", "open": 233.92, "high": 234.8, "low": 220.21, "close": 222.83, "volume": 7365800},
    {"time": "2026-10-15", "open": 212.2, "high": 215.36, "low": 204.38, "close": 214.75, "volume": 12921900},
    {"time": "2026-10-16", "open": 211.02, "high": 213.39, "low": 205.88, "close": 206.42, "volume": 6447300},
    {"time": "2026-10-19", "open": 214.0, "high": 214.71, "low": 205.44, "close": 206.08, "volume": 4891200},
    {"time": "2026-10-20", "open": 202.49, "high": 208.94, "low": 197.9, "close": 203.56, "volume": 6804100},
    {"time": "2026-10-21", "open": 216.58, "high": 220.0, "low": 210.94, "close": 212.15, "volume": 6412200},
    {"time": "2026-10-22", "open": 203.61, "high": 204.0, "low": 193.14, "close": 195.59, "volume": 8434200},
    {"time": "2026-10-23", "open": 191.6, "high": 196.73, "low": 187.24, "close": 194.32, "volume": 7398300},
    {"time": "2026-10-26", "open": 197.63, "high": 201.68, "low": 194.55, "close": 199.78, "volume": 5530500},
    {"time": "2026-10-27", "open": 203.0, "high": 210.92, "low": 203.0, "close": 208.56, "volume": 8407800},
    {"time": "2026-10-28", "open": 243.0, "high": 243.0, "low": 228.82, "close": 234.5, "volume": 8105463},
]

NOW_FIXTURE_CANDLES = [
    {"time": "2026-09-10", "open": 130.64, "high": 134.7, "low": 130.64, "close": 131.17, "volume": 13852200},
    {"time": "2026-09-11", "open": 130.5, "high": 134.45, "low": 130.39, "close": 132.53, "volume": 10730000},
    {"time": "2026-09-14", "open": 140.0, "high": 143.19, "low": 137.24, "close": 142.35, "volume": 17501800},
    {"time": "2026-09-15", "open": 139.15, "high": 147.57, "low": 139.0, "close": 141.9, "volume": 14704500},
    {"time": "2026-09-16", "open": 139.2, "high": 141.67, "low": 138.33, "close": 139.82, "volume": 9855600},
    {"time": "2026-09-17", "open": 139.07, "high": 140.54, "low": 136.0, "close": 138.47, "volume": 9857700},
    {"time": "2026-09-18", "open": 139.71, "high": 139.94, "low": 135.07, "close": 135.47, "volume": 19250600},
    {"time": "2026-09-21", "open": 136.82, "high": 140.16, "low": 135.62, "close": 137.68, "volume": 10893000},
    {"time": "2026-09-22", "open": 141.83, "high": 142.1, "low": 135.23, "close": 137.0, "volume": 12580700},
    {"time": "2026-09-23", "open": 137.22, "high": 141.54, "low": 136.15, "close": 140.78, "volume": 11366200},
    {"time": "2026-09-24", "open": 139.9, "high": 141.04, "low": 137.53, "close": 137.78, "volume": 9578700},
    {"time": "2026-09-25", "open": 137.25, "high": 139.83, "low": 135.6, "close": 135.62, "volume": 8239600},
    {"time": "2026-09-28", "open": 129.8, "high": 131.89, "low": 126.75, "close": 131.45, "volume": 11936000},
    {"time": "2026-09-29", "open": 130.83, "high": 132.44, "low": 128.12, "close": 129.94, "volume": 10080300},
    {"time": "2026-09-30", "open": 129.75, "high": 135.08, "low": 128.85, "close": 134.01, "volume": 9032800},
    {"time": "2026-10-01", "open": 139.05, "high": 140.8, "low": 134.77, "close": 137.76, "volume": 10217300},
    {"time": "2026-10-02", "open": 139.42, "high": 139.57, "low": 133.47, "close": 134.38, "volume": 8859800},
    {"time": "2026-10-05", "open": 135.22, "high": 137.9, "low": 134.15, "close": 136.08, "volume": 7836100},
    {"time": "2026-10-06", "open": 138.46, "high": 140.6, "low": 136.18, "close": 137.97, "volume": 9476600},
    {"time": "2026-10-07", "open": 139.5, "high": 140.8, "low": 137.49, "close": 137.87, "volume": 8030800},
    {"time": "2026-10-08", "open": 139.25, "high": 142.51, "low": 135.58, "close": 139.75, "volume": 11834400},
    {"time": "2026-10-09", "open": 141.26, "high": 142.47, "low": 139.43, "close": 140.86, "volume": 6287800},
    {"time": "2026-10-12", "open": 145.54, "high": 148.14, "low": 139.76, "close": 140.32, "volume": 9632900},
    {"time": "2026-10-13", "open": 140.19, "high": 145.17, "low": 138.16, "close": 138.61, "volume": 13213900},
    {"time": "2026-10-14", "open": 139.49, "high": 142.8, "low": 138.39, "close": 139.98, "volume": 13372900},
    {"time": "2026-10-15", "open": 139.65, "high": 149.34, "low": 139.58, "close": 148.57, "volume": 17629000},
    {"time": "2026-10-16", "open": 151.92, "high": 154.2, "low": 139.94, "close": 141.97, "volume": 15529100},
    {"time": "2026-10-19", "open": 141.09, "high": 145.48, "low": 140.7, "close": 145.36, "volume": 9564200},
    {"time": "2026-10-20", "open": 148.08, "high": 150.04, "low": 146.31, "close": 149.54, "volume": 10796700},
    {"time": "2026-10-21", "open": 149.64, "high": 153.98, "low": 148.4, "close": 153.12, "volume": 13065200},
    {"time": "2026-10-22", "open": 154.25, "high": 157.6, "low": 153.57, "close": 157.0, "volume": 17406900},
    {"time": "2026-10-23", "open": 156.38, "high": 159.5, "low": 153.72, "close": 158.96, "volume": 11100800},
    {"time": "2026-10-26", "open": 158.55, "high": 159.3, "low": 155.0, "close": 158.18, "volume": 14739100},
    {"time": "2026-10-27", "open": 156.1, "high": 157.13, "low": 152.88, "close": 154.78, "volume": 13462300},
    {"time": "2026-10-28", "open": 151.6, "high": 155.15, "low": 151.13, "close": 152.61, "volume": 5234261},
]


def make_4pt_candles(p1: float, t1: float, p2: float, t2: float, total: int = 36):
    """
    Generate synthetic candles with 4 alternating swing points:
    Peak 1 at index 5, Trough 1 at index 14, Peak 2 at index 23, Trough 2 at index 31.
    """
    candles = []
    for i in range(total):
        if i <= 5:
            val = t1 + (p1 - t1) * (i / 5.0)
        elif i <= 14:
            val = p1 - (p1 - t1) * ((i - 5) / 9.0)
        elif i <= 23:
            val = t1 + (p2 - t1) * ((i - 14) / 9.0)
        elif i <= 31:
            val = p2 - (p2 - t2) * ((i - 23) / 8.0)
        else:
            val = t2 + (i - 31) * 0.6

        if i == 5:
            h, l = p1, p1 - 1.0
        elif i == 14:
            h, l = t1 + 1.0, t1
        elif i == 23:
            h, l = p2, p2 - 1.0
        elif i == 31:
            h, l = t2 + 1.0, t2
        else:
            h, l = val + 0.2, val - 0.2
        o = (h + l) / 2.0
        c = o
        t_str = f"2026-08-{i+1:02d}" if i < 31 else f"2026-09-{i-30:02d}"
        candles.append({
            "time": t_str,
            "open": round(o, 2),
            "high": round(h, 2),
            "low": round(l, 2),
            "close": round(c, 2),
            "volume": 1000000
        })
    return candles


class TestPatternGeometry(unittest.TestCase):
    def test_vrt_screenshot_case_does_not_declare_falling_wedge_or_wide_box(self):
        """
        In the user screenshot for VRT, Wedge Low 1 ($238.30) was higher than Wedge High 2 ($220.00),
        slopes diverged, swings were non-alternating, and the 30-bar span is 37.8% (> 15% box limit).
        The system must NOT declare Falling Wedge, and must NOT declare Consolidation Box.
        Uses VRT fixture candles directly (never reads disk cache).
        """
        self.assertGreater(len(VRT_FIXTURE_CANDLES), 30)
        pat = detect_chart_patterns(VRT_FIXTURE_CANDLES)
        self.assertIsNone(pat)

    def test_now_screenshot_case_does_not_declare_expanding_triangle_or_wide_box(self):
        """
        In the user screenshot for NOW, both lows preceded both highs (T1 < T2 < P1 < P2),
        and the 30-bar span is 25.8% (> 15% box limit).
        The system must NOT declare Expanding Triangle, and must NOT declare Consolidation Box.
        Uses NOW fixture candles directly (never reads disk cache).
        """
        self.assertGreater(len(NOW_FIXTURE_CANDLES), 30)
        pat = detect_chart_patterns(NOW_FIXTURE_CANDLES)
        self.assertIsNone(pat)

    def test_valid_falling_wedge_converges_and_confirms_on_breakout(self):
        """
        A geometrically valid Falling Wedge has:
        - Alternating swings: P1 -> T1 -> P2 -> T2
        - Both slopes negative (sloping down)
        - Lower line flatter than upper line (trough_slope > peak_slope)
        - End spread strictly narrower than start spread (converging)
        - Forms as 'forming' until close breaks out above upper resistance.
        """
        candles = make_4pt_candles(100.0, 88.0, 91.5, 83.2)

        # Pre-breakout state
        pat = detect_chart_patterns(candles)
        self.assertIsNotNone(pat)
        self.assertEqual(pat.get("name"), "Bullish Falling Wedge (ลิ่มเฉียงลงสะสมแรง)")
        self.assertEqual(pat.get("status"), "forming")

        # Verify lines pass through points and converge
        lines = pat.get("lines", [])
        self.assertEqual(len(lines), 2)
        upper_line = [l for l in lines if "Upper" in l["name"]][0]
        lower_line = [l for l in lines if "Lower" in l["name"]][0]
        self.assertEqual(upper_line["points"][0]["value"], 100.0)
        self.assertEqual(lower_line["points"][0]["value"], 88.0)

        start_spread = 100.0 - 88.0
        end_spread = upper_line["points"][1]["value"] - lower_line["points"][1]["value"]
        self.assertGreater(end_spread, 0)
        self.assertLess(end_spread, start_spread)

        # Breakout state: add candle closing above the falling wedge roof
        breakout_c = {
            "time": "2026-09-06",
            "open": 86.0,
            "high": 93.0,
            "low": 85.5,
            "close": 92.0,
            "volume": 2500000
        }
        pat_bo = detect_chart_patterns(candles + [breakout_c])
        self.assertIsNotNone(pat_bo)
        self.assertEqual(pat_bo.get("name"), "Bullish Falling Wedge (ลิ่มเฉียงลงสะสมแรง)")
        self.assertEqual(pat_bo.get("status"), "confirmed")

    def test_valid_ascending_triangle_detected_and_lines_flat(self):
        """
        Ascending Triangle requires:
        - Alternating swings: P1 -> T1 -> P2 -> T2
        - P1 ~= P2 (flat horizontal resistance ceiling)
        - T2 > T1 (rising support line)
        - Flat resistance line has identical values for start and end point (average value).
        """
        candles = make_4pt_candles(100.0, 88.0, 100.0, 94.0)

        pat = detect_chart_patterns(candles)
        self.assertIsNotNone(pat)
        self.assertIn("Ascending Triangle", pat.get("name", ""))
        self.assertEqual(pat.get("status"), "forming")

        # Flat Resistance line must use single flat value (average of p1 and p2 = 100.0)
        lines = pat.get("lines", [])
        flat_res_lines = [l for l in lines if "Flat Resistance" in l["name"]]
        self.assertEqual(len(flat_res_lines), 1)
        res_pts = flat_res_lines[0]["points"]
        self.assertEqual(res_pts[0]["value"], 100.0)
        self.assertEqual(res_pts[1]["value"], 100.0)

    def test_ascending_triangle_breakout_confirmed(self):
        """
        When price in Ascending Triangle closes above the flat resistance ceiling (100.0 * 1.002 = 100.2),
        the status must transition from 'forming' to 'confirmed'.
        """
        candles = make_4pt_candles(100.0, 88.0, 100.0, 94.0)
        bo_c = {
            "time": "2026-09-06",
            "open": 99.0,
            "high": 102.0,
            "low": 98.5,
            "close": 101.5,
            "volume": 2000000
        }
        pat_bo = detect_chart_patterns(candles + [bo_c])
        self.assertIsNotNone(pat_bo)
        self.assertIn("Ascending Triangle", pat_bo.get("name", ""))
        self.assertEqual(pat_bo.get("status"), "confirmed")

    def test_valid_descending_triangle_detected_forming_above_floor(self):
        """
        Descending Triangle requires:
        - Alternating swings: P1 -> T1 -> P2 -> T2
        - P2 < P1 (falling resistance line)
        - T1 ~= T2 (flat horizontal support floor)
        - Flat support line has identical values for start and end point (average value).
        - Status must be 'forming' while price is above floor (NOT failed).
        """
        candles = make_4pt_candles(100.0, 85.0, 93.0, 85.0)

        pat = detect_chart_patterns(candles)
        self.assertIsNotNone(pat)
        self.assertIn("Descending Triangle", pat.get("name", ""))
        self.assertEqual(pat.get("status"), "forming")

        # Flat Support line must be truly horizontal with single flat value 85.0
        lines = pat.get("lines", [])
        flat_sup_lines = [l for l in lines if "Flat Support" in l["name"]]
        self.assertEqual(len(flat_sup_lines), 1)
        sup_pts = flat_sup_lines[0]["points"]
        self.assertEqual(sup_pts[0]["value"], 85.0)
        self.assertEqual(sup_pts[1]["value"], 85.0)

    def test_descending_triangle_confirmed_and_failed_lifecycle(self):
        """
        Descending Triangle lifecycle:
        - Confirmed breakdown when close <= floor * 0.998 (85.0 * 0.998 = 84.83).
        - Failed pattern when close breaks above dynamic descending upper resistance roof.
        """
        base_candles = make_4pt_candles(100.0, 85.0, 93.0, 85.0)

        # 1. Confirmed breakdown below floor
        c_conf = base_candles + [{
            "time": "2026-09-06",
            "open": 86.0,
            "high": 86.5,
            "low": 84.0,
            "close": 84.5,
            "volume": 2000000
        }]
        pat_conf = detect_chart_patterns(c_conf)
        self.assertIsNotNone(pat_conf)
        self.assertIn("Descending Triangle", pat_conf.get("name", ""))
        self.assertEqual(pat_conf.get("status"), "confirmed")

        # 2. Failed pattern breaking out above falling roof
        c_fail = base_candles + [{
            "time": "2026-09-06",
            "open": 92.0,
            "high": 96.0,
            "low": 91.5,
            "close": 95.0,
            "volume": 2000000
        }]
        pat_fail = detect_chart_patterns(c_fail)
        self.assertIsNotNone(pat_fail)
        self.assertIn("Descending Triangle", pat_fail.get("name", ""))
        self.assertEqual(pat_fail.get("status"), "failed")

    def test_valid_symmetrical_triangle_with_slanted_breakout(self):
        """
        Symmetrical Triangle requires:
        - P2 < P1 (lower high)
        - T2 > T1 (higher low)
        - Slanted upper resistance and lower support
        - Breakout evaluated against the dynamic slanted upper line.
        """
        candles = make_4pt_candles(100.0, 80.0, 94.0, 86.0)

        pat = detect_chart_patterns(candles)
        self.assertIsNotNone(pat)
        self.assertIn("Symmetrical Triangle", pat.get("name", ""))
        self.assertEqual(pat.get("status"), "forming")

        # Slanted roof at bar 36 is ~89.67. Candle closing at 94.0 breaks out above slanted roof!
        bo_candle = {
            "time": "2026-09-07",
            "open": 88.0,
            "high": 95.0,
            "low": 87.5,
            "close": 94.0,
            "volume": 2000000
        }
        pat_bo = detect_chart_patterns(candles + [bo_candle])
        self.assertIsNotNone(pat_bo)
        self.assertEqual(pat_bo.get("status"), "confirmed")

    def test_symmetrical_triangle_breakdown_reports_broke_down_status(self):
        """
        When price breaks down below the lower rising support line of a Symmetrical Triangle,
        the status must be 'broke_down' (not 'failed') to indicate a directional bearish breakdown.
        """
        candles = make_4pt_candles(100.0, 80.0, 94.0, 86.0)
        bd_candle = {
            "time": "2026-09-07",
            "open": 87.0,
            "high": 87.5,
            "low": 84.5,
            "close": 85.0,
            "volume": 2000000
        }
        pat_bd = detect_chart_patterns(candles + [bd_candle])
        self.assertIsNotNone(pat_bd)
        self.assertIn("Symmetrical Triangle", pat_bd.get("name", ""))
        self.assertEqual(pat_bd.get("status"), "broke_down")
        self.assertIsNone(pat_bd.get("target"))

    def test_valid_parallel_channel_detected_as_forming(self):
        """
        Bullish Ascending Channel with parallel boundaries (slope difference ratio <= 0.25)
        and price moving inside the channel must be detected as 'forming'.
        """
        p1, t1, p2, t2 = 100.0, 80.0, 118.0, 98.0
        candles = []
        for i in range(36):
            if i <= 5:
                val = t1 + (p1 - t1) * (i / 5.0)
            elif i <= 14:
                val = p1 - (p1 - t1) * ((i - 5) / 9.0)
            elif i <= 23:
                val = t1 + (p2 - t1) * ((i - 14) / 9.0)
            elif i <= 31:
                val = p2 - (p2 - t2) * ((i - 23) / 8.0)
            else:
                val = t2 + (i - 31) * 1.05
            if i == 5:
                h, l = p1, p1 - 1.0
            elif i == 14:
                h, l = t1 + 1.0, t1
            elif i == 23:
                h, l = p2, p2 - 1.0
            elif i == 31:
                h, l = t2 + 1.0, t2
            else:
                h, l = val + 0.5, val - 0.5
            o = c = val
            t_str = f"2026-08-{i+1:02d}" if i < 31 else f"2026-09-{i-30:02d}"
            candles.append({
                "time": t_str,
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(c, 2),
                "volume": 1000000
            })

        pat = detect_chart_patterns(candles)
        self.assertIsNotNone(pat)
        self.assertEqual(pat.get("name"), "Bullish Ascending Channel (ช่องคู่ขนานขาขึ้น)")
        self.assertEqual(pat.get("status"), "forming")
        lines = pat.get("lines", [])
        self.assertEqual(len(lines), 2)
        upper_line = [l for l in lines if "Upper" in l["name"]][0]
        lower_line = [l for l in lines if "Lower" in l["name"]][0]
        self.assertEqual(upper_line["points"][0]["value"], 100.0)
        self.assertEqual(lower_line["points"][0]["value"], 80.0)

    def test_non_parallel_channel_rejected(self):
        """
        Bullish Ascending Channel requires boundaries to be roughly parallel
        (slope difference / average slope <= 0.25).
        If peaks rise steeply (+1.5/bar) while troughs rise very slowly (+0.1/bar),
        it must NOT be declared as Bullish Ascending Channel.
        Asserts directly without empty if guard.
        """
        candles = make_4pt_candles(100.0, 80.0, 130.0, 81.7)

        pat = detect_chart_patterns(candles)
        self.assertIsNotNone(pat)
        self.assertNotEqual(pat.get("name"), "Bullish Ascending Channel (ช่องคู่ขนานขาขึ้น)")
        self.assertEqual(pat.get("name"), "Bullish Double Bottom (W-Shape)")

    def test_double_pattern_rejected_when_too_narrow_or_too_shallow(self):
        """
        Double Top and Double Bottom require:
        - Width between swing peaks/troughs >= 6 bars.
        - Swing bounce/pullback depth >= 5%.
        When these criteria are violated, Double Top/Bottom must NOT be declared.
        """
        # 1. Double Bottom too narrow (troughs only 4 bars apart: index 10 and 14)
        c_narrow = []
        for i in range(30):
            val = 100.0
            if i == 10: val = 90.0
            elif i == 12: val = 98.0
            elif i == 14: val = 90.5
            c_narrow.append({
                "time": f"2026-08-{i+1:02d}",
                "open": val, "high": val + 0.5, "low": val - 0.5, "close": val, "volume": 1000
            })
        pat_narrow = detect_chart_patterns(c_narrow)
        self.assertNotEqual(pat_narrow.get("name", "") if pat_narrow else "", "Bullish Double Bottom (W-Shape)")

        # 2. Double Bottom too shallow (bounce only 2.7% < 5%)
        c_shallow = []
        for i in range(30):
            val = 100.0
            if i == 5: val = 90.0
            elif i == 15: val = 92.5
            elif i == 25: val = 90.2
            c_shallow.append({
                "time": f"2026-08-{i+1:02d}",
                "open": val, "high": val + 0.5, "low": val - 0.5, "close": val, "volume": 1000
            })
        pat_shallow = detect_chart_patterns(c_shallow)
        self.assertNotEqual(pat_shallow.get("name", "") if pat_shallow else "", "Bullish Double Bottom (W-Shape)")

    def test_wide_box_range_30pct_rejected(self):
        """
        Consolidation Box represents tight accumulation (span <= 15%).
        A wide 30% range must NOT be declared as a Consolidation Box.
        """
        candles = []
        for i in range(30):
            val = 100.0 + (i / 29.0) * 30.0
            candles.append({
                "time": f"2026-09-{i+1:02d}",
                "open": val,
                "high": val + 0.5,
                "low": val - 0.5,
                "close": val,
                "volume": 1000
            })

        pat = detect_chart_patterns(candles)
        self.assertIsNone(pat)

    def test_tight_box_range_detected_no_target_until_confirmed(self):
        """
        A tight box (span 5% <= 15%) is declared as Consolidation Box.
        While in 'forming' status, target and upside_pct must be None,
        and target_calc must not contain numerical targets.
        Once price confirms breakout, target, upside_pct, and numerical target_calc are calculated.
        """
        candles = []
        for i in range(30):
            t_str = f"2026-09-{i+1:02d}"
            # high 105.0 at bar 5, low 100.0 at bar 15 -> span = 5%
            h = 105.0 if i == 5 else 103.0
            l = 100.0 if i == 15 else 102.0
            o = (h + l) / 2
            c = o
            candles.append({
                "time": t_str,
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(c, 2),
                "volume": 1000000
            })

        pat = detect_chart_patterns(candles)
        self.assertIsNotNone(pat)
        self.assertEqual(pat.get("name"), "Consolidation Box (กรอบสะสมพลัง)")
        self.assertEqual(pat.get("status"), "forming")
        self.assertIsNone(pat.get("target"))
        self.assertIsNone(pat.get("upside_pct"))
        self.assertNotIn("เป้าหมาย $", pat.get("target_calc", ""))

        # Confirmed breakout candle closing at 106.0 > prior_high 105.0
        bo_c = {
            "time": "2026-10-01",
            "open": 104.0,
            "high": 106.5,
            "low": 103.5,
            "close": 106.0,
            "volume": 2000000
        }
        pat_bo = detect_chart_patterns(candles + [bo_c])
        self.assertIsNotNone(pat_bo)
        self.assertEqual(pat_bo.get("status"), "confirmed")
        self.assertIsNotNone(pat_bo.get("target"))
        self.assertGreater(pat_bo.get("target"), 105.0)
        self.assertIn("เป้าหมาย $", pat_bo.get("target_calc", ""))

    def test_ohlc_invariant_clamping(self):
        """
        Verify that anomalous candle quotes with open > high or close > high
        are clamped so high = max(o, h, c) and low = min(o, l, c).
        """
        anomalous_candles = [
            {"time": "2026-10-25", "open": 200.0, "high": 205.0, "low": 195.0, "close": 202.0, "volume": 1000},
            {"time": "2026-10-26", "open": 202.0, "high": 206.0, "low": 198.0, "close": 204.0, "volume": 1000},
            {"time": "2026-10-27", "open": 204.0, "high": 208.0, "low": 200.0, "close": 206.0, "volume": 1000},
            {"time": "2026-10-28", "open": 243.0, "high": 241.55, "low": 228.82, "close": 234.5, "volume": 1000},
            {"time": "2026-10-29", "open": 235.0, "high": 236.0, "low": 240.0, "close": 238.0, "volume": 1000},
        ]
        res = compute_fibo_and_indicators(anomalous_candles)
        c_list = res.get("candles", [])
        self.assertEqual(len(c_list), 5)

        c28 = [c for c in c_list if c["time"] == "2026-10-28"][0]
        self.assertEqual(c28["high"], 243.0)
        self.assertGreaterEqual(c28["high"], c28["open"])
        self.assertGreaterEqual(c28["high"], c28["close"])

        c29 = [c for c in c_list if c["time"] == "2026-10-29"][0]
        self.assertEqual(c29["low"], 235.0)
        self.assertLessEqual(c29["low"], c29["open"])
        self.assertLessEqual(c29["low"], c29["close"])


if __name__ == "__main__":
    unittest.main()
