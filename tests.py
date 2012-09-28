import unittest
from emailvision import EmailVision
from tests_settings import (EMAILVISION_SERVER_URL,
                            EMAILVISION_API_KEY,
                            EMAILVISION_API_LOGIN,
                            EMAILVISION_API_PASSWORD)


class TestEmailVisionCampaignManagement(unittest.TestCase):
    def setUp(self):
        self.api = EmailVision(api="apiccmd",
                               server=EMAILVISION_SERVER_URL,
                               login=EMAILVISION_API_LOGIN,
                               password=EMAILVISION_API_PASSWORD,
                               api_key=EMAILVISION_API_KEY,
                               secure=False)

    def tearDown(self):
        self.api.close()

    def test_open_close(self):
        pass

if __name__ == "__main__":
    unittest.main()
