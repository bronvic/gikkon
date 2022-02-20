from unittest import SkipTest, TestCase


class TestWrapper(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skipTest(cls, "this wrappers would be refactored")
