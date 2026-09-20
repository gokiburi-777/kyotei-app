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
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Chrome/120.0.0.0 Safari/537.36)'
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        odds_data = {}

        # 3連単テーブル (table.table1) を解析
        tables = soup.find_all('table', class_='table1')
        
        for table in tables:
            # 1着の各ブロック (tbody) ごとにループ
            tbodies = table.find_all('tbody')
            for tbody in tbodies:
                rows = tbody.find_all('tr')
                if not rows:
                    continue
                
                # 1着艇番号の特定
                first_boat = None
                for row in rows:
                    th_first = row.find('th', class_=re.compile(r'is-boatColor\d'))
                    if th_first and th_first.get_text(strip=True).isdigit():
                        first_boat = th_first.get_text(strip=True)
                        break
                
                if not first_boat:
                    continue

                # 各行から2着・3着・オッズを抽出
                current_second = None
                for row in rows:
                    tds = row.find_all('td')
                    if not tds:
                        continue

                    # 2着艇が含まれるセルがあるか
                    td_second = row.find('td', class_=re.compile(r'is-boatColor\d'))
                    if td_second and td_second.get_text(strip=True).isdigit():
                        current_second = td_second.get_text(strip=True)

                    # 3着艇とオッズ数値の抽出
                    # オッズが入るセルは class="oddsPoint" またはテキストが数値
                    for i, td in enumerate(tds):
                        text = td.get_text(strip=True)
                        # 小数点を含む数値（例: 12.4）または不成立等（---）
                        if re.match(r'^\d+\.\d+$', text) or text == '---':
                            # 直前または同ブロック内の3着艇を探す
                            # 艇番号(1~6)とオッズ値のペア
                            third_boat = None
                            if i > 0 and tds[i-1].get_text(strip=True).isdigit():
                                third_boat = tds[i-1].get_text(strip=True)

                            if current_second and third_boat:
                                key = f"{first_boat}-{current_second}-{third_boat}"
                                odds_data[key] = text

        # 上記で万が一漏れた場合のフォールバック（文字列全走査）
        if not odds_data:
            # ページ内の「1-2-3 12.3」または「1 2 3 12.3」のパターンを抽出
            full_text = soup.get_text(" ", strip=True)
            matches = re.findall(r'(\d)\s*[\-\s]\s*(\d)\s*[\-\s]\s*(\d)\s+([\d\.]+)', full_text)
            for m in matches:
                if len(set(m[:3])) == 3: # 1-2-3が全て異なる番号の場合のみ
                    key = f"{m[0]}-{m[1]}-{m[2]}"
                    odds_data[key] = m[3]

        return jsonify({
            'success': True, 
            'odds': odds_data, 
            'count': len(odds_data)
        })

    except Exception as e:
        print(f"Error fetching odds: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
