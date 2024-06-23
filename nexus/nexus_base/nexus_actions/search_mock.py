import wikipedia

from nexus.nexus_base.action_manager import agent_action


def mock_search_results(query):
    """Returns a list[] of mock search results for the given query."""
    search_results = [f"{query} result 1", f"{query} result 2", f"{query} result 3"]
    return search_results


def mock_summary(page_id):
    """Returns a mock summary for the given page_id."""
    summary = f"Summary for {page_id}"
    return summary


def mock_page(page_id):
    """Returns a mock Wikipedia page for the given page_id."""
    page = wikipedia.WikipediaPage(
        title=page_id,
        pageid=1234,
        summary=f"Summary for {page_id}",
        content=f"Content for {page_id}",
    )
    return page


@agent_action
def search_wikipedia_mock(query):
    """Searches Wikipedia for the given query and returns a list[] of matching page_ids."""
    search_results = mock_search_results(query)
    return search_results


@agent_action
def get_wikipedia_summary_mock(page_id):
    """Gets the summary of the Wikipedia page for the given page_id."""
    summary = mock_summary(page_id)
    return summary


@agent_action
def get_wikipedia_page_mock(page_id):
    """Gets the full content of the Wikipedia page for the given page_id."""
    page = mock_page(page_id)
    return page.content
