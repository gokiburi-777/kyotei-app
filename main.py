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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        odds_data = {}

        # 方式1: oddsPoint クラスから抽出
        for td in soup.select('td.oddsPoint'):
            val = td.get_text(strip=True)
            if not val or val == '---':
                continue
            
            # クラス名から p3t_123 形式の組番を探す（td要素および親要素）
            classes = " ".join(td.get('class', []))
            parent = td.find_parent('tr')
            if parent:
                classes += " " + " ".join(parent.get('class', []))
            
            m = re.search(r'p3t_(\d)(\d)(\d)', classes)
            if m:
                key = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                odds_data[key] = val

        # 方式2: 万が一上記で取れない場合、テーブル内のテキスト（1-2-3 12.3 形式）から広域抽出
        if not odds_data:
            tables = soup.find_all('table')
            for table in tables:
                for row in table.find_all('tr'):
                    text = row.get_text(" ", strip=True)
                    # 組番とオッズ値のパターンにマッチング
                    matches = re.findall(r'(\d)-(\d)-(\d)\s+([\d\.]+)', text)
                    for m in matches:
                        key = f"{m[0]}-{m[1]}-{m[2]}"
                        odds_data[key] = m[3]

        return jsonify({'success': True, 'odds': odds_data, 'count': len(odds_data)})

    except Exception as e:
        print(f"Error fetching odds: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
