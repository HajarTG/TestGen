"""
Step 1: Java Analyzer - calls the JavaParser CLI JAR via subprocess.

Input:  path to a directory of .java files
Output: dict (CodeModel) with classes, methods, annotations, control-flow metadata
"""
import os
import json
import subprocess
import logging
from typing import Dict, Any

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _find_java_files(directory: str) -> list:
    """Recursively find all .java files in a directory."""
    java_files = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".java"):
                java_files.append(os.path.join(root, f))
    return java_files


def _run_parser_jar(source_dir: str) -> Dict[str, Any]:
    """
    Invoke the JavaParser CLI JAR as a subprocess.
    The JAR reads a directory and outputs JSON to stdout.
    """
    jar_path = settings.java_parser_jar

    if not os.path.exists(jar_path):
        logger.warning(f"JavaParser JAR not found at {jar_path}, using fallback parser")
        return _fallback_parse(source_dir)

    try:
        result = subprocess.run(
            ["java", "-jar", jar_path, source_dir],
            capture_output=True,
            text=True,
            timeout=120,
        )
        raw_data = json.loads(result.stdout)
        classes = []
        for file_data in raw_data.get("files", []):
            file_path = file_data.get("path")
            source = ""
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        source = f.read()
                except Exception as e:
                    logger.warning(f"Could not read source file {file_path}: {e}")
            
            for cls in file_data.get("classes", []):
                cls["file_path"] = file_path
                cls["source"] = source
                classes.append(cls)
        return {"classes": classes}
        
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning(f"JAR execution failed ({e}), using fallback parser")
        return _fallback_parse(source_dir)


def _fallback_parse(source_dir: str) -> Dict[str, Any]:
    """
    Simple regex-based fallback parser for when the JAR is unavailable.
    Extracts basic class/method structure from .java files.
    """
    import re

    classes = []
    java_files = _find_java_files(source_dir)

    for filepath in java_files:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        # Extract class-level annotations
        class_annotations = re.findall(r'@(\w+)', source.split("class ")[0] if "class " in source else "")

        # Extract class name
        class_match = re.search(r'(?:public\s+)?class\s+(\w+)', source)
        if not class_match:
            continue
        class_name = class_match.group(1)

        # Extract methods
        methods = []
        # Pattern: annotations + modifiers + return_type + name(params) { body }
        method_pattern = re.compile(
            r'((?:@\w+(?:\([^)]*\))?\s*)*)'  # annotations
            r'((?:public|private|protected)\s+)?'  # visibility
            r'((?:static\s+)?(?:final\s+)?)'  # modifiers
            r'(\w[\w<>\[\], ]*)\s+'  # return type
            r'(\w+)\s*\(([^)]*)\)\s*'  # method name + params
            r'(?:throws\s+[\w, ]+\s*)?'  # throws clause
            r'\{',  # opening brace
            re.MULTILINE
        )

        for m in method_pattern.finditer(source):
            method_name = m.group(5)
            if method_name in ("if", "for", "while", "switch", "catch", "try"):
                continue

            # Extract method body (find matching brace)
            start = m.end() - 1
            brace_count = 1
            pos = start + 1
            while pos < len(source) and brace_count > 0:
                if source[pos] == '{':
                    brace_count += 1
                elif source[pos] == '}':
                    brace_count -= 1
                pos += 1
            method_source = source[m.start():pos]

            # Analyze method body
            body = source[start:pos]
            has_try_catch = "try" in body and "catch" in body
            has_loops = bool(re.search(r'\b(for|while)\s*\(', body))
            branch_count = body.count("if ") + body.count("else ") + body.count("switch ")
            method_annotations = re.findall(r'@(\w+)', m.group(1))

            methods.append({
                "name": method_name,
                "return_type": m.group(4).strip(),
                "parameters": m.group(6).strip(),
                "visibility": (m.group(2) or "package-private").strip(),
                "annotations": method_annotations,
                "source": method_source,
                "has_try_catch": has_try_catch,
                "has_loops": has_loops,
                "branch_count": branch_count,
                "cyclomatic_complexity": max(1, branch_count + 1),
            })

        classes.append({
            "name": class_name,
            "file_path": filepath,
            "annotations": class_annotations,
            "source": source,
            "methods": methods,
        })

    return {"classes": classes}


def analyze_java_code(source_path: str) -> Dict[str, Any]:
    """
    Public API: Analyze Java source code at the given path.
    Returns a CodeModel dictionary.
    """
    if os.path.isfile(source_path):
        source_dir = os.path.dirname(source_path)
    else:
        source_dir = source_path

    java_files = _find_java_files(source_dir)
    if not java_files:
        logger.warning(f"No .java files found in {source_dir}")
        return {"classes": []}

    logger.info(f"Analyzing {len(java_files)} Java files in {source_dir}")
    code_model = _run_parser_jar(source_dir)

    total_methods = sum(len(c.get("methods", [])) for c in code_model.get("classes", []))
    logger.info(f"Found {len(code_model.get('classes', []))} classes, {total_methods} methods")

    return code_model
