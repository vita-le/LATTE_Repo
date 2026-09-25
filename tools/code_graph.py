import ast
import html
from pathlib import Path

from pyvis.network import Network


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"

OUTPUT_DIR = PROJECT_ROOT / "docs" / "architecture"
OUTPUT_FILE = OUTPUT_DIR / "code_graph.html"


# ============================================================
# PROJECT DISCOVERY
# ============================================================

def collect_python_files():
    """Return all Python files inside src/."""

    return list(
        SRC_ROOT.rglob("*.py")
    )


def get_module_name(file_path):
    """Convert a Python file path into a Python module name."""

    relative = file_path.relative_to(
        PROJECT_ROOT
    )

    parts = list(relative.parts)

    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = Path(
            parts[-1]
        ).stem

    return ".".join(parts)


def get_relative_path(file_path):
    """Return the project-relative file path."""

    return file_path.relative_to(
        PROJECT_ROOT
    )


# ============================================================
# CATEGORIES
# ============================================================

CATEGORY_COLORS = {
    "Core": "#4C78A8",
    "Visualization": "#59A14F",
    "Analysis": "#F28E2B",
    "GUI": "#B07AA1",
    "Main Window": "#E15759",
    "Analysis GUI": "#9C755F",
    "Tests": "#76B7B2",
    "Other": "#98A2B3",
}


def get_category(file_path):
    """Determine the architectural category."""

    relative = file_path.relative_to(
        SRC_ROOT
    )

    parts = relative.parts

    if not parts:
        return "Other"

    first = parts[0]

    if first == "core":
        return "Core"

    if first == "visualization":
        return "Visualization"

    if first == "analysis":
        return "Analysis"

    if first == "tests":
        return "Tests"

    if first == "gui":

        if len(parts) > 1:

            if parts[1] == "main_window":
                return "Main Window"

            if parts[1] == "analysis_window":
                return "Analysis GUI"

        return "GUI"

    return "Other"


# ============================================================
# AST
# ============================================================

def parse_file(file_path):
    """Parse a Python file with AST."""

    try:

        source = file_path.read_text(
            encoding="utf-8"
        )

        return ast.parse(source)

    except (
        SyntaxError,
        UnicodeDecodeError,
    ):

        return None


def get_imports(file_path):
    """Extract imported modules."""

    tree = parse_file(file_path)

    if tree is None:
        return []

    imports = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):

            if node.module:
                imports.append(
                    node.module
                )

    return imports


# ============================================================
# MODULE MATCHING
# ============================================================

def resolve_import(
    imported_module,
    modules,
):
    """Resolve an import to a local module."""

    if imported_module in modules:
        return imported_module

    candidates = []

    for module in modules:

        if imported_module.startswith(
            module + "."
        ):
            candidates.append(module)

        elif module.startswith(
            imported_module + "."
        ):
            candidates.append(module)

    if not candidates:
        return None

    return min(
        candidates,
        key=len,
    )


# ============================================================
# NETWORK STYLE
# ============================================================

def configure_network(net):
    """Apply common graph styling."""

    net.set_options(
        """
        {
          "nodes": {
            "shape": "box",
            "margin": 12,
            "borderWidth": 1,
            "shadow": {
              "enabled": true,
              "size": 5,
              "x": 2,
              "y": 2
            },
            "font": {
              "face": "Segoe UI",
              "size": 14
            }
          },

          "edges": {
            "width": 1,
            "color": {
              "color": "#98A2B3",
              "highlight": "#344054",
              "hover": "#667085"
            },
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 0.6
              }
            },
            "smooth": {
              "enabled": true,
              "type": "dynamic"
            }
          },

          "physics": {
            "enabled": true,
            "forceAtlas2Based": {
              "gravitationalConstant": -100,
              "centralGravity": 0.015,
              "springLength": 170,
              "springConstant": 0.05,
              "damping": 0.4
            },
            "solver": "forceAtlas2Based",
            "stabilization": {
              "enabled": true,
              "iterations": 800,
              "fit": true
            }
          },

          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true,
            "dragNodes": true,
            "zoomView": true
          }
        }
        """
    )


# ============================================================
# ARCHITECTURE GRAPH
# ============================================================

def build_architecture_graph(
    modules,
):
    """Build the high-level architecture graph."""

    net = Network(
        height="800px",
        width="100%",
        bgcolor="#F4F6F8",
        font_color="#1F2933",
        directed=True,
    )

    configure_network(net)

    for module_name, file_path in modules.items():

        category = get_category(
            file_path
        )

        color = CATEGORY_COLORS[
            category
        ]

        display_name = module_name.split(
            "."
        )[-1]

        relative_path = get_relative_path(
            file_path
        )

        net.add_node(
            module_name,
            label=display_name,
            title=(
                f"<b>{html.escape(str(relative_path))}</b>"
                f"<br>Category: {category}"
            ),
            color={
                "background": color,
                "border": color,
                "highlight": {
                    "background": color,
                    "border": "#1F2933",
                },
            },
            font={
                "color": "#FFFFFF",
                "face": "Segoe UI",
                "size": 14,
            },
        )

    for module_name, file_path in modules.items():

        imports = get_imports(
            file_path
        )

        for imported_module in imports:

            target = resolve_import(
                imported_module,
                modules,
            )

            if target is None:
                continue

            if target == module_name:
                continue

            net.add_edge(
                module_name,
                target,
            )

    return net


# ============================================================
# DEPENDENCY GRAPH
# ============================================================

def build_dependency_graph(
    modules,
):
    """Build detailed import dependency graph."""

    net = Network(
        height="800px",
        width="100%",
        bgcolor="#F4F6F8",
        font_color="#1F2933",
        directed=True,
    )

    configure_network(net)

    for module_name, file_path in modules.items():

        category = get_category(
            file_path
        )

        color = CATEGORY_COLORS[
            category
        ]

        relative_path = get_relative_path(
            file_path
        )

        net.add_node(
            module_name,
            label=module_name.split(".")[-1],
            title=(
                f"<b>{html.escape(str(relative_path))}</b>"
                f"<br>Category: {category}"
            ),
            color={
                "background": color,
                "border": color,
            },
            font={
                "color": "#FFFFFF",
                "face": "Segoe UI",
                "size": 13,
            },
        )

    edges = set()

    for module_name, file_path in modules.items():

        imports = get_imports(
            file_path
        )

        for imported_module in imports:

            target = resolve_import(
                imported_module,
                modules,
            )

            if target is None:
                continue

            if target == module_name:
                continue

            edge = (
                module_name,
                target,
            )

            if edge in edges:
                continue

            edges.add(edge)

            net.add_edge(
                module_name,
                target,
            )

    return net


# ============================================================
# CALL GRAPH
# ============================================================

def get_functions(file_path):
    """
    Extract functions and methods from a Python file.

    Returns:
        {
            function_name: ast.FunctionDef
        }
    """

    tree = parse_file(file_path)

    if tree is None:
        return {}

    functions = {}

    for node in ast.walk(tree):

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):

            functions[node.name] = node

    return functions


def get_function_calls(function_node):
    """Extract direct function calls from a function."""

    calls = []

    for node in ast.walk(
        function_node
    ):

        if isinstance(
            node,
            ast.Call,
        ):

            if isinstance(
                node.func,
                ast.Name,
            ):

                calls.append(
                    node.func.id
                )

            elif isinstance(
                node.func,
                ast.Attribute,
            ):

                calls.append(
                    node.func.attr
                )

    return calls


def build_call_graph(
    modules,
):
    """
    Build a basic function call graph.

    This version focuses on calls that can be
    resolved statically from the AST.
    """

    net = Network(
        height="800px",
        width="100%",
        bgcolor="#F4F6F8",
        font_color="#1F2933",
        directed=True,
    )

    configure_network(net)

    all_functions = {}

    # --------------------------------------------------------
    # Add function nodes
    # --------------------------------------------------------

    for module_name, file_path in modules.items():

        category = get_category(
            file_path
        )

        color = CATEGORY_COLORS[
            category
        ]

        functions = get_functions(
            file_path
        )

        for function_name, function_node in functions.items():

            node_id = (
                f"{module_name}."
                f"{function_name}"
            )

            all_functions[
                function_name
            ] = all_functions.get(
                function_name,
                [],
            ) + [node_id]

            relative_path = get_relative_path(
                file_path
            )

            net.add_node(
                node_id,
                label=function_name,
                title=(
                    f"<b>{html.escape(str(relative_path))}</b>"
                    f"<br>"
                    f"{function_name}()"
                ),
                color={
                    "background": color,
                    "border": color,
                },
                font={
                    "color": "#FFFFFF",
                    "face": "Segoe UI",
                    "size": 13,
                },
            )

    # --------------------------------------------------------
    # Add function call edges
    # --------------------------------------------------------

    for module_name, file_path in modules.items():

        functions = get_functions(
            file_path
        )

        for function_name, function_node in functions.items():

            source_id = (
                f"{module_name}."
                f"{function_name}"
            )

            calls = get_function_calls(
                function_node
            )

            for called_name in calls:

                targets = all_functions.get(
                    called_name,
                    [],
                )

                for target_id in targets:

                    if target_id == source_id:
                        continue

                    net.add_edge(
                        source_id,
                        target_id,
                    )

    return net


# ============================================================
# HTML
# ============================================================

def write_graph(
    net,
    filename,
):
    """Write a PyVis graph to HTML."""

    net.write_html(
        str(filename),
        notebook=False,
    )


def generate_html(
    architecture_file,
    dependency_file,
    call_file,
):
    """
    Create the main HTML interface containing
    all three graphs.
    """

    architecture_url = architecture_file.name
    dependency_url = dependency_file.name
    call_url = call_file.name

    html_content = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>LATTE Code Graph</title>

<style>

html,
body {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    font-family: "Segoe UI", Arial, sans-serif;
    background: #F4F6F8;
}}

.header {{
    height: 75px;
    background: #FFFFFF;
    border-bottom: 1px solid #D0D5DD;

    display: flex;
    align-items: center;

    padding-left: 30px;
    padding-right: 30px;

    box-sizing: border-box;
}}

.title {{
    font-size: 24px;
    font-weight: 700;
    color: #1F2933;
}}

.subtitle {{
    margin-left: 15px;
    font-size: 13px;
    color: #667085;
}}

.tabs {{
    height: 55px;
    background: #FFFFFF;
    border-bottom: 1px solid #D0D5DD;

    display: flex;
    align-items: center;

    padding-left: 30px;
    gap: 8px;
}}

.tab {{
    border: none;
    background: transparent;

    padding: 9px 18px;

    border-radius: 6px;

    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    font-weight: 600;

    color: #667085;

    cursor: pointer;
}}

.tab:hover {{
    background: #F2F4F7;
    color: #1F2933;
}}

.tab.active {{
    background: #1F5A7A;
    color: #FFFFFF;
}}

.graph-container {{
    width: 100%;
    height: calc(100vh - 130px);

    display: none;
}}

.graph-container.active {{
    display: block;
}}

</style>

<script>

function showGraph(name) {{

    const graphs = [
        "architecture",
        "dependencies",
        "calls"
    ];

    const tabs = [
        "tab-architecture",
        "tab-dependencies",
        "tab-calls"
    ];

    for (const graph of graphs) {{

        document
            .getElementById(graph)
            .classList
            .remove("active");
    }}

    for (const tab of tabs) {{

        document
            .getElementById(tab)
            .classList
            .remove("active");
    }}

    document
        .getElementById(name)
        .classList
        .add("active");

    document
        .getElementById(
            "tab-" + name
        )
        .classList
        .add("active");
}}

</script>

</head>

<body>

<div class="header">

    <div class="title">
        LATTE Code Graph
    </div>

    <div class="subtitle">
        Interactive software architecture
    </div>

</div>


<div class="tabs">

    <button
        id="tab-architecture"
        class="tab active"
        onclick="showGraph('architecture')"
    >
        Architecture
    </button>

    <button
        id="tab-dependencies"
        class="tab"
        onclick="showGraph('dependencies')"
    >
        Dependencies
    </button>

    <button
        id="tab-calls"
        class="tab"
        onclick="showGraph('calls')"
    >
        Call Graph
    </button>

</div>


<div
    id="architecture"
    class="graph-container active"
>

    <iframe
        src="{architecture_url}"
        style="
            width:100%;
            height:100%;
            border:none;
        "
    ></iframe>

</div>


<div
    id="dependencies"
    class="graph-container"
>

    <iframe
        src="{dependency_url}"
        style="
            width:100%;
            height:100%;
            border:none;
        "
    ></iframe>

</div>


<div
    id="calls"
    class="graph-container"
>

    <iframe
        src="{call_url}"
        style="
            width:100%;
            height:100%;
            border:none;
        "
    ></iframe>

</div>

</body>

</html>
"""

    main_file = OUTPUT_DIR / "code_graph.html"

    main_file.write_text(
        html_content,
        encoding="utf-8",
    )

    return main_file


# ============================================================
# MAIN
# ============================================================

def generate_graph():

    files = collect_python_files()

    modules = {}

    for file_path in files:

        module_name = get_module_name(
            file_path
        )

        modules[
            module_name
        ] = file_path

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Architecture
    # --------------------------------------------------------

    architecture_net = (
        build_architecture_graph(
            modules
        )
    )

    architecture_file = (
        OUTPUT_DIR /
        "architecture.html"
    )

    write_graph(
        architecture_net,
        architecture_file,
    )

    # --------------------------------------------------------
    # Dependencies
    # --------------------------------------------------------

    dependency_net = (
        build_dependency_graph(
            modules
        )
    )

    dependency_file = (
        OUTPUT_DIR /
        "dependencies.html"
    )

    write_graph(
        dependency_net,
        dependency_file,
    )

    # --------------------------------------------------------
    # Call graph
    # --------------------------------------------------------

    call_net = (
        build_call_graph(
            modules
        )
    )

    call_file = (
        OUTPUT_DIR /
        "calls.html"
    )

    write_graph(
        call_net,
        call_file,
    )

    # --------------------------------------------------------
    # Main interface
    # --------------------------------------------------------

    main_file = generate_html(
        architecture_file,
        dependency_file,
        call_file,
    )

    print()
    print(
        "LATTE code graph generated."
    )
    print()

    print(
        f"Python files: {len(files)}"
    )

    print(
        f"Architecture: {architecture_file}"
    )

    print(
        f"Dependencies: {dependency_file}"
    )

    print(
        f"Call graph:   {call_file}"
    )

    print(
        f"Main graph:   {main_file}"
    )

    print()


if __name__ == "__main__":
    generate_graph()