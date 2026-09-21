from typing import List, Dict, Any

class VCLSVGRenderer:
    """
    Deterministic VCL (Visual Context Language) SVG Graph Renderer.
    Renders topology nodes, relations, and dependency paths into clean SVG maps.
    """
    @classmethod
    def render_graph_svg(cls, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], width: int = 600, height: int = 400) -> str:
        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" style="background:#0f172a; font-family:sans-serif;">',
            '  <defs>',
            '    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
            '      <path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1" />',
            '    </marker>',
            '  </defs>',
            '  <!-- Title -->',
            '  <text x="20" y="30" fill="#f8fafc" font-size="14" font-weight="bold">ContextOS VCL Visual Context Map</text>'
        ]

        if not nodes:
            svg_lines.append('  <text x="20" y="70" fill="#94a3b8" font-size="12">No graph nodes active in working context.</text>')
            svg_lines.append('</svg>')
            return "\n".join(svg_lines)

        # Calculate node positions in grid
        cols = 3
        positions = {}
        for i, node in enumerate(nodes):
            r = i // cols
            c = i % cols
            cx = 100 + c * 180
            cy = 100 + r * 100
            positions[node["id"]] = (cx, cy)

        # Draw Edges
        for edge in edges:
            src_pos = positions.get(edge["source"])
            tgt_pos = positions.get(edge["target"])
            if src_pos and tgt_pos:
                svg_lines.append(
                    f'  <line x1="{src_pos[0]}" y1="{src_pos[1]}" x2="{tgt_pos[0]}" y2="{tgt_pos[1]}" stroke="#6366f1" stroke-width="2" marker-end="url(#arrow)" opacity="0.8" />'
                )

        # Draw Nodes
        for node in nodes:
            pos = positions.get(node["id"], (100, 100))
            label = node.get("label", node["id"])[:18]
            svg_lines.append(
                f'  <g transform="translate({pos[0]-60}, {pos[1]-20})">'
                f'    <rect width="120" height="40" rx="8" fill="#1e293b" stroke="#3b82f6" stroke-width="1.5" />'
                f'    <text x="60" y="24" fill="#f8fafc" font-size="11" text-anchor="middle" font-weight="600">{label}</text>'
                f'  </g>'
            )

        svg_lines.append('</svg>')
        return "\n".join(svg_lines)
