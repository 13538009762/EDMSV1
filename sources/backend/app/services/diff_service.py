"""Structural diff and historical blame for TipTap JSON."""
from __future__ import annotations
import difflib
import html
import json
from typing import Any

def _node_to_text(n: dict[str, Any]) -> str:
    if not n: return ""
    if n.get("type") == "text": return n.get("text", "")
    return "".join(_node_to_text(c) for c in n.get("content") or [])

def _render_node(node: dict[str, Any], old_node: dict[str, Any] = None) -> str:
    """Render a node, diffing it against old_node if provided."""
    if not node and not old_node: return ""
    
    # If one is missing, it's a block level add/delete
    if not old_node: # Added
        return f'<div style="background:#e6ffe6; border-left:4px solid #388e3c; padding:2px 10px;">{_render_simple(node)}</div>'
    if not node: # Deleted
        return f'<div style="background:#ffe6e6; border-left:4px solid #d32f2f; padding:2px 10px; text-decoration:line-through; opacity:0.6;">{_render_simple(old_node)}</div>'

    t = node.get("type", "")
    # If types differ, show replace
    if t != old_node.get("type"):
        return _render_node(None, old_node) + _render_node(node, None)

    # If same type, diff content
    if t in ("paragraph", "heading", "table_cell", "table_header", "listItem"):
        txt_old = _node_to_text(old_node)
        txt_new = _node_to_text(node)
        if txt_old == txt_new: return _render_simple(node)
        
        diff_out = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, txt_old, txt_new).get_opcodes():
            if tag == "equal": diff_out.append(html.escape(txt_old[i1:i2]))
            elif tag == "delete": diff_out.append(f'<del style="background:#ffe6e6;color:#d32f2f;">{html.escape(txt_old[i1:i2])}</del>')
            elif tag == "insert": diff_out.append(f'<ins style="background:#e6ffe6;color:#388e3c;font-weight:bold;text-decoration:none;">{html.escape(txt_new[j1:j2])}</ins>')
            elif tag == "replace":
                diff_out.append(f'<del style="background:#ffe6e6;color:#d32f2f;">{html.escape(txt_old[i1:i2])}</del>')
                diff_out.append(f'<ins style="background:#e6ffe6;color:#388e3c;font-weight:bold;text-decoration:none;">{html.escape(txt_new[j1:j2])}</ins>')
        
        res = "".join(diff_out)
        if t == "paragraph": return f"<p style='margin:8px 0;'>{res}</p>"
        if t == "heading": return f"<h{node.get('attrs',{}).get('level',3)}>{res}</h{node.get('attrs',{}).get('level',3)}>"
        if t == "listItem": return f"<li>{res}</li>"
        return res

    if t == "table":
        # Align rows
        old_rows = old_node.get("content") or []
        new_rows = node.get("content") or []
        row_out = []
        sm = difflib.SequenceMatcher(None, [_node_to_text(r) for r in old_rows], [_node_to_text(r) for r in new_rows])
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for idx in range(i2-i1):
                    row_out.append(_diff_table_row(old_rows[i1+idx], new_rows[j1+idx]))
            elif tag == "delete":
                for idx in range(i1, i2): row_out.append(f'<tr style="background:#ffe6e6;">{_render_simple(old_rows[idx])}</tr>')
            elif tag == "insert":
                for idx in range(j1, j2): row_out.append(f'<tr style="background:#e6ffe6;">{_render_simple(new_rows[idx])}</tr>')
            elif tag == "replace":
                for idx in range(i1, i2): row_out.append(f'<tr style="background:#ffe6e6;">{_render_simple(old_rows[idx])}</tr>')
                for idx in range(j1, j2): row_out.append(f'<tr style="background:#e6ffe6;">{_render_simple(new_rows[idx])}</tr>')
        return f'<table border="1" style="border-collapse:collapse;width:100%;border:1px solid #ddd;">{"".join(row_out)}</table>'

    return _render_simple(node)

def _diff_table_row(r_old, r_new):
    cells_old = r_old.get("content") or []
    cells_new = r_new.get("content") or []
    res = []
    for i in range(max(len(cells_old), len(cells_new))):
        c_o = cells_old[i] if i < len(cells_old) else None
        c_n = cells_new[i] if i < len(cells_new) else None
        tag = "th" if (c_n or c_o).get("type") == "table_header" else "td"
        res.append(f'<{tag} style="border:1px solid #ddd;padding:8px;">{_render_node(c_n, c_o)}</{tag}>')
    return f"<tr>{''.join(res)}</tr>"

def _render_simple(n: dict[str, Any]) -> str:
    if not n: return ""
    t = n.get("type", "")
    if t == "text":
        s = html.escape(n.get("text", ""))
        for m in n.get("marks", []):
            if m["type"] == "bold": s = f"<b>{s}</b>"
            if m["type"] == "textStyle":
                c = m.get("attrs", {}).get("color")
                if c: s = f'<span style="color:{c}">{s}</span>'
        return s
    inner = "".join(_render_simple(c) for c in n.get("content") or [])
    if t == "paragraph": return f"<p style='margin:8px 0;'>{inner}</p>"
    if t == "heading": return f"<h{n.get('attrs',{}).get('level',3)}>{inner}</h{n.get('attrs',{}).get('level',3)}>"
    if t == "table": return f'<table border="1" style="border-collapse:collapse;width:100%;border:1px solid #ddd;">{inner}</table>'
    if t == "table_row": return f"<tr>{inner}</tr>"
    if t == "table_cell": return f'<td style="border:1px solid #ddd;padding:8px;">{inner}</td>'
    if t == "table_header": return f'<th style="border:1px solid #ddd;padding:8px;background:#f5f5f5;">{inner}</th>'
    if t == "image": return f'<img src="{n.get("attrs",{}).get("src","")}" style="max-width:300px;display:block;margin:10px 0;" />'
    if t == "bulletList": return f"<ul>{inner}</ul>"
    if t == "orderedList": return f"<ol>{inner}</ol>"
    if t == "listItem": return f"<li>{inner}</li>"
    return inner

def diff_html(old_json: str, new_json: str) -> str:
    try:
        old_doc, new_doc = json.loads(old_json), json.loads(new_json)
    except: return ""
    c_o, c_n = old_doc.get("content", []), new_doc.get("content", [])
    sm = difflib.SequenceMatcher(None, [_node_to_text(n) for n in c_o], [_node_to_text(n) for n in c_n])
    
    out = ['<div style="font-family:sans-serif;max-width:900px;margin:auto;padding:40px;background:white;box-shadow:0 0 10px rgba(0,0,0,0.1);">']
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for idx in range(i1, i2): out.append(_render_node(c_n[j1 + (idx-i1)], c_o[idx]))
        elif tag == "delete":
            for idx in range(i1, i2): out.append(_render_node(None, c_o[idx]))
        elif tag == "insert":
            for idx in range(j1, j2): out.append(_render_node(c_n[idx], None))
        elif tag == "replace":
            for idx in range(i1, i2): out.append(_render_node(None, c_o[idx]))
            for idx in range(j1, j2): out.append(_render_node(c_n[idx], None))
    return "".join(out) + "</div>"

def side_by_side_diff(old_json: str, new_json: str) -> str:
    try: h_o, h_n = _render_simple(json.loads(old_json)), _render_simple(json.loads(new_json))
    except: return ""
    return f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;background:#f5f5f5;padding:20px;"><div style="background:white;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,0.1);"><div style="color:#888;font-size:12px;margin-bottom:10px;border-bottom:1px solid #eee;">OLD VERSION</div>{h_o}</div><div style="background:white;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,0.1);"><div style="color:#888;font-size:12px;margin-bottom:10px;border-bottom:1px solid #eee;">NEW VERSION</div>{h_n}</div></div>'

def blame_html(versions_data: list[dict[str, Any]]) -> str:
    """
    Generate a 'Blame' view like Git, but optimized for TipTap JSON blocks.
    Groups consecutive blocks from the same author into 'modules'.
    """
    if not versions_data: return ""
    versions = sorted(versions_data, key=lambda x: x.get("version_no", 0))
    
    # Use the LATEST version as the template for display
    latest_doc = json.loads(versions[-1].get("content_json", "{}"))
    latest_content = latest_doc.get("content", [])
    if not latest_content: return '<div style="padding:40px;text-align:center;color:#999;">No content to trace.</div>'

    # Track attribution for each block in the latest content
    # We use stable JSON fingerprint instead of pure text to catch formatting changes (bold, color, etc.)
    def get_fingerprint(n):
        return json.dumps(n, sort_keys=True)

    # Progression: Start from v0, then apply changes from v1, v2...
    current_blame = [] # list of {"fingerprint": str, "author": str, "color": str}
    
    # Initialize with V0
    v0 = versions[0]
    v0_content = json.loads(v0.get("content_json", "{}")).get("content", [])
    for n in v0_content:
        current_blame.append({
            "fingerprint": get_fingerprint(n),
            "author": v0.get("author_name", "Unknown"),
            "color": v0.get("author_color", "#888")
        })

    # Progressively update based on each new version
    for i in range(1, len(versions)):
        v = versions[i]
        v_content = json.loads(v.get("content_json", "{}")).get("content", [])
        v_fingerprints = [get_fingerprint(n) for n in v_content]
        prev_fingerprints = [m["fingerprint"] for m in current_blame]
        
        new_blame = []
        sm = difflib.SequenceMatcher(None, prev_fingerprints, v_fingerprints)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                # Content is identical to previous version, preserve original attribution
                new_blame.extend(current_blame[i1:i2])
            else:
                # Content changed or added, attribute to current version's author
                for idx in range(j1, j2):
                    new_blame.append({
                        "fingerprint": v_fingerprints[idx],
                        "author": v.get("author_name", "Unknown"),
                        "color": v.get("author_color", "#888")
                    })
        current_blame = new_blame

    # --- Grouping into Modules ---
    # Merge consecutive blocks with the same author
    modules = []
    if current_blame:
        # Note: We must ensure we align with latest_content exactly
        # current_blame size should match latest_content because it was derived from versions[-1] in the last loop
        
        # Start the first module
        first_info = current_blame[0] if len(current_blame) > 0 else {"author": "Unknown", "color": "#888"}
        curr_mod = {
            "author": first_info["author"],
            "color": first_info["color"],
            "nodes": [latest_content[0]]
        }
        
        for i in range(1, len(latest_content)):
            info = current_blame[i] if i < len(current_blame) else {"author": "Unknown", "color": "#888"}
            if info["author"] == curr_mod["author"]:
                curr_mod["nodes"].append(latest_content[i])
            else:
                modules.append(curr_mod)
                curr_mod = {
                    "author": info["author"],
                    "color": info["color"],
                    "nodes": [latest_content[i]]
                }
        modules.append(curr_mod)

    # --- Render High-End Module UI ---
    out = [f'''
    <style>
        .blame-container {{ font-family: "Inter", -apple-system, sans-serif; background: #f4f7f9; padding: 30px; }}
        .blame-module {{ display: flex; margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.05); background: #fff; }}
        .blame-sidebar {{ width: 150px; flex-shrink: 0; padding: 15px; background: #fff; border-right: 4px solid var(--bar-color); display: flex; flex-direction: column; justify-content: flex-start; }}
        .blame-author {{ font-size: 13px; font-weight: 700; color: #2c3e50; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .blame-tag {{ font-size: 10px; color: #aeb9c7; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }}
        .blame-content {{ flex: 1; padding: 20px 30px; line-height: 1.6; color: #34495e; min-width: 0; }}
        .blame-content p {{ margin: 0 0 12px 0; }}
        .blame-content p:last-child {{ margin-bottom: 0; }}
        .blame-content table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        .blame-content td, .blame-content th {{ border: 1px solid #edf2f7; padding: 10px; }}
    </style>
    <div class="blame-container">
    ''']

    for mod in modules:
        bar_color = mod["color"]
        out.append(f'''
        <div class="blame-module" style="--bar-color: {bar_color}">
            <div class="blame-sidebar">
                <div class="blame-author" title="{mod["author"]}">{mod["author"]}</div>
                <div class="blame-tag">Last Modified By</div>
            </div>
            <div class="blame-content">
                {''.join(_render_simple(n) for n in mod["nodes"])}
            </div>
        </div>
        ''')

    return "".join(out) + "</div>"

