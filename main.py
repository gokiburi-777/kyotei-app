from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)

# 3連単120通りの画面上の出現順序（HTMLのテーブル構造）を正確に再現
def generate_combo_order():
    combos = []
    # 2着のブロック（上から下へ5パターン）
    for second_idx in range(5):
        # 3着の行（各2着ブロック内で上から下へ4行）
        for third_idx in range(4):
            # 1着の列（左から右へ1号艇〜6号艇の6列）
            for first in range(1, 7):
                
                # 1着以外の5艇から、該当する2着を選択
                seconds = [x for x in range(1, 7) if x != first]
                second = seconds[second_idx]
                
                # 1着、2着以外の4艇から、該当する3着を選択
                thirds = [y for y in range(1, 7) if y != first and y != second]
                third = thirds[third_idx]
                
                combos.append(f"{first}-{second}-{third}")
    return combos

# 起動時に1回だけ120通りの正しい順番リストを生成
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

        soup = BeautifulSoup(res.content, 'html.parser')
        # td.oddsPoint を抽出すると、必ず「左から右、上から下」の順番で120個取得される
        odds_elements = soup.select('td.oddsPoint')

        if len(odds_elements) != 120:
            return jsonify({'error': f'オッズの要素数が不正です ({len(odds_elements)}件)。まだ公開されていないか、欠場艇がいる可能性があります。'}), 404

        # 順番リストと抽出したオッズをガッチャンコする
        result_odds = {}
        for combo, el in zip(COMBO_ORDER, odds_elements):
            text = el.get_text(strip=True)
            result_odds[combo] = text

        return jsonify(result_odds)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
