import os

from unittest import TestLoader, TestSuite, TextTestRunner


def load_tests():
    test_suite = TestSuite()
    this_dir = os.path.dirname(__file__)
    loader = TestLoader()
    package_tests = loader.discover(start_dir=this_dir)
    test_suite.addTests(package_tests)
    return test_suite


if __name__ == "__main__":
    runner = TextTestRunner(verbosity=2)
    runner.run(load_tests())
