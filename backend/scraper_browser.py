"""基于 Playwright 浏览器的在线查询模块"""
import re
import time
from typing import Optional, Dict
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

_browser = None
_context = None

def _get_browser():
    global _browser, _context
    if _browser is None or not _browser.is_connected():
        pw = sync_playwright().start()
        _browser = pw.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-background-networking',
            ]
        )
        _context = _browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True,
        )
    return _context

def close_browser():
    global _browser, _context
    if _browser:
        try:
            _browser.close()
        except Exception:
            pass
        _browser = None
        _context = None

def query_csres_browser(standard_number: str) -> Optional[Dict]:
    """工标网浏览器查询"""
    try:
        ctx = _get_browser()
        page = ctx.new_page()

        # 搜索页面
        search_url = f'https://www.csres.com/s.html?q={standard_number.replace(" ", "+")}'
        page.goto(search_url, timeout=20000, wait_until='domcontentloaded')
        time.sleep(2)

        # 等待搜索结果
        try:
            page.wait_for_selector('.result-list, .search-result, table, .list', timeout=10000)
        except PwTimeout:
            pass

        html = page.content()
        page.close()

        # 解析结果
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        std_no_clean = standard_number.replace(' ', '').upper()
        std_prefix = re.sub(r'[\-\.]?\d{4}$', '', std_no_clean)

        # 在页面中查找匹配的标准号和名称
        # 工标网搜索结果通常在表格或列表中
        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            row_text = ' '.join(td.get_text(strip=True) for td in tds)
            if std_prefix in row_text.replace(' ', '').upper() or std_no_clean[:8] in row_text.replace(' ', '').upper():
                for td in tds:
                    td_text = td.get_text(strip=True)
                    if len(td_text) > 5 and ('规范' in td_text or '标准' in td_text or '规程' in td_text):
                        # 提取行中的标准号
                        row_std = re.search(r'(GB\s?\d+[\-\.]?\d*\-?\d{2,4}|GB/T\s?\d+[\-\.]?\d*\-?\d{2,4}|JGJ\s?\d+[\-\.]?\d*\-?\d{2,4}|JC/T\s?\d+[\-\.]?\d*\-?\d{2,4}|CECS\s?\d+:?\d*\-?\d{2,4})', row_text, re.IGNORECASE)
                        if row_std:
                            extracted = row_std.group(1).replace(' ', '').upper()
                            extracted_prefix = re.sub(r'[\-\.]?\d{4}$', '', extracted)
                            if extracted_prefix == std_prefix:
                                # 检查状态
                                status = '现行'
                                if '废止' in row_text or '被代替' in row_text or '作废' in row_text:
                                    status = '废止'
                                elif '即将实施' in row_text:
                                    status = '即将实施'
                                return {
                                    'source': '工标网(浏览器)',
                                    'standard_number': standard_number,
                                    'standard_name': td_text,
                                    'status': status,
                                    'message': '浏览器查询成功',
                                    'replace_by': '',
                                }

        # 尝试从链接中提取
        for a in soup.find_all('a'):
            text = a.get_text(strip=True)
            href = a.get('href', '')
            if len(text) > 5 and ('规范' in text or '标准' in text or '规程' in text):
                # 检查链接地址是否包含标准号
                href_upper = href.upper().replace(' ', '')
                if std_prefix in href_upper or std_no_clean[:8] in href_upper:
                    return {
                        'source': '工标网(浏览器)',
                        'standard_number': standard_number,
                        'standard_name': text,
                        'status': '现行',
                        'message': '浏览器查询成功',
                        'replace_by': '',
                    }

        return None

    except Exception as e:
        try:
            page.close()
        except Exception:
            pass
        return None

def query_openstd_browser(standard_number: str) -> Optional[Dict]:
    """全国标准信息公共服务平台浏览器查询"""
    try:
        ctx = _get_browser()
        page = ctx.new_page()

        # 访问搜索页面
        search_url = f'https://openstd.samr.gov.cn/bzgk/std/search?q={standard_number.replace(" ", "%20")}'
        page.goto(search_url, timeout=20000, wait_until='domcontentloaded')
        time.sleep(3)

        html = page.content()
        page.close()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        std_no_clean = standard_number.replace(' ', '').upper()
        std_prefix = re.sub(r'[\-\.]?\d{4}$', '', std_no_clean)

        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            row_text = ' '.join(td.get_text(strip=True) for td in tds)
            if std_prefix in row_text.replace(' ', '').upper() or std_no_clean[:8] in row_text.replace(' ', '').upper():
                for td in tds:
                    td_text = td.get_text(strip=True)
                    if len(td_text) > 5 and ('规范' in td_text or '标准' in td_text or '规程' in td_text):
                        row_std = re.search(r'(GB\s?\d+[\-\.]?\d*\-?\d{2,4}|GB/T\s?\d+[\-\.]?\d*\-?\d{2,4}|JGJ\s?\d+[\-\.]?\d*\-?\d{2,4})', row_text, re.IGNORECASE)
                        if row_std:
                            extracted = row_std.group(1).replace(' ', '').upper()
                            extracted_prefix = re.sub(r'[\-\.]?\d{4}$', '', extracted)
                            if extracted_prefix == std_prefix:
                                status = '现行'
                                if '废止' in row_text:
                                    status = '废止'
                                return {
                                    'source': '全国标准信息公共服务平台(浏览器)',
                                    'standard_number': standard_number,
                                    'standard_name': td_text,
                                    'status': status,
                                    'message': '浏览器查询成功',
                                    'replace_by': '',
                                }

        return None

    except Exception:
        try:
            page.close()
        except Exception:
            pass
        return None

def query_jianbiaoku_browser(standard_number: str) -> Optional[Dict]:
    """建标库浏览器查询（支持所有标准类型）"""
    try:
        ctx = _get_browser()
        page = ctx.new_page()

        std_no_clean = standard_number.replace(' ', '').upper()
        std_prefix = re.sub(r'[\-\.]?\d{4}$', '', std_no_clean)

        # 访问首页并使用搜索表单
        page.goto('https://www.jianbiaoku.com/', timeout=30000, wait_until='networkidle')
        time.sleep(2)

        # 查找搜索框并输入
        search_input = page.query_selector('input#keyword')
        if search_input:
            search_input.fill(standard_number)
            page.keyboard.press('Enter')
            time.sleep(3)

            html = page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # 从搜索结果中提取
            for tr in soup.find_all('tr'):
                tds = tr.find_all('td')
                row_text = ' '.join(td.get_text(strip=True) for td in tds)
                if std_prefix in row_text.replace(' ', '').upper() or std_no_clean[:8] in row_text.replace(' ', '').upper():
                    for td in tds:
                        td_text = td.get_text(strip=True)
                        if len(td_text) > 5 and ('规范' in td_text or '标准' in td_text or '规程' in td_text):
                            page.close()
                            return {
                                'source': '建标库(浏览器)',
                                'standard_number': standard_number,
                                'standard_name': td_text,
                                'status': '现行',
                                'message': '浏览器查询成功',
                                'replace_by': '',
                            }

            # 从链接中提取
            for a in soup.find_all('a'):
                text = a.get_text(strip=True)
                href = a.get('href', '')
                if len(text) > 5 and ('规范' in text or '标准' in text or '规程' in text):
                    href_upper = href.upper().replace(' ', '')
                    if std_prefix in href_upper or std_no_clean[:8] in href_upper:
                        page.close()
                        return {
                            'source': '建标库(浏览器)',
                            'standard_number': standard_number,
                            'standard_name': text,
                            'status': '现行',
                            'message': '浏览器查询成功',
                            'replace_by': '',
                        }

        page.close()
        return None

    except Exception:
        try:
            page.close()
        except Exception:
            pass
        return None
