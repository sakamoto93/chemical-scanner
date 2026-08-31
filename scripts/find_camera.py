#!/usr/bin/env python3
"""
接続されているカメラのインデックス番号を確認するためのスクリプト

MacBookに外付けWebcamを接続すると、内蔵カメラと外付けWebcamの両方が
認識され、どちらが index 0 でどちらが index 1（以降）になるかは環境に
よって変わる。このスクリプトは各インデックスから1フレームずつ撮影し、
scripts/camera_test_output/ に保存する。保存された画像を見比べることで、
どのインデックスが外付けWebcamかを判別できる。

使い方:
  python scripts/find_camera.py

その後、正しいインデックスが分かったら、以下のようにサーバーを起動する:
  CAMERA_INDEX=1 python app.py   （例: 外付けWebcamが index 1 の場合）
"""
import cv2
import os

OUTPUT_DIR = "scripts/camera_test_output"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("🔍 カメラインデックス 0〜4 を順に試します...\n")

    found_any = False
    for index in range(5):
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            print(f"  index {index}: ❌ 開けませんでした（カメラが存在しない可能性）")
            cap.release()
            continue

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            print(f"  index {index}: ⚠️  開けたがフレーム取得に失敗")
            continue

        found_any = True
        h, w = frame.shape[:2]
        out_path = os.path.join(OUTPUT_DIR, f"camera_{index}.jpg")
        cv2.imwrite(out_path, frame)
        print(f"  index {index}: ✅ 撮影成功 ({w}x{h}) -> {out_path}")

    print()
    if found_any:
        print(f"📂 {OUTPUT_DIR}/ 内の画像を開いて、どのインデックスが")
        print("   外付けWebcamの映像かを確認してください。")
        print()
        print("   確認できたら、そのインデックスを指定してサーバーを起動:")
        print("   CAMERA_INDEX=<番号> python app.py")
    else:
        print("❌ どのインデックスでもカメラを検出できませんでした。")
        print("   Webcamが正しく接続されているか、macOSのカメラアクセス")
        print("   許可設定（システム設定 → プライバシーとセキュリティ → カメラ）")
        print("   でターミナル/Pythonが許可されているか確認してください。")


if __name__ == "__main__":
    main()
