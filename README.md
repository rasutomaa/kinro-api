# 📽️ 金曜ロードショー API

日本テレビ「金曜ロードショー」の放送スケジュールを JSON で返す非公式 Web API です。  
Google Apps Script (GAS) で動作し、公式サイト [kinro.ntv.co.jp](https://kinro.ntv.co.jp/) から情報を取得します。

## 🌐 エンドポイント

```
https://script.google.com/macros/s/AKfycbwvEaAgnS1a8fgqeKTMYswgjNmCY14XDPmI09YOv8rogSjVw1-1SUEdiaL88ZcBZfFg/exec
```

---

## 📡 API リファレンス

| パラメータ | 説明 |
|---|---|
| *(なし)* | 全データ（次回放送 + ラインナップ + ニュース） |
| `?type=next` | 次回放送のみ |
| `?type=lineup` | 放送ラインナップ一覧 |
| `?type=detail&date=YYYYMMDD` | 特定日の詳細 |
| `?type=news` | 新着ニュース一覧 |
| `?callback=関数名` | JSONP 形式で返す |

---

## 💻 使用例

### curl

```bash
# リダイレクトがあるので -L が必要
curl -L "https://script.google.com/macros/s/AKfycbydtL5-KrZ7Oha7ZlZ8BAuuHiFqHlhMtCAryPyNN7b3GZZJhkEJgbZTDjfeulLOfF4z/exec"

# 次回放送だけ
curl -L "...exec?type=next"

# 特定日の詳細
curl -L "...exec?type=detail&date=20261009"
```

### JavaScript (fetch)

```javascript
const BASE = 'https://script.google.com/macros/s/AKfycbydtL5-KrZ7Oha7ZlZ8BAuuHiFqHlhMtCAryPyNN7b3GZZJhkEJgbZTDjfeulLOfF4z/exec';

const res = await fetch(BASE);
const data = await res.json();

console.log(data.next.title);         // "インサイド・ヘッド"
console.log(data.next.broadcast_text); // "10月9日よる9時放送"
console.log(data.next.youtube_url);   // "https://www.youtube.com/watch?v=..."
```

### Python

```python
import requests

BASE = 'https://script.google.com/macros/s/AKfycbydtL5-KrZ7Oha7ZlZ8BAuuHiFqHlhMtCAryPyNN7b3GZZJhkEJgbZTDjfeulLOfF4z/exec'

res = requests.get(BASE, params={'type': 'next'})
data = res.json()

print(data['next']['title'])          # インサイド・ヘッド
print(data['next']['broadcast_text']) # 10月9日よる9時放送
```

---

## 📦 レスポンス仕様

### `GET /exec` — 全データ

```json
{
  "status": "ok",
  "fetched_at": "2026-10-05T13:15:28+09:00",
  "next": {
    "broadcast_text": "10月9日よる9時放送",
    "title": "インサイド・ヘッド",
    "url": "https://kinro.ntv.co.jp/lineup/20261009",
    "date": "20261009",
    "thumbnail": "https://dtg3yjoeemd2c.cloudfront.net/cms/lineup/xxx.jpg",
    "want_to_watch": 18383,
    "youtube_id": "hgq0jBFM48w",
    "youtube_url": "https://www.youtube.com/watch?v=hgq0jBFM48w"
  },
  "lineup": [
    {
      "date": "2026.10.16",
      "title": "インサイド・ヘッド2",
      "url": "https://kinro.ntv.co.jp/lineup/20261016",
      "date_key": "20261016",
      "thumbnail": "https://...",
      "want_to_watch": 12726
    },
    {
      "date": "2026.10.23",
      "title": "ALWAYS 三丁目の夕日",
      "url": "https://kinro.ntv.co.jp/lineup/20261023",
      "date_key": "20261023",
      "thumbnail": "https://...",
      "want_to_watch": 1418
    },
    {
      "date": "2026.10.30",
      "title": "ゴジラ-1.0",
      "url": "https://kinro.ntv.co.jp/lineup/20261030",
      "date_key": "20261030",
      "thumbnail": "https://...",
      "want_to_watch": 2072
    }
  ],
  "news": [
    {
      "url": "https://kinro.ntv.co.jp/article/detail/20261002",
      "title": "『ゴジラ-0.0』公開記念!! 2週連続・山崎貴監督作品を放送！...",
      "published_at": "2026.10.2",
      "thumbnail": "https://..."
    }
  ]
}
```

### フィールド説明

#### `next` — 次回放送

| フィールド | 型 | 説明 |
|---|---|---|
| `broadcast_text` | string | 放送日時テキスト（例: "10月9日よる9時放送"） |
| `title` | string | 映画タイトル |
| `url` | string | 公式サイトの作品ページ URL |
| `date` | string | 放送日 (YYYYMMDD) |
| `thumbnail` | string | サムネイル画像 URL |
| `want_to_watch` | number | 「みたい！」ボタンの押された数 |
| `youtube_id` | string \| null | YouTube 予告動画 ID |
| `youtube_url` | string \| null | YouTube 予告動画 URL |

#### `lineup[]` — ラインナップ

| フィールド | 型 | 説明 |
|---|---|---|
| `date` | string | 放送日（例: "2026.10.16"） |
| `title` | string | 映画タイトル |
| `url` | string | 公式サイトの作品ページ URL |
| `date_key` | string | 放送日 (YYYYMMDD) |
| `thumbnail` | string | サムネイル画像 URL |
| `want_to_watch` | number | 「みたい！」ボタンの押された数 |

#### エラー時

```json
{
  "status": "error",
  "fetched_at": "2026-10-05T13:00:00+09:00",
  "message": "date パラメータが必要です (例: date=20261009)"
}
```

---



## ⚠️ 注意事項

- 本ツールは個人・学習・非商用目的での利用を想定しています
- 公式サイトの HTML 構造が変わるとパースが壊れる場合があります
- レスポンスは **1時間キャッシュ** されます（`CACHE_TTL_SECONDS` で変更可能）
