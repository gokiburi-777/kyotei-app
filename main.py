from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)

@app.route('/api/odds', methods=['GET'])
def get_odds():
    jyo = request.args.get('jyo')
    race = request.args.get('race')

    if not jyo or not race:
        return jsonify({'error': 'jyo and race are required'}), 400

    jyo_formatted = str(jyo).zfill(2)
    
    # 日本時間で当日の日付を取得 (例: 20240101)
    today = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y%m%d')
    
    # URLパラメータを「jlc」から「jcd」に修正し、「hd(日付)」を追加
    target_url = f"https://www.boatrace.jp/owpc/pc/race/odds3t?rno={race}&jcd={jyo_formatted}&hd={today}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(target_url, headers=headers, timeout=10)
        
        # 正常に取得できなかった場合のエラーハンドリング
        if res.status_code != 200:
            return jsonify({'error': f'ボートレース公式サイトからの取得に失敗しました (ステータスコード: {res.status_code})'}), res.status_code
            
        return Response(res.text, status=res.status_code, content_type='text/html; charset=utf-8')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
