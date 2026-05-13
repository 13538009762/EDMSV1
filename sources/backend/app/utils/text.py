def extract_text_from_tiptap(content: dict | list) -> str:
    """Recursively extract plain text from TipTap JSON."""
    text = ""
    if isinstance(content, dict):
        if content.get("type") == "text":
            text += content.get("text", "")
        elif "content" in content:
            text += extract_text_from_tiptap(content["content"])
    elif isinstance(content, list):
        for item in content:
            text += extract_text_from_tiptap(item) + "\n"
    return text.strip()
