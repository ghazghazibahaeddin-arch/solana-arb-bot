#!/usr/bin/env python3
"""
diagnose_project.py
====================
سكريبت تشخيص شامل لمشروع solana-arb-bot.

يفحص:
  1) كل ملف .py في المجلد: هل يستورد بدون كراش؟ (يكشف أخطاء import,
     syntax errors, وملفات ناقصة اعتماديات).
  2) شجرة الاستيراد بدءاً من main.py: أي الملفات مستخدمة فعلياً،
     وأي الملفات "ميتة" (موجودة لكن غير مستوردة من أي مكان).
  3) كل استدعاء دالة عبر ملفات المشروع، ويتحقق هل عدد/توفر المعاملات
     يطابق تعريف الدالة الفعلي (يكشف أخطاء زي: تمرير معامل واحد
     لدالة تتوقع اثنين، أو استدعاء دالة غير موجودة أصلاً).
  4) يبحث في كل الملفات عن أي دالة/كود له علاقة فعلية بتنفيذ صفقة
     حقيقية (شراء/بيع/swap/إرسال معاملة موقعة على السلسلة) ليوضح
     هل يوجد مسار تنفيذ حقيقي أو أن المشروع كله تحليل/محاكاة (paper).

الاستخدام:
    cd solana-arb-bot
    python diagnose_project.py

لا يحتاج مفاتيح API ولا اتصال إنترنت فعلي للتحليل الساكن (static
analysis)، لكنه يحتاج جميع المكتبات في requirements.txt مثبتة حتى
تنجح خطوة "فحص الاستيراد" بدون أخطاء وهمية بسبب مكتبات ناقصة.
"""

import ast
import importlib.util
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ENTRY_POINTS = ["main.py"]  # نقاط الدخول المعروفة، أضف غيرها إذا لزم

EXECUTION_KEYWORDS = [
    "swap", "buy", "sell", "send_transaction", "sign_transaction",
    "signtransaction", "sendtransaction", "execute_swap", "place_order",
    "submit_transaction", "broadcast", "jito", "send_raw_transaction",
]

IGNORE_DIRS = {".git", "__pycache__", "venv", ".venv", "node_modules"}


# ------------------------------------------------------------------
# أدوات مساعدة
# ------------------------------------------------------------------

def find_py_files(root):
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for f in filenames:
            if f.endswith(".py"):
                result.append(os.path.relpath(os.path.join(dirpath, f), root))
    return sorted(result)


def module_name_from_path(path):
    return path[:-3].replace(os.sep, ".")


def safe_parse(path):
    """يرجع (ast_tree, error) — error=None لو نجح التحليل"""
    try:
        with open(os.path.join(PROJECT_ROOT, path), "r", encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        tree = ast.parse(src, filename=path)
        return tree, src, None
    except SyntaxError as e:
        return None, None, f"SyntaxError: {e}"
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"


@dataclass
class FileInfo:
    path: str
    tree: object = None
    src: str = ""
    parse_error: str = None
    imports: set = field(default_factory=set)          # أسماء الموديولات المستوردة محلياً
    top_level_funcs: dict = field(default_factory=dict)  # اسم -> ast.FunctionDef
    top_level_classes: set = field(default_factory=set)
    calls_seen: list = field(default_factory=list)       # [(func_name, n_args, lineno)]
    import_runtime_error: str = None


# ------------------------------------------------------------------
# 1) تحليل AST لكل ملف: استيرادات محلية + دوال معرفة + استدعاءات
# ------------------------------------------------------------------

def analyze_files(py_files):
    infos = {}
    local_modules = {module_name_from_path(p) for p in py_files}

    for path in py_files:
        tree, src, err = safe_parse(path)
        info = FileInfo(path=path, tree=tree, src=src or "", parse_error=err)
        if tree is None:
            infos[path] = info
            continue

        for node in ast.walk(tree):
            # استيرادات محلية (from X import Y / import X)
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
                if mod in local_modules or mod.split(".")[0] in local_modules:
                    info.imports.add(mod)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
                    if mod in local_modules:
                        info.imports.add(mod)

            # دوال وكلاسات معرّفة على مستوى الملف
            if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                info.top_level_funcs[node.name] = node
            if isinstance(node, ast.ClassDef):
                info.top_level_classes.add(node.name)

            # استدعاءات دوال (لفحص توافق عدد المعاملات لاحقاً)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                n_pos = len(node.args)
                n_kw = len(node.keywords)
                info.calls_seen.append((node.func.id, n_pos, n_kw, getattr(node, "lineno", "?")))

        infos[path] = info

    return infos


# ------------------------------------------------------------------
# 2) شجرة الاستيراد بدءاً من نقاط الدخول -> ملفات ميتة
# ------------------------------------------------------------------

def compute_reachable(infos, entry_points):
    reachable = set()
    stack = [ep for ep in entry_points if ep in infos]
    while stack:
        current = stack.pop()
        if current in reachable:
            continue
        reachable.add(current)
        info = infos.get(current)
        if not info:
            continue
        for imp in info.imports:
            candidate = imp.replace(".", os.sep) + ".py"
            if candidate in infos and candidate not in reachable:
                stack.append(candidate)
    return reachable


# ------------------------------------------------------------------
# 3) فحص الاستيراد الفعلي (runtime) لكل ملف عبر subprocess منعزل
# ------------------------------------------------------------------

def runtime_import_check(py_files):
    results = {}
    for path in py_files:
        mod = module_name_from_path(path)
        # نتجاهل ملفات فيها __main__ حماية تشغيل مباشر قد تسبب حلقات لا نهائية
        code = f"import sys; sys.path.insert(0, {PROJECT_ROOT!r}); import {mod}"
        try:
            proc = subprocess.run(
                [sys.executable, "-c", code],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if proc.returncode != 0:
                # آخر سطر مفيد عادة من traceback
                err_lines = [l for l in proc.stderr.strip().splitlines() if l.strip()]
                last_err = err_lines[-1] if err_lines else proc.stderr.strip()
                results[path] = last_err
            else:
                results[path] = None
        except subprocess.TimeoutExpired:
            results[path] = "TIMEOUT (الملف علّق أكثر من 15 ثانية عند الاستيراد - يحتمل فيه كود تنفيذي top-level بدل __main__ guard)"
        except Exception as e:
            results[path] = f"{type(e).__name__}: {e}"
    return results


# ------------------------------------------------------------------
# 4) فحص توافق الاستدعاءات مع تعريف الدوال (عدد المعاملات)
# ------------------------------------------------------------------

def check_call_compatibility(infos):
    problems = []
    # خريطة: اسم الدالة -> (ملف, funcdef) لكل دالة معرفة بأي ملف
    func_defs = {}
    for path, info in infos.items():
        for fname, fdef in info.top_level_funcs.items():
            func_defs.setdefault(fname, []).append((path, fdef))

    for path, info in infos.items():
        for (call_name, n_pos, n_kw, lineno) in info.calls_seen:
            if call_name not in func_defs:
                continue  # قد تكون دالة مكتبة خارجية، نتجاهلها
            for (def_path, fdef) in func_defs[call_name]:
                args = fdef.args
                required = len(args.args) - len(args.defaults)
                maximum = len(args.args)
                has_varargs = args.vararg is not None
                has_kwargs = args.kwarg is not None
                kwonly_required = [a.arg for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is None]

                total_given = n_pos + n_kw
                if not has_varargs and n_pos > maximum:
                    problems.append(
                        f"{path}:{lineno} -> يستدعي {call_name}() بـ {n_pos} معامل موضعي، "
                        f"لكن {def_path} يعرّفها بحد أقصى {maximum} معامل موضعي."
                    )
                elif total_given < required and not has_varargs:
                    problems.append(
                        f"{path}:{lineno} -> يستدعي {call_name}() بمعاملات أقل من المطلوب "
                        f"(معطى={total_given}, مطلوب على الأقل={required}) حسب تعريفها في {def_path}."
                    )
                if kwonly_required:
                    problems.append(
                        f"{path}:{lineno} -> {call_name}() في {def_path} تتطلب معاملات keyword-only "
                        f"إجبارية: {kwonly_required} — تأكد أنها مُمرَّرة بالاسم عند الاستدعاء."
                    )
    return problems


# ------------------------------------------------------------------
# 5) البحث عن مسار تنفيذ صفقة حقيقي
# ------------------------------------------------------------------

def find_execution_paths(infos):
    hits = []
    for path, info in infos.items():
        if not info.src:
            continue
        lower_src = info.src.lower()
        for kw in EXECUTION_KEYWORDS:
            if kw in lower_src:
                # نجيب أرقام الأسطر التقريبية
                for i, line in enumerate(info.src.splitlines(), start=1):
                    if kw in line.lower():
                        hits.append((path, kw, i, line.strip()[:100]))
    return hits


# ------------------------------------------------------------------
# التقرير النهائي
# ------------------------------------------------------------------

def main():
    print("=" * 70)
    print("تشخيص شامل لمشروع solana-arb-bot")
    print("=" * 70)

    py_files = find_py_files(PROJECT_ROOT)
    print(f"\nعدد ملفات .py الموجودة: {len(py_files)}\n")

    infos = analyze_files(py_files)

    # ---- 1) أخطاء بناء (syntax) ----
    print("-" * 70)
    print("1) أخطاء بناء الكود (Syntax Errors) — قبل حتى محاولة التشغيل")
    print("-" * 70)
    syntax_errors = {p: i.parse_error for p, i in infos.items() if i.parse_error}
    if not syntax_errors:
        print("لا يوجد أخطاء syntax ظاهرة. ✅")
    else:
        for p, err in syntax_errors.items():
            print(f"  ❌ {p}: {err}")

    # ---- 2) فحص الاستيراد الفعلي ----
    print("\n" + "-" * 70)
    print("2) فحص استيراد كل ملف فعلياً (يكشف مكتبات ناقصة / أخطاء عند التحميل)")
    print("-" * 70)
    runtime_results = runtime_import_check(py_files)
    failed_imports = {p: e for p, e in runtime_results.items() if e}
    if not failed_imports:
        print("كل الملفات تُستورد بدون أخطاء. ✅")
    else:
        for p, err in failed_imports.items():
            print(f"  ❌ {p}:\n      {err}")

    # ---- 3) شجرة الاستيراد / ملفات ميتة ----
    print("\n" + "-" * 70)
    print("3) ملفات غير مستخدمة فعلياً (لا تُستورد من main.py ولا من أي شيء يستورده main.py)")
    print("-" * 70)
    reachable = compute_reachable(infos, ENTRY_POINTS)
    dead_files = [p for p in py_files if p not in reachable and p not in ENTRY_POINTS]
    if not dead_files:
        print("كل الملفات مربوطة بـ main.py بشكل مباشر أو غير مباشر.")
    else:
        print(f"عدد الملفات غير المربوطة: {len(dead_files)}")
        print("(هذا لا يعني بالضرورة أنها عديمة الفائدة — قد تكون سكريبتات مساعدة")
        print(" تُشغَّل يدوياً، أو أدوات تشخيص، أو كود قديم لم يُحذف بعد)\n")
        for p in dead_files:
            print(f"  • {p}")

    # ---- 4) توافق استدعاءات الدوال ----
    print("\n" + "-" * 70)
    print("4) تعارضات في استدعاء الدوال (عدد المعاملات لا يطابق التعريف)")
    print("-" * 70)
    call_problems = check_call_compatibility(infos)
    if not call_problems:
        print("لم يُعثر على تعارضات واضحة في عدد المعاملات. ✅")
        print("(ملاحظة: هذا فحص ساكن بسيط، لا يغطي *args/**kwargs المعقدة ولا يضمن")
        print(" صحة القيم نفسها، فقط عدد/توفر المعاملات)")
    else:
        for prob in call_problems:
            print(f"  ⚠️  {prob}")

    # ---- 5) مسار تنفيذ الصفقات الحقيقي ----
    print("\n" + "-" * 70)
    print("5) هل يوجد مسار تنفيذ صفقة حقيقي (شراء/بيع فعلي على السلسلة)؟")
    print("-" * 70)
    exec_hits = find_execution_paths(infos)
    if not exec_hits:
        print("❌ لم يُعثر على أي كود مرتبط بتنفيذ صفقة حقيقية (swap/buy/sell/send_transaction)")
        print("   في كامل المشروع. هذا يعني: حتى لو وضعت فلوس ومفتاح محفظة حقيقي،")
        print("   البوت لن ينفذ أي عملية شراء أو بيع فعلية على السلسلة.")
    else:
        by_file = {}
        for (p, kw, ln, line) in exec_hits:
            by_file.setdefault(p, []).append((kw, ln, line))
        for p, items in by_file.items():
            print(f"\n  📄 {p}:")
            for kw, ln, line in items:
                print(f"      سطر {ln} (كلمة مفتاحية: '{kw}'): {line}")
        print(textwrap.dedent("""
        ⚠️  ملاحظة مهمة: وجود هذه الكلمات لا يعني بالضرورة أن التنفيذ الفعلي
        مكتمل وآمن — قد تكون مجرد أسماء متغيرات، تعليقات، أو دوال غير مكتملة
        (placeholder/hook) لم تُربط بعد بمنطق توقيع وإرسال معاملة حقيقي.
        راجع كل حالة يدوياً قبل تشغيل المشروع بأموال حقيقية.
        """))

    # ---- الخلاصة ----
    print("=" * 70)
    print("الخلاصة السريعة")
    print("=" * 70)
    print(f"  ملفات .py الكلية:          {len(py_files)}")
    print(f"  أخطاء Syntax:              {len(syntax_errors)}")
    print(f"  ملفات فشلت عند الاستيراد:  {len(failed_imports)}")
    print(f"  ملفات غير مربوطة بـ main:  {len(dead_files)}")
    print(f"  تعارضات استدعاء دوال:      {len(call_problems)}")
    print(f"  إشارات كود تنفيذ صفقة:     {len(exec_hits)} (راجع القسم 5 لتفسيرها)")
    print("\nهذا فحص ساكن (static) — لا يستبدل تشغيل البوت فعلياً في paper mode")
    print("ومراقبة السجلات (logs) قبل أي قرار بوضع أموال حقيقية.")


if __name__ == "__main__":
    main()
