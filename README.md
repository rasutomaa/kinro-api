# 金曜ロードショー API

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)


日本テレビ「金曜ロードショー」の放送スケジュールを JSON で返す非公式 Web API。  
Google Apps Script (GAS) で動作し、公式サイト [kinro.ntv.co.jp](https://kinro.ntv.co.jp/) から情報を取得する。

---

## エンドポイント

```
https://script.google.com/macros/s/AKfycbwvEaAgnS1a8fgqeKTMYswgjNmCY14XDPmI09YOv8rogSjVw1-1SUEdiaL88ZcBZfFg/exec
```

---

## パラメータ

| パラメータ | 値 | 説明 |
|---|---|---|
| `type` | 省略 / `next` / `lineup` / `detail` / `news` | 取得するデータ種別。省略時は全データ |
| `date` | `YYYYMMDD` | `type=detail` のとき必須 |
| `callback` | 関数名 | 指定時は JSONP 形式で返す |

---

## 日付フィールドの統一ルール

| フィールド | 形式 | 用途 |
|---|---|---|
| `date` | `YYYY.MM.DD` | 画面表示用 |
| `date_key` | `YYYYMMDD` | `?date=` にそのまま渡せる |
| `published_at` | `YYYY.MM.DD` | ニュース公開日 |
| `fetched_at` | ISO 8601（`+09:00`） | データ取得時刻 |

---

## レスポンス仕様

### 共通フィールド

```json
{
  "status": "ok",
  "fetched_at": "2026-10-05T13:15:28+09:00"
}
```

### `type` 省略 — 全データ

```json
{
  "status": "ok",
  "fetched_at": "2026-10-05T13:15:28+09:00",
  "next": { "...": "下記 next を参照" },
  "lineup": [ { "...": "下記 lineup[] を参照" } ],
  "news": [ { "...": "下記 news[] を参照" } ]
}
```

### `?type=next` — 次回放送のみ

```json
{
  "status": "ok",
  "fetched_at": "2026-10-05T13:15:28+09:00",
  "next": {
    "date": "2026.10.09",
    "date_key": "20261009",
    "broadcast_text": "10月9日よる9時放送",
    "title": "インサイド・ヘッド",
    "url": "https://kinro.ntv.co.jp/lineup/20261009",
    "thumbnail": "https://dtg3yjoeemd2c.cloudfront.net/cms/lineup/xxx.jpg",
    "want_to_watch": 18383,
    "youtube_id": "hgq0jBFM48w",
    "youtube_url": "https://www.youtube.com/watch?v=hgq0jBFM48w"
  }
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `date` | string | 放送日（表示用 `YYYY.MM.DD`） |
| `date_key` | string | 放送日（`YYYYMMDD`） |
| `broadcast_text` | string | 放送日時テキスト |
| `title` | string | 映画タイトル |
| `url` | string | 公式サイト作品ページ |
| `thumbnail` | string | サムネイル画像 URL |
| `want_to_watch` | number | 「みたい！」数 |
| `youtube_id` | string \| null | YouTube 予告 ID |
| `youtube_url` | string \| null | YouTube 予告 URL |

### `?type=lineup` — ラインナップ一覧

```json
{
  "status": "ok",
  "fetched_at": "2026-10-05T13:15:28+09:00",
  "lineup": [
    {
      "date": "2026.10.16",
      "date_key": "20261016",
      "title": "インサイド・ヘッド2",
      "url": "https://kinro.ntv.co.jp/lineup/20261016",
      "thumbnail": "https://...",
      "want_to_watch": 12726
    }
  ]
}
```

### `?type=detail&date=YYYYMMDD` — 特定日の詳細

```json
{
  "status": "ok",
  "fetched_at": "2026-10-05T13:15:28+09:00",
  "detail": {
    "date": "2026.10.09",
    "date_key": "20261009",
    "broadcast_text": "10月9日よる9時放送",
    "title": "インサイド・ヘッド",
    "url": "https://kinro.ntv.co.jp/lineup/20261009",
    "thumbnail": "https://...",
    "want_to_watch": 18383,
    "youtube_id": "hgq0jBFM48w",
    "youtube_url": "https://www.youtube.com/watch?v=hgq0jBFM48w"
  }
}
```

### `?type=news` — 新着ニュース

```json
{
  "status": "ok",
  "fetched_at": "2026-10-05T13:15:28+09:00",
  "news": [
    {
      "url": "https://kinro.ntv.co.jp/article/detail/20261002",
      "title": "『ゴジラ-0.0』公開記念!! 2週連続・山崎貴監督作品を放送！...",
      "published_at": "2026.10.02",
      "thumbnail": "https://..."
    }
  ]
}
```

### `?callback=関数名` — JSONP

`Content-Type: application/javascript`

```javascript
cb({"status":"ok","fetched_at":"...","next":{...}});
```

### エラー時

```json
{
  "status": "error",
  "fetched_at": "2026-10-05T13:00:00+09:00",
  "message": "date パラメータが必要です (例: date=20261009)"
}
```

| 条件 | `message` |
|---|---|
| `type=detail` で `date` 未指定 | `date パラメータが必要です (例: date=20261009)` |
| `type=detail` で該当なし | `指定日のデータが見つかりません: 20261009` |
| 不明な `type` | `不明な type です: xxxx` |
| 公式サイト取得失敗 | `公式サイトの取得に失敗しました` |

---

## 💻 使用例

### curl

```bash
BASE="https://script.google.com/macros/s/AKfycbwvEaAgnS1a8fgqeKTMYswgjNmCY14XDPmI09YOv8rogSjVw1-1SUEdiaL88ZcBZfFg/exec"

# リダイレクトがあるので -L が必要
curl -L "$BASE"
curl -L "$BASE?type=next"
curl -L "$BASE?type=lineup"
curl -L "$BASE?type=detail&date=20261009"
curl -L "$BASE?type=news"
curl -L "$BASE?callback=cb"
```

### JavaScript (fetch)

```javascript
const BASE = 'https://script.google.com/macros/s/AKfycbwvEaAgnS1a8fgqeKTMYswgjNmCY14XDPmI09YOv8rogSjVw1-1SUEdiaL88ZcBZfFg/exec';

const res  = await fetch(BASE);
const data = await res.json();

console.log(data.next.title);          // "インサイド・ヘッド"
console.log(data.next.broadcast_text); // "10月9日よる9時放送"
console.log(data.next.date_key);       // "20261009"
console.log(data.next.youtube_url);    // "https://www.youtube.com/watch?v=..."
```

### Python

```python
import requests

BASE = 'https://script.google.com/macros/s/AKfycbwvEaAgnS1a8fgqeKTMYswgjNmCY14XDPmI09YOv8rogSjVw1-1SUEdiaL88ZcBZfFg/exec'

res  = requests.get(BASE, params={'type': 'next'})
data = res.json()

print(data['next']['title'])          # インサイド・ヘッド
print(data['next']['broadcast_text']) # 10月9日よる9時放送
print(data['next']['date_key'])       # 20261009
```

---

## ⚠️ 注意事項

- 個人・学習・非商用目的での利用を想定
- 公式サイトの HTML 構造が変わるとパースが壊れる場合がある
