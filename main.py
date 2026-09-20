from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)

# 3連単120通りの画面上の出現順序を生成する関数
def generate_combo_order():
    combos = []
    for first in range(1, 7):
        seconds = [x for x in range(1, 7) if x != first]
        # 公式サイトの表は縦に4行並んでいる
        for row in range(4):
            for second in seconds:
                thirds = [y for y in range(1, 7) if y != first and y != second]
                third = thirds[row]
                combos.append(f"{first}-{second}-{third}")
    return combos

COMBO_ORDER = generate_combo_order()

@app.route('/api/odds', methods=['GET'])
def get_odds():
    jyo = request.args.get('jyo')
    race = request.args.get('race')

    if not jyo or not race:
        return jsonify({'error': 'jyo and race are required'}), 400

    jyo_formatted = str(jyo).zfill(2)
    today = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y%m%d')
    target_url = f"https://www.boatrace.jp/owpc/pc/race/odds3t?rno={race}&jcd={jyo_formatted}&hd={today}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=10)
        if res.status_code != 200:
            return jsonify({'error': f'取得失敗 (ステータス: {res.status_code})'}), res.status_code

        # BeautifulSoupでオッズのセルをすべて取得
        soup = BeautifulSoup(res.content, 'html.parser')
        odds_elements = soup.select('td.oddsPoint')

        # 発売前や中止などでオッズが120個ない場合の処理
        if len(odds_elements) != 120:
            return jsonify({'error': 'オッズがまだ公開されていないか、取得できませんでした。'}), 404

        # 120通りの組み合わせと抽出したオッズをマッピング
        result_odds = {}
        for combo, el in zip(COMBO_ORDER, odds_elements):
            text = el.get_text(strip=True)
            result_odds[combo] = text

        return jsonify(result_odds)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
