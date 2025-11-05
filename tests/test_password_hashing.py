import unittest
from werkzeug.security import generate_password_hash, check_password_hash


class TestPasswordHashing(unittest.TestCase):
    def test_generate_and_check(self):
        pw = 'secret1234'
        hashed = generate_password_hash(pw)
        self.assertTrue(hashed and hashed != pw)
        self.assertTrue(check_password_hash(hashed, pw))
        self.assertFalse(check_password_hash(hashed, 'wrong'))


if __name__ == '__main__':
    unittest.main()
