import base64
import mimetypes
import re
from html import escape as _esc
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

_VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
              "link", "meta", "source", "track", "wbr"}
_UNITLESS_STYLES = {"fontWeight", "font-weight", "opacity", "zIndex", "z-index",
                    "lineHeight", "line-height", "flex", "flexGrow", "flexShrink", "order"}
_ATTR_MAP = {"className": "class", "htmlFor": "for", "colSpan": "colspan", "rowSpan": "rowspan"}
_PASS_ATTRS = {"id", "class", "href", "target", "rel", "src", "alt", "title",
               "width", "height", "scope", "role", "lang", "colspan", "rowspan", "for"}

REPORT_MAX_WIDTH = "50vw"
TABLE_FONT_SIZE = "14px"
TABLE_CELL_PADDING = "6px 10px"
NEWEST_YEAR_FIRST = True
TRANSPOSE_YEAR_TABLES = True

HIDDEN_COLUMN_IDS = {"Target_80%"}

STATIC_TABLE_CSS = f"""
.dash-static-table {{ border-collapse: collapse; width: 100%; font-family: 'Open Sans', verdana, arial, sans-serif; }}
.dash-static-table th, .dash-static-table td {{ border: 1px solid lightgrey;
    font-size: {TABLE_FONT_SIZE} !important; padding: {TABLE_CELL_PADDING} !important; }}
.report-page {{ max-width: {REPORT_MAX_WIDTH}; margin: 0 auto; padding: 2rem; }}
@media print {{ .report-page {{ max-width: none; padding: 0; }} }}"""


def css_key(key):
    return re.sub(r"(?<!^)(?=[A-Z])", "-", key).lower()


def style_to_css(style : dict):
    """Dash style to css"""
    if not style:
        return ""
    out = []
    for key, value in style.items():
        if value is None:
            continue
        if (isinstance(value, (int, float)) and not isinstance(value, bool)
                and key not in _UNITLESS_STYLES and value != 0):
            value = f"{value}px"
        out.append(f"{css_key(key)}: {value}")
    return "; ".join(out)


def attrs(props):
    parts = []
    for key, value in props.items():
        if key == "children" or value is None or value is False:
            continue
        if key == "style":
            css = style_to_css(value)
            if css:
                parts.append(f'style="{_esc(css, quote=True)}"')
            continue
        name = _ATTR_MAP.get(key, key)
        if name in _PASS_ATTRS or name.startswith(("data-", "aria-")):
            parts.append(f'{name}="{_esc(str(value), quote=True)}"')
    return (" " + " ".join(parts)) if parts else ""


def rule_matches(condition, row_idx, col_id):
    """Supports the style_data_conditional conditions used in this project:
    row_index ('odd' / 'even' / int / list) and column_id (str / list).
    Any other condition (e.g. filter_query) makes the rule be skipped."""
    if not condition:
        return True
    if set(condition) - {"row_index", "column_id"}:
        return False
    row_index = condition.get("row_index")
    if row_index is not None:
        if row_index == "odd":
            ok = row_idx % 2 == 1
        elif row_index == "even":
            ok = row_idx % 2 == 0
        elif isinstance(row_index, list):
            ok = row_idx in row_index
        else:
            ok = row_idx == row_index
        if not ok:
            return False
    column_id = condition.get("column_id")
    if column_id is not None:
        ids = column_id if isinstance(column_id, list) else [column_id]
        if col_id not in ids:
            return False
    return True


def format_value(value, column):
    if value is None:
        return ""
    spec = (column.get("format") or {}).get("specifier")
    if spec and isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return format(value, spec)
        except (ValueError, TypeError):
            pass
    return str(value)

def render_transposed_datatable(data, columns, style_cell, style_header, style_data,
                                 conditional, wrapper_style):
    """Same table with the axes swapped: one column per year (header row = years),
    one row per statistic (first column = the original column names).

    The original styling is mapped to the new orientation:
      - `column_id` rules (e.g. the highlighted % columns) now highlight a whole row;
      - `row_index` rules (odd-row banding) now follow the displayed statistic rows,
        like in the Word report."""
    year_col = next(c for c in columns if c.get("id") == "Year")
    stat_columns = [c for c in columns if c.get("id") != "Year"]

    header_css = _esc(style_to_css({**style_cell, **style_header}), quote=True)
    header_cells = f'<th style="{header_css}"></th>' + "".join(
        f'<th style="{header_css}">{_esc(format_value(row.get("Year"), year_col))}</th>'
        for row in data
    )

    body_rows = []
    for i, column in enumerate(stat_columns):
        col_id = column.get("id")
        style = {**style_cell, **style_data}
        for rule in conditional:
            if rule_matches(rule.get("if"), i, col_id):
                style.update({k: v for k, v in rule.items() if k != "if"})
        css = _esc(style_to_css(style), quote=True)
        label_css = _esc(style_to_css({**style, "textAlign": "left", "fontWeight": "bold"}),
                         quote=True)
        label = _esc(str(column.get("name", col_id)))
        cells = "".join(
            f'<td style="{css}">{_esc(format_value(row.get(col_id), column))}</td>'
            for row in data
        )
        body_rows.append(f'<tr><th scope="row" style="{label_css}">{label}</th>{cells}</tr>')

    wrapper_attr = f' style="{_esc(wrapper_style, quote=True)}"' if wrapper_style else ""
    return (
        f"<div{wrapper_attr}>"
        f'<table class="dash-static-table"><thead><tr>{header_cells}</tr></thead>'
        f"<tbody>{''.join(body_rows)}</tbody></table></div>"
    )

def render_datatable(props, expand_tables=True):
    data = props.get("data") or []
    columns = [c for c in (props.get("columns") or [])
               if c.get("id") not in HIDDEN_COLUMN_IDS]
    has_year = any(c.get("id") == "Year" for c in columns)
    if NEWEST_YEAR_FIRST and has_year:
        data = list(reversed(data))
    style_cell = props.get("style_cell") or {}
    style_header = props.get("style_header") or {}
    style_data = props.get("style_data") or {}
    conditional = props.get("style_data_conditional") or []

    style_table = dict(props.get("style_table") or {})
    if expand_tables:
        for key in ("height", "maxHeight", "max-height", "overflowY", "overflow-y"):
            style_table.pop(key, None)
    wrapper_style = style_to_css(style_table)

    if TRANSPOSE_YEAR_TABLES and has_year:
        return render_transposed_datatable(data, columns, style_cell, style_header,
                                            style_data, conditional, wrapper_style)

    header_css = style_to_css({**style_cell, **style_header})
    header_cells = "".join(
        f'<th style="{_esc(header_css, quote=True)}">{_esc(str(c.get("name", c.get("id", ""))))}</th>'
        for c in columns
    )

    body_rows = []
    for row_idx, row in enumerate(data):
        cells = []
        for column in columns:
            col_id = column.get("id")
            style = {**style_cell, **style_data}
            for rule in conditional:
                if rule_matches(rule.get("if"), row_idx, col_id):
                    style.update({k: v for k, v in rule.items() if k != "if"})
            cells.append(
                f'<td style="{_esc(style_to_css(style), quote=True)}">'
                f'{_esc(format_value(row.get(col_id), column))}</td>'
            )
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    wrapper_attr = f' style="{_esc(wrapper_style, quote=True)}"' if wrapper_style else ""
    return (
        f"<div{wrapper_attr}>"
        f'<table class="dash-static-table"><thead><tr>{header_cells}</tr></thead>'
        f"<tbody>{''.join(body_rows)}</tbody></table></div>"
    )

def render_component(comp, expand_tables=True):
    """Dash component tree (html.*, DataTable, dbc.Alert, lists, text) -> HTML string."""
    if comp is None or comp is False:
        return ""
    if isinstance(comp, (str, int, float)):
        return _esc(str(comp))
    if isinstance(comp, (list, tuple)):
        return "".join(render_component(c, expand_tables) for c in comp)

    node = comp.to_plotly_json() if hasattr(comp, "to_plotly_json") else comp
    if not isinstance(node, dict) or "type" not in node:
        return _esc(str(comp))

    ctype = node["type"]
    namespace = node.get("namespace", "")
    props = node.get("props") or {}

    if ctype == "DataTable":
        return render_datatable(props, expand_tables)

    inner = render_component(props.get("children"), expand_tables)

    if namespace == "dash_bootstrap_components":
        if ctype == "Alert":
            classes = f"alert alert-{props.get('color', 'success')} {props.get('className', '')}".strip()
            return f'<div class="{_esc(classes)}" role="alert">{inner}</div>'
        return f"<div{attrs(props)}>{inner}</div>"  # Card, Row, ... keep className

    if namespace in ("dash_html_components", "dash.html", ""):
        tag = ctype.lower()
        if tag in _VOID_TAGS:
            return f"<{tag}{attrs(props)}>"
        return f"<{tag}{attrs(props)}>{inner}</{tag}>"

    return f"<div{attrs(props)}>{inner}</div>"  # unknown component: keep its children


# -----------------------------------------------------------------------------
# CSS collection + page assembly
# -----------------------------------------------------------------------------
_MAX_EMBED_BYTES = 3_000_000   # resources above this stay as absolute URLs
_FETCH_TIMEOUT = 10            # seconds, per remote resource
_RESOURCE_CACHE = {}           # (kind, location) -> (bytes, content_type); successes only

# One pass over a stylesheet: either an @import or a url(...) reference.
# data: URIs and #fragment-only references are left untouched.
_CSS_REF_RE = re.compile(
    r"""@import\s+(?:url\(\s*)?(?P<q1>['"]?)(?P<imp>[^'")\s;]+)(?P=q1)\s*\)?(?P<media>[^;]*);"""
    r"""|url\(\s*(?P<q2>['"]?)(?P<u>(?!data:|\#)[^'")]+?)(?P=q2)\s*\)""",
    re.IGNORECASE,
)
_SOURCEMAP_RE = re.compile(r"/\*#\s*sourceMappingURL=.*?\*/", re.DOTALL)


def read_resource(location, remote):
    """Returns (bytes, content_type) or None. Only successes are cached."""
    key = ("remote" if remote else "local", location)
    if key in _RESOURCE_CACHE:
        return _RESOURCE_CACHE[key]
    try:
        if remote:
            # A browser-like User-Agent makes services such as Google Fonts
            # answer with woff2 files instead of legacy formats.
            req = Request(location, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=_FETCH_TIMEOUT) as response:
                data = response.read(_MAX_EMBED_BYTES + 1)
                ctype = response.headers.get_content_type()
        else:
            data = Path(location).read_bytes()
            ctype = mimetypes.guess_type(location)[0] or "application/octet-stream"
    except Exception as e:
        print(f"HTML export: could not read {location}: {e}")
        return None
    result = (data, ctype)
    _RESOURCE_CACHE[key] = result
    return result


def inline_css_references(css, base, remote, assets_folder, depth=0):
    """Makes a stylesheet self-contained: @import rules are replaced by the imported
    stylesheet's content and url(...) references (fonts, images) by base64 data URIs.
    `base` is the stylesheet's URL (remote) or file path (local), used to resolve
    relative references. A resource that cannot be fetched or is too large keeps a
    working reference (absolute URL when remote) instead of being dropped."""

    def resolve(ref):
        """Returns (location, is_remote) for a reference found in this stylesheet."""
        if re.match(r"^(https?:)?//", ref):
            return ("https:" + ref if ref.startswith("//") else ref), True
        if remote:
            return urljoin(base, ref), True
        clean = ref.split("#")[0].split("?")[0]
        if clean.startswith("/"):  # e.g. /assets/images/bg.png as served by Dash
            return str(Path(assets_folder).parent / clean.lstrip("/")), False
        return str((Path(base).parent / clean).resolve()), False

    def replace(match):
        if match.group("imp") is not None:
            if depth >= 3:
                return match.group(0)
            location, is_remote = resolve(match.group("imp"))
            res = read_resource(location, is_remote)
            if res is None:
                return match.group(0)
            imported = inline_css_references(
                res[0].decode("utf-8", errors="replace"), location, is_remote,
                assets_folder, depth + 1)
            media = (match.group("media") or "").strip()
            return f"@media {media} {{\n{imported}\n}}" if media else imported

        ref = match.group("u").strip()
        location, is_remote = resolve(ref)
        keep = f'url("{location}")' if is_remote else match.group(0)
        if "#" in ref:  # e.g. svg font fragments: cannot live in a data URI
            return keep
        res = read_resource(location, is_remote)
        if res is None or len(res[0]) > _MAX_EMBED_BYTES:
            return keep
        data, ctype = res
        return f'url("data:{ctype};base64,{base64.b64encode(data).decode("ascii")}")'

    return _CSS_REF_RE.sub(replace, _SOURCEMAP_RE.sub("", css))


def collect_app_css(app, css_files=None, embed_external=True):
    """Returns (fallback_urls, inlined_css) for the app.

    - external_stylesheets (Bootstrap, ...) are fetched and inlined, in the same
      order Dash loads them (first), with their fonts/images embedded.
    - the assets folder .css files (custom-style.css, ...) follow, so they still
      override the external ones. css_files restricts this to given file names;
      by default every .css file there is included.
    - fallback_urls lists external stylesheets that could not be fetched (or all
      of them when embed_external=False); the caller links those instead.
    """
    assets_folder = app.config.get("assets_folder") or "assets"
    fallback_urls = []
    chunks = []

    for item in app.config.get("external_stylesheets") or []:
        href = item.get("href") if isinstance(item, dict) else item
        if not href:
            continue
        if not embed_external:
            fallback_urls.append(href)
            continue
        res = read_resource(href, remote=True)
        if res is None:
            fallback_urls.append(href)
            continue
        css = res[0].decode("utf-8", errors="replace")
        chunks.append(f"/* {href} */\n"
                      + inline_css_references(css, href, True, assets_folder))

    folder = Path(assets_folder)
    if css_files:
        files = [folder / name for name in css_files]
    else:
        files = sorted(folder.rglob("*.css")) if folder.exists() else []

    for path in files:
        try:
            css = path.read_text(encoding="utf-8")
            chunks.append(f"/* {path.name} */\n"
                          + inline_css_references(css, str(path.resolve()), False, assets_folder))
        except Exception as e:
            print(f"CSS file not embedded in HTML export ({path}): {e}")
    return fallback_urls, "\n".join(chunks)


def build_html_from_components(components, app, title="Report", css_files=None,
                               expand_tables=True, embed_external=True):
    """Concatenates dash components into one standalone HTML document.
    All stylesheets are embedded (see collect_app_css), so the file does not
    depend on the network or on the app being reachable."""
    urls, inline_css = collect_app_css(app, css_files, embed_external)
    links = "\n".join(f'<link rel="stylesheet" href="{_esc(u, quote=True)}">' for u in urls)
    body = render_component(list(components), expand_tables)
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{_esc(title)}</title>\n{links}\n"
        f"<style>\n{inline_css}\n{STATIC_TABLE_CSS}\n</style>\n</head>\n"
        f"<body>\n<main class=\"report-page\">\n{body}\n</main>\n</body>\n</html>\n"
    )


def logo_data_uri(paths=("assets/images/logo.svg", "assets/images/logo.png")):
    """Embeds the first logo file that exists (SVG preferred, PNG as fallback).
    The MIME type follows the extension, so an SVG stays a vector image."""
    mime_by_ext = {".svg": "image/svg+xml", ".png": "image/png",
                   ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    for path in paths:
        file = Path(path)
        if not file.exists():
            continue
        try:
            mime = mime_by_ext.get(file.suffix.lower(), "application/octet-stream")
            return f"data:{mime};base64," + base64.b64encode(file.read_bytes()).decode("ascii")
        except Exception as e:
            print(f"Logo not embedded in HTML export ({path}): {e}")
    return None
