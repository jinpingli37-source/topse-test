import pytest


@pytest.fixture(scope="session")
def base_url():
    return "https://192.168.3.56"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "ignore_https_errors": True,
    }
