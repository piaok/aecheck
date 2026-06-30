from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import init_db, db
from schemas import ValidateRequest, StandardCreate, StandardResponse, PaginatedResponse
from ai_processor import extract_standards
from checker import check_standard_with_logs
from typing import List, Optional
import json

init_db()

app = FastAPI(title="建筑结构规范校验系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/extract")
async def extract_text(request: ValidateRequest):
    extracted = extract_standards(request.text)
    return {"extracted": [{"id": i+1, "standard_number": num, "standard_name": name} for i, (num, name) in enumerate(extracted)]}

@app.post("/api/validate")
async def validate_standards(request: ValidateRequest):
    extracted = extract_standards(request.text)

    results = []
    logs = []
    update_suggestions = []
    logs.append(f"🔍 解析输入文本，识别到 {len(extracted)} 条规范")

    for idx, (number, name) in enumerate(extracted):
        logs.append(f"📝 [{idx+1}] 处理规范: {number} - {name or '未识别名称'}")
        try:
            result, item_logs, suggestion = check_standard_with_logs(number, name, online=request.online)
            result.id = idx + 1
            results.append(result)
            logs.extend(item_logs)
            if suggestion:
                update_suggestions.append(suggestion)
        except Exception as e:
            logs.append(f"  ❌ 处理异常: {str(e)}")
            results.append(CheckResult(
                id=idx + 1,
                input_number=number,
                input_name=name or '',
                matched_number=None,
                matched_name=None,
                status="处理异常",
                matched_percentage=0,
                message=f"处理时发生错误: {str(e)}"
            ))

    logs.append(f"✅ 校验完成，共处理 {len(results)} 条规范")

    return {"results": results, "logs": logs, "update_suggestions": update_suggestions}

@app.get("/api/standards/count")
async def get_standards_count():
    return {"total": db.count()}

@app.get("/api/standards")
async def get_standards(skip: int = 0, limit: int = 20, keyword: Optional[str] = None):
    total, items = db.get_all(keyword=keyword, skip=skip, limit=limit)
    return {"total": total, "items": items, "skip": skip, "limit": limit}

@app.get("/api/standards/{standard_id}")
async def get_standard(standard_id: int):
    standard = db.get_by_id(standard_id)
    if not standard:
        raise HTTPException(status_code=404, detail="标准未找到")
    return standard

@app.post("/api/standards")
async def create_standard(standard: StandardCreate):
    existing = db.get_by_number(standard.standard_number)
    if existing:
        raise HTTPException(status_code=400, detail="该标准号已存在")

    data = standard.model_dump()
    new_standard = db.create(**data)
    return new_standard

@app.put("/api/standards/{standard_id}")
async def update_standard(standard_id: int, standard: StandardCreate):
    existing = db.get_by_id(standard_id)
    if not existing:
        raise HTTPException(status_code=404, detail="标准未找到")

    data = standard.model_dump(exclude_unset=True)
    updated = db.update(standard_id, **data)
    return updated

@app.delete("/api/standards/{standard_id}")
async def delete_standard(standard_id: int):
    success = db.delete(standard_id)
    if not success:
        raise HTTPException(status_code=404, detail="标准未找到")
    return {"message": "删除成功"}

@app.post("/api/standards/batch-update")
async def batch_update_standards(suggestions: List[dict]):
    results = []
    for suggestion in suggestions:
        action = suggestion.get('action')
        data = suggestion.get('data', {})

        try:
            if action == 'update':
                standard_id = suggestion.get('id')
                existing = db.get_by_id(standard_id)
                if existing:
                    db.update(standard_id,
                              standard_name=data.get('standard_name', existing.get('standard_name')),
                              status=data.get('status', existing.get('status')),
                              replace_by=data.get('replace_by', existing.get('replace_by')),
                              source=data.get('source', existing.get('source')))
                    results.append({"success": True, "action": "update", "id": standard_id, "message": "更新成功"})
                else:
                    results.append({"success": False, "action": "update", "id": standard_id, "message": "标准未找到"})

            elif action == 'create':
                existing = db.get_by_number(data.get('standard_number', ''))
                if existing:
                    results.append({"success": False, "action": "create", "message": "标准号已存在"})
                else:
                    new_item = db.create(
                        standard_number=data.get('standard_number', ''),
                        standard_name=data.get('standard_name', ''),
                        status=data.get('status', '未知'),
                        source=data.get('source', '在线查询'),
                        replace_by=data.get('replace_by', ''),
                    )
                    results.append({"success": True, "action": "create", "id": new_item["id"], "message": "添加成功"})

            else:
                results.append({"success": False, "action": action, "message": "未知操作"})

        except Exception as e:
            results.append({"success": False, "action": action, "message": f"操作失败: {str(e)}"})

    return {"results": results}

# ===== AI大模型配置与校验 =====

class AIConfigRequest(BaseModel):
    base_url: str
    token: str
    model: str

class AIValidateRequest(BaseModel):
    standards: List[dict]

@app.get("/api/ai/config")
def get_ai_config():
    from ai_validator import get_config
    return get_config()

@app.post("/api/ai/config")
def update_ai_config(req: AIConfigRequest):
    from ai_validator import update_config
    update_config(req.base_url, req.token, req.model)
    return {"message": "配置已保存"}

@app.post("/api/ai/validate")
def ai_validate(req: AIValidateRequest):
    from ai_validator import validate_standards_with_ai, get_config
    config = get_config()
    if not config["has_token"]:
        raise HTTPException(status_code=400, detail="请先配置AI大模型（base_url和token）")
    
    results = validate_standards_with_ai(req.standards)
    if not results:
        raise HTTPException(status_code=500, detail="AI校验失败，请检查配置是否正确")
    
    return {"results": results}
