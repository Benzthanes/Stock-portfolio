import unittest

from src.profiles import CURATED_PROFILES, get_business_summary


class ProfilesTest(unittest.TestCase):
    def test_curated_profiles_count_and_keys(self):
        self.assertEqual(len(CURATED_PROFILES), 109)
        self.assertIn("AAPL", CURATED_PROFILES)
        self.assertIn("MSFT", CURATED_PROFILES)
        self.assertIn("SCB", CURATED_PROFILES)

    def test_get_business_summary_curated(self):
        aapl_desc = get_business_summary("AAPL")
        self.assertEqual(aapl_desc, "ผู้ผลิต iPhone, Mac, iPad และระบบนิเวศบริการ Apple Services")

        # Case insensitive lookup
        msft_desc = get_business_summary("  msft  ")
        self.assertEqual(msft_desc, "ผู้นำระบบปฏิบัติการ Windows, คลาวด์ Azure, ซอฟต์แวร์ Office และ AI Copilot")

        scb_desc = get_business_summary("SCB")
        self.assertIn("ธนาคารไทยพาณิชย์", scb_desc)

    def test_get_business_summary_fallbacks(self):
        # 1. Both industry and sector
        res1 = get_business_summary("XYZ", sector="เทคโนโลยี", industry="ซอฟต์แวร์องค์กร")
        self.assertEqual(res1, "ธุรกิจ ซอฟต์แวร์องค์กร (กลุ่ม เทคโนโลยี)")

        # 2. Industry only
        res2 = get_business_summary("XYZ", industry="พลังงานแสงอาทิตย์")
        self.assertEqual(res2, "ธุรกิจ พลังงานแสงอาทิตย์")

        # 3. Sector only
        res3 = get_business_summary("XYZ", sector="การเงิน")
        self.assertEqual(res3, "กลุ่มอุตสาหกรรม การเงิน")

        # 4. Neither industry nor sector
        res4 = get_business_summary("XYZ")
        self.assertEqual(res4, "บริษัทจดทะเบียนในตลาดหลักทรัพย์")


if __name__ == "__main__":
    unittest.main()
