import unittest

from kero_fish.security import _BOOTSTRAP_USERS, _new_password_material, verify_password


class SecurityTests(unittest.TestCase):
    def test_initial_password_for_all_bootstrap_users(self):
        for username, cfg in _BOOTSTRAP_USERS.items():
            with self.subTest(username=username):
                self.assertTrue(verify_password("1234", cfg["salt"], cfg["password_hash"]))
                self.assertFalse(verify_password("1235", cfg["salt"], cfg["password_hash"]))

    def test_new_password_material_uses_random_salt(self):
        salt1, hash1 = _new_password_material("senha-forte-1")
        salt2, hash2 = _new_password_material("senha-forte-1")
        self.assertNotEqual(salt1, salt2)
        self.assertNotEqual(hash1, hash2)
        self.assertTrue(verify_password("senha-forte-1", salt1, hash1))


if __name__ == "__main__":
    unittest.main()
