"""
化学物質名の日本語→英語変換ヘルパー

PubChemは英語名（IUPAC名・慣用英語名）での検索に強く、日本語名では
ほとんどヒットしない。このモジュールは、手入力検索で日本語名が入力された
場合に、PubChem検索に使える英語名の候補を生成するためのもの。

対応する変換方法:
1. 元素名＋陰イオン名のパターンマッチによる無機化合物名の機械的変換
   （例：「塩化ナトリウム」→「sodium chloride」）
2. よく使われる慣用名の辞書引き（例：「チモール」→「Thymol」）

完全な翻訳エンジンではなく、あくまで検索の当たりを付けるためのヒューリスティック。
変換できない場合は None を返すので、呼び出し側はPubChem検索自体（原文のまま、
または英語名のまま）やオートコンプリートAPIによる候補提示にフォールバックすること。
"""
import re

# 元素名（日本語 → 英語）
ELEMENTS_JP_EN = {
    "水素": "hydrogen", "ヘリウム": "helium", "リチウム": "lithium",
    "ベリリウム": "beryllium", "ホウ素": "boron", "炭素": "carbon",
    "窒素": "nitrogen", "酸素": "oxygen", "フッ素": "fluorine", "弗素": "fluorine",
    "ナトリウム": "sodium", "マグネシウム": "magnesium", "アルミニウム": "aluminum",
    "ケイ素": "silicon", "珪素": "silicon", "リン": "phosphorus", "燐": "phosphorus",
    "硫黄": "sulfur", "塩素": "chlorine", "カリウム": "potassium",
    "カルシウム": "calcium", "チタン": "titanium", "バナジウム": "vanadium",
    "クロム": "chromium", "マンガン": "manganese", "鉄": "iron",
    "コバルト": "cobalt", "ニッケル": "nickel", "銅": "copper", "亜鉛": "zinc",
    "ガリウム": "gallium", "ヒ素": "arsenic", "砒素": "arsenic",
    "セレン": "selenium", "臭素": "bromine", "ストロンチウム": "strontium",
    "ジルコニウム": "zirconium", "銀": "silver", "カドミウム": "cadmium",
    "スズ": "tin", "錫": "tin", "アンチモン": "antimony", "テルル": "tellurium",
    "ヨウ素": "iodine", "沃素": "iodine", "バリウム": "barium",
    "タングステン": "tungsten", "白金": "platinum", "金": "gold",
    "水銀": "mercury", "鉛": "lead", "ビスマス": "bismuth",
    "オスミウム": "osmium", "イリジウム": "iridium", "ウラン": "uranium",
}

# 陰イオン・官能基の接頭辞（日本語 → 英語）
# 長い表記が短い表記の一部にならないよう、長い順に定義する
ANION_PATTERNS_JP_EN = [
    ("過マンガン酸", "permanganate"),
    ("重クロム酸", "dichromate"),
    ("次亜塩素酸", "hypochlorite"),
    ("亜塩素酸", "chlorite"),
    ("過塩素酸", "perchlorate"),
    ("塩素酸", "chlorate"),
    ("重炭酸", "bicarbonate"),
    ("炭酸水素", "bicarbonate"),
    ("炭酸", "carbonate"),
    ("硫酸水素", "bisulfate"),
    ("亜硫酸", "sulfite"),
    ("硫酸", "sulfate"),
    ("亜硝酸", "nitrite"),
    ("硝酸", "nitrate"),
    ("亜リン酸", "phosphite"),
    ("亜燐酸", "phosphite"),
    ("リン酸", "phosphate"),
    ("燐酸", "phosphate"),
    ("重クロム酸", "dichromate"),
    ("クロム酸", "chromate"),
    ("ホウ酸", "borate"),
    ("硼酸", "borate"),
    ("ケイ酸", "silicate"),
    ("珪酸", "silicate"),
    ("酢酸", "acetate"),
    ("シュウ酸", "oxalate"),
    ("蓚酸", "oxalate"),
    ("塩化", "chloride"),
    ("臭化", "bromide"),
    ("フッ化", "fluoride"),
    ("弗化", "fluoride"),
    ("ヨウ化", "iodide"),
    ("沃化", "iodide"),
    ("過酸化", "peroxide"),
    ("酸化", "oxide"),
    ("水酸化", "hydroxide"),
    ("硫化", "sulfide"),
    ("シアン化", "cyanide"),
    ("青化", "cyanide"),
    ("窒化", "nitride"),
    ("炭化", "carbide"),
]

# よく使われる慣用名の辞書（日本語 → 英語）。生化学・有機試薬系を中心に。
COMMON_NAME_JP_EN = {
    "イミダゾール": "imidazole",
    "チモール": "thymol",
    "カテコール": "catechol",
    "グアヤコル": "guaiacol",
    "トリフルオロ酢酸": "trifluoroacetic acid",
    "メルカプト酢酸": "thioglycolic acid",
    "ヨード酢酸": "iodoacetic acid",
    "クロロ酢酸": "chloroacetic acid",
    "アミノアンチピリン": "4-aminoantipyrine",
    "エチジウムブロマイド": "ethidium bromide",
    "アクリルアミド": "acrylamide",
    "アニリン": "aniline",
    "クロロホルム": "chloroform",
    "ホルムアルデヒド": "formaldehyde",
    "アセトニトリル": "acetonitrile",
    "アセトン": "acetone",
    "メタノール": "methanol",
    "エタノール": "ethanol",
    "イソプロパノール": "isopropanol",
    "イソプロピルアルコール": "isopropyl alcohol",
    "ジエチルエーテル": "diethyl ether",
    "エチルエーテル": "ethyl ether",
    "トルエン": "toluene",
    "キシレン": "xylene",
    "ベンゼン": "benzene",
    "フェノール": "phenol",
    "グリセリン": "glycerin",
    "グリセロール": "glycerol",
    "尿素": "urea",
    "蟻酸": "formic acid",
    "ぎ酸": "formic acid",
    "酢酸エチル": "ethyl acetate",
    "酢酸メチル": "methyl acetate",
}


def contains_japanese(text):
    """文字列に日本語（ひらがな・カタカナ・漢字）が含まれるか判定"""
    return bool(re.search(r'[぀-ヿ一-鿿]', text))


def translate_japanese_inorganic_name(name):
    """日本語の無機化合物名を「陰イオン名＋元素名」パターンから英語名へ機械的に変換する

    例: "塩化ナトリウム" -> "sodium chloride"
        "水酸化カリウム" -> "potassium hydroxide"

    パターンに一致しない場合、または元素名が特定できない場合は None を返す。
    """
    name = name.strip()
    for jp_anion, en_anion in ANION_PATTERNS_JP_EN:
        if name.startswith(jp_anion):
            remainder = name[len(jp_anion):].strip()
            # 元素名を長い表記から順に照合（複合語の誤マッチを避けるため）
            for jp_elem in sorted(ELEMENTS_JP_EN.keys(), key=len, reverse=True):
                if remainder == jp_elem or remainder.startswith(jp_elem):
                    en_elem = ELEMENTS_JP_EN[jp_elem]
                    return f"{en_elem} {en_anion}"
    return None


def translate_japanese_chemical_name(name):
    """日本語の化合物名から、PubChem検索に使えそうな英語名候補を返す（複数試行）

    1. 慣用名辞書に完全一致すればそれを返す
    2. 無機化合物の機械的変換を試みる
    3. どちらも失敗すれば None
    """
    name = name.strip()
    if name in COMMON_NAME_JP_EN:
        return COMMON_NAME_JP_EN[name]

    inorganic = translate_japanese_inorganic_name(name)
    if inorganic:
        return inorganic

    return None
