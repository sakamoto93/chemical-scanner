from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
from paddleocr import PaddleOCR
import io
from PIL import Image

app = FastAPI()
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_camera_frame():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # JPEG エンコード
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n\r\n'
               + frame_bytes + b'\r\n')

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(
        get_camera_frame(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.post("/ocr")
async def perform_ocr(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image_array = np.array(image)

        result = ocr.ocr(image_array, cls=True)

        texts = []
        for line in result:
            for word_info in line:
                text = word_info[1]
                confidence = float(word_info[2])
                texts.append({
                    "text": text,
                    "confidence": confidence
                })

        return JSONResponse({"texts": texts})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
