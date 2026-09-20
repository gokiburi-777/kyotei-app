from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import time

app = Flask(__name__)
CORS(app)

# 1. まず最初に「generate_combo_order関数」を定義する
def generate_combo_order():
    combos = []
    for second_idx in range(5):
        for third_idx in range(4):
            for first in range(1, 7):
                seconds = [x for x in range(1, 7) if x != first]
                second = seconds[second_idx]
                thirds = [y for y in range(1, 7) if y != first and y != second]
                third = thirds[third_idx]
                combos.append(f"{first}-{second}-{third}")
    return combos

# 2. その後で関数を呼び出して定数に代入する
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
        max_retries = 3
        res = None
        
        for attempt in range(max_retries):
            try:
                res = requests.get(target_url, headers=headers, timeout=20)
                if res.status_code == 200:
                    break
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    return jsonify({'error': '公式サイトが混雑しており、タイムアウトしました。少し時間をおいて再度お試しください。'}), 504
                time.sleep(1)
        
        if res is None or res.status_code != 200:
            status = res.status_code if res else 'Unknown'
            return jsonify({'error': f'取得失敗 (ステータス: {status})'}), 500

        soup = BeautifulSoup(res.content, 'html.parser')
        odds_elements = soup.select('td.oddsPoint')

        if len(odds_elements) != 120:
            return jsonify({'error': f'オッズの要素数が不正です ({len(odds_elements)}件)。まだ公開されていないか、欠場艇がいる可能性があります。'}), 404

        result_odds = {}
        for combo, el in zip(COMBO_ORDER, odds_elements):
            text = el.get_text(strip=True)
            result_odds[combo] = text

        return jsonify(result_odds)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
