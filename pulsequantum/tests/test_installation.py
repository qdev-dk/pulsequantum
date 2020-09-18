"""
Simple test file to verify the installation.

This test file is included so that the tests can run immediately after the
template creation of the repo
"""

from pulsequantum.hello_world import greeter, hello_world


def test_greeter():
    assert greeter("name") == f"Hello, name!"
