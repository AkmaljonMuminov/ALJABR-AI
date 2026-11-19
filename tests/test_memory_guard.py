import unittest

from memory.guard import contains_sensitive


class GuardTests(unittest.TestCase):
    def test_secrets_are_detected(self):
        samples = [
            "sk-abcdefghijkl1234",
            "Authorization: Bearer abcdefghijklmnop",
            "password: hunter2",
            "api_key=abc123",
            "OPENAI_API_KEY = zzz999",
            "token: xyz",
            "parolim 12345",
            "parol: qwerty",
            "my pin is 4821",
            "пароль от почты qwerty123",
            "karta 4111 1111 1111 1111",
            "4111-1111-1111-1111",
            "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6",
            "GITHUB_TOKEN=abc",          # "_" must not hide the keyword
            "TOKEN_VALUE = xyz",
            "API_KEY_PROD: k",
            "парол: 123",
        ]
        for text in samples:
            with self.subTest(text=text):
                self.assertTrue(contains_sensitive(text))

    def test_normal_notes_are_allowed(self):
        samples = [
            "Mening sevimli rangim ko'k",
            "Ertaga soat 15:00 da uchrashuv bor",
            "Do'stim Alisherning tug'ilgan kuni 12-mart",
            "Mening parolim haqida gap ketmayapti",
            "Telefon raqami 998901234567",
            "Toshkentda 2 million aholi yashaydi",
            "Мой любимый цвет синий",
            "supercalifragilisticexpialidocious_and_more_letters",
            "1234 5678 9012 3456",  # 16 digits but fails the Luhn check: not a card number
            "Secretary of state ertaga keladi",  # contains "secret" only as part of a word
            "pinhona rangi qizil",
            "Tokenlar haqida kitob o'qidim",
            "kalit so'z: salom",
        ]
        for text in samples:
            with self.subTest(text=text):
                self.assertFalse(contains_sensitive(text))

    def test_empty_text(self):
        self.assertFalse(contains_sensitive(""))


if __name__ == "__main__":
    unittest.main()
