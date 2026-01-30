"""
UpSet.js Embedded Visualizations for Dash

This module generates HTML content using the UpSet.js library loaded from CDN,
which can be embedded in Dash applications via an iframe using data URL.
"""

import pandas as pd
import json
import base64
from typing import List, Dict, Any, Optional


def generate_upsetjs_html(data: pd.DataFrame, 
                          set_columns: List[str],
                          title: str = "UpSet Plot",
                          max_combinations: int = 30,
                          min_patients: int = 1,
                          height: int = 600,
                          color_main: str = "#0D3182",
                          color_highlight: str = "#c0392b") -> str:
    """
    Generate HTML content with an embedded UpSet.js visualization.
    
    Uses a base64 data URL to avoid CORB issues with external scripts.
    
    Args:
        data: DataFrame containing the data
        set_columns: List of column names representing the sets
        title: Title of the visualization
        max_combinations: Maximum number of combinations to display
        min_patients: Minimum number of patients for a combination to be shown
        height: Height of the visualization in pixels
        color_main: Main color for the bars
        color_highlight: Highlight color for single sets
        
    Returns:
        Base64-encoded data URL that can be used as iframe src
    """
    
    # Filter to available columns and convert to binary
    available_cols = [col for col in set_columns if col in data.columns]
    if not available_cols:
        return _generate_error_html("No valid set columns found")
    
    # Convert to binary format
    binary_data = data[available_cols].copy()
    for col in available_cols:
        binary_data[col] = binary_data[col].apply(
            lambda x: 1 if str(x).lower() in ['oui', 'yes', '1', 'true'] else 0
        )
    
    # Generate element assignments for each set
    element_assignments = {col: [] for col in available_cols}
    
    for idx, row in binary_data.iterrows():
        for col in available_cols:
            if row[col] == 1:
                element_assignments[col].append(int(idx))
    
    # Build sets array for UpSet.js
    sets_data = []
    for col in available_cols:
        sets_data.append({
            "name": col,
            "elems": element_assignments[col]
        })
    
    # Generate combinations and their intersections
    combinations = []
    seen_combos = {}
    
    for idx, row in binary_data.iterrows():
        sets_in_row = [col for col in available_cols if row[col] == 1]
        if len(sets_in_row) >= 1:
            combo_key = ','.join(sorted(sets_in_row))
            if combo_key not in seen_combos:
                seen_combos[combo_key] = {
                    'sets': sets_in_row,
                    'elems': []
                }
            seen_combos[combo_key]['elems'].append(int(idx))
    
    # Filter by minimum patients and convert to array
    combo_list = []
    for combo_key, combo_data in seen_combos.items():
        if len(combo_data['elems']) >= min_patients:
            combo_list.append({
                'name': ' ∩ '.join(combo_data['sets']),
                'sets': combo_data['sets'],
                'cardinality': len(combo_data['elems']),
                'elems': combo_data['elems']
            })
    
    # Sort by cardinality descending and limit
    combo_list.sort(key=lambda x: x['cardinality'], reverse=True)
    combo_list = combo_list[:max_combinations]
    
    if not combo_list:
        return _generate_error_html("No treatment combinations found")
    
    # Prepare data for JavaScript
    sets_json = json.dumps(sets_data)
    combos_json = json.dumps(combo_list)
    total_patients = len(data)
    
    # Generate the HTML - using an interactive SVG-based approach
    html_content = _generate_interactive_svg_upset(sets_data, combo_list, title, total_patients, height, color_main, color_highlight)
    
    return html_content


def _generate_interactive_svg_upset(sets_data, combinations, title, total_patients, height, color_main, color_highlight):
    """
    Generate an interactive SVG-based UpSet-like visualization with hover effects.
    Proper UpSet layout: vertical bars on left (set sizes), horizontal bars on top (intersection sizes).
    Includes hover highlighting and tooltips.
    """
    
    n_sets = len(sets_data)
    n_combos = len(combinations)
    
    # Sort sets by size (descending) - highest to lowest
    sets_data = sorted(sets_data, key=lambda x: len(x['elems']), reverse=True)
    
    # Layout parameters - proper UpSet orientation
    margin_left = 150  # Space for set labels
    margin_top = 200   # Space for top bar chart
    margin_right = 40
    margin_bottom = 60
    
    # Calculate dimensions
    matrix_col_width = 35
    matrix_row_height = 28
    set_bar_width = 80  # Width of set size bars on left
    
    # Calculate dynamic height based on number of sets
    matrix_height = n_sets * matrix_row_height + 80  # Extra space for labels
    calculated_height = margin_top + matrix_height + margin_bottom
    height = max(height, calculated_height)  # Use provided height or calculated, whichever is larger
    
    chart_width = max(600, n_combos * matrix_col_width + 100)
    total_width = margin_left + chart_width + margin_right
    
    # Calculate max values for scaling
    max_set_size = max(len(s['elems']) for s in sets_data) if sets_data else 1
    max_combo_size = max(c['cardinality'] for c in combinations) if combinations else 1
    
    # Start building SVG
    svg_parts = []
    svg_parts.append(f'<svg width="100%" height="{height}" viewBox="0 0 {total_width} {height}" xmlns="http://www.w3.org/2000/svg">')
    
    # Title
    svg_parts.append(f'<text x="{total_width / 2}" y="30" text-anchor="middle" font-size="16" font-weight="bold" fill="#333">{title}</text>')
    svg_parts.append(f'<text x="{total_width / 2}" y="50" text-anchor="middle" font-size="12" fill="#666">Total patients: {total_patients} | Combinations shown: {len(combinations)}</text>')
    
    # --- TOP: Horizontal bars for intersection sizes ---
    combo_x_positions = {}
    
    # Build combination info for tooltips
    combos_info = []
    for combo in combinations:
        combos_info.append({
            'name': combo['name'],
            'size': combo['cardinality'],
            'sets': ', '.join(combo['sets'])
        })
    combos_info_json = json.dumps(combos_info)
    
    for i, combo in enumerate(combinations):
        x = margin_left + 40 + i * matrix_col_width
        combo_x_positions[i] = x
        
        # Bar dimensions
        bar_w = matrix_col_width * 0.7
        bar_max_h = margin_top - 90
        bar_h = (combo['cardinality'] / max_combo_size) * bar_max_h
        
        # Bar color based on number of sets in combination
        color = color_highlight if len(combo['sets']) == 1 else color_main
        
        # Horizontal bar going DOWN from top margin with data attributes for interactivity
        bar_y = margin_top - 20 - bar_h
        sets_str = ' ∩ '.join(combo['sets'])
        svg_parts.append(f'<rect class="combo-bar col-{i}" x="{x - bar_w/2}" y="{bar_y}" width="{bar_w}" height="{bar_h}" fill="{color}" data-combo-index="{i}" data-combo-name="{combo["name"]}" data-combo-size="{combo["cardinality"]}" data-sets="{sets_str}"/>')
        
        # Value label on top of bar
        svg_parts.append(f'<text x="{x}" y="{bar_y - 5}" text-anchor="middle" font-size="9" fill="#333">{combo["cardinality"]}</text>')
    
    # Y-axis label for top chart - positioned at bar start height, horizontal, moved left
    svg_parts.append(f'<text x="{margin_left - 90}" y="{margin_top - 25}" text-anchor="start" font-size="12" fill="#333" font-weight="500">Intersection Size</text>')
    
    # --- LEFT SIDE: Vertical bars for set sizes ---
    matrix_start_y = margin_top + 20
    set_y_positions = {}
    
    for i, s in enumerate(sets_data):
        y = matrix_start_y + i * matrix_row_height
        set_y_positions[s['name']] = y
        set_size = len(s['elems'])
        
        # Bar dimensions - vertical bar going right
        bar_max_w = set_bar_width
        bar_w = (set_size / max_set_size) * bar_max_w
        bar_h = matrix_row_height * 0.6
        
        # Vertical bar (actually horizontal, going from left to right) with interactivity
        bar_x = margin_left - 20 - bar_max_w
        svg_parts.append(f'<rect class="set-bar" x="{bar_x + bar_max_w - bar_w}" y="{y - bar_h/2}" width="{bar_w}" height="{bar_h}" fill="#555" data-set-name="{s["name"]}" data-set-size="{set_size}"/>')
        
        # Value label at end of bar
        svg_parts.append(f'<text x="{bar_x + bar_max_w + 5}" y="{y + 3}" text-anchor="start" font-size="10" fill="#333">{set_size}</text>')
        
        # Set name on far left
        svg_parts.append(f'<text x="{bar_x - 10}" y="{y + 3}" text-anchor="end" font-size="11" fill="#333">{s["name"][:22]}{"..." if len(s["name"]) > 22 else ""}</text>')
    
    # X-axis label for set sizes
    svg_parts.append(f'<text x="{margin_left - 60}" y="{matrix_start_y + n_sets * matrix_row_height + 30}" text-anchor="middle" font-size="12" fill="#333">Set Size</text>')
    
    # --- MIDDLE: Matrix with dots ---
    # Background alternating rows for readability
    for i in range(n_sets):
        y = matrix_start_y + i * matrix_row_height
        if i % 2 == 0:
            svg_parts.append(f'<rect x="{margin_left}" y="{y - matrix_row_height/2}" width="{n_combos * matrix_col_width}" height="{matrix_row_height}" fill="#f5f5f5" opacity="0.5"/>')
    
    # Empty circles for all positions (grey background dots)
    for i in range(n_combos):
        x = combo_x_positions[i]
        for j in range(n_sets):
            y = matrix_start_y + j * matrix_row_height
            svg_parts.append(f'<circle class="matrix-bg col-{i}" cx="{x}" cy="{y}" r="5" fill="#ddd"/>')
    
    # Filled circles and connections for actual combinations with interactivity
    for i, combo in enumerate(combinations):
        x = combo_x_positions[i]
        set_indices = [j for j, s in enumerate(sets_data) if s['name'] in combo['sets']]
        sets_str = ' ∩ '.join(combo['sets'])
        
        if len(set_indices) == 1:
            # Single filled dot
            y = matrix_start_y + set_indices[0] * matrix_row_height
            set_name = sets_data[set_indices[0]]['name']
            svg_parts.append(f'<circle class="matrix-dot col-{i}" cx="{x}" cy="{y}" r="7" fill="{color_highlight}" data-combo-index="{i}" data-set-name="{set_name}" data-combo-size="{combo["cardinality"]}" data-combo-sets="{sets_str}"/>')
        elif len(set_indices) > 1:
            # Connection line between dots
            min_y = matrix_start_y + min(set_indices) * matrix_row_height
            max_y = matrix_start_y + max(set_indices) * matrix_row_height
            svg_parts.append(f'<line class="matrix-line col-{i}" x1="{x}" y1="{min_y}" x2="{x}" y2="{max_y}" stroke="{color_main}" stroke-width="4" data-combo-index="{i}" data-combo-size="{combo["cardinality"]}" data-combo-sets="{sets_str}"/>')
            
            # Filled dots
            for idx in set_indices:
                y = matrix_start_y + idx * matrix_row_height
                set_name = sets_data[idx]['name']
                svg_parts.append(f'<circle class="matrix-dot col-{i}" cx="{x}" cy="{y}" r="6" fill="{color_main}" data-combo-index="{i}" data-set-name="{set_name}" data-combo-size="{combo["cardinality"]}" data-combo-sets="{sets_str}"/>')
    
    # X-axis label for matrix
    svg_parts.append(f'<text x="{margin_left + n_combos * matrix_col_width / 2}" y="{matrix_start_y + n_sets * matrix_row_height + 40}" text-anchor="middle" font-size="12" fill="#666">Combination</text>')
    
    svg_parts.append('</svg>')
    
    # Build the SVG with interactivity
    svg_content = ''.join(svg_parts)
    
    # Wrap in HTML with interactivity
    full_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ margin: 0; padding: 10px; font-family: Arial, sans-serif; background: white; overflow: auto; }}
        .container {{ width: 100%; min-height: 100%; display: flex; flex-direction: column; align-items: center; }}
        
        /* Hover effects */
        .combo-bar:hover {{ opacity: 0.8; filter: brightness(1.2); }}
        .combo-bar {{ transition: all 0.2s; cursor: pointer; }}
        
        .set-bar:hover {{ opacity: 0.8; filter: brightness(1.2); }}
        .set-bar {{ transition: all 0.2s; cursor: pointer; }}
        
        .matrix-dot {{ transition: all 0.2s; }}
        .matrix-dot:hover {{ r: 9; filter: brightness(1.3); cursor: pointer; }}
        
        .matrix-line {{ transition: all 0.2s; }}
        
        /* Column highlighting - keep grey dots visible */
        .col-highlight {{ 
            filter: brightness(1.2); 
            stroke-width: 6;
        }}
        .col-highlight-bg {{ 
            fill: #bbdefb; 
            opacity: 0.9;
        }}
        /* Ensure grey background dots stay visible on hover */
        .matrix-bg.col-highlight {{
            fill: #bbb !important;
            opacity: 1 !important;
        }}
        
        /* Tooltip styles - matching Plotly style exactly */
        .tooltip {{
            position: absolute;
            background: #fff;
            color: #444;
            padding: 6px 10px;
            border-radius: 0;
            font-size: 12px;
            font-family: 'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            pointer-events: none;
            z-index: 1000;
            max-width: 250px;
            box-shadow: 0 0 2px rgba(0,0,0,0.25);
            border: 1px solid #bbb;
            display: none;
            line-height: 1.4;
        }}
        
        .tooltip-title {{ font-weight: normal; margin-bottom: 2px; color: #000; font-size: 12px; }}
        .tooltip-content {{ color: #444; }}
        .tooltip-content strong {{ color: #000; font-weight: normal; }}
        
        /* Column highlighting */
        .combo-column {{ transition: all 0.2s; }}
        .combo-column:hover .matrix-bg {{ fill: #e3f2fd; opacity: 0.8; }}
        .combo-column:hover .matrix-dot {{ r: 8; }}
        .combo-column:hover .matrix-line {{ stroke-width: 6; }}
    </style>
</head>
<body>
    <div class="container">
        {svg_content}
    </div>
    <div id="tooltip" class="tooltip">
        <div class="tooltip-title" id="tooltip-title"></div>
        <div class="tooltip-content" id="tooltip-content"></div>
    </div>
    
    <script>
        const tooltip = document.getElementById('tooltip');
        const tooltipTitle = document.getElementById('tooltip-title');
        const tooltipContent = document.getElementById('tooltip-content');
        const totalPatients = ''' + str(total_patients) + ''';
        
        function showTooltip(e, title, content) {
            tooltipTitle.textContent = title;
            tooltipContent.innerHTML = content;
            tooltip.style.display = 'block';
            positionTooltip(e);
        }
        
        function positionTooltip(e) {
            const rect = document.body.getBoundingClientRect();
            let x = e.clientX + 15;
            let y = e.clientY + 15;
            
            // Keep tooltip within viewport
            if (x + tooltip.offsetWidth > window.innerWidth) {
                x = e.clientX - tooltip.offsetWidth - 10;
            }
            if (y + tooltip.offsetHeight > window.innerHeight) {
                y = e.clientY - tooltip.offsetHeight - 10;
            }
            
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        }
        
        function hideTooltip() {
            tooltip.style.display = 'none';
        }
        
        function getPercentage(setSize) {
            return ((setSize / totalPatients) * 100).toFixed(1);
        }
        
        // Add hover listeners to elements
        document.querySelectorAll('.combo-bar').forEach(bar => {
            bar.addEventListener('mouseenter', (e) => {
                const comboIndex = bar.dataset.comboIndex;
                const comboName = bar.dataset.comboName;
                const comboSize = bar.dataset.comboSize;
                const sets = bar.dataset.sets;
                
                showTooltip(e, 'Combination #' + (parseInt(comboIndex) + 1), 
                    '<strong>Size:</strong> ' + comboSize + ' patients<br>' +
                    '<strong>Treatments:</strong> ' + sets);
                
                // Highlight related column
                document.querySelectorAll('.col-' + comboIndex).forEach(el => {
                    el.classList.add('col-highlight');
                });
            });
            
            bar.addEventListener('mousemove', positionTooltip);
            
            bar.addEventListener('mouseleave', () => {
                hideTooltip();
                const comboIndex = bar.dataset.comboIndex;
                document.querySelectorAll('.col-' + comboIndex).forEach(el => {
                    el.classList.remove('col-highlight');
                });
            });
        });
        
        document.querySelectorAll('.set-bar').forEach(bar => {
            bar.addEventListener('mouseenter', (e) => {
                const setName = bar.dataset.setName;
                const setSize = bar.dataset.setSize;
                
                showTooltip(e, setName, 
                    '<strong>Total patients:</strong> ' + setSize + '<br>' +
                    '<strong>Percentage:</strong> ' + getPercentage(setSize) + '%');
            });
            
            bar.addEventListener('mousemove', positionTooltip);
            bar.addEventListener('mouseleave', hideTooltip);
        });
        
        document.querySelectorAll('.matrix-dot, .matrix-line').forEach(dot => {
            dot.addEventListener('mouseenter', (e) => {
                const comboIndex = dot.dataset.comboIndex;
                const setName = dot.dataset.setName;
                const comboSize = dot.dataset.comboSize;
                const comboSets = dot.dataset.comboSets;
                
                showTooltip(e, setName || 'Combination', 
                    '<strong>In combination:</strong> ' + comboSets + '<br>' +
                    '<strong>Patients in this intersection:</strong> ' + comboSize);
                
                // Highlight the column
                document.querySelectorAll('.col-' + comboIndex).forEach(el => {
                    el.classList.add('col-highlight');
                });
            });
            
            dot.addEventListener('mousemove', positionTooltip);
            
            dot.addEventListener('mouseleave', () => {
                hideTooltip();
                const comboIndex = dot.dataset.comboIndex;
                document.querySelectorAll('.col-' + comboIndex).forEach(el => {
                    el.classList.remove('col-highlight');
                });
            });
        });
    </script>
</body>
</html>'''
    
    # Convert to base64 data URL
    html_bytes = full_html.encode('utf-8')
    base64_html = base64.b64encode(html_bytes).decode('utf-8')
    
    return f'data:text/html;base64,{base64_html}'


def _generate_error_html(message: str) -> str:
    """Generate a simple error HTML page as data URL."""
    html = f'''<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; color: #666; }}
        .error {{ text-align: center; padding: 20px; }}
    </style>
</head>
<body>
    <div class="error"><h3>{message}</h3></div>
</body>
</html>'''
    html_bytes = html.encode('utf-8')
    base64_html = base64.b64encode(html_bytes).decode('utf-8')
    return f'data:text/html;base64,{base64_html}'


def create_upsetjs_dash_component(data: pd.DataFrame,
                                  set_columns: List[str],
                                  title: str = "UpSet Plot",
                                  height: int = 600,
                                  remove_prefix: str = None,
                                  **kwargs) -> Dict[str, Any]:
    """
    Create a Dash component configuration for embedding UpSet.js-like visualization.
    
    Returns a dictionary that can be used with html.Iframe(**component).
    Uses a pure SVG approach to avoid external dependencies and CORB issues.
    
    Args:
        data: DataFrame with the data
        set_columns: List of column names representing sets
        title: Title of the plot
        height: Height in pixels
        remove_prefix: Prefix to remove from set names for display (e.g., "Prep Regimen ")
        **kwargs: Additional arguments for generate_upsetjs_html
        
    Returns:
        Dictionary with 'src' (data URL) and 'style' keys for html.Iframe
    """
    # Create a copy of data with renamed columns if prefix removal is needed
    if remove_prefix:
        data = data.copy()
        rename_map = {col: col.replace(remove_prefix, '') for col in set_columns if col.startswith(remove_prefix)}
        data = data.rename(columns=rename_map)
        set_columns = [rename_map.get(col, col) for col in set_columns]
    
    data_url = generate_upsetjs_html(
        data=data,
        set_columns=set_columns,
        title=title,
        height=height,
        **kwargs
    )
    
    return {
        'src': data_url,
        'style': {'width': '100%', 'height': f'{height}px', 'border': 'none'},
    }
