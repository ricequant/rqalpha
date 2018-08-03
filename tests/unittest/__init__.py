import os

from unittest import TestLoader, TestSuite, TextTestRunner


def load_tests():
    test_sute = TestSuite()
    this_dir = os.path.dirname(__file__)
    loader = TestLoader()
    package_tests = loader.discover(start_dir=this_dir)
    test_sute.addTests(package_tests)
    return test_sute


if __name__ == "__main__":
    runner = TextTestRunner(verbosity=2)
    runner.run(load_tests())
