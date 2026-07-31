import pytest

integration_test = pytest.mark.integration_test
skip = pytest.mark.skip(reason="skipped explicitly by developer")
