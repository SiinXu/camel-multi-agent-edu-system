from duckduckgo_search import DDGS

class DuckDuckGoSearchTool:
    """DuckDuckGo 搜索工具."""

    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str, max_results: int = 5) -> str:
        """使用 DuckDuckGo 搜索并返回结果."""
        try:
            results = self.ddgs.text(query, max_results=max_results)
            if results:
                return "\n".join([r["body"] for r in results])
            else:
                return "No results found."
        except Exception as e:
            return f"An error occurred: {e}"

    def __call__(self, query: str, max_results: int = 5) -> str:
        """使实例可调用."""
        return self.search(query, max_results)