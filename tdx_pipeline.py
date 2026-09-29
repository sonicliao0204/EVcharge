from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # 🆕 允許前端讀取靜態 JSON
from pydantic import BaseModel
import os

# 🆕 載入我們剛剛寫好的 TDX 管線
from tdx_pipeline import TDXIngestion, EVDataProcessor, EVDatabaseMart

# ... (保留您原本的 LangChain 與 Chroma 設定) ...

app = FastAPI(title="充電樁戰情室 Backend")

# 允許跨域請求 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🆕 掛載 data 資料夾，讓前端能直接用 http://localhost:8000/data/... 讀取 json
os.makedirs("data", exist_ok=True)
app.mount("/data", StaticFiles(directory="data"), name="data")

class TdxRequest(BaseModel):
    client_id: str
    client_secret: str

# 🆕 新增端點：觸發 TDX 管線
@app.post("/sync_tdx")
async def sync_tdx_data(req: TdxRequest):
    try:
        # 1. 抓取資料
        ingestion = TDXIngestion(client_id=req.client_id, client_secret=req.client_secret)
        raw_static, raw_dynamic = ingestion.fetch_raw_data()
        
        # 2. 清洗與去重
        cleaned_data = EVDataProcessor.process_and_deduplicate(raw_static, raw_dynamic)
        
        # 3. 存入 DB 並輸出為 stations_live.json
        mart = EVDatabaseMart("data/evcharge.db")
        mart.save(cleaned_data)
        mart.export_marts()
        
        return {"message": "✅ TDX 同步完成", "count": len(cleaned_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ... (保留您原本的 /analyze_log 和 /ingest_kb 端點) ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
