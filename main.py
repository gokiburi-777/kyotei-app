<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>競艇オッズ確認アプリ</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #f4f6f9;
            color: #333;
            padding: 15px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: #fff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        h1 {
            font-size: 1.4rem;
            margin-bottom: 20px;
            text-align: center;
            color: #1a365d;
        }
        .control-panel {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 20px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        label {
            font-size: 0.85rem;
            font-weight: bold;
            color: #4a5568;
        }
        select, button {
            padding: 10px;
            font-size: 1rem;
            border-radius: 8px;
            border: 1px solid #cbd5e0;
            outline: none;
        }
        select:focus {
            border-color: #3182ce;
        }
        .btn-update {
            grid-column: span 2;
            background-color: #3182ce;
            color: white;
            font-weight: bold;
            border: none;
            cursor: pointer;
            transition: background 0.2s;
            margin-top: 5px;
        }
        .btn-update:hover {
            background-color: #2b6cb0;
        }
        .btn-update:disabled {
            background-color: #a0aec0;
            cursor: not-allowed;
        }
        #status-message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 6px;
            font-size: 0.9rem;
            text-align: center;
            display: none;
        }
        .status-loading {
            background-color: #ebf8ff;
            color: #2b6cb0;
        }
        .status-success {
            background-color: #f0fff4;
            color: #2f855a;
        }
        .status-error {
            background-color: #fff5f5;
            color: #c53030;
        }
        .odds-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
            gap: 8px;
            margin-top: 15px;
        }
        .odds-card {
            background: #edf2f7;
            padding: 8px;
            border-radius: 6px;
            text-align: center;
            font-size: 0.85rem;
        }
        .odds-card .kumi {
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 4px;
        }
        .odds-card .val {
            color: #e53e3e;
            font-weight: bold;
        }
    </style>
</head>
<body>

<div class="container">
    <h1>🚤 3連単オッズ取得</h1>

    <div class="control-panel">
        <div class="form-group">
            <label for="jyo-select">競艇場</label>
            <select id="jyo-select">
                <option value="01">01# 桐生</option>
                <option value="02">02# 戸田</option>
                <option value="03">03# 江戸川</option>
                <option value="04">04# 平和島</option>
                <option value="05">05# 多摩川</option>
                <option value="06">06# 浜名湖</option>
                <option value="07">07# 蒲郡</option>
                <option value="08">08# 常滑</option>
                <option value="09">09# 津</option>
                <option value="10">10# 三国</option>
                <option value="11">11# びわこ</option>
                <option value="12">12# 住之江</option>
                <option value="13">13# 尼崎</option>
                <option value="14">14# 鳴門</option>
                <option value="15">15# 丸亀</option>
                <option value="16">16# 児島</option>
                <option value="17">17# 宮島</option>
                <option value="18">18# 徳山</option>
                <option value="19">19# 下関</option>
                <option value="20">20# 若松</option>
                <option value="21">21# 芦屋</option>
                <option value="22">22# 福岡</option>
                <option value="23">23# 唐津</option>
                <option value="24">24# 大村</option>
            </select>
        </div>

        <div class="form-group">
            <label for="race-select">レース番号</label>
            <select id="race-select">
                <option value="1">1 R</option>
                <option value="2">2 R</option>
                <option value="3">3 R</option>
                <option value="4">4 R</option>
                <option value="5">5 R</option>
                <option value="6">6 R</option>
                <option value="7">7 R</option>
                <option value="8">8 R</option>
                <option value="9">9 R</option>
                <option value="10">10 R</option>
                <option value="11">11 R</option>
                <option value="12">12 R</option>
            </select>
        </div>

        <button id="btn-fetch" class="btn-update" onclick="loadOdds()">オッズ更新</button>
    </div>

    <div id="status-message"></div>

    <div id="odds-list" class="odds-container"></div>
</div>

<script>
    const RENDER_API_BASE = "https://kyotei-app-41wq.onrender.com";

    async function loadOdds() {
        const jyo = document.getElementById("jyo-select").value;
        const race = document.getElementById("race-select").value;
        const btn = document.getElementById("btn-fetch");
        const status = document.getElementById("status-message");
        const oddsList = document.getElementById("odds-list");

        btn.disabled = true;
        status.style.display = "block";
        status.className = "status-loading";
        status.textContent = "オッズデータを取得中...";
        oddsList.innerHTML = "";

        try {
            const apiUrl = `${RENDER_API_BASE}/api/odds?jyo=${jyo}&race=${race}`;
            const response = await fetch(apiUrl);

            if (!response.ok) {
                throw new Error(`サーバーエラー: ${response.status}`);
            }

            const htmlText = await response.text();
            
            // 解析実行
            const oddsData = parseOddsHTML(htmlText);
            const count = Object.keys(oddsData).length;

            if (count === 0) {
                status.className = "status-error";
                status.textContent = "オッズを取得できませんでした。（発売前・締切後・または指定レース未開催の可能性があります）";
            } else {
                status.className = "status-success";
                status.textContent = `取得成功！ 合計 ${count} 件のオッズを表示中`;
                renderOdds(oddsData);
            }

        } catch (error) {
            console.error("エラー詳細:", error);
            status.className = "status-error";
            status.textContent = `通信エラーが発生しました: ${error.message}`;
        } finally {
            btn.disabled = false;
        }
    }

    // より堅牢なオッズ解析ロジック
    function parseOddsHTML(htmlText) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlText, "text/html");
        const oddsData = {};

        // 1. oddsPoint クラスのセルからのダイレクト抽出
        const oddsTds = doc.querySelectorAll("td.oddsPoint");
        oddsTds.forEach(td => {
            const val = td.textContent.trim();
            if (!val) return;

            // クラス名 (例: p3t_123 や p3t_1-2-3) を探索
            let classStr = td.className || "";
            const parentTr = td.closest("tr");
            if (parentTr) {
                classStr += " " + parentTr.className;
            }

            const match = classStr.match(/p3t_(\d)[\-_]?(\d)[\-_]?(\d)/);
            if (match) {
                const key = `${match[1]}-${match[2]}-${match[3]}`;
                oddsData[key] = val;
            }
        });

        // 2. 万が一取れなかった場合の全テーブル行スキャン
        if (Object.keys(oddsData).length === 0) {
            const trs = doc.querySelectorAll("tr");
            trs.forEach(tr => {
                const text = tr.innerText || tr.textContent;
                // 「1-2-3 12.3」のパターンを全てマッチング
                const matches = [...text.matchAll(/(\d)\s*[\-\s]\s*(\d)\s*[\-\s]\s*(\d)\s+([\d\.]+)/g)];
                matches.forEach(m => {
                    const [_, b1, b2, b3, val] = m;
                    if (new Set([b1, b2, b3]).size === 3) {
                        oddsData[`${b1}-${b2}-${b3}`] = val;
                    }
                });
            });
        }

        console.log("解析成功件数:", Object.keys(oddsData).length, oddsData);
        return oddsData;
    }

    function renderOdds(oddsData) {
        const oddsList = document.getElementById("odds-list");
        oddsList.innerHTML = "";

        const keys = Object.keys(oddsData).sort();

        keys.forEach(key => {
            const card = document.createElement("div");
            card.className = "odds-card";
            card.innerHTML = `
                <div class="kumi">${key}</div>
                <div class="val">${oddsData[key]}</div>
            `;
            oddsList.appendChild(card);
        });
    }
</script>

</body>
</html>
