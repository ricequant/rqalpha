import os


def load_tests(loader, standard_tests, pattern):
    this_dir = os.path.dirname(__file__)
    standard_tests.addTests(loader.discover(start_dir=this_dir, pattern=pattern))
    return standard_tests
