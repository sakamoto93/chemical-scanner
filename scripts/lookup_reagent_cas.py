#!/usr/bin/env python3
"""
試薬リスト（name, 容量, Cat#, 会社, 容器素材 の5列）から
CAS番号を検索し、労働安全衛生法リスクアセスメント対象かどうかを
判定するスクリプト。

【重要な注意】
このスクリプトはネットワーク経由でPubChemにアクセスするため、
クラウド環境ではなく、実際にPubChemへアクセスできるMac/Windows環境で
実行すること（クラウドの開発環境ではPubChemへの接続がブロックされている
ため、このスクリプト自体はクラウド環境では動作検証できていない）。

日本語の試薬名はPubChemでの検索に適した英語名へあらかじめ変換してから
検索する。JP_TO_EN辞書に無い名称は、日本語のまま検索を試みるが
（ヒットしない可能性が高い）、失敗した場合は手動確認が必要な旨を出力する。

【結果の正確性について】
- 同じ分子でも「遊離酸」と「塩」、立体異性体（D体/L体/DL体、o-/m-/p-等）で
  CAS番号が異なる。試薬名から塩の形態や異性体が明確でない場合は、
  スクリプトが検索した名称と実際のPubChemのヒット結果（IUPAC名）を
  必ず見比べて確認すること。
- Polybuffer、Formyl-Cellulofineのような独自調合・樹脂製品は、
  単一のCAS番号が存在しないため検索対象外としてスキップする。

使い方:
    python scripts/lookup_reagent_cas.py <元のExcelファイル> \\
        [--risk-csv data/risk_assessment.csv] \\
        [--output 出力CSVファイル名]
"""
import sys
import os
import argparse
import csv
import re
import time

sys.path.insert(0, os.path.dirname(__file__))
from process_management_ledger import load_risk_db  # noqa: E402

import pubchempy as pcp  # noqa: E402
import openpyxl  # noqa: E402


# 日本語名 -> (英語検索名, 備考)
# 備考が None の場合は特に注意事項なし
JP_TO_EN = {
    "トリフルオロ酢酸": ("Trifluoroacetic acid", None),
    "ピルビン酸ナトリウム": ("Sodium pyruvate", None),
    "α-フェニレンジアミン": (None,
        "「α-フェニレンジアミン」という異性体表記はベンゼン環のジアミンでは"
        "通常使われない（o-/m-/p-で呼ぶのが標準）ため自動検索対象外。"
        "同リスト内のCat#160-11022はWakoのo-フェニレンジアミン"
        "（CAS 95-54-5）の可能性が高いが、断定できないため手動確認必須。"),
    "ｍ-フェニレンジアミン": ("m-Phenylenediamine", None),
    "ジメチルジクロロシラン": ("Dichlorodimethylsilane", None),
    "ヘキサン酸": ("Hexanoic acid", None),
    "ヘキサン酸メチル": ("Methyl hexanoate", None),
    "N －エチルマレイミド": ("N-Ethylmaleimide", None),
    "パントテン酸カルシウム": ("Calcium pantothenate", "D体かDL体か試薬ラベルで要確認（CASが異なる）"),
    "アルブチン標準品": ("Arbutin", None),
    "アセチルシコニン": ("Acetylshikonin", None),
    "シコニン標準品": ("Shikonin", None),
    "（－）-（R）-エピネフリン": ("(R)-(-)-Epinephrine", None),
    "塩化3-（ｐ－ヨードフェニル）-2-（ｐ-ニトロフェニル）\n-5-フェニルテトラゾリウム":
        ("2-(4-Iodophenyl)-3-(4-nitrophenyl)-5-phenyltetrazolium chloride", "通称INT"),
    "ヨード酢酸": ("Iodoacetic acid", None),
    "ニトロブルーテトラゾリウム": ("Nitro blue tetrazolium chloride", "通称NBT"),
    "Polybuffer　74": (None, "クロマトグラフィー用の複数成分混合緩衝液の商品名。単一のCAS番号は存在しない可能性が高い。自動検索対象外。"),
    "ペルオキシターゼ用発色基質": ("3,3',5,5'-Tetramethylbenzidine dihydrochloride",
        "Cat#「TMBZ-HCL」から塩酸塩（TMB・2HCl）と推測。遊離塩基とはCASが異なるため要確認。"),
    "ホルミル-セルロファイン": (None, "セルロースビーズを基材としたクロマトグラフィー用樹脂製品（商品名）。単一のCAS番号なし。自動検索対象外。"),
    "TEMED": ("N,N,N',N'-Tetramethylethylenediamine", None),
    "DL-Homocysteine，95％": ("DL-Homocysteine", None),
    "2-Ketobutyric acid，sodiumsalt monohydate,98%": ("2-Ketobutyric acid sodium salt monohydrate",
        "遊離酸とは別CAS。無水物/一水和物でもCASが異なる場合があるため要確認。"),
}


def resolve_search_name(original_name):
    """試薬名から、PubChem検索に使う英語名を決定する"""
    original_name = original_name.strip()
    if original_name in JP_TO_EN:
        return JP_TO_EN[original_name]
    # 全角スペース・読点混じりの表記はPubChem検索に渡す前に半角へ正規化
    normalized = original_name.replace('　', ' ').replace('，', ',')
    # 既に英語表記と判断できるもの（ASCII文字が主体）はそのまま使う
    ascii_ratio = sum(1 for c in original_name if ord(c) < 128) / max(len(original_name), 1)
    if ascii_ratio > 0.8:
        return normalized, None
    return None, "英語名への変換候補が見つからない。手動で確認・検索してください。"


def search_pubchem_by_name(compound_name):
    """app.py と同等のPubChem検索（軽量版・スタンドアロン）"""
    try:
        compounds = pcp.get_compounds(compound_name, 'name')
        if compounds:
            compound = compounds[0]
            cas_number = None
            if hasattr(compound, 'synonyms'):
                try:
                    for syn in compound.synonyms:
                        m = re.search(r'^\d{2,7}-\d{2}-\d$', str(syn))
                        if m:
                            cas_number = m.group(0)
                            break
                except Exception:
                    pass
            return {
                "cas": cas_number or "N/A",
                "pubchem_name": getattr(compound, 'iupac_name', compound_name),
                "formula": getattr(compound, 'molecular_formula', 'N/A'),
                "weight": getattr(compound, 'molecular_weight', 'N/A'),
                "cid": compound.cid,
            }
    except Exception as e:
        return {"error": str(e)}
    return None


def process(input_path, risk_csv_path, output_csv_path):
    risk_db = load_risk_db(risk_csv_path)
    print(f"✅ リスクアセスメント対象DB読み込み: {len(risk_db)}件\n")

    wb = openpyxl.load_workbook(input_path, data_only=True)
    ws = wb.active

    rows_out = []
    for row_idx, row in enumerate(ws.iter_rows(values_only=True), 1):
        if row_idx == 1:
            continue  # ヘッダー行
        if row is None or all(c is None for c in row):
            continue
        name, volume, catno, company, container = (list(row) + [None] * 5)[:5]
        if not name:
            continue

        search_name, note = resolve_search_name(str(name))

        result_row = {
            "試薬名": name,
            "容量": volume,
            "Cat#": catno,
            "会社": company,
            "検索に使った英語名": search_name or "",
            "備考": note or "",
            "CAS番号": "",
            "PubChem化合物名": "",
            "分子式": "",
            "分子量": "",
            "リスクアセスメント対象": "",
            "リスク対象化合物名": "",
        }

        if search_name:
            print(f"🔍 検索中: {name} -> {search_name}")
            info = search_pubchem_by_name(search_name)
            time.sleep(0.3)  # PubChemへの負荷軽減
            if info and "error" not in info and info.get("cas") and info["cas"] != "N/A":
                cas = info["cas"]
                result_row["CAS番号"] = cas
                result_row["PubChem化合物名"] = info.get("pubchem_name", "")
                result_row["分子式"] = info.get("formula", "")
                result_row["分子量"] = info.get("weight", "")
                risk_info = risk_db.get(cas)
                if risk_info:
                    result_row["リスクアセスメント対象"] = "対象"
                    result_row["リスク対象化合物名"] = risk_info["name"]
                else:
                    result_row["リスクアセスメント対象"] = "-"
            else:
                result_row["備考"] = (result_row["備考"] + " / " if result_row["備考"] else "") + \
                    "PubChemでCAS番号を特定できず。手動確認が必要。"
        rows_out.append(result_row)

    with open(output_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()) if rows_out else [])
        writer.writeheader()
        writer.writerows(rows_out)

    risk_count = sum(1 for r in rows_out if r["リスクアセスメント対象"] == "対象")
    unresolved_count = sum(1 for r in rows_out if not r["CAS番号"])

    print()
    print("=" * 60)
    print("処理結果サマリー")
    print("=" * 60)
    print(f"総件数: {len(rows_out)}")
    print(f"CAS番号を特定できた件数: {len(rows_out) - unresolved_count}")
    print(f"リスクアセスメント対象件数: {risk_count}")
    print(f"手動確認が必要な件数: {unresolved_count}")
    print()
    print(f"💾 出力ファイル: {output_csv_path}")
    print("   ※ 「備考」欄に要確認事項がある行は、台帳に反映する前に必ず確認してください。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_xlsx", help="試薬リストのExcelファイル（1列目から name, 容量, Cat#, 会社, 容器素材）")
    parser.add_argument("--risk-csv", default="data/risk_assessment.csv")
    parser.add_argument("--output", default="reagent_cas_result.csv")
    args = parser.parse_args()

    process(args.input_xlsx, args.risk_csv, args.output)
