from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  # GitHub Pagesからのアクセスを許可

@app.route('/api/odds', methods=['GET'])
def get_odds():
    jyo = request.args.get('jyo')
    race = request.args.get('race')

    if not jyo or not race:
        return jsonify({'success': False, 'error': 'jyo and race are required'}), 400

    target_url = f"https://www.boatrace.jp/owpc/pc/race/odds3t?rno={race}&jlc={jyo}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        odds_data = {}

        # 3連単オッズテーブルの解析
        tables = soup.find_all('table', class_='table1')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                combo_td = row.find('td', class_='oddsPoint')
                if combo_td:
                    tr_class = " ".join(row.get('class', []))
                    import re
                    match = re.search(r'p3t_(\d)(\d)(\d)', tr_class)
                    if match:
                        key = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                        val = combo_td.get_text(strip=True)
                        odds_data[key] = val if val else '---'

        if not odds_data:
            # フォールバック処理
            odds_tds = soup.find_all('td', class_='oddsPoint')
            for td in odds_tds:
                val = td.get_text(strip=True)
                prev = td.find_previous_sibling()
                if prev:
                    prev_text = prev.get_text(strip=True)
                    if re.match(r'^\d-\d-\d$', prev_text):
                        odds_data[prev_text] = val

        return jsonify({'success': True, 'odds': odds_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
