"""Text diff between two TipTap JSON snapshots."""
from __future__ import annotations

import difflib
import html
import json
from typing import Any


def _extract_plain(node: dict[str, Any], lines: list[str]) -> None:
    t = node.get("type")
    if t == "text":
        lines.append(node.get("text") or "")
        return
    for ch in node.get("content") or []:
        _extract_plain(ch, lines)
    if t in ("paragraph", "heading"):
        lines.append("\n")


def json_to_lines(doc_json: str) -> str:
    try:
        root = json.loads(doc_json)
    except json.JSONDecodeError:
        return ""
    parts: list[str] = []
    _extract_plain(root, parts)
    return "".join(parts)


def diff_html(old_json: str, new_json: str) -> str:
    # 移除 .splitlines()，改为直接对比字符，实现精准的字级别差异对比
    a = json_to_lines(old_json)
    b = json_to_lines(new_json)
    
    out: list[str] = ['<div class="diff" style="white-space: pre-wrap; font-family: inherit; line-height: 1.8;">']
    
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            out.append(f"<span>{html.escape(a[i1:i2])}</span>")
        elif tag == "delete":
            out.append(f'<del class="diff-del" style="background:#ffe6e6; color:#d32f2f; text-decoration:line-through; padding:0 2px; border-radius:3px;">{html.escape(a[i1:i2])}</del>')
        elif tag == "insert":
            out.append(f'<ins class="diff-ins" style="background:#e6ffe6; color:#388e3c; text-decoration:none; padding:0 2px; border-radius:3px; font-weight:bold;">{html.escape(b[j1:j2])}</ins>')
        elif tag == "replace":
            out.append(f'<del class="diff-del" style="background:#ffe6e6; color:#d32f2f; text-decoration:line-through; padding:0 2px; border-radius:3px;">{html.escape(a[i1:i2])}</del>')
            out.append(f'<ins class="diff-ins" style="background:#e6ffe6; color:#388e3c; text-decoration:none; padding:0 2px; border-radius:3px; font-weight:bold;">{html.escape(b[j1:j2])}</ins>')
            
    out.append("</div>")
    return "".join(out)

def side_by_side_diff(old_json: str, new_json: str) -> str:
    from difflib import HtmlDiff
    a = json_to_lines(old_json).splitlines()
    b = json_to_lines(new_json).splitlines()
    
    hd = HtmlDiff(tabsize=4, wrapcolumn=60)
    # make_table generates a <table> string
    table = hd.make_table(a, b, context=True, numlines=5)
    
    # Custom styling for the table to make it fit our UI
    styled_table = f"""
    <style>
        table.diff {{ font-family: Courier, monospace; font-size: 13px; border: 1px solid #ddd; width: 100%; border-collapse: collapse; }}
        .diff_header {{ background-color: #f0f0f0; color: #666; text-align: right; padding: 2px 8px; width: 40px; border: 1px solid #ddd; }}
        .diff_next {{ background-color: #f0f0f0; border: 1px solid #ddd; }}
        .diff_add {{ background-color: #e6ffe6; }}
        .diff_chg {{ background-color: #ffffd1; }}
        .diff_sub {{ background-color: #ffe6e6; }}
        td {{ padding: 0 10px; border: none; word-break: break-all; }}
    </style>
    {table}
    """
    return styled_table

def blame_html(versions_data: list[dict[str, Any]]) -> str:
    """Generate a grouped blame view across multiple versions."""
    if not versions_data:
        return ""

    class Chunk:
        def __init__(self, text: str, author: str, color: str, time: str):
            self.text = text
            self.author = author
            self.color = color
            self.time = time

    chunks: list[Chunk] = []

    for v in sorted(versions_data, key=lambda x: x.get("version_no", 0)):
        new_lines = json_to_lines(v.get("content_json") or "{}").splitlines(keepends=True)
        old_lines = [c.text for c in chunks]
        
        sm = difflib.SequenceMatcher(None, old_lines, new_lines)
        new_chunks = []
        
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                new_chunks.extend(chunks[i1:i2])
            elif tag == "insert":
                for line in new_lines[j1:j2]:
                    new_chunks.append(Chunk(line, v.get("author_name", "Unknown"), v.get("author_color", "#888"), v.get("created_at", "")))
            elif tag == "replace":
                for line in new_lines[j1:j2]:
                    new_chunks.append(Chunk(line, v.get("author_name", "Unknown"), v.get("author_color", "#888"), v.get("created_at", "")))
        chunks = new_chunks

    # Group into blocks
    blocks = []
    if chunks:
        current_block = {"author": chunks[0].author, "color": chunks[0].color, "time": chunks[0].time, "lines": [chunks[0].text]}
        for i in range(1, len(chunks)):
            if chunks[i].author == chunks[i-1].author and chunks[i].time == chunks[i-1].time:
                current_block["lines"].append(chunks[i].text)
            else:
                blocks.append(current_block)
                current_block = {"author": chunks[i].author, "color": chunks[i].color, "time": chunks[i].time, "lines": [chunks[i].text]}
        blocks.append(current_block)

    out = ['''<div class="blame-view" style="font-family: inherit; width: 100%; border-collapse: separate; border-spacing: 0;">''']
    
    for b in blocks:
        author = html.escape(b["author"])
        time_str = html.escape(b["time"])
        color = b["color"]
        content = html.escape("".join(b["lines"]))
        
        out.append(f'''
        <div class="blame-row" style="display: flex; border-bottom: 1px solid #efefef; min-height: 48px;">
            <div class="blame-gutter" style="width: 140px; flex-shrink: 0; padding: 12px 16px; background: #fafafa; position: relative; border-right: 3px solid {color}; overflow: hidden;">
                <div style="font-weight: 600; font-size: 13px; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{author}">{author}</div>
                <div style="font-size: 11px; color: #888; margin-top: 4px;">{time_str}</div>
            </div>
            <div class="blame-content" style="flex: 1; padding: 12px 20px; line-height: 1.7; font-size: 14px; color: #444; white-space: pre-wrap; background: white;">{content}</div>
        </div>
        ''')
        
    out.append("</div>")
    return "".join(out)

