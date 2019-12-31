"""A base bootstrap for tests - useful if you don't have anything better"""

import os
import sys
import unittest
import logging

# ugh. How much do I dislike this
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
import test_knobwrangler  # noqa: E402


def knobwrangler_core_suite():
    suite = unittest.TestSuite()
    suite.addTest(test_knobwrangler.suite())
    return suite

if __name__ == '__main__':
    _ROOT_LOGGER = logging.getLogger()
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        '%(asctime)s -'
        '%(name)s - '
        '%(levelname)s - '
        '%(message)s'
        )
    _handler.setFormatter(_formatter)
    _ROOT_LOGGER.addHandler(_handler)
    _ROOT_LOGGER.setLevel(logging.INFO)

    unittest.main(defaultTest='knobwrangler_core_suite')
