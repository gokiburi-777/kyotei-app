from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re  # 先頭でインポート

app = Flask(__name__)
CORS(app)  # 全ドメインからのアクセスを許可

@app.route('/api/odds', methods=['GET'])
def get_odds():
    jyo = request.args.get('jyo')
    race = request.args.get('race')

    if not jyo or not race:
        return jsonify({'success': False, 'error': 'jyo and race are required'}), 400

    # 場コードを2桁（例: 1 -> 01）に補正
    jyo_formatted = str(jyo).zfill(2)
    target_url = f"https://www.boatrace.jp/owpc/pc/race/odds3t?rno={race}&jlc={jyo_formatted}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        odds_data = {}

        # 方法1: oddsPoint クラスのセルから直接探索
        odds_tds = soup.find_all('td', class_='oddsPoint')
        for td in odds_tds:
            val = td.get_text(strip=True)
            # td要素のクラス名（例: p3t_123）から組番を取得
            td_classes = " ".join(td.get('class', []))
            match = re.search(r'p3t_(\d)(\d)(\d)', td_classes)
            if match:
                key = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                odds_data[key] = val if val else '---'
            else:
                # 親の tr 要素のクラス名からも探す
                parent_tr = td.find_parent('tr')
                if parent_tr:
                    tr_classes = " ".join(parent_tr.get('class', []))
                    match_tr = re.search(r'p3t_(\d)(\d)(\d)', tr_classes)
                    if match_tr:
                        key = f"{match_tr.group(1)}-{match_tr.group(2)}-{match_tr.group(3)}"
                        odds_data[key] = val if val else '---'

        # 方法2: テーブル行のテキストからフォールバック解析
        if not odds_data:
            rows = soup.find_all('tr')
            for row in rows:
                text = row.get_text(" ", strip=True)
                # 「1-2-3 12.3」のようなパターンを検出
                m = re.search(r'(\d)-(\d)-(\d)\s+([\d\.]+)', text)
                if m:
                    key = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                    odds_data[key] = m.group(4)

        return jsonify({'success': True, 'odds': odds_data})

    except Exception as e:
        print(f"Error fetching odds: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
