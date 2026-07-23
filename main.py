import uvicorn

if __name__ == "__main__":
    print("Starting TenderIQ AI Platform Server on http://0.0.0.0:8000 ...")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
