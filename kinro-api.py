/**
 * 金曜ロードショー API (Google Apps Script)
 * 
 * 公式サイト https://kinro.ntv.co.jp/ をスクレイピングして
 * 放送スケジュールを JSON で返す Web API。
 *
 * === デプロイ方法 ===
 * 1. Apps Script (script.google.com) で新規プロジェクトを作成
 * 2. このファイルの内容を貼り付け
 * 3. [デプロイ] → [新しいデプロイ] → 種類: ウェブアプリ
 *    - 実行ユーザー: 自分
 *    - アクセスできるユーザー: 全員
 * 4. デプロイ後の URL で API を呼び出す
 *
 * === エンドポイント ===
 * GET /exec                       → 次回放送 + 直近ラインナップ
 * GET /exec?type=next             → 次回放送のみ
 * GET /exec?type=lineup           → 放送作品ラインナップ一覧
 * GET /exec?type=detail&date=YYYYMMDD → 特定日の詳細
 * GET /exec?type=news             → 新着情報一覧
 * GET /exec?callback=myFunc       → JSONP 形式
 *
 * === レスポンス例 ===
 * {
 *   "status": "ok",
 *   "fetched_at": "2026-10-05T13:00:00+09:00",
 *   "next": { "title": "...", "date": "...", "url": "..." },
 *   "lineup": [ { "title": "...", "date": "...", "url": "..." } ]
 * }
 */

// ── 設定 ───────────────────────────────────────────────
const BASE_URL = 'https://kinro.ntv.co.jp';
const CACHE_KEY = 'kinro_api_cache';
const CACHE_TTL_SECONDS = 3600; // 1時間キャッシュ

// ── エントリーポイント ──────────────────────────────────

/**
 * HTTP GET リクエストを処理する。
 * @param {GoogleAppsScript.Events.DoGet} e
 */
function doGet(e) {
  const params = e.parameter || {};
  const type = params.type || 'all';
  const callback = params.callback || null;

  try {
    let data;
    switch (type) {
      case 'next':
        data = getNextBroadcast_();
        break;
      case 'lineup':
        data = getLineup_();
        break;
      case 'detail':
        if (!params.date) throw new Error('date パラメータが必要です (例: date=20261009)');
        data = getDetail_(params.date);
        break;
      case 'news':
        data = getNews_();
        break;
      case 'all':
      default:
        data = getAllData_();
        break;
    }

    const response = {
      status: 'ok',
      fetched_at: getJSTTimestamp_(),
      ...data
    };

    return buildOutput_(response, callback);

  } catch (err) {
    const errResponse = {
      status: 'error',
      fetched_at: getJSTTimestamp_(),
      message: err.message
    };
    return buildOutput_(errResponse, callback);
  }
}

// ── データ取得関数 ──────────────────────────────────────

/**
 * 全データ（次回放送 + ラインナップ + ニュース）を返す。
 */
function getAllData_() {
  const html = fetchHTML_(BASE_URL + '/');
  return {
    next: parseNext_(html),
    lineup: parseLineup_(html),
    news: parseNews_(html)
  };
}

/**
 * 次回放送情報のみ返す。
 */
function getNextBroadcast_() {
  const html = fetchHTML_(BASE_URL + '/');
  return { next: parseNext_(html) };
}

/**
 * 放送作品ラインナップを返す。
 */
function getLineup_() {
  const html = fetchHTML_(BASE_URL + '/lineup');
  return { lineup: parseLineupPage_(html) };
}

/**
 * 特定日付の放送詳細を返す。
 * @param {string} date - YYYYMMDD 形式
 */
function getDetail_(date) {
  if (!/^\d{8}$/.test(date)) {
    throw new Error('date は YYYYMMDD 形式で指定してください');
  }
  const url = `${BASE_URL}/lineup/${date}`;
  const html = fetchHTML_(url);
  return { detail: parseDetail_(html, date) };
}

/**
 * 新着ニュース一覧を返す。
 */
function getNews_() {
  const html = fetchHTML_(BASE_URL + '/');
  return { news: parseNews_(html) };
}

// ── HTML パース関数 ─────────────────────────────────────

/**
 * トップページから「次回の放送作品」をパースする。
 */
function parseNext_(html) {
  const result = {};

  // 放送日時
  const dateMatch = html.match(/<div class="mds"><h2 class="ico_next">次回の放送作品<\/h2><time>([^<]+)<\/time>/);
  result.broadcast_text = dateMatch ? dateMatch[1].trim() : null;

  // タイトル
  const titleMatch = html.match(/<p class="title">([^<]+)<\/p>/);
  result.title = titleMatch ? titleMatch[1].trim() : null;

  // 詳細URL
  const urlMatch = html.match(/<div class="photo imgfit">\s*<a href='(\/lineup\/\d+)'>/);
  if (urlMatch) {
    result.url = BASE_URL + urlMatch[1];
    result.date = urlMatch[1].replace('/lineup/', '');
  }

  // サムネイル画像
  const imgMatch = html.match(/<div class="photo imgfit">\s*<a href='\/lineup\/\d+'>\s*<img src="([^"]+)"/);
  result.thumbnail = imgMatch ? imgMatch[1] : null;

  // 「みたい!」カウント
  const mitaiMatch = html.match(/<a id="mitai_\d+" class="mitai"[^>]*>.*?<mark class="en">(\d+)<\/mark>/s);
  result.want_to_watch = mitaiMatch ? parseInt(mitaiMatch[1], 10) : null;

  // YouTube 紹介動画 ID
  const ytMatch = html.match(/\/assets\/players\/youtube\/\?id=([A-Za-z0-9_-]+)/);
  result.youtube_id = ytMatch ? ytMatch[1] : null;
  result.youtube_url = ytMatch ? `https://www.youtube.com/watch?v=${ytMatch[1]}` : null;

  return result;
}

/**
 * トップページからラインナップ（次回以降の作品）をパースする。
 */
function parseLineup_(html) {
  const lineup = [];

  // after_lineup セクション内のリストアイテムを抽出
  const sectionMatch = html.match(/<section id="after_lineup">([\s\S]*?)<\/section>/);
  if (!sectionMatch) return lineup;

  const section = sectionMatch[1];

  // 各 <li> を処理
  const liRegex = /<li>([\s\S]*?)<\/li>/g;
  let liMatch;
  while ((liMatch = liRegex.exec(section)) !== null) {
    const li = liMatch[1];
    const item = {};

    // 放送日
    const dateMatch = li.match(/<div class="date">(\d{4}\.\d{1,2}\.\d{1,2})放送<\/div>/);
    item.date = dateMatch ? dateMatch[1] : null;

    // タイトル
    const titleMatch = li.match(/<div class="title">\s*<a href='\/lineup\/\d+'>(.*?)<\/a>/s);
    item.title = titleMatch ? titleMatch[1].trim() : null;

    // URL
    const urlMatch = li.match(/href='(\/lineup\/(\d+))'/);
    if (urlMatch) {
      item.url = BASE_URL + urlMatch[1];
      item.date_key = urlMatch[2];
    }

    // サムネイル
    const imgMatch = li.match(/<img src="([^"]+)" alt="[^"]*" \/>/);
    item.thumbnail = imgMatch ? imgMatch[1] : null;

    // 「みたい!」カウント
    const mitaiMatch = li.match(/<mark class="en">(\d+)<\/mark>/);
    item.want_to_watch = mitaiMatch ? parseInt(mitaiMatch[1], 10) : null;

    if (item.title) {
      lineup.push(item);
    }
  }

  return lineup;
}

/**
 * ラインナップページ (/lineup) をパースする。
 */
function parseLineupPage_(html) {
  const lineup = [];

  const liRegex = /<li>([\s\S]*?)<\/li>/g;
  let liMatch;
  while ((liMatch = liRegex.exec(html)) !== null) {
    const li = liMatch[1];
    if (!li.includes('/lineup/')) continue;

    const item = {};

    const dateMatch = li.match(/(\d{4}\.\d{1,2}\.\d{1,2})放送/);
    item.date = dateMatch ? dateMatch[1] : null;

    const titleMatch = li.match(/<div class="title">\s*<a href='\/lineup\/\d+'>(.*?)<\/a>/s);
    item.title = titleMatch ? titleMatch[1].trim() : null;

    const urlMatch = li.match(/href='(\/lineup\/(\d+))'/);
    if (urlMatch) {
      item.url = BASE_URL + urlMatch[1];
      item.date_key = urlMatch[2];
    }

    const imgMatch = li.match(/<img src="([^"]+)"/);
    item.thumbnail = imgMatch ? imgMatch[1] : null;

    const mitaiMatch = li.match(/<mark class="en">(\d+)<\/mark>/);
    item.want_to_watch = mitaiMatch ? parseInt(mitaiMatch[1], 10) : null;

    if (item.title) {
      lineup.push(item);
    }
  }

  // 重複除去
  const seen = new Set();
  return lineup.filter(item => {
    if (!item.date_key || seen.has(item.date_key)) return false;
    seen.add(item.date_key);
    return true;
  });
}

/**
 * 個別詳細ページをパースする。
 */
function parseDetail_(html, date) {
  const detail = { date_key: date };

  // タイトル (h1 or og:title)
  const h1Match = html.match(/<h1[^>]*class="[^"]*title[^"]*"[^>]*>([\s\S]*?)<\/h1>/);
  const ogMatch = html.match(/<meta property="og:title" content="([^"]+)"/);
  detail.title = h1Match
    ? h1Match[1].replace(/<[^>]+>/g, '').trim()
    : (ogMatch ? ogMatch[1].trim() : null);

  // OGP サムネイル
  const ogImgMatch = html.match(/<meta property="og:image" content="([^"]+)"/);
  detail.thumbnail = ogImgMatch ? ogImgMatch[1] : null;

  // OGP 説明
  const ogDescMatch = html.match(/<meta property="og:description" content="([^"]+)"/);
  detail.description = ogDescMatch ? ogDescMatch[1].trim() : null;

  // 放送日テキスト
  const castMatch = html.match(/<p class="air_date[^"]*">([\s\S]*?)<\/p>/);
  detail.broadcast_text = castMatch ? castMatch[1].replace(/<[^>]+>/g, '').trim() : null;

  // YouTube
  const ytMatch = html.match(/\/assets\/players\/youtube\/\?id=([A-Za-z0-9_-]+)/);
  detail.youtube_id = ytMatch ? ytMatch[1] : null;
  detail.youtube_url = ytMatch ? `https://www.youtube.com/watch?v=${ytMatch[1]}` : null;

  // 「みたい!」カウント
  const mitaiMatch = html.match(/<mark class="en">(\d+)<\/mark>/);
  detail.want_to_watch = mitaiMatch ? parseInt(mitaiMatch[1], 10) : null;

  detail.url = `${BASE_URL}/lineup/${date}`;
  return detail;
}

/**
 * トップページから新着ニュースをパースする。
 */
function parseNews_(html) {
  const news = [];

  const sectionMatch = html.match(/<section id="head_line">([\s\S]*?)<\/section>/);
  if (!sectionMatch) return news;

  const section = sectionMatch[1];
  const liRegex = /<li>([\s\S]*?)<\/li>/g;
  let liMatch;

  while ((liMatch = liRegex.exec(section)) !== null) {
    const li = liMatch[1];
    const item = {};

    const urlMatch = li.match(/href="(\/article\/detail\/[^"]+)"/);
    item.url = urlMatch ? BASE_URL + urlMatch[1] : null;

    const txtMatch = li.match(/<div class="txt">([\s\S]*?)<\/div>/);
    item.title = txtMatch ? txtMatch[1].trim() : null;

    const dateMatch = li.match(/<div class="date">([^<]+)<\/div>/);
    item.published_at = dateMatch ? dateMatch[1].trim() : null;

    const imgMatch = li.match(/<img src="([^"]+)"/);
    item.thumbnail = imgMatch ? imgMatch[1] : null;

    if (item.title) {
      news.push(item);
    }
  }

  return news;
}

// ── ユーティリティ ──────────────────────────────────────

/**
 * URL から HTML を取得する。キャッシュあり。
 * @param {string} url
 * @returns {string} HTML 文字列
 */
function fetchHTML_(url) {
  const cache = CacheService.getScriptCache();
  const cacheKey = CACHE_KEY + '_' + url;

  // キャッシュを確認
  const cached = cache.get(cacheKey);
  if (cached) {
    return cached;
  }

  const response = UrlFetchApp.fetch(url, {
    muteHttpExceptions: true,
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; KinroGASApi/1.0)',
      'Accept': 'text/html,application/xhtml+xml',
      'Accept-Language': 'ja,en;q=0.9'
    }
  });

  if (response.getResponseCode() !== 200) {
    throw new Error(`HTTP ${response.getResponseCode()}: ${url} の取得に失敗しました`);
  }

  const html = response.getContentText('UTF-8');

  // キャッシュに保存 (最大 100KB まで)
  if (html.length < 100000) {
    cache.put(cacheKey, html, CACHE_TTL_SECONDS);
  }

  return html;
}

/**
 * JSON または JSONP のレスポンスを生成する。
 */
function buildOutput_(data, callback) {
  const json = JSON.stringify(data, null, 2);

  if (callback) {
    // JSONP
    return ContentService
      .createTextOutput(`${callback}(${json});`)
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }

  return ContentService
    .createTextOutput(json)
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * JST (UTC+9) の ISO 8601 タイムスタンプを返す。
 */
function getJSTTimestamp_() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().replace('Z', '+09:00');
}

// ── テスト用関数（GASエディタから実行可能）──────────────

/**
 * トップページの全データをログに出力してテストする。
 */
function testAll() {
  const result = getAllData_();
  Logger.log(JSON.stringify(result, null, 2));
}

/**
 * 次回放送情報をテストする。
 */
function testNext() {
  const result = getNextBroadcast_();
  Logger.log(JSON.stringify(result, null, 2));
}

/**
 * ラインナップ一覧をテストする。
 */
function testLineup() {
  const result = getLineup_();
  Logger.log(JSON.stringify(result, null, 2));
}

/**
 * キャッシュをクリアする。
 */
function clearCache() {
  const cache = CacheService.getScriptCache();
  cache.remove(CACHE_KEY + '_' + BASE_URL + '/');
  cache.remove(CACHE_KEY + '_' + BASE_URL + '/lineup');
  Logger.log('キャッシュをクリアしました');
}
