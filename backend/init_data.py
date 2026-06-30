import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "standards.json")

INITIAL_DATA = [
    {"standard_number": "GB 50010-2010", "standard_name": "混凝土结构设计规范", "status": "现行", "release_date": "2010-08-18", "implement_date": "2011-07-01", "source": "工标网"},
    {"standard_number": "GB 50010-2020", "standard_name": "混凝土结构设计规范", "status": "现行", "release_date": "2020-12-23", "implement_date": "2021-10-01", "source": "工标网"},
    {"standard_number": "GB 50007-2011", "standard_name": "建筑地基基础设计规范", "status": "现行", "release_date": "2011-07-26", "implement_date": "2012-08-01", "source": "工标网"},
    {"standard_number": "GB 50017-2017", "standard_name": "钢结构设计标准", "status": "现行", "release_date": "2017-12-22", "implement_date": "2018-07-01", "source": "工标网"},
    {"standard_number": "GB 50009-2012", "standard_name": "建筑结构荷载规范", "status": "现行", "release_date": "2012-05-28", "implement_date": "2012-10-01", "source": "工标网"},
    {"standard_number": "GBJ 10-89", "standard_name": "混凝土结构设计规范", "status": "废止", "release_date": "1989-03-23", "implement_date": "1989-10-01", "abolish_date": "2011-07-01", "replace_by": "GB 50010-2010", "source": "工标网"},
    {"standard_number": "JGJ 107-2016", "standard_name": "钢筋机械连接技术规程", "status": "现行", "release_date": "2016-12-16", "implement_date": "2017-08-01", "source": "住建部"},
    {"standard_number": "JGJ 3-2010", "standard_name": "高层建筑混凝土结构技术规程", "status": "现行", "release_date": "2010-10-15", "implement_date": "2011-10-01", "source": "住建部"},
    {"standard_number": "JGJ/T 114-2014", "standard_name": "钢筋焊接网混凝土结构技术规程", "status": "现行", "release_date": "2014-12-01", "implement_date": "2015-08-01", "source": "住建部"},
    {"standard_number": "GB 50011-2010", "standard_name": "建筑抗震设计规范", "status": "现行", "release_date": "2010-05-31", "implement_date": "2010-12-01", "source": "工标网"},
    {"standard_number": "GB 50204-2015", "standard_name": "混凝土结构工程施工质量验收规范", "status": "现行", "release_date": "2015-09-18", "implement_date": "2015-12-01", "source": "工标网"},
    {"standard_number": "GB 50205-2020", "standard_name": "钢结构工程施工质量验收标准", "status": "现行", "release_date": "2020-11-18", "implement_date": "2021-06-01", "source": "工标网"},
    {"standard_number": "CECS 200:2006", "standard_name": "建筑钢结构防火技术规范", "status": "现行", "release_date": "2006-12-01", "implement_date": "2007-04-01", "source": "中国工程建设标准化协会"},
    {"standard_number": "GB/T 50081-2019", "standard_name": "混凝土物理力学性能试验方法标准", "status": "现行", "release_date": "2019-12-18", "implement_date": "2020-07-01", "source": "工标网"},
    {"standard_number": "JGJ 94-2008", "standard_name": "建筑桩基技术规范", "status": "现行", "release_date": "2008-09-19", "implement_date": "2009-03-01", "source": "住建部"},
    {"standard_number": "GB 50003-2011", "standard_name": "砌体结构设计规范", "status": "现行", "release_date": "2011-07-26", "implement_date": "2012-08-01", "source": "工标网"},
    {"standard_number": "GB 50016-2014", "standard_name": "建筑设计防火规范", "status": "现行", "release_date": "2014-08-27", "implement_date": "2015-05-01", "source": "工标网"},
    {"standard_number": "GB/T 50105-2010", "standard_name": "建筑结构制图标准", "status": "现行", "release_date": "2010-03-01", "implement_date": "2010-10-01", "source": "工标网"},
    {"standard_number": "GB/T 50123-2019", "standard_name": "土工试验方法标准", "status": "现行", "release_date": "2019-05-24", "implement_date": "2019-10-01", "source": "工标网"},
    {"standard_number": "JGJ/T 10-2011", "standard_name": "混凝土泵送施工技术规程", "status": "现行", "release_date": "2011-04-22", "implement_date": "2011-10-01", "source": "住建部"},
]

def ensure_init_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        data = []
        for i, item in enumerate(INITIAL_DATA, 1):
            item["id"] = i
            item["created_at"] = ""
            item["updated_at"] = ""
            data.append(item)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Initialized {len(data)} standards to {DATA_FILE}")
    else:
        print(f"Data file already exists: {DATA_FILE}")

if __name__ == "__main__":
    ensure_init_data()
