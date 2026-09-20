from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

@app.route('/api/odds', methods=['GET'])
def get_odds():
    jyo = request.args.get('jyo')
    race = request.args.get('race')

    if not jyo or not race:
        return jsonify({'success': False, 'error': 'jyo and race are required'}), 400

    jyo_formatted = str(jyo).zfill(2)
    target_url = f"https://www.boatrace.jp/owpc/pc/race/odds3t?rno={race}&jlc={jyo_formatted}"
    
    # ブラウザに完全に偽装するための標準ヘッダー
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Referer': 'https://www.boatrace.jp/'
    }

    try:
        session = requests.Session()
        res = session.get(target_url, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        odds_data = {}

        # 3連単テーブル (table1) の解析
        tables = soup.select('table.table1')
        
        for table in tables:
            tbodies = table.select('tbody')
            for tbody in tbodies:
                rows = tbody.select('tr')
                if not rows:
                    continue

                # 1着艇の番号を取得
                first_boat = None
                for r in rows:
                    th = r.select_one('th[class*="is-boatColor"]')
                    if th and th.get_text(strip=True).isdigit():
                        first_boat = th.get_text(strip=True)
                        break

                if not first_boat:
                    continue

                # 2着・3着・オッズを取得
                current_second = None
                for r in rows:
                    # 2着の艇番号
                    td_sec = r.select_one('td[class*="is-boatColor"]')
                    if td_sec and td_sec.get_text(strip=True).isdigit():
                        current_second = td_sec.get_text(strip=True)

                    # 3着とオッズ値のペアを解析
                    tds = r.select('td')
                    for i, td in enumerate(tds):
                        text = td.get_text(strip=True)
                        # オッズ数値（12.3 や --- など）
                        if re.match(r'^[\d\.\-]+$', text) and len(text) > 0:
                            # 前のセルに3着艇の数字があるか確認
                            third_boat = None
                            if i > 0 and tds[i-1].get_text(strip=True).isdigit():
                                third_boat = tds[i-1].get_text(strip=True)

                            if current_second and third_boat:
                                key = f"{first_boat}-{current_second}-{third_boat}"
                                odds_data[key] = text

        # バックアップ解析（テキスト全体から抽出）
        if not odds_data:
            text = soup.get_text(" ", strip=True)
            matches = re.findall(r'(\d)\s*[\-\s]\s*(\d)\s*[\-\s]\s*(\d)\s+([\d\.]+)', text)
            for m in matches:
                if len(set(m[:3])) == 3:
                    odds_data[f"{m[0]}-{m[1]}-{m[2]}"] = m[3]

        return jsonify({
            'success': True,
            'odds': odds_data,
            'count': len(odds_data),
            'html_len': len(res.text)  # デバッグ用：取得したHTMLの長さ
        })

    except Exception as e:
        print(f"Error fetching odds: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
