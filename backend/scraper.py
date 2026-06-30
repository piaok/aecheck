import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
import time
import ssl
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
})

query_cache = {}

def validate_result(result: Dict, input_number: str) -> bool:
    if not result.get('standard_name'):
        return False
    
    std_name = result.get('standard_name', '')
    if len(std_name) < 5:
        return False
    
    # 过滤通用页面文本
    blacklist = ['没有您要找', '通知', '在此检索', '收录现行', '强制性', '推荐性', '指导性技术文件',
                 '本系统收录', '有效强制性', '有效推荐性', '国家标准全文', '标准分类', 'GB强制性', 'GB/T推荐性']
    for kw in blacklist:
        if kw in std_name:
            return False
    
    # 检查返回的标准号是否与查询的标准号一致
    result_number = result.get('standard_number', '').replace(' ', '').upper()
    input_clean = input_number.replace(' ', '').upper()
    
    # 标准号必须匹配（去掉年份后比较）
    result_prefix = re.sub(r'[\-\.]?\d{4}$', '', result_number)
    input_prefix = re.sub(r'[\-\.]?\d{4}$', '', input_clean)
    
    # 必须都有数字前缀才算匹配（排除纯中文名称）
    if not re.search(r'\d', result_prefix) or not re.search(r'\d', input_prefix):
        return False
    
    if result_prefix != input_prefix:
        return False
    
    return True

def extract_std_name_from_html(html_text: str, std_no: str) -> tuple:
    """返回 (name, extracted_number) 或 (None, None)"""
    candidates = []  # (name, extracted_std_no) tuples
    
    std_no_clean = std_no.replace(' ', '').upper()
    
    # 提取标准号前缀（去掉年份）
    std_prefix = re.sub(r'[\-\.]?\d{4}$', '', std_no_clean)
    
    # 正则匹配标准号+名称对
    all_std_pattern = r'(GB\s?\d+[\-\.]?\d*\-?\d{2,4}|GB/T\s?\d+[\-\.]?\d*\-?\d{2,4}|JGJ\s?\d+[\-\.]?\d*\-?\d{2,4}|JC/T\s?\d+[\-\.]?\d*\-?\d{2,4}|CECS\s?\d+:?\d*\-?\d{2,4})'
    
    # 在HTML中查找标准号及其附近的名称
    for m in re.finditer(all_std_pattern, html_text, re.IGNORECASE):
        found_no = m.group(1).replace(' ', '').upper()
        found_prefix = re.sub(r'[\-\.]?\d{4}$', '', found_no)
        
        # 在标准号附近200字符内查找名称
        start = max(0, m.start() - 200)
        end = min(len(html_text), m.end() + 200)
        context = html_text[start:end]
        
        name_match = re.search(r'《([^》]+)》', context)
        if name_match:
            name = name_match.group(1).strip()
            if found_prefix == std_prefix:
                candidates.append((name, m.group(1).strip()))
    
    # searchSWithWord 调用
    for m in re.finditer(r"searchSWithWord\(['\"]([^'\"]+)['\"]\)", html_text):
        text = m.group(1)
        if len(text) > 5:
            candidates.append((text, ''))
    
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # 从页面标题提取
    generic_titles = ['国家标准全文公开', '全国标准信息公共服务平台', '标准分类']
    for tag in soup.find_all(['h1', 'h2', 'h3', 'title', 'caption']):
        text = tag.get_text(strip=True)
        if len(text) > 10 and ('规范' in text or '标准' in text or '规程' in text):
            text = text.replace('国家标准全文公开', '').replace('全国标准信息公共服务平台', '').strip()
            is_generic = any(text == gt or text.startswith(gt) or len(text) < 10 for gt in generic_titles)
            if is_generic:
                continue
            if std_prefix in text.replace(' ', '').upper() or std_no_clean[:8] in text.replace(' ', '').upper():
                candidates.append((text, ''))
    
    # 从表格行提取
    for tr in soup.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) >= 2:
            row_text = ' '.join(td.get_text(strip=True) for td in tds)
            if std_prefix in row_text.replace(' ', '').upper() or std_no_clean[:8] in row_text.replace(' ', '').upper():
                # 提取行中的标准号
                row_std_match = re.search(all_std_pattern, row_text, re.IGNORECASE)
                row_std_no = row_std_match.group(1).strip() if row_std_match else ''
                for td in tds:
                    td_text = td.get_text(strip=True)
                    if len(td_text) > 5 and ('规范' in td_text or '标准' in td_text or '规程' in td_text):
                        candidates.append((td_text, row_std_no))
    
    if not candidates:
        return None, None
    
    # 优先选择标准号前缀匹配的候选
    for name, extracted_no in candidates:
        if extracted_no:
            extracted_prefix = re.sub(r'[\-\.]?\d{4}$', '', extracted_no.replace(' ', '').upper())
            if extracted_prefix == std_prefix:
                return name, extracted_no
    
    # 其次选择名称中包含标准号前缀的候选
    for name, extracted_no in candidates:
        if std_prefix in name.replace(' ', '').upper():
            return name, extracted_no
    
    return None, None

def _try_extract_and_validate(html_text: str, standard_number: str, source: str, session_obj=None) -> Optional[Dict]:
    """从HTML提取标准名称，验证后返回结果字典"""
    std_no_clean = standard_number.replace(' ', '').upper()
    std_name, extracted_no = extract_std_name_from_html(html_text, std_no_clean)
    
    if not std_name:
        return None
    
    # 如果提取到了标准号，验证是否匹配
    if extracted_no:
        extracted_clean = extracted_no.replace(' ', '').upper()
        extracted_prefix = re.sub(r'[\-\.]?\d{4}$', '', extracted_clean)
        input_prefix = re.sub(r'[\-\.]?\d{4}$', '', std_no_clean)
        if extracted_prefix != input_prefix:
            return None
    
    return {
        'source': source,
        'standard_number': standard_number,
        'standard_name': std_name,
        'status': '现行',
        'message': '在线查询成功',
        'replace_by': '',
    }

def query_std_samr(standard_number: str) -> Optional[Dict]:
    """全国标准信息公共服务平台查询"""
    try:
        std_no_clean = standard_number.replace(' ', '').upper()
        
        # 尝试多种URL格式
        urls = [
            f"https://openstd.samr.gov.cn/bzgk/std/gbDetailed?id={std_no_clean}",
            f"https://openstd.samr.gov.cn/bzgk/std/search?q={standard_number.replace(' ', '%20')}",
        ]
        
        for url in urls:
            try:
                response = session.get(url, timeout=10, verify=True)
                
                if response.status_code == 200 and len(response.text) > 1000:
                    result = _try_extract_and_validate(response.text, standard_number, '全国标准信息公共服务平台')
                    if result:
                        return result
            except Exception:
                continue
        
        return None
        
    except Exception:
        return None

def query_bzw(standard_number: str) -> Optional[Dict]:
    """标准信息网查询"""
    try:
        std_no_clean = standard_number.replace(' ', '')
        
        url = f'http://www.bzw.com.cn/standard/GB-{std_no_clean.replace("GB", "")}.htm'
        response = session.get(url, timeout=10)
        
        if response.status_code == 200 and len(response.text) > 1000:
            result = _try_extract_and_validate(response.text, standard_number, '标准信息网')
            if result:
                return result
        
        return None
        
    except Exception:
        return None

def query_std_info(standard_number: str) -> Optional[Dict]:
    """标准查询网"""
    try:
        std_no_clean = standard_number.replace(' ', '')
        
        url = f'http://www.std-info.com/standard/{std_no_clean}.html'
        response = session.get(url, timeout=10)
        
        if response.status_code == 200 and len(response.text) > 1000:
            result = _try_extract_and_validate(response.text, standard_number, '标准查询网')
            if result:
                return result
        
        return None
        
    except Exception:
        return None

def query_openstd_api(standard_number: str) -> Optional[Dict]:
    """全国标准信息公共服务平台API查询"""
    try:
        std_no_clean = standard_number.replace(' ', '').upper()
        
        api_urls = [
            f'https://openstd.samr.gov.cn/api/std/search?q={std_no_clean}',
            f'https://openstd.samr.gov.cn/bzgk/std/search?q={std_no_clean}',
        ]
        
        for api_url in api_urls:
            try:
                response = session.get(api_url, timeout=10)
                
                if response.status_code == 200 and len(response.text) > 1000:
                    result = _try_extract_and_validate(response.text, standard_number, '全国标准信息公共服务平台')
                    if result:
                        return result
            except Exception:
                continue
        
        return None
        
    except Exception:
        return None

def query_jianbiaoku(standard_number: str) -> Optional[Dict]:
    """建标库查询（支持行标、地标等）"""
    try:
        std_no_clean = standard_number.replace(' ', '').upper()
        
        url = f'https://www.jianbiaoku.com/webarbs/book/{std_no_clean}/'
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200 and len(response.text) > 1000:
                result = _try_extract_and_validate(response.text, standard_number, '建标库')
                if result:
                    return result
        except Exception:
            pass
        
        search_url = f'https://www.jianbiaoku.com/search?keyword={standard_number.replace(" ", "+")}'
        try:
            response = session.get(search_url, timeout=10)
            if response.status_code == 200 and len(response.text) > 1000:
                result = _try_extract_and_validate(response.text, standard_number, '建标库')
                if result:
                    return result
        except Exception:
            pass
        
        return None
    except Exception:
        return None

def query_ccgb(standard_number: str) -> Optional[Dict]:
    """中国工程建设标准化网查询（CECS标准）"""
    try:
        std_no_clean = standard_number.replace(' ', '').upper()
        
        url = f'http://www.ccsn.org.cn/ccsn/zcfl/{std_no_clean}.html'
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200 and len(response.text) > 1000:
                result = _try_extract_and_validate(response.text, standard_number, '中国工程建设标准化网')
                if result:
                    return result
        except Exception:
            pass
        
        return None
    except Exception:
        return None

def query_online(standard_number: str) -> Optional[Dict]:
    """综合在线查询"""
    if standard_number in query_cache:
        return query_cache[standard_number]
    
    # 第一梯队：HTTP直接查询（快）
    queries = [
        query_std_samr,
        query_openstd_api,
        query_jianbiaoku,
        query_bzw,
        query_std_info,
        query_ccgb,
    ]
    
    for query_func in queries:
        try:
            result = query_func(standard_number)
            if result:
                query_cache[standard_number] = result
                return result
        except Exception:
            pass
        time.sleep(0.3)
    
    # 第二梯队：浏览器查询（慢但更可靠）
    try:
        from scraper_browser import query_jianbiaoku_browser, query_csres_browser, query_openstd_browser
        for browser_func in [query_jianbiaoku_browser, query_csres_browser, query_openstd_browser]:
            try:
                result = browser_func(standard_number)
                if result:
                    query_cache[standard_number] = result
                    return result
            except Exception:
                pass
            time.sleep(0.5)
    except ImportError:
        pass
    
    return None