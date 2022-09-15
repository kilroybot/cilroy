"""

Notice we don't follow the same test structure as in unit tests.
That's because functional tests should test the code from "outside".
So we don't need to follow any hierarchy.

"""

import pytest
from typer.testing import CliRunner

from cilroy.__main__ import cli


class TestCilroy:

    # pytest fixture, passed to all methods by argument
    @pytest.fixture(autouse=True, scope="class")
    def runner(self):
        return CliRunner()

    def test_cilroy_prints_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert "Usage" in result.output
