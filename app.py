from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
from paddleocr import PaddleOCR
import io
from PIL import Image
import re
import pubchempy as pcp

app = FastAPI()
ocr = PaddleOCR(use_textline_orientation=True, lang='en')

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

def extract_cas_number(texts):
    """OCRテキストからCAS番号を抽出"""
    cas_pattern = r'\d{2,7}-\d{2}-\d'
    for text_obj in texts:
        text = text_obj.get('text', '') if isinstance(text_obj, dict) else text_obj
        match = re.search(cas_pattern, text)
        if match:
            return match.group(0)
    return None

def validate_cas_checkdigit(cas_number):
    """CAS番号のチェックディジットを検証"""
    try:
        parts = cas_number.split('-')
        if len(parts) != 3:
            return False

        main_part = parts[0] + parts[1]
        check_digit = int(parts[2])

        total = 0
        for i, digit in enumerate(reversed(main_part)):
            total += int(digit) * (i + 1)

        calculated_check = (10 - (total % 10)) % 10
        return check_digit == calculated_check
    except:
        return False

def search_pubchem_by_cas(cas_number):
    """CAS番号からPubChemで化合物情報を取得"""
    try:
        # CAS番号で検索（'name'パラメータを使用）
        compounds = pcp.get_compounds(cas_number, 'name')

        if compounds:
            compound = compounds[0]
            return {
                "cas": cas_number,
                "name": getattr(compound, 'iupac_name', 'N/A'),
                "formula": getattr(compound, 'molecular_formula', 'N/A'),
                "weight": getattr(compound, 'molecular_weight', 'N/A'),
                "cid": compound.cid
            }
    except Exception as e:
        pass
    return None

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
@app.get("/capture")
async def capture_frame():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return JSONResponse({"error": "Failed to capture frame"}, status_code=400)
    
    ret, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()
    
    return StreamingResponse(
        iter([frame_bytes]),
        media_type="image/jpeg"
    )
@app.post("/ocr")
async def perform_ocr(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image_array = np.array(image)

        result = ocr.ocr(image_array)

        texts = []
        if result and isinstance(result, list) and len(result) > 0:
            result_dict = result[0]
            if isinstance(result_dict, dict):
                rec_texts = result_dict.get('rec_texts', [])
                rec_scores = result_dict.get('rec_scores', [])
                for text, score in zip(rec_texts, rec_scores):
                    texts.append({
                        "text": text,
                        "confidence": float(score)
                    })

        # CAS番号を抽出
        cas_number = extract_cas_number(texts)
        compound_info = None

        if cas_number:
            # PubChemで化合物情報を取得
            compound_info = search_pubchem_by_cas(cas_number)

        return JSONResponse({
            "texts": texts,
            "cas_number": cas_number,
            "compound_info": compound_info
        })
    except Exception as e:
        import traceback
        return JSONResponse({"error": str(e), "traceback": traceback.format_exc()}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
