#!/usr/bin/env python3
"""
「検索されない劇物、有毒」シート用の CAS番号・リスクアセスメント対象判定スクリプト

このシートの物質は「化学物質一覧（書込み不可）」（毒物及び劇物取締法マスタ）の
生工研No.検索にヒットしなかったため、生工研No.経由でのCAS番号取得ができない。
そのため PubChem を化合物名で検索して CAS番号を取得する必要がある。

これまでの運用で分かっている通り、PubChem は日本語名での検索にほぼ対応して
おらず、英語名（IUPAC名・慣用英語名）でないとヒットしない。そこで、シート内の
日本語名をあらかじめ英語名に変換したテーブル（JP_TO_EN）を用意し、それを
検索クエリとして使う。

【重要な注意】
このスクリプトはネットワーク経由でPubChemにアクセスするため、
クラウド環境ではなく、実際にPubChemへアクセスできるMac環境で実行すること。

【要確認項目】
- 一部の物質名は日本語表記からの類推・翻訳であり、正確性を保証できない
  （例：「塩化鉄」はFeCl2/FeCl3どちらか不明、「DTT」は文脈上DDTの可能性が高い
   等）。出力される「備考」欄に不確実な項目は明記しているので、
   実際にリストに追加する前に化学物質管理者が名称とCAS番号を確認すること。
- 染料・市販品名（Reactive blue2、Polybuffer、ピコタグ等）はPubChemに
  単一のCAS番号で登録されていない可能性が高い。ヒットしない場合は
  Webアプリの「試薬名を手入力して検索」機能で追加の候補名を試すか、
  製造元のSDSでCAS番号を直接確認すること。

使い方:
    python scripts/lookup_unlisted_toxic.py <元のExcelファイル> \\
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
    "イミダゾール": ("Imidazole", None),
    "酢酸亜鉛": ("Zinc acetate", "無水物と二水和物でCASが異なる。管理簿の608-619番(無機亜鉛塩類)は酢酸塩(有機酸塩)を含まない可能性が高く、該当しない可能性がある。要確認。"),
    "塩化マンガン": ("Manganese(II) chloride", None),
    "チモール": ("Thymol", None),
    "塩化鉄": ("Ferric chloride", "FeCl2(塩化鉄(II))とFeCl3(塩化鉄(III))のどちらか不明。手元の試薬瓶で確認要。"),
    "硫酸鉄": ("Ferrous sulfate", "FeSO4(硫酸鉄(II))とFe2(SO4)3(硫酸鉄(III))のどちらか不明。手元の試薬瓶で確認要。"),
    "酸化オスミウム": ("Osmium tetroxide", None),
    "エチジウムブロマイド": ("Ethidium bromide", None),
    "トリフルオロ酢酸": ("Trifluoroacetic acid", None),
    "ピコタグ": ("Acetonitrile", "「Pico-Tag」は市販キット名。備考欄に記載の通りアセトニトリルが主成分（40%以下は劇物非該当）。単一物質としてのCAS登録は不適切な可能性あり。"),
    "アミノアンチピリン": ("4-Aminoantipyrine", None),
    "N,N-ジメチル-1,4-フェニレンジアミン": ("N,N-Dimethyl-1,4-phenylenediamine", None),
    "メルカプト酢酸": ("Thioglycolic acid", None),
    "カテコール": ("Catechol", None),
    "2,6-ジメトキシフェノール": ("2,6-Dimethoxyphenol", None),
    "キシリジン": ("Xylidine", "異性体（2,4-/2,5-/3,4-キシリジン等）により個別のCASが異なる。混合物CASは1300-73-8。要確認。"),
    "vioruric acid": ("Violuric acid", "原表記のスペルミスと推測（Violuric acidの可能性）。要確認。"),
    "p-n-オクチルフェノール": ("4-n-Octylphenol", None),
    "2,4-ジクロロフェノール標準品": ("2,4-Dichlorophenol", "「標準品」は分析用標準試薬の意味。化合物自体はCAS検索可能。"),
    "p-（1,3,3-テトラメチルブチル）フェノール標準品": ("4-tert-Octylphenol", "p-(1,1,3,3-テトラメチルブチル)フェノール = 4-tert-オクチルフェノールと推測。"),
    "p-n-ノニルフェノール": ("4-Nonylphenol", None),
    "イブコナゾール標準品": ("Ipconazole", "「イブコナゾール」はカタカナ表記から Ipconazole（イプコナゾール、農薬・防カビ剤）の可能性が高いが確定ではない。要確認。"),
    "グアヤコル": ("Guaiacol", None),
    "ヨード酢酸": ("Iodoacetic acid", None),
    "2,4-ジクロロフェノキシ酢酸": ("2,4-Dichlorophenoxyacetic acid", None),
    "シュウ酸アルミニウム": ("Aluminum oxalate", "管理簿の生工研No.735(蓚酸/オキサリン酸、CAS 144-62-7)を含有する製剤としての劇物該当性は化学物質管理者の判断が必要。化合物自体のCASはアルミニウム蓚酸塩として別に存在する。"),
    "クロロ酢酸": ("Chloroacetic acid", "別名モノクロル酢酸として管理簿M0122に既に登録済み(CAS 79-11-8)の可能性が高い。重複登録に注意。"),
    "4,4'-DTT": ("p,p'-DDT", "第一種特定化学物質のグループ内にあるため、生化学試薬のDTT(ジチオスレイトール)ではなくDDT(有機塩素系農薬)の異性体表記の可能性が高い。要確認。"),
    "2,4'-DTT": ("o,p'-DDT", "同上。DDTの異性体表記の可能性が高い。要確認。"),
    "DTT": ("p,p'-DDT", "文脈（第一種特定化学物質グループ内）から、生化学試薬のジチオスレイトールではなくDDTの可能性が高い。ただし確定ではないため要確認。"),
    "alpha-HCH": ("alpha-Hexachlorocyclohexane", None),
    "beta-HCH": ("beta-Hexachlorocyclohexane", None),
    "gamma-HCH": ("Lindane", "gamma-HCH = リンデン"),
    "delta-HCH": ("delta-Hexachlorocyclohexane", None),
    "fast blue salt B": ("Fast Blue B salt", "染料・診断薬。PubChemにヒットしない場合あり。"),
    "Chicago sky blue 6B": ("Chicago Sky Blue 6B", "染料。PubChemにヒットしない場合あり。"),
    "Reactive blue2": ("Reactive Blue 2", "染料。PubChemにヒットしない場合あり。"),
    "Polybuffer": (None, "クロマトグラフィー用の複数成分混合緩衝液の商品名。単一のCAS番号は存在しない可能性が高い。自動検索対象外。"),
}


def resolve_search_name(original_name):
    """シート上の名称から、PubChem検索に使う英語名を決定する"""
    original_name = original_name.strip()
    if original_name in JP_TO_EN:
        return JP_TO_EN[original_name]
    # 既に英語表記と判断できるもの（ASCII文字が主体）はそのまま使う
    ascii_ratio = sum(1 for c in original_name if ord(c) < 128) / max(len(original_name), 1)
    if ascii_ratio > 0.8:
        return original_name, None
    return None, "英語名への変換候補が見つからない。手動で確認・検索してください。"


def search_pubchem_by_name(compound_name):
    """app.py と同等のPubChem検索（軽量版・スタンドアロン）"""
    try:
        compounds = pcp.get_compounds(compound_name, 'name')
        if compounds:
            compound = compounds[0]
            cas_number = None
            if hasattr(compound, 'iupac_name'):
                m = re.search(r'\d{2,7}-\d{2}-\d', str(getattr(compound, 'iupac_name', '')))
                if m:
                    cas_number = m.group(0)
            if not cas_number and hasattr(compound, 'synonyms'):
                try:
                    for syn in compound.synonyms:
                        m = re.search(r'\d{2,7}-\d{2}-\d', str(syn))
                        if m:
                            cas_number = m.group(0)
                            break
                except Exception:
                    pass
            return {
                "cas": cas_number or "N/A",
                "name": getattr(compound, 'iupac_name', compound_name),
                "formula": getattr(compound, 'molecular_formula', 'N/A'),
                "cid": compound.cid,
            }
    except Exception as e:
        return {"error": str(e)}
    return None


def process(input_path, risk_csv_path, output_csv_path):
    risk_db = load_risk_db(risk_csv_path)
    print(f"✅ リスクアセスメント対象DB読み込み: {len(risk_db)}件\n")

    wb = openpyxl.load_workbook(input_path, data_only=True)
    ws = wb['検索されない劇物、有毒']

    rows_out = []
    for row_idx, row in enumerate(ws.iter_rows(values_only=True), 1):
        if row is None or all(c is None for c in row):
            continue
        original_name = row[0]
        if not original_name:
            continue

        search_name, note = resolve_search_name(str(original_name))

        result_row = {
            "元の名称": original_name,
            "検索に使った英語名": search_name or "",
            "備考": note or "",
            "CAS番号": "",
            "PubChem化合物名": "",
            "リスクアセスメント対象": "",
            "リスク対象化合物名": "",
        }

        if search_name:
            print(f"🔍 検索中: {original_name} -> {search_name}")
            info = search_pubchem_by_name(search_name)
            time.sleep(0.3)  # PubChemへの負荷軽減
            if info and "error" not in info and info.get("cas") and info["cas"] != "N/A":
                cas = info["cas"]
                result_row["CAS番号"] = cas
                result_row["PubChem化合物名"] = info.get("name", "")
                risk_info = risk_db.get(cas)
                if risk_info:
                    result_row["リスクアセスメント対象"] = "対象"
                    result_row["リスク対象化合物名"] = risk_info["name"]
                else:
                    result_row["リスクアセスメント対象"] = "-"
            else:
                result_row["備考"] = (result_row["備考"] + " / " if result_row["備考"] else "") + "PubChemでCAS番号を特定できず。手動確認が必要。"
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
    print("   ※ 「備考」欄に要確認事項がある行は、リストに追加する前に必ず確認してください。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_xlsx", help="元の化学物質管理簿.xlsxファイル")
    parser.add_argument("--risk-csv", default="data/risk_assessment.csv")
    parser.add_argument("--output", default="unlisted_toxic_result.csv")
    args = parser.parse_args()

    process(args.input_xlsx, args.risk_csv, args.output)
