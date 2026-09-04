import pytest

from finauditpro.application.security.security_context import SecurityContext


@pytest.fixture(autouse=True)
def reset_security_context():
    SecurityContext.clear()
    yield
    SecurityContext.clear()
