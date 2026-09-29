from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

# 載入我們寫好的 TDX 管線
from tdx_pipeline import TDXIngestion, EVDataProcessor, EVDatabaseMart

app = FastAPI(title="充電樁戰情室 Backend")

# 允許跨域請求 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 讓前端可以讀取生成的 json 檔案
os.makedirs("data", exist_ok=True)
app.mount("/data", StaticFiles(directory="data"), name="data")

# 定義前端傳來的資料格式
class TdxRequest(BaseModel):
    client_id: str
    client_secret: str

class LogRequest(BaseModel):
    log_content: str

# 🆕 這是讓 TDX 按鈕可以呼叫的新路徑
@app.post("/sync_tdx")
async def sync_tdx_data(req: TdxRequest):
    try:
        # 執行 TDX 資料拉取與清洗
        ingestion = TDXIngestion(client_id=req.client_id, client_secret=req.client_secret)
        raw_static, raw_dynamic = ingestion.fetch_raw_data()
        cleaned_data = EVDataProcessor.process_and_deduplicate(raw_static, raw_dynamic)
        
        # 存入資料庫並產出 JSON
        mart = EVDatabaseMart("data/evcharge.db")
        mart.save(cleaned_data)
        mart.export_marts()
        
        return {"message": "TDX 同步完成", "count": len(cleaned_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 這是原本的 AI 診斷路徑
@app.post("/analyze_log")
async def analyze_log(req: LogRequest):
    return {"diagnosis_html": "<strong>API 接收成功！</strong><br>此為後端 RAG 回傳測試。"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
