#!/usr/bin/env python3

# 这个脚本的作用:
# 扫描当前项目里的代码和支撑文本文件, 提取 imports, exports, symbols,
# 然后生成根小地图和按后缀拆分的详细索引.
#
# 它不调用 LLM, 不联网, 不花 token.

import json
import re
from pathlib import Path
from datetime import datetime, timezone


# 项目根目录.
# Path.cwd() 表示你在哪个目录运行脚本, 哪个目录就是根目录.
ROOT = Path.cwd()

# 输出目录和输出文件.
OUT_DIR = ROOT / ".project-index"
MAP_FILE = OUT_DIR / "project-map.json"


# 不扫描这些目录.
# 这些一般是依赖, Git 数据, 构建产物, 缓存目录.
SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".project-index",
    "target",
}


# 只扫描这些后缀的代码文件.
# 支持常见的 JS, TS, Python, Java, Vue, Svelte.
CODE_EXTS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".py",
    ".java",
    ".vue",
    ".svelte",
}


# 支撑功能排查的文本文件后缀.
# 这些文件不是业务代码, 但会影响页面样式, 配置, 数据库和接口取数.
SUPPORT_EXTS = {
    ".css",
    ".html",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".properties",
    ".sql",
    ".md",
}


# 地图会索引的全部文本后缀.
INDEX_EXTS = CODE_EXTS | SUPPORT_EXTS


# JS/TS 系列文件后缀.
JS_LIKE_EXTS = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".vue",
    ".svelte",
}


# Python 文件后缀.
PYTHON_EXTS = {
    ".py",
}


# Java 文件后缀.
JAVA_EXTS = {
    ".java",
}


# 支撑文件系列后缀.
XML_EXTS = {
    ".xml",
}

YAML_EXTS = {
    ".yaml",
    ".yml",
}

PROPERTIES_EXTS = {
    ".properties",
}

CSS_EXTS = {
    ".css",
}

HTML_EXTS = {
    ".html",
}

SQL_EXTS = {
    ".sql",
}

JSON_EXTS = {
    ".json",
}

MARKDOWN_EXTS = {
    ".md",
}


# JS/TS import 提取规则.
JS_IMPORT_PATTERNS = [
    # 匹配: import xxx from "xxx"
    re.compile(r"^\s*import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE),

    # 匹配: import "xxx"
    re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]", re.MULTILINE),

    # 匹配: require("xxx")
    re.compile(r"require\(['\"]([^'\"]+)['\"]\)"),
]


# Python import 提取规则.
PYTHON_IMPORT_PATTERNS = [
    # 匹配 Python: from xxx import yyy
    re.compile(r"^\s*from\s+([\w\.]+)\s+import\s+", re.MULTILINE),

    # 匹配 Python: import xxx
    re.compile(r"^\s*import\s+([\w\.]+)\s*$", re.MULTILINE),
]


# Java import 提取规则.
JAVA_IMPORT_PATTERNS = [
    # 匹配 Java: import xxx;
    # 匹配 Java: import static xxx;
    re.compile(r"^\s*import\s+(?:static\s+)?([\w\.\*]+)\s*;", re.MULTILINE),
]


# JS/TS export 提取规则.
JS_EXPORT_PATTERNS = [
    # 匹配: export class UserService
    # 匹配: export function login
    # 匹配: export const foo
    # 匹配: export type User
    # 匹配: export interface User
    re.compile(
        r"^\s*export\s+(?:default\s+)?(?:class|function|const|let|var|interface|type|enum)\s+([A-Za-z_$][\w$]*)",
        re.MULTILINE,
    ),

    # 匹配: export { login, logout }
    re.compile(r"^\s*export\s*\{([^}]+)\}", re.MULTILINE),
]


# Java 公开入口提取规则.
JAVA_EXPORT_PATTERNS = [
    # 匹配 Java: public class UserService
    # 匹配 Java: public interface UserService
    # 匹配 Java: public record UserRequest
    # Java 没有 JS 那种 export, 这里把公开类型当成文件对外入口.
    re.compile(
        r"^\s*public\s+(?:abstract\s+|final\s+|sealed\s+|non-sealed\s+)*"
        r"(?:class|interface|enum|record)\s+([A-Za-z_]\w*)",
        re.MULTILINE,
    ),
]


# JS/TS symbol 提取规则.
JS_SYMBOL_PATTERNS = [
    # JS/TS 函数: function login()
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", re.MULTILINE),

    # JS/TS 类: class UserService
    re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)", re.MULTILINE),

    # TS interface: interface User
    re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z_$][\w$]*)", re.MULTILINE),

    # TS type: type User = ...
    re.compile(r"^\s*(?:export\s+)?type\s+([A-Za-z_$][\w$]*)", re.MULTILINE),

    # TS enum: enum Role
    re.compile(r"^\s*(?:export\s+)?enum\s+([A-Za-z_$][\w$]*)", re.MULTILINE),

    # JS/TS 变量或函数表达式: const login = ...
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)", re.MULTILINE),
]


# Python symbol 提取规则.
PYTHON_SYMBOL_PATTERNS = [
    # Python 函数: def login():
    re.compile(r"^\s*def\s+([A-Za-z_]\w*)", re.MULTILINE),

    # Python 类: class UserService:
    re.compile(r"^\s*class\s+([A-Za-z_]\w*)", re.MULTILINE),
]


# Java symbol 提取规则.
JAVA_SYMBOL_PATTERNS = [
    # Java 类型: class UserService / interface UserService / record UserRequest / enum Role
    re.compile(
        r"^[ \t]*(?:public|protected|private)?[ \t]*"
        r"(?:abstract[ \t]+|final[ \t]+|sealed[ \t]+|non-sealed[ \t]+)*"
        r"(?:class|interface|enum|record)[ \t]+([A-Za-z_]\w*)",
        re.MULTILINE,
    ),

    # Java 方法: public ApiResponse<Card> getCard(...)
    # 也支持接口里的方法: List<Card> findByDeckId(...)
    re.compile(
        r"^[ \t]*(?!(?:if|for|while|switch|catch|return|new|super)\b)"
        r"(?:@[A-Za-z_][\w\.]*(?:\([^)]*\))?[ \t]*)*"
        r"(?:public|protected|private)?[ \t]*"
        r"(?:static[ \t]+|final[ \t]+|abstract[ \t]+|synchronized[ \t]+|native[ \t]+|default[ \t]+)*"
        r"(?:<[^>\n]+>[ \t]*)?"
        r"(?!(?:public|protected|private|if|for|while|switch|catch|return|throw|new|super)\b)"
        r"[A-Za-z_][\w<>\[\], ? extends super\.]*[ \t]+"
        r"([A-Za-z_]\w*)[ \t]*\(",
        re.MULTILINE,
    ),
]


XML_SYMBOL_PATTERNS = [
    # XML/MyBatis 常用定位点: namespace, id, name.
    re.compile(r"\b(?:namespace|id|name)=['\"]([^'\"]+)['\"]"),
]


YAML_SYMBOL_PATTERNS = [
    # YAML key: server:, datasource:, spring:
    re.compile(r"^\s*([A-Za-z_][\w.-]*)\s*:", re.MULTILINE),
]


PROPERTIES_SYMBOL_PATTERNS = [
    # Properties key: spring.datasource.url=...
    re.compile(r"^\s*([A-Za-z_][\w.-]*)\s*[=:]", re.MULTILINE),
]


CSS_SYMBOL_PATTERNS = [
    # CSS selector: .practice-card, #root.
    re.compile(r"(?<![\w-])[.#]([A-Za-z_][\w-]*)"),
]


HTML_SYMBOL_PATTERNS = [
    # HTML 常用定位点: id, class, name.
    re.compile(r"\b(?:id|class|name)=['\"]([^'\"]+)['\"]"),
]


SQL_SYMBOL_PATTERNS = [
    # SQL 常用定位点: 表名.
    re.compile(
        r"\b(?:CREATE\s+TABLE|ALTER\s+TABLE|INSERT\s+INTO|UPDATE|FROM|JOIN)\s+([A-Za-z_][\w.]*)",
        re.IGNORECASE,
    ),
]


MARKDOWN_SYMBOL_PATTERNS = [
    # Markdown 标题作为文档定位点.
    re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", re.MULTILINE),
]


PACKAGE_PATTERN = re.compile(r"^\s*package\s+([\w\.]+)\s*;", re.MULTILINE)


IMPORT_PATTERNS_BY_EXT = {
    **{ext: JS_IMPORT_PATTERNS for ext in JS_LIKE_EXTS},
    **{ext: PYTHON_IMPORT_PATTERNS for ext in PYTHON_EXTS},
    **{ext: JAVA_IMPORT_PATTERNS for ext in JAVA_EXTS},
}


EXPORT_PATTERNS_BY_EXT = {
    **{ext: JS_EXPORT_PATTERNS for ext in JS_LIKE_EXTS},
    **{ext: [] for ext in PYTHON_EXTS},
    **{ext: JAVA_EXPORT_PATTERNS for ext in JAVA_EXTS},
}


SYMBOL_PATTERNS_BY_EXT = {
    **{ext: JS_SYMBOL_PATTERNS for ext in JS_LIKE_EXTS},
    **{ext: PYTHON_SYMBOL_PATTERNS for ext in PYTHON_EXTS},
    **{ext: JAVA_SYMBOL_PATTERNS for ext in JAVA_EXTS},
    **{ext: XML_SYMBOL_PATTERNS for ext in XML_EXTS},
    **{ext: YAML_SYMBOL_PATTERNS for ext in YAML_EXTS},
    **{ext: PROPERTIES_SYMBOL_PATTERNS for ext in PROPERTIES_EXTS},
    **{ext: CSS_SYMBOL_PATTERNS for ext in CSS_EXTS},
    **{ext: HTML_SYMBOL_PATTERNS for ext in HTML_EXTS},
    **{ext: SQL_SYMBOL_PATTERNS for ext in SQL_EXTS},
    **{ext: MARKDOWN_SYMBOL_PATTERNS for ext in MARKDOWN_EXTS},
}


JAVA_SYMBOL_BLOCKLIST = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "new",
    "super",
}


MAX_PROJECT_MAP_ENTRIES = 3
MAX_PROJECT_MAP_KEYWORDS = 12
MAX_BUCKET_KEYWORDS = 60
WORD_PATTERN = re.compile(r"[A-Za-z][a-z]*|[0-9]+")


def should_skip(path: Path) -> bool:
    """
    判断一个路径是否应该跳过.

    path.parts 会把路径拆成一段一段.
    比如:
    node_modules/react/index.js
    会变成:
    ("node_modules", "react", "index.js")

    只要路径里包含 SKIP_DIRS 里的目录名, 就跳过.
    """
    return any(part in SKIP_DIRS for part in path.parts)


def read_text(path: Path) -> str:
    """
    读取文件内容.

    正常按 utf-8 读取.
    如果遇到奇怪编码, 就忽略无法识别的字符.
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def unique(items):
    """
    去重, 但保持原来的顺序.

    比如:
    ["login", "logout", "login"]
    会变成:
    ["login", "logout"]
    """
    result = []
    seen = set()

    for item in items:
        item = item.strip()

        if item and item not in seen:
            seen.add(item)
            result.append(item)

    return result


def bucket_name_for_suffix(suffix: str) -> str:
    """
    把文件后缀转成分桶目录名.

    .jsx 会写到 .project-index/jsx, 避免目录名以点开头变成隐藏目录.
    """
    return suffix.lstrip(".") or "no-ext"


def split_words(value: str):
    """
    把路径和符号拆成适合 AI 搜索的小写关键词.

    例如 CardController 会拆成 card, controller.
    cards 这类复数会归一成 card, 避免关键词列表被同义词撑大.
    """
    words = []

    for raw_part in re.split(r"[^A-Za-z0-9]+", value):
        for match in WORD_PATTERN.findall(raw_part):
            word = match.lower()

            if len(word) > 3 and word.endswith("s"):
                word = word[:-1]

            words.append(word)

    return words


def patterns_for_suffix(patterns_by_ext, suffix: str):
    """
    按文件后缀选择提取规则.

    这样 Python 测试里的 Java 示例文本不会污染 Python 文件自己的地图.
    """
    return patterns_by_ext.get(suffix, [])


def extract_imports(text: str, suffix: str):
    """
    从文件文本里提取 imports.
    """
    imports = []

    for pattern in patterns_for_suffix(IMPORT_PATTERNS_BY_EXT, suffix):
        imports.extend(pattern.findall(text))

    return unique(imports)


def extract_exports(text: str, suffix: str):
    """
    从文件文本里提取 exports.
    """
    exports = []

    for pattern in patterns_for_suffix(EXPORT_PATTERNS_BY_EXT, suffix):
        for match in pattern.findall(text):
            # 有些正则可能返回 tuple, 这里做一下兼容.
            if isinstance(match, tuple):
                match = match[0]

            # 处理 export { a, b, c }
            if "," in match:
                names = []

                for item in match.split(","):
                    # 处理 export { foo as bar }
                    # 这里保留原始名字 foo.
                    name = item.strip().split(" as ")[0].strip()
                    names.append(name)

                exports.extend(names)
            else:
                exports.append(match.strip())

    return unique(exports)


def extract_package(text: str, suffix: str):
    """
    从 Java 文件文本里提取 package.

    package 能帮 AI 先判断这个文件属于 controller, service, mapper 还是 entity.
    非 Java 文件没有 package 时返回 None.
    """
    if suffix not in JAVA_EXTS:
        return None

    match = PACKAGE_PATTERN.search(text)
    return match.group(1) if match else None


def extract_symbols(text: str, suffix: str):
    """
    从文件文本里提取 symbols.
    """
    if suffix in JSON_EXTS:
        return extract_json_symbols(text)

    symbols = []

    for pattern in patterns_for_suffix(SYMBOL_PATTERNS_BY_EXT, suffix):
        symbols.extend(pattern.findall(text))

    if suffix in JAVA_EXTS:
        symbols = [symbol for symbol in symbols if symbol not in JAVA_SYMBOL_BLOCKLIST]

    return unique(symbols)


def extract_json_symbols(text: str):
    """
    从 JSON 文本里提取 key.

    package.json, 配置 JSON 都靠 key 定位, 不用正则猜字符串内容.
    """
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return []

    keys = []
    collect_json_keys(value, keys)
    return unique(keys)


def collect_json_keys(value, keys):
    """
    递归收集 JSON 对象 key.

    列表里的对象也收集, 方便定位数组配置.
    """
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            collect_json_keys(child, keys)
        return

    if isinstance(value, list):
        for child in value:
            collect_json_keys(child, keys)


def build_project_map_entry(path: str, file_info: dict):
    """
    从详细索引里压缩出单个文件的小地图条目.

    小地图只保留第一轮定位要用的信息, 不放 imports 和完整 symbols.
    """
    candidates = []
    candidates.extend(file_info.get("exports", []))
    candidates.extend(file_info.get("symbols", []))
    entries = unique(candidates)[:MAX_PROJECT_MAP_ENTRIES]

    keyword_source = [path, file_info.get("package") or ""]
    keyword_source.extend(file_info.get("exports", []))
    keyword_source.extend(file_info.get("symbols", []))

    keywords = []
    for value in keyword_source:
        keywords.extend(split_words(value))

    return {
        "ext": file_info.get("ext"),
        "lines": file_info.get("lines"),
        "package": file_info.get("package"),
        "entries": entries,
        "keywords": unique(keywords)[:MAX_PROJECT_MAP_KEYWORDS],
    }


def build_project_map(code_index: dict):
    """
    根据详细代码索引生成 AI 首轮读取的小地图.

    project-map.json 用于先定位文件; 分桶 code-index.json 用于二次确认细节.
    """
    files = {}

    for path, file_info in code_index["files"].items():
        files[path] = build_project_map_entry(path, file_info)

    return {
        "generatedAt": code_index["generatedAt"],
        "root": code_index["root"],
        "buckets": build_bucket_manifest(code_index),
        "files": files,
    }


def build_bucket_manifest(code_index: dict):
    """
    生成根地图里的分桶入口.

    根地图用于第一跳定位; 真正细节在各后缀目录的 code-index 和 project-map.
    """
    buckets = {}

    for path, file_info in code_index["files"].items():
        ext = file_info.get("ext") or ""
        name = bucket_name_for_suffix(ext)
        bucket = buckets.setdefault(
            name,
            {
                "ext": ext,
                "files": 0,
                "codeIndex": f"{name}/code-index.json",
                "projectMap": f"{name}/project-map.json",
                "keywords": [],
            },
        )

        bucket["files"] += 1
        bucket["keywords"].extend(split_words(path))
        bucket["keywords"].extend(split_words(file_info.get("package") or ""))

        for value in file_info.get("exports", []):
            bucket["keywords"].extend(split_words(value))

        for value in file_info.get("symbols", []):
            bucket["keywords"].extend(split_words(value))

    for bucket in buckets.values():
        bucket["keywords"] = unique(bucket["keywords"])[:MAX_BUCKET_KEYWORDS]

    return dict(sorted(buckets.items()))


def build_bucket_indexes(code_index: dict):
    """
    按文件后缀拆分详细索引.

    每个后缀目录都有自己的 code-index.json 和 project-map.json.
    """
    buckets = {}

    for path, file_info in code_index["files"].items():
        name = bucket_name_for_suffix(file_info.get("ext") or "")
        files = buckets.setdefault(name, {})
        files[path] = file_info

    result = {}
    for name, files in buckets.items():
        result[name] = {
            "generatedAt": code_index["generatedAt"],
            "root": code_index["root"],
            "ext": files[next(iter(files))].get("ext"),
            "files": dict(sorted(files.items())),
        }

    return dict(sorted(result.items()))


def build_index():
    """
    构建整个项目的代码索引.
    """
    files = {}

    # ROOT.rglob("*") 会递归遍历项目里的所有文件和目录.
    for path in ROOT.rglob("*"):
        # 只处理文件, 不处理目录.
        if not path.is_file():
            continue

        # 转成相对于项目根目录的路径.
        # 比如:
        # /home/me/project/src/a.ts
        # 变成:
        # src/a.ts
        rel = path.relative_to(ROOT)

        # 跳过 node_modules, .git 等目录.
        if should_skip(rel):
            continue

        # 只处理指定后缀的文本文件.
        if path.suffix not in INDEX_EXTS:
            continue

        # 读取文件内容.
        text = read_text(path)

        # 写入索引.
        files[str(rel)] = {
            "ext": path.suffix,
            "lines": text.count("\n") + 1,
            "package": extract_package(text, path.suffix),
            "imports": extract_imports(text, path.suffix),
            "exports": extract_exports(text, path.suffix),
            "symbols": extract_symbols(text, path.suffix),
        }

    return {
        # 生成时间.
        "generatedAt": datetime.now(timezone.utc).isoformat(),

        # 项目根目录.
        "root": str(ROOT),

        # 文件索引.
        # sorted 是为了让输出顺序稳定, 方便 git diff.
        "files": dict(sorted(files.items())),
    }


def main():
    """
    脚本入口.
    """
    # 确保 .project-index 目录存在.
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 构建索引.
    index = build_index()
    project_map = build_project_map(index)
    bucket_indexes = build_bucket_indexes(index)

    # 写入小地图.
    MAP_FILE.write_text(
        json.dumps(project_map, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 按后缀写入分桶索引.
    for bucket_name, bucket_index in bucket_indexes.items():
        bucket_dir = OUT_DIR / bucket_name
        bucket_dir.mkdir(parents=True, exist_ok=True)

        bucket_code_index = bucket_dir / "code-index.json"
        bucket_project_map = bucket_dir / "project-map.json"
        bucket_project_map_data = build_project_map(bucket_index)

        bucket_code_index.write_text(
            json.dumps(bucket_index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        bucket_project_map.write_text(
            json.dumps(bucket_project_map_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # 告诉你写到哪里了.
    print(f"wrote {MAP_FILE}")


if __name__ == "__main__":
    main()
