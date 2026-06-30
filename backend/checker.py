import re
from database import db
from schemas import CheckResult
from scraper import query_online
from typing import Tuple, List, Optional, Dict, Any

def check_standard_with_logs(input_number: str, input_name: str, online: bool = False) -> Tuple[CheckResult, List[str], Optional[dict]]:
    logs = []
    input_number_clean = re.sub(r'\s+', '', input_number).upper()

    logs.append(f"  📖 查询本地数据库...")

    matched_standard = None
    matched_percentage = 0

    matched_standard = db.find_exact_match(input_number)

    if matched_standard:
        matched_percentage = 100.0
        logs.append(f"  ✓ 本地数据库找到精确匹配: {matched_standard['standard_number']}")
    else:
        prefix = input_number_clean[:8]
        similar_standards = db.search_by_number_prefix(prefix, limit=10)

        for standard in similar_standards:
            db_number_clean = re.sub(r'\s+', '', standard['standard_number']).upper()
            if input_number_clean in db_number_clean or db_number_clean in input_number_clean:
                similarity = min(len(input_number_clean), len(db_number_clean)) / max(len(input_number_clean), len(db_number_clean)) * 100
                if similarity > matched_percentage:
                    matched_percentage = similarity
                    matched_standard = standard

        if matched_standard:
            logs.append(f"  ✓ 本地数据库找到相似匹配: {matched_standard['standard_number']} ({matched_percentage:.0f}%)")
        else:
            logs.append(f"  ✗ 本地数据库未找到匹配")

    online_result = None
    update_suggestion = None

    if online:
        logs.append(f"  🌐 开始在线查询...")
        online_result = query_online(input_number)
        if online_result:
            logs.append(f"  ✓ 在线查询成功: {online_result.get('source', '未知来源')}")
            logs.append(f"    - 名称: {online_result.get('standard_name', '未知')}")
            logs.append(f"    - 状态: {online_result.get('status', '未知')}")

            existing = db.find_exact_match(input_number)

            if existing:
                changes = []
                if online_result.get('standard_name') and existing['standard_name'] != online_result.get('standard_name'):
                    changes.append(f"名称: {existing['standard_name']} -> {online_result.get('standard_name')}")
                if online_result.get('status') and existing['status'] != online_result.get('status'):
                    changes.append(f"状态: {existing['status']} -> {online_result.get('status')}")
                if online_result.get('replace_by') and existing.get('replace_by') != online_result.get('replace_by'):
                    changes.append(f"替代标准: {existing.get('replace_by') or '无'} -> {online_result.get('replace_by')}")

                if changes:
                    logs.append(f"  ⚠️ 在线查询发现差异，建议更新:")
                    for change in changes:
                        logs.append(f"    - {change}")
                    update_suggestion = {
                        'action': 'update',
                        'id': existing['id'],
                        'changes': changes,
                        'data': online_result,
                    }
            else:
                logs.append(f"  ⚠️ 在线查询找到新规范，建议添加到数据库")
                update_suggestion = {
                    'action': 'create',
                    'data': online_result,
                }
        else:
            logs.append(f"  ✗ 在线查询失败，所有平台均无响应")

    if online_result and matched_standard:
        matched_percentage = 100.0
    elif online_result and not matched_standard:
        matched_percentage = 100.0
        matched_standard = {
            'standard_number': online_result.get('standard_number', input_number),
            'standard_name': online_result.get('standard_name', ''),
            'status': online_result.get('status', '未知'),
            'source': online_result.get('source', '在线查询'),
            'replace_by': online_result.get('replace_by', ''),
        }

    if not matched_standard:
        logs.append(f"  ❌ 校验失败: 未找到匹配的规范")
        return CheckResult(
            id=0,
            input_number=input_number,
            input_name=input_name,
            matched_number=None,
            matched_name=None,
            status="规范名称错误",
            matched_percentage=0,
            message="未找到匹配的规范，请检查标准号是否正确"
        ), logs, update_suggestion

    if '废止' in matched_standard['status'] or '过期' in matched_standard['status']:
        logs.append(f"  ⚠️ 规范已过期")
        return CheckResult(
            id=0,
            input_number=input_number,
            input_name=input_name,
            matched_number=matched_standard['standard_number'],
            matched_name=matched_standard['standard_name'],
            status="规范已过期",
            matched_percentage=matched_percentage,
            message=f"该规范已过期，被 {matched_standard.get('replace_by')} 替代" if matched_standard.get('replace_by') else "该规范已过期"
        ), logs, update_suggestion

    if matched_percentage == 100.0:
        if input_name and matched_standard['standard_name']:
            name_similarity = calculate_name_similarity(input_name, matched_standard['standard_name'])
            if name_similarity >= 60:
                logs.append(f"  ✅ 校验通过: 标准号和名称均匹配")
                return CheckResult(
                    id=0,
                    input_number=input_number,
                    input_name=input_name,
                    matched_number=matched_standard['standard_number'],
                    matched_name=matched_standard['standard_name'],
                    status="正确",
                    matched_percentage=100.0,
                    message="规范校验通过"
                ), logs, update_suggestion
            else:
                logs.append(f"  ⚠️ 名称相似度较低 ({name_similarity:.0f}%)")
                return CheckResult(
                    id=0,
                    input_number=input_number,
                    input_name=input_name,
                    matched_number=matched_standard['standard_number'],
                    matched_name=matched_standard['standard_name'],
                    status="名称/版本不一致",
                    matched_percentage=matched_percentage,
                    message=f"标准号匹配，但名称相似度较低（{name_similarity:.1f}%）"
                ), logs, update_suggestion
        else:
            logs.append(f"  ✅ 校验通过")
            return CheckResult(
                id=0,
                input_number=input_number,
                input_name=input_name,
                matched_number=matched_standard['standard_number'],
                matched_name=matched_standard['standard_name'],
                status="正确",
                matched_percentage=100.0,
                message="规范校验通过"
            ), logs, update_suggestion
    else:
        logs.append(f"  ⚠️ 标准号不完全匹配")
        return CheckResult(
            id=0,
            input_number=input_number,
            input_name=input_name,
            matched_number=matched_standard['standard_number'],
            matched_name=matched_standard['standard_name'],
            status="规范标准号错误",
            matched_percentage=matched_percentage,
            message=f"标准号不完全匹配，建议核对标准号"
        ), logs, update_suggestion

def calculate_name_similarity(name1: str, name2: str) -> float:
    name1_clean = re.sub(r'[\s\-/]+', '', name1).lower()
    name2_clean = re.sub(r'[\s\-/]+', '', name2).lower()

    if not name1_clean or not name2_clean:
        return 0

    intersection = set(name1_clean) & set(name2_clean)
    union = set(name1_clean) | set(name2_clean)

    if not union:
        return 0

    return len(intersection) / len(union) * 100
