

class Search:
    def __init__(self, core=None):
        self.core = core

    def replace_core(self, new_core):
        self.core = new_core

    def search(self, prompt: str = ""):
        return self.core.search(prompt)


class BingSearchCore:
    def search(self, prompt):
        return prompt


class GoogleSearchCore:
    def search(self, prompt):
        return prompt


if __name__ == "__main__":
    searcher = Search(BingSearchCore)
    searcher.search("Hello World")
    searcher.replace_core(GoogleSearchCore)
    searcher.search()
