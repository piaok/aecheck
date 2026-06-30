# AECheck - 建筑结构规范校验系统

建筑结构规范名称与标准号匹配校验工具，支持本地数据库校验、AI大模型校验、在线查询三种方式。

## 功能

- **文本解析**：从非结构化文本中自动识别规范标准号和名称，支持 GB、JC/T、JGJ、CECS、DB 等多种格式
- **本地数据库校验**：基于本地 JSON 数据库快速匹配校验（内置 67 条建筑结构规范）
- **AI大模型校验**：接入 OpenAI 兼容接口（DeepSeek、通义千问、智谱等），智能判断标准号与名称是否正确匹配
- **在线查询**：通过 Playwright 浏览器自动化查询标准网站
- **数据库管理**：可视化管理界面，支持分页搜索、增删改查
- **符号统一**：自动处理中英文符号差异（如《》→ <>）

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + TypeScript + Vite + TailwindCSS |
| 后端 | FastAPI + Python 3.11 |
| 存储 | JSON 文件存储 |
| 浏览器 | Playwright (Chromium) |
| 部署 | Docker Compose |

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/piaok/aecheck.git
cd aecheck
```

### 2. 启动服务

```bash
docker compose up -d --build
```

### 3. 访问系统

- 前端页面：http://localhost:8017
- 后端 API：http://localhost:8017/api/docs

## 使用方法

### 规范校验

1. 在输入框中粘贴包含规范的文本
2. 点击 **解析文本** - 系统自动提取规范信息并显示表格
3. 确认提取结果后，点击 **开始校验**（本地数据库）或 **AI校验**（AI大模型）

### AI 校验配置

1. 点击 **设置** 标签页
2. 填写 AI 接口信息：
   - **Base URL**：API 地址，如 `https://api.deepseek.com`
   - **API Token**：接口密钥
   - **模型名称**：如 `deepseek-chat`、`gpt-4o`、`qwen-plus`
3. 点击 **保存配置**

支持所有 OpenAI 兼容接口，包括：
- DeepSeek：`https://api.deepseek.com`
- 通义千问：`https://dashscope.aliyuncs.com/compatible-mode`
- 智谱 AI：`https://open.bigmodel.cn/api/paas/v4`

### 数据库管理

- 点击 **数据库管理** 标签页查看所有标准
- 支持按标准号、名称搜索
- 支持在线编辑、新增、删除标准

## 项目结构

```
aecheck/
├── backend/
│   ├── main.py              # FastAPI 主程序
│   ├── ai_processor.py      # 文本解析（标准号+名称提取）
│   ├── checker.py           # 校验逻辑
│   ├── scraper.py           # HTTP 在线查询
│   ├── scraper_browser.py   # Playwright 浏览器查询
│   ├── ai_validator.py      # AI 大模型校验
│   ├── database.py          # JSON 数据库操作
│   ├── schemas.py           # Pydantic 数据模型
│   ├── init_data.py         # 初始数据导入
│   ├── data/                # 运行时数据目录
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # 主界面
│   │   ├── api/             # API 调用
│   │   ├── types/           # TypeScript 类型
│   │   └── index.css        # 样式
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── .gitignore
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/parse` | 解析文本，提取规范列表 |
| POST | `/api/validate` | 校验规范（本地+在线） |
| GET | `/api/standards` | 查询数据库（支持分页搜索） |
| POST | `/api/standards` | 新增标准 |
| PUT | `/api/standards/{id}` | 更新标准 |
| DELETE | `/api/standards/{id}` | 删除标准 |
| POST | `/api/ai/config` | 保存 AI 配置 |
| GET | `/api/ai/config` | 获取 AI 配置 |
| POST | `/api/ai/validate` | AI 大模型校验 |

## License

MIT
