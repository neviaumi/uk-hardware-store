from parsel import Selector


def clean_html(html):
    if not html:
        return html
    sel = Selector(text=html)
    # Iterate through every node in the tree
    for node in sel.xpath("//*"):
        # Access the underlying lxml element via .root
        node.root.attrib.pop("style", None)
        node.root.attrib.pop("class", None)

    # Return the serialised HTML
    return sel.get()


def clean_text(text: list[str], separator: str = " ") -> str:
    if not text:
        return ""
    return separator.join(
        [string.strip() for string in text if len(string.strip()) > 0]
    )


def remove_spaces(text: str | None) -> str | None:
    if not text:
        return None
    return " ".join(text.split())
