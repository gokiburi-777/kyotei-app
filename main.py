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
    # PC版オッズページURL
    target_url = f"https://www.boatrace.jp/owpc/pc/race/odds3t?rno={race}&jlc={jyo_formatted}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8'
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        odds_data = {}

        # td要素の中から、クラス名「oddsPoint」または数値データが入っているセルを全網羅
        # 公式サイトの oddsPoint セルは内包テキストにオッズ値（例: 12.3）が入る
        points = soup.find_all('td', class_='oddsPoint')
        
        for pt in points:
            val = pt.get_text(strip=True)
            if not val:
                continue
            
            # 親の tr や td 自身の class に含まれる p3t_1-2-3 や p3t_123 などの識別文字列を探す
            parent_tr = pt.find_parent('tr')
            classes_str = " ".join(pt.get('class', []))
            if parent_tr:
                classes_str += " " + " ".join(parent_tr.get('class', []))

            # クラス名から 3連単の組み合せ（1-2-3）を抽出
            m = re.search(r'p3t_(\d)(\d)(\d)', classes_str)
            if m:
                key = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                odds_data[key] = val

        # 上記で取れなかった場合：テーブル全行から強引に「1 2 3 12.3」の並びを直接パース
        if not odds_data:
            for tr in soup.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th']) if td.get_text(strip=True)]
                # セル数が足りない行はスキップ
                if len(cells) < 3:
                    continue
                # 文字列全体から「数字-数字-数字 数値」パターンを検出
                line = " ".join(cells)
                matches = re.findall(r'(\d)\s*[\-\s]\s*(\d)\s*[\-\s]\s*(\d)\s+([\d\.\-]+)', line)
                for m in matches:
                    if len(set(m[:3])) == 3: # 舟番が重複していない場合
                        odds_data[f"{m[0]}-{m[1]}-{m[2]}"] = m[3]

        return jsonify({
            'success': True,
            'odds': odds_data,
            'count': len(odds_data),
            'url': target_url
        })

    except Exception as e:
        print(f"Error fetching odds: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
