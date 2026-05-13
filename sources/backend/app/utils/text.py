def extract_text_from_tiptap(content: dict | list) -> str:
    """Recursively extract text from TipTap JSON, preserving Markdown-style headers."""
    text = ""
    if isinstance(content, dict):
        node_type = content.get("type")
        if node_type == "text":
            text += content.get("text", "")
        elif node_type == "heading":
            level = content.get("attrs", {}).get("level", 1)
            header_prefix = "#" * level + " "
            text += "\n" + header_prefix + extract_text_from_tiptap(content.get("content", [])) + "\n"
        elif "content" in content:
            text += extract_text_from_tiptap(content["content"])
    elif isinstance(content, list):
        for item in content:
            # Avoid excessive newlines but keep nodes separate
            node_text = extract_text_from_tiptap(item)
            if node_text:
                text += node_text + "\n"
    return text.strip()
