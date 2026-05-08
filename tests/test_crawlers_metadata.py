import pytest

import app.crawlers.diy_dot_com_crawler as diy_dot_com_crawler
import app.crawlers.homebase_crawler as homebase_crawler
import app.crawlers.screwfix_crawler as screwfix_crawler
import app.crawlers.toolstation_crawler as toolstation_crawler
import app.crawlers.wickes_crawler as wickes_crawler

CRAWLERS = [
    diy_dot_com_crawler,
    homebase_crawler,
    screwfix_crawler,
    toolstation_crawler,
    wickes_crawler,
]


@pytest.mark.parametrize("crawler", CRAWLERS)
def test_crawler_metadata_exists(crawler):
    """
    Test that each crawler defines both SOURCE_IDENTIFIER and SOURCE_DESCRIPTION.
    """
    assert hasattr(crawler, "SOURCE_IDENTIFIER"), (
        f"{crawler.__name__} is missing SOURCE_IDENTIFIER"
    )
    assert hasattr(crawler, "SOURCE_DESCRIPTION"), (
        f"{crawler.__name__} is missing SOURCE_DESCRIPTION"
    )

    assert isinstance(crawler.SOURCE_IDENTIFIER, str)
    assert isinstance(crawler.SOURCE_DESCRIPTION, str)

    assert len(crawler.SOURCE_IDENTIFIER) > 0
    assert len(crawler.SOURCE_DESCRIPTION) > 0
