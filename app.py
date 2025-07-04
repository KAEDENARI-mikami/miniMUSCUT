#!/usr/bin/env python3
"""
Flask版 統合大学ポータルシステム v6.1 (NameError修正版)
 - ゲーム機能、ポイント送金機能など全機能搭載
"""
import os
import json
import hashlib
import calendar
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, date
from functools import wraps
try:
    from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
except ImportError:
    raise ImportError("Flaskがインストールされていません。'pip install flask' を実行してください。")

# ───────── グローバル設定 ─────────
DATA_DIR = "."
USER_FILE = os.path.join(DATA_DIR, "portal_users.json")
POST_FILE = os.path.join(DATA_DIR, "portal_posts.json")
RESV_FILE = os.path.join(DATA_DIR, "portal_reservations.json")
ANNOUNCE_FILE = os.path.join(DATA_DIR, "portal_announcements.json")
SCHEDULE_FILE = os.path.join(DATA_DIR, "portal_schedules.json")
SECRET_KEY = "a-super-secure-key-for-the-game-version"

CAMPUSES = { "ariake": {"name": "有明キャンパス", "rooms": 30}, "musashino": {"name": "武蔵野キャンパス", "rooms": 30} }
OPEN_TIME, CLOSE_TIME = 8, 22
MAX_HOURS_PER_DAY = 4
VIOLATION_LIMIT = 3
POINT_ON_QUESTION, POINT_ON_ANSWER, POINT_ON_BEST_ANSWER = 1, 2, 10
TITLES = { "駆け出し投稿者": {"type": "points", "value": 10, "desc": "累計10ポイント獲得"}, "知恵の共有者": {"type": "points", "value": 50, "desc": "累計50ポイント獲得"}, "コミュニティの賢者": {"type": "points", "value": 200, "desc": "累計200ポイント獲得"}, "質問者": {"type": "questions", "value": 5, "desc": "5回質問する"}, "回答者": {"type": "answers", "value": 10, "desc": "10回回答する"}, "ベストアンサーマスター": {"type": "best_answers", "value": 5, "desc": "ベストアンサーを5回獲得"}, "予約デビュー": {"type": "reservations", "value": 1, "desc": "初めて予約する"}, "計画の達人": {"type": "reservations", "value": 10, "desc": "10回予約する"}, "自習室の主": {"type": "reservations", "value": 50, "desc": "50回予約する"}, }
SECRET_TITLES = { "自己解決者": "自分の質問に自分で回答し、BAに選ぶ", "深夜のフクロウ": "深夜2時～4時の間に投稿または予約する", "探求者": "存在しないページに3回アクセスしようとする", "朝活": "朝8時に予約を入れる", }
SHOP_TITLES = { "富豪": {"price": 500, "desc": "500ptで交換できる称号"}, "大富豪": {"price": 1000, "desc": "1000ptで交換できる称号"}, "ポータルマスター": {"price": 2500, "desc": "このサイトを極めた者の証"}, }
PROFILE_THEMES = { "theme-default": {"name": "デフォルト", "price": 0}, "theme-night": {"name": "ナイトモード", "price": 100}, "theme-sakura": {"name": "桜", "price": 200}, "theme-ocean": {"name": "オーシャン", "price": 300}, }

# ───────── 1. ユーザー管理 (UserManager) ─────────
class UserManager:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(USER_FILE):
            with open(USER_FILE, "w") as f: json.dump({}, f)
        self._load()
        if "admin" not in self.users: self.register("admin", "admin", role="admin")
    def _load(self):
        with open(USER_FILE, 'r') as f: self.users = json.load(f)
    def _save(self):
        with open(USER_FILE, "w") as f: json.dump(self.users, f, indent=2)
    @staticmethod
    def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()
    def get_user(self, uid): return self.users.get(uid)
    def get_all_users(self): return self.users.keys()
    def register(self, uid, pw, role="user"):
        if uid in self.users: return False
        self.users[uid] = {"pw": self._hash(pw), "role": role, "status": "active", "points": 0, "titles": [],
                           "questions": 0, "answers": 0, "best_answers": 0, "vio": 0, "reservations": 0, "404_count": 0,
                           "unlocked_themes": ["theme-default"], "current_theme": "theme-default"}
        self._save(); return True
    def verify(self, uid, pw):
        user = self.get_user(uid); return user and user["pw"] == self._hash(pw)
    def is_admin(self, uid):
        user = self.get_user(uid); return user and user.get("role") == "admin"
    def add_points(self, uid, points):
        if uid in self.users:
            self.users[uid]["points"] += points; self._save(); self.check_and_award_titles(uid)
    def increment_counter(self, uid, counter_type):
        if uid in self.users and counter_type in self.users[uid]:
            self.users[uid][counter_type] += 1; self._save(); self.check_and_award_titles(uid)
    def adjust_violation(self, uid, amount):
        if uid in self.users:
            self.users[uid]["vio"] = max(0, self.users[uid]["vio"] + amount) 
            if amount > 0:
                flash(f"違反カウントが1増加しました (現在: {self.users[uid]['vio']})", "warning")
                if self.users[uid]["vio"] >= VIOLATION_LIMIT:
                    self.users[uid]["status"] = "banned"; flash("違反回数が上限に達したためアカウントが利用停止になりました", "danger")
            else: flash(f"違反カウントが1減少しました (現在: {self.users[uid]['vio']})", "info")
            self._save()
    def toggle_ban(self, uid):
        if uid in self.users and uid != 'admin':
            self.users[uid]["status"] = "active" if self.users[uid]["status"] == "banned" else "banned"; self._save()
    def award_title(self, uid, title):
        if uid in self.users and title not in self.users[uid].get("titles", []):
            if "titles" not in self.users[uid]: self.users[uid]["titles"] = []
            self.users[uid]["titles"].append(title); flash(f"称号「{title}」を獲得しました！", "success"); self._save()
    def check_and_award_titles(self, uid, **kwargs):
        user = self.get_user(uid)
        if not user: return
        for title, cond in TITLES.items():
            if user.get(cond["type"], 0) >= cond["value"]: self.award_title(uid, title)
        if kwargs.get("self_answered"): self.award_title(uid, "自己解決者")
        if kwargs.get("night_activity"): self.award_title(uid, "深夜のフクロウ")
        if user.get("404_count", 0) >= 3: self.award_title(uid, "探求者")
        if kwargs.get("early_bird"): self.award_title(uid, "朝活")
    def purchase_item(self, uid, item_id, item_type):
        user = self.get_user(uid)
        if not user: return False, "ユーザーが存在しません。"
        item_list = SHOP_TITLES if item_type == "title" else PROFILE_THEMES
        if item_id not in item_list: return False, "存在しないアイテムです。"
        item = item_list[item_id]
        if user["points"] < item["price"]: return False, "ポイントが不足しています。"
        if item_type == "title":
            if item_id in user.get("titles", []): return False, "その称号は既に所有しています。"
            user["points"] -= item["price"]; self.award_title(uid, item_id)
        elif item_type == "theme":
            if item_id in user.get("unlocked_themes", []): return False, "そのテーマは既に解放済みです。"
            user["points"] -= item["price"]
            if "unlocked_themes" not in user: user["unlocked_themes"] = []
            user["unlocked_themes"].append(item_id)
        self._save(); return True, f"「{item_id if item_type == 'title' else item['name']}」を解放しました！"
    def set_profile_theme(self, uid, theme_id):
        user = self.get_user(uid)
        if not user or theme_id not in user.get("unlocked_themes", []): return False
        user["current_theme"] = theme_id; self._save(); return True
    def transfer_points(self, from_uid, to_uid, amount):
        sender = self.get_user(from_uid)
        receiver = self.get_user(to_uid)
        if not sender or not receiver: return False, "ユーザーが存在しません。"
        if from_uid == to_uid: return False, "自分自身にポイントを送ることはできません。"
        if amount <= 0: return False, "正のポイント数を入力してください。"
        if sender["points"] < amount: return False, "所持ポイントが不足しています。"
        sender["points"] -= amount; receiver["points"] += amount; self._save()
        return True, f"{to_uid}さんに{amount}ポイントを送りました。"

# ───────── 2. マネージャークラス (変更なし) ─────────
class AnnouncementManager:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(ANNOUNCE_FILE):
            with open(ANNOUNCE_FILE, "w") as f: json.dump({"announcements": []}, f, indent=2)
        with open(ANNOUNCE_FILE) as f: self.data = json.load(f)
    def _save(self):
        with open(ANNOUNCE_FILE, "w") as f: json.dump(self.data, f, indent=2)
    def get_all(self): return sorted(self.data["announcements"], key=lambda x: x['timestamp'], reverse=True)
    def add(self, title, content):
        new_ann = {"id": str(uuid.uuid4()), "title": title, "content": content, "timestamp": datetime.now().isoformat()}
        self.data["announcements"].append(new_ann); self._save()
    def delete(self, ann_id):
        self.data["announcements"] = [ann for ann in self.data["announcements"] if ann["id"] != ann_id]
        self._save()
class ScheduleManager:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, "w") as f: json.dump({}, f, indent=2)
        with open(SCHEDULE_FILE) as f: self.schedules = defaultdict(lambda: defaultdict(list), json.load(f))
    def _save(self):
        with open(SCHEDULE_FILE, "w") as f: json.dump(self.schedules, f, indent=2)
    def get_user_schedule_for_month(self, uid, year, month):
        user_sched = self.schedules.get(uid, {})
        month_sched = {}
        for d_str, events in user_sched.items():
            if d_str.startswith(f"{year:04d}-{month:02d}"):
                day = int(d_str.split('-')[2]); month_sched[day] = True
        return month_sched
    def get_user_schedule_for_day(self, uid, d_str):
        return sorted(self.schedules.get(uid, {}).get(d_str, []), key=lambda x: x.get('time', '00:00'))
    def add(self, uid, d_str, time, title):
        new_event = {"id": str(uuid.uuid4()), "time": time, "title": title}
        if uid not in self.schedules or not isinstance(self.schedules[uid], dict):
            self.schedules[uid] = {}
        if d_str not in self.schedules[uid] or not isinstance(self.schedules[uid][d_str], list):
            self.schedules[uid][d_str] = []
        self.schedules[uid][d_str].append(new_event)
        self._save()

    def delete(self, uid, d_str, event_id):
        user_day_sched = self.schedules.get(uid, {}).get(d_str)
        if user_day_sched:
            self.schedules[uid][d_str] = [e for e in user_day_sched if e["id"] != event_id]
            if not self.schedules[uid][d_str]: del self.schedules[uid][d_str]
            if not self.schedules[uid]: del self.schedules[uid]
            self._save()
class PostManager:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(POST_FILE):
            with open(POST_FILE, "w") as f: json.dump({}, f)
        with open(POST_FILE) as f: self.posts = json.load(f)
    def _save(self):
        with open(POST_FILE, "w") as f: json.dump(self.posts, f, indent=2)
    def get_question(self, qid): return self.posts.get(qid)
    def get_user_posts(self, uid): return [p for p in self.posts.values() if p['author'] == uid]
    def search_questions(self, keyword="", tag=""):
        results = sorted(self.posts.values(), key=lambda x: x["timestamp"], reverse=True)
        if keyword:
            kw = keyword.lower(); results = [p for p in results if kw in p['title'].lower() or kw in p['content'].lower()]
        if tag: results = [p for p in results if tag in p.get('tags', [])]
        return results
    def add_question(self, author, title, content, tags_str):
        qid = "q-" + str(uuid.uuid4()); tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        self.posts[qid] = {"id": qid, "title": title, "content": content, "author": author, "timestamp": datetime.now().isoformat(),
                           "best_answer_id": None, "answers": {}, "tags": tags}
        self._save(); return qid
    def add_answer(self, qid, author, content):
        if qid not in self.posts: return None
        aid = "a-" + str(uuid.uuid4())
        self.posts[qid]["answers"][aid] = {"id": aid, "content": content, "author": author, "timestamp": datetime.now().isoformat()}
        self._save(); return aid
    def set_best_answer(self, qid, aid):
        q = self.get_question(qid)
        if not q or aid not in q["answers"]: return None, None
        q["best_answer_id"] = aid; self._save()
        return q["answers"][aid]["author"], q["author"] == q["answers"][aid]["author"]
class ReservationSystem:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(RESV_FILE):
            with open(RESV_FILE, "w") as f: json.dump({}, f)
        with open(RESV_FILE) as f: self.res = defaultdict(lambda: defaultdict(dict), json.load(f))
    def _save(self):
        with open(RESV_FILE, "w") as f: json.dump(self.res, f, indent=2)
    def get_day_reservations(self, campus, d_str): return self.res.get(d_str, {}).get(campus, {})
    def get_user_reservations_for_day(self, d_str, user):
        count = 0; day_data = self.res.get(d_str, {})
        for campus_data in day_data.values():
            for room_data in campus_data.values():
                for res_user in room_data.values():
                    if res_user == user: count += 1
        return count
    def reserve(self, user, campus, room, d_str, start, dur):
        if self.get_user_reservations_for_day(d_str, user) + dur > MAX_HOURS_PER_DAY: return False, f"1日の最大予約時間({MAX_HOURS_PER_DAY}h)を超えます"
        day_res = self.res.setdefault(d_str, {}).setdefault(campus, {}); room_res = day_res.setdefault(str(room), {})
        for h in range(start, start + dur):
            if str(h) in room_res: return False, f"{h}:00は既に予約されています"
        for h in range(start, start + dur): room_res[str(h)] = user
        self._save(); return True, "予約が完了しました"
    def cancel(self, user, campus, room, d_str, hour):
        h_str = str(hour)
        if self.res.get(d_str, {}).get(campus, {}).get(str(room), {}).get(h_str) == user:
            del self.res[d_str][campus][str(room)][h_str]
            if not self.res[d_str][campus][str(room)]: del self.res[d_str][campus][str(room)]
            if not self.res[d_str][campus]: del self.res[d_str][campus]
            if not self.res[d_str]: del self.res[d_str]
            self._save(); return True
        return False

# ───────── 4. Flask App & HTML Templates ─────────
app = Flask(__name__)
app.secret_key = SECRET_KEY
from jinja2 import DictLoader, ChoiceLoader

BASE_HTML = """
<!doctype html><html lang="ja"><meta charset="utf-8">
<title>大学ポータル</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
<style>
 :root { --bs-primary-rgb: 8, 86, 131; --bs-link-color-rgb: 8, 86, 131; }
 body { background-color: #eef2f5; font-family: 'Helvetica Neue', 'Arial', sans-serif; padding-bottom: 5rem; }
 .navbar { box-shadow: 0 2px 4px rgba(0,0,0,.1); }
 .card { border: none; border-radius: 0.5rem; box-shadow: 0 4px 6px rgba(0,0,0,.05); }
 .tag { font-size: 0.8em; } .banned { opacity:0.5; }
 .theme-night { background: #2c3e50; color: #ecf0f1; } .theme-night .card, .theme-night .alert { background: #34495e; color: #ecf0f1; border-color: #46627f; } .theme-night .list-group-item { background-color: #34495e; }
 .theme-sakura { background-image: linear-gradient(to top, #fff1f2 0%, #fde6e9 100%); }
 .theme-ocean { background-image: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%); }
 .cal-day-event { background-color: var(--bs-primary); color: white; border-radius: 8px; font-size: 0.9em; padding: 0.1em 0.4em; }
</style>
<body class="{% if 'profile' in request.path and p_user %}{{ p_user.data.get('current_theme', 'theme-default') }}{% endif %}">
<nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4 sticky-top">
  <div class="container-fluid">
    <a class="navbar-brand fw-bold" href="{{ url_for('index') }}"><i class="bi bi-building"></i> 大学ポータル</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"><span class="navbar-toggler-icon"></span></button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav me-auto">
        {% if session.user %}
        <li class="nav-item"><a class="nav-link" href="{{ url_for('index') }}"><i class="bi bi-patch-question"></i> Q&A</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('reservation_home') }}"><i class="bi bi-calendar-check"></i> 自習室予約</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('schedule_month') }}"><i class="bi bi-calendar-event"></i> 個人スケジュール</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('shop') }}"><i class="bi bi-shop"></i> ポイント交換所</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('game_center') }}"><i class="bi bi-controller"></i> ゲーム</a></li>
        {% endif %}
      </ul>
      {% if session.user %}
        <span class="navbar-text me-3"><a href="{{ url_for('profile', uid=session.user) }}" class="text-white text-decoration-none"><i class="bi bi-person-circle"></i> {{ session.user }}</a><small> ({{ um.get_user(session.user).points }}pt)</small></span>
        {% if um.is_admin(session.user) %}<a href="{{url_for('admin')}}" class="btn btn-warning btn-sm me-2"><i class="bi bi-shield-lock"></i> 管理者</a>{% endif %}
        <a href="{{ url_for('logout') }}" class="btn btn-outline-light btn-sm"><i class="bi bi-box-arrow-right"></i> ログアウト</a>
      {% else %}
        <a href="{{ url_for('login') }}" class="btn btn-outline-light btn-sm"><i class="bi bi-box-arrow-in-right"></i> ログイン</a>
      {% endif %}
    </div>
  </div>
</nav>
<div class="container py-4">
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for category, message in messages %}
    <div class="alert alert-{{ category or 'info' }} alert-dismissible fade show" role="alert">{{ message }} <button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>
  {% endfor %}
{% endwith %}
{% block body %}{% endblock %}
</div>
<footer class="text-center text-muted py-4"><p>© 2023 University Portal System.</p></footer>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body></html>"""

PROFILE_HTML = """
{% extends 'base.html' %}{% block body %}
<h2 class="mb-4"><i class="bi bi-person-badge"></i> {{ p_user.uid }} さんのプロフィール</h2>
<div class="row">
  <div class="col-md-6">
    <div class="card mb-4"><div class="card-header fw-bold">ステータス</div><div class="card-body">
        <p><strong><i class="bi bi-gem"></i> ポイント:</strong> {{ p_user.data.points }} pt</p>
        <p><strong><i class="bi bi-exclamation-triangle"></i> 違反回数:</strong> {{ p_user.data.vio }} / {{ violation_limit }} 回</p>
        <p><strong><i class="bi bi-award"></i> 獲得した称号:</strong>
          {% for title in p_user.data.get('titles', []) %}<span class="badge bg-info">{{ title }}</span>{% else %}なし{% endfor %}
        </p>
    </div></div>
    {% if session.user == p_user.uid %}
    <div class="card mb-4"><div class="card-header fw-bold">プロフィールテーマ設定</div><div class="card-body">
      <form method="post" action="{{ url_for('set_theme') }}">
        <div class="input-group">
          <select name="theme_id" class="form-select">
            {% for theme_id, theme_info in themes.items() %}
              {% if theme_id in p_user.data.get('unlocked_themes', []) %}
                <option value="{{ theme_id }}" {% if theme_id == p_user.data.get('current_theme') %}selected{% endif %}>{{ theme_info.name }}</option>
              {% endif %}
            {% endfor %}
          </select>
          <button class="btn btn-primary">テーマを適用</button>
        </div>
      </form>
      <small class="form-text text-muted">新しいテーマはポイント交換所で解放できます。</small>
    </div></div>
    <div class="card mb-4"><div class="card-header fw-bold">ポイントを送る</div><div class="card-body">
      <form method="post" action="{{ url_for('transfer_points') }}">
        <div class="input-group">
          <span class="input-group-text">To:</span><input type="text" name="to_uid" class="form-control" placeholder="相手のID" required>
          <span class="input-group-text">Amount:</span><input type="number" name="amount" class="form-control" placeholder="ポイント数" required min="1">
          <button class="btn btn-primary">送金</button>
        </div>
      </form>
    </div></div>
    {% endif %}
  </div>
  <div class="col-md-6">
    <div class="card mb-4"><div class="card-header fw-bold">称号獲得への道</div><div class="card-body">
        <ul class="list-group list-group-flush">
        {% set user_titles = p_user.data.get('titles', []) %}
        {% for title, cond in titles.items() %}{% if title not in user_titles %}<li class="list-group-item"><strong>{{ title }}</strong>: <span class="text-muted">{{ cond.desc }}</span><div class="progress mt-1" style="height: 5px;"><div class="progress-bar" style="width: {{ (p_user.data.get(cond.type, 0) / cond.value * 100)|int }}%"></div></div></li>{% endif %}{% endfor %}
        </ul>
    </div></div>
  </div>
</div>{% endblock %}"""

GAME_CENTER_HTML = """
{% extends 'base.html' %}{% block body %}
<h2 class="mb-4"><i class="bi bi-controller"></i> ゲームセンター</h2>
<p>ゲームをプレイしてポイントを獲得しましょう！</p>
<div class="row">
    <div class="col-md-6 col-lg-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">テトリス</h5>
                <p class="card-text">定番のブロック落ち物パズルゲームです。</p>
                <a href="{{ url_for('game_tetris') }}" class="btn btn-primary">プレイする</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

GAME_HTML = """
{% extends 'base.html' %}{% block body %}
<h2 class="mb-4">テトリス</h2>
<div class="row">
    <div class="col-md-8 text-center">
        <canvas id="tetris" width="240" height="400" style="background-color: #000; border: 2px solid #333;"></canvas>
    </div>
    <div class="col-md-4">
        <h4>Score: <span id="score">0</span></h4>
        <div id="game-over-message" class="alert alert-danger mt-3" style="display: none;"></div>
        <button id="restart-button" class="btn btn-primary mt-3">リスタート</button>
        <hr>
        <h5>操作方法</h5>
        <ul>
            <li><strong>←/→</strong>: 左右移動</li>
            <li><strong>↓</strong>: ソフトドロップ</li>
            <li><strong>↑</strong>: 回転</li>
            <li><strong>Space</strong>: ハードドロップ</li>
        </ul>
    </div>
</div>
<script>
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('tetris');
    const context = canvas.getContext('2d');
    const scoreElement = document.getElementById('score');
    const gameOverMessage = document.getElementById('game-over-message');
    const restartButton = document.getElementById('restart-button');
    const COLS = 10, ROWS = 20, BLOCK_SIZE = 20;
    const COLORS = [null, '#FF0D72', '#0DC2FF', '#0DFF72', '#F538FF', '#FF8E0D', '#FFE138', '#3877FF'];
    const SHAPES = [ [], [[1,1,1,1]], [[1,1],[1,1]], [[0,1,1],[1,1,0]], [[1,1,0],[0,1,1]], [[1,0,0],[1,1,1]], [[0,0,1],[1,1,1]], [[0,1,0],[1,1,1]] ];
    let grid, score, gameOver, piece, dropInterval, lastTime, dropCounter;
    function createPiece() {
        const typeId = Math.floor(Math.random() * (SHAPES.length - 1)) + 1;
        const shape = SHAPES[typeId];
        return { x: Math.floor(COLS / 2) - Math.floor(shape[0].length / 2), y: 0, shape: shape, color: COLORS[typeId] };
    }
    function draw() {
        context.clearRect(0, 0, canvas.width, canvas.height);
        for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) if (grid[r][c]) {
            context.fillStyle = COLORS[grid[r][c]];
            context.fillRect(c * BLOCK_SIZE, r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
            context.strokeRect(c * BLOCK_SIZE, r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
        }
        context.fillStyle = piece.color;
        piece.shape.forEach((row, y) => row.forEach((value, x) => {
            if (value > 0) {
                context.fillRect((piece.x + x) * BLOCK_SIZE, (piece.y + y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
                context.strokeRect((piece.x + x) * BLOCK_SIZE, (piece.y + y) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
            }
        }));
    }
    function move() {
        if (gameOver) return; piece.y++;
        if (collides()) { piece.y--; freeze(); piece = createPiece(); if (collides()) endGame(); }
    }
    function collides() {
        for (let y = 0; y < piece.shape.length; y++) for (let x = 0; x < piece.shape[y].length; x++)
            if (piece.shape[y][x] && (grid[piece.y + y] && grid[piece.y + y][piece.x + x]) !== 0) return true;
        return false;
    }
    function freeze() {
        piece.shape.forEach((row, y) => row.forEach((value, x) => { if (value > 0) grid[piece.y + y][piece.x + x] = COLORS.indexOf(piece.color); }));
        checkLines();
    }
    function checkLines() {
        let lines = 0;
        for (let r = ROWS - 1; r >= 0; r--) {
            if (grid[r].every(cell => cell > 0)) { lines++; grid.splice(r, 1); grid.unshift(Array(COLS).fill(0)); r++; }
        }
        if (lines > 0) { score += lines * 10 * lines; scoreElement.textContent = score; }
    }
    function rotate() {
        const newShape = piece.shape[0].map((_, i) => piece.shape.map(r => r[i]).reverse());
        const originalShape = piece.shape; piece.shape = newShape;
        if (collides()) piece.shape = originalShape;
    }
    function update(time = 0) {
        if (gameOver) return;
        dropCounter += time - lastTime; lastTime = time;
        if (dropCounter > dropInterval) { move(); dropCounter = 0; }
        draw(); requestAnimationFrame(update);
    }
    function endGame() {
        gameOver = true; gameOverMessage.style.display = 'block';
        fetch("{{ url_for('game_submit_score') }}", {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ score: score })
        }).then(r => r.json()).then(d => {
            gameOverMessage.innerHTML = d.status === 'success' ? `<h4>ゲームオーバー！</h4><p>獲得ポイント: <strong>${d.points_earned} pt</strong></p>` : `<h4>ゲームオーバー！</h4><p>スコア送信失敗</p>`;
        });
    }
    function reset() {
        grid = Array.from({ length: ROWS }, () => Array(COLS).fill(0));
        score = 0; gameOver = false; dropCounter = 0; dropInterval = 1000; lastTime = 0;
        scoreElement.textContent = score; gameOverMessage.style.display = 'none';
        piece = createPiece(); update();
    }
    restartButton.addEventListener('click', reset);
    document.addEventListener('keydown', e => {
        if (gameOver) return;
        if (e.key === 'ArrowLeft') { piece.x--; if (collides()) piece.x++; }
        else if (e.key === 'ArrowRight') { piece.x++; if (collides()) piece.x--; }
        else if (e.key === 'ArrowDown') move();
        else if (e.key === 'ArrowUp') rotate();
        else if (e.code === 'Space') { while(!collides()) piece.y++; piece.y--; freeze(); piece = createPiece(); }
    });
    reset();
});
</script>
{% endblock %}"""

# ★★★ 修正: 全てのHTMLテンプレートをこの辞書に集約 ★★★
ALL_HTMLS = {
    "base.html": BASE_HTML, "profile.html": PROFILE_HTML, "game_center.html": GAME_CENTER_HTML, "game.html": GAME_HTML,
    "login_register.html": "{% extends 'base.html' %}{% block body %}<div class='row justify-content-center'><div class='col-lg-5 col-md-8'><div class='card'><div class='card-body p-4'><h3 class='card-title text-center mb-4'>{{ title }}</h3><form method=post><div class='mb-3'><label class='form-label'><i class='bi bi-person'></i> ユーザID</label><input name=uid class='form-control' required></div><div class='mb-3'><label class='form-label'><i class='bi bi-key'></i> パスワード</label><input type=password name=pw class='form-control' required></div><div class='d-grid'><button class='btn btn-primary btn-lg'>{{ title }}</button></div></form><hr><div class='text-center'>{% if title == 'ログイン' %}<a href='{{url_for('register')}}'>新規登録はこちら</a>{% else %}<a href='{{url_for('login')}}'>ログインはこちら</a>{% endif %}</div></div></div></div></div>{% endblock %}",
    "index.html": """{% extends 'base.html' %}{% block body %}{% if announcements %}<div class="mb-4"><h4 class="h5"><i class="bi bi-info-circle-fill text-primary"></i> お知らせ</h4>{% for ann in announcements %}<div class="alert alert-light border"><strong class="alert-heading">{{ ann.title }}</strong><p class="mb-0 mt-2" style="white-space: pre-wrap;">{{ ann.content }}</p><hr><p class="mb-0 text-end text-muted small">{{ ann.timestamp.split('T')[0] }}</p></div>{% endfor %}</div>{% endif %}<div class="d-flex justify-content-between align-items-center mb-4"><h2 class="h4 mb-0"><i class="bi bi-chat-left-text"></i> Q&A - 質問一覧</h2><a href="{{ url_for('ask') }}" class="btn btn-primary"><i class="bi bi-plus-circle"></i> 新しい質問</a></div><div class="card mb-4"><div class="card-body"><form method="get" class="row g-3 align-items-center"><div class="col"><input type="text" name="keyword" class="form-control" placeholder="キーワードで検索..." value="{{ request.args.get('keyword', '') }}"></div><div class="col"><input type="text" name="tag" class="form-control" placeholder="タグで検索..." value="{{ request.args.get('tag', '') }}"></div><div class="col-auto"><button type="submit" class="btn btn-outline-primary"><i class="bi bi-search"></i> 検索</button></div></form></div></div>{% for q in questions %}<div class="card mb-3"><div class="card-body"><div class="d-flex w-100 justify-content-between"><h5 class="mb-1"><a href="{{ url_for('question_detail', qid=q.id) }}" class="text-decoration-none">{{ q.title }}</a></h5><small class="text-muted">{{ q.timestamp.split('T')[0] }}</small></div><p class="mb-1 text-muted small">投稿者: <a href="{{ url_for('profile', uid=q.author) }}">{{ q.author }}</a> | 回答: {{ q.answers|length }}{% if q.best_answer_id %}<span class="badge bg-success ms-2">解決済み</span>{% endif %}</p>{% if q.tags %}{% for tag in q.tags %}<a href="{{ url_for('index', tag=tag) }}" class="badge bg-secondary text-decoration-none tag">{{ tag }}</a>{% endfor %}{% endif %}</div></div>{% else %}<div class="alert alert-info">該当する質問はありません。</div>{% endfor %}{% endblock %}""",
    "admin.html": """{% extends 'base.html' %}{% block body %}<div class="row"><div class="col-lg-8"><h3><i class='bi bi-people-fill'></i> ユーザー管理</h3><div class='table-responsive'><table class='table table-bordered table-striped table-hover'><thead><tr><th>ユーザ</th><th>状態</th><th>Pt</th><th>違反</th><th>操作</th></tr></thead><tbody>{% for uid, u in users.items() %}<tr class='{{'table-warning' if u.status == 'banned' else ''}}'><td>{{uid}} <small class="text-muted">({{u.role}})</small></td><td>{{u.status}}</td><td>{{u.points}}</td><td>{{u.vio}}</td><td>{% if uid != 'admin' %}<form method=post action='{{url_for('admin_user_action')}}' class='d-inline-flex flex-wrap align-items-center gap-1'><input type=hidden name=uid value='{{uid}}'><button name=act value='vio_add' class='btn btn-sm btn-outline-danger' title="違反+1"><i class="bi bi-plus-circle"></i></button><button name=act value='vio_sub' class='btn btn-sm btn-outline-success' title="違反-1"><i class="bi bi-dash-circle"></i></button><button name=act value='ban' class='btn btn-sm btn-warning' onclick="return confirm('本当にこのユーザーを「{{'利用可能に' if u.status == 'banned' else '利用停止に'}}」しますか？')">{{'解除' if u.status == 'banned' else '停止'}}</button><div class='input-group input-group-sm' style='width: 120px;'><input type=number name=points class='form-control' value=10><button name=act value='adjust_points' class='btn btn-sm btn-info'>Pt</button></div></form>{% endif %}</td></tr>{% endfor %}</tbody></table></div></div><div class="col-lg-4"><div class="card"><div class="card-header fw-bold"><i class="bi bi-megaphone-fill"></i> お知らせ管理</div><div class="card-body"><form action="{{ url_for('admin_announcement_action') }}" method="post"><input type="hidden" name="act" value="add"><div class="mb-2"><input type="text" name="title" class="form-control" placeholder="タイトル" required></div><div class="mb-2"><textarea name="content" class="form-control" rows="3" placeholder="内容" required></textarea></div><div class="d-grid"><button type="submit" class="btn btn-primary">お知らせを投稿</button></div></form></div><ul class="list-group list-group-flush"><li class="list-group-item active">投稿済みのお知らせ</li>{% for ann in announcements %}<li class="list-group-item d-flex justify-content-between align-items-center"><span class="text-truncate" title="{{ ann.title }}">{{ ann.title }}</span><form action="{{ url_for('admin_announcement_action') }}" method="post" onsubmit="return confirm('このお知らせを削除しますか？');"><input type="hidden" name="act" value="delete"><input type="hidden" name="ann_id" value="{{ ann.id }}"><button type="submit" class="btn btn-sm btn-danger"><i class="bi bi-trash"></i></button></form></li>{% else %}<li class="list-group-item">まだお知らせはありません。</li>{% endfor %}</ul></div></div></div>{% endblock %}""",
    "shop.html": """{% extends 'base.html' %}{% block body %}<h2 class="mb-4"><i class="bi bi-shop"></i> ポイント交換所</h2><div class="alert alert-info">あなたのポイント: <strong>{{ current_user.points }} pt</strong></div><div class="row"><div class="col-md-6"><h4><i class="bi bi-award-fill"></i> 交換限定称号</h4>{% for title_id, title_info in shop_titles.items() %}<div class="card mb-3"><div class="card-body d-flex justify-content-between align-items-center"><div><h5 class="card-title">{{ title_id }}</h5><p class="card-text mb-0">{{ title_info.desc }} - <strong class="text-primary">{{ title_info.price }} pt</strong></p></div>{% if title_id in current_user.get('titles', []) %}<button class="btn btn-success" disabled>交換済み</button>{% elif current_user.points >= title_info.price %}<form method="post" action="{{ url_for('purchase') }}"><input type="hidden" name="item_id" value="{{ title_id }}"><input type="hidden" name="item_type" value="title"><button type="submit" class="btn btn-primary">交換する</button></form>{% else %}<button class="btn btn-secondary" disabled>ポイント不足</button>{% endif %}</div></div>{% endfor %}</div><div class="col-md-6"><h4><i class="bi bi-palette-fill"></i> プロフィールテーマ</h4>{% for theme_id, theme_info in themes.items() %}{% if theme_info.price > 0 %}<div class="card mb-3"><div class="card-body d-flex justify-content-between align-items-center"><div><h5 class="card-title">{{ theme_info.name }}</h5><p class="card-text mb-0">プロフィールページの背景を変更します - <strong class="text-primary">{{ theme_info.price }} pt</strong></p></div>{% if theme_id in current_user.get('unlocked_themes', []) %}<button class="btn btn-success" disabled>解放済み</button>{% elif current_user.points >= theme_info.price %}<form method="post" action="{{ url_for('purchase') }}"><input type="hidden" name="item_id" value="{{ theme_id }}"><input type="hidden" name="item_type" value="theme"><button type="submit" class="btn btn-primary">解放する</button></form>{% else %}<button class="btn btn-secondary" disabled>ポイント不足</button>{% endif %}</div></div>{% endif %}{% endfor %}</div></div>{% endblock %}""",
    "schedule_month.html": """{% extends 'base.html' %}{% block body %}<h2 class="mb-4"><i class="bi bi-calendar-event"></i> 個人スケジュール ({{ year }}年 {{ month }}月)</h2><div class="d-flex justify-content-between mb-3"><a href="{{ url_for('schedule_month', ym=prev_ym) }}" class="btn btn-outline-secondary"><i class="bi bi-chevron-left"></i> 前月</a><a href="{{ url_for('schedule_month', ym=today.strftime('%Y-%m')) }}" class="btn btn-secondary">今月</a><a href="{{ url_for('schedule_month', ym=next_ym) }}" class="btn btn-outline-secondary">翌月 <i class="bi bi-chevron-right"></i></a></div><table class="table table-bordered text-center bg-white">  <thead class="table-light"><tr><th>日</th><th>月</th><th>火</th><th>水</th><th>木</th><th>金</th><th>土</th></tr></thead>  <tbody>  {% for week in weeks %}  <tr>    {% for d in week %}      {% if d == 0 %}<td></td>      {% else %}        {% set ds = '%04d-%02d-%02d' % (year, month, d) %}        <td class="{% if today.year == year and today.month == month and today.day == d %}table-info{% endif %}">          <a href="{{ url_for('schedule_day', day_str=ds) }}" class="d-block text-decoration-none text-dark" style="min-height: 5em;">            <div class="text-end">{{ d }}</div>            {% if month_events.get(d) %}<div class="cal-day-event mx-auto">●</div>{% endif %}          </a>        </td>      {% endif %}    {% endfor %}  </tr>  {% endfor %}  </tbody></table>{% endblock %}""",
    "schedule_day.html": """{% extends 'base.html' %}{% block body %}<h2 class="mb-4"><i class="bi bi-calendar-date"></i> {{ day_dt.strftime('%Y年%m月%d日 (%a)') }} の予定</h2><div class="card mb-4"><div class="card-body"><h5 class="card-title">予定を追加</h5><form action="{{ url_for('schedule_add') }}" method="post" class="d-flex gap-2"><input type="hidden" name="date" value="{{ day_str }}"><input type="time" name="time" class="form-control" style="max-width: 120px;" value="09:00"><input type="text" name="title" class="form-control" placeholder="予定を入力" required><button type="submit" class="btn btn-primary">追加</button></form></div></div><ul class="list-group">{% for event in events %}<li class="list-group-item d-flex justify-content-between align-items-center"><span><strong>{{ event.time }}</strong> - {{ event.title }}</span><form action="{{ url_for('schedule_delete') }}" method="post" onsubmit="return confirm('この予定を削除しますか？');"><input type="hidden" name="date" value="{{ day_str }}"><input type="hidden" name="event_id" value="{{ event.id }}"><button type="submit" class="btn btn-sm btn-outline-danger" title="削除"><i class="bi bi-trash"></i></button></form></li>{% else %}<li class="list-group-item">この日の予定はありません。</li>{% endfor %}</ul><a href="{{ url_for('schedule_month', ym=day_dt.strftime('%Y-%m')) }}" class="btn btn-link mt-3"><i class="bi bi-arrow-left"></i> 月表示に戻る</a>{% endblock %}""",
    "ask.html": "{% extends 'base.html' %}{% block body %}<div class='card'><div class='card-body'><h3 class='card-title'><i class='bi bi-pencil-square'></i> 新しい質問</h3><form method=post><div class='mb-3'><label class='form-label'>タイトル</label><input name=title class='form-control' required></div><div class='mb-3'><label class='form-label'>内容</label><textarea name=content class='form-control' rows=5 required></textarea></div><div class='mb-3'><label class='form-label'>タグ (カンマ区切り)</label><input name=tags class='form-control' placeholder='例: python, flask, 課題'></div><button class='btn btn-primary'><i class='bi bi-send'></i> 投稿する</button></form></div></div>{% endblock %}",
    "question_detail.html": "{% extends 'base.html' %}{% block body %}<div class='card mb-4'><div class='card-header fw-bold'>質問</div><div class='card-body'><h3 class='card-title'>{{ q.title }}</h3><p style='white-space: pre-wrap;'>{{ q.content }}</p><p class='text-muted small'>投稿者: <a href='{{ url_for('profile', uid=q.author) }}'>{{ q.author }}</a></p>{% if q.tags %}{% for tag in q.tags %}<span class='badge bg-secondary tag'>{{ tag }}</span>{% endfor %}{% endif %}</div></div><h4><i class='bi bi-chat-dots'></i> 回答 ({{ q.answers|length }})</h4>{% for a in q.answers.values()|sort(attribute='timestamp') %}<div class='card mb-3 {% if a.id == q.best_answer_id %}border-success border-2{% endif %}'><div class='card-body'>{% if a.id == q.best_answer_id %}<span class='badge bg-success float-end'>ベストアンサー</span>{% endif %}<p style='white-space: pre-wrap;'>{{ a.content }}</p><p class='text-muted small'>回答者: <a href='{{ url_for('profile', uid=a.author) }}'>{{ a.author }}</a>{% if session.user == q.author and not q.best_answer_id %}<a href='{{ url_for('best_answer', qid=q.id, aid=a.id) }}' class='btn btn-sm btn-outline-success ms-2'><i class='bi bi-check-circle'></i> BAに選ぶ</a>{% endif %}</p></div></div>{% else %}<p>まだ回答はありません。</p>{% endfor %}{% if session.user and session.user != q.author and not q.best_answer_id %}<div class='card'><div class='card-body'><h4>回答する</h4><form method=post action='{{ url_for('answer', qid=q.id) }}'><textarea name=content class='form-control' rows=4 required></textarea><button class='btn btn-primary mt-2'><i class='bi bi-reply'></i> 回答を投稿</button></form></div></div>{% elif q.best_answer_id %}<div class='alert alert-success'>この質問は解決済みです。</div>{% endif %}<a href='{{ url_for('index') }}' class='btn btn-link mt-3'><i class='bi bi-arrow-left'></i> 質問一覧に戻る</a>{% endblock %}",
    "reservation_home.html": "{% extends 'base.html' %}{% block body %}<h2 class='mb-4'><i class='bi bi-calendar-check'></i> 自習室予約</h2><p>予約するキャンパスを選択してください。</p><div class='row'>{% for campus_id, campus_info in campuses.items() %}<div class='col-md-6 mb-3'><div class='card h-100'><div class='card-body text-center'><h5 class='card-title'>{{ campus_info.name }}</h5><p class='card-text'>{{ campus_info.rooms }}教室 利用可能</p><a href='{{ url_for('reservation_campus_day', campus=campus_id, day_str=today) }}' class='btn btn-primary'><i class='bi bi-arrow-right-circle'></i> 今日の予約状況を見る</a></div></div></div>{% endfor %}</div>{% endblock %}",
    "reservation_day.html": "{% extends 'base.html' %}{% block body %}<h2 class='mb-4'><i class='bi bi-calendar3'></i> {{ campus_info.name }} - {{ day_dt.strftime('%Y年%m月%d日 (%a)') }} の予約状況</h2><div class='d-flex justify-content-between mb-3'><a href='{{ url_for('reservation_campus_day', campus=campus, day_str=prev_day) }}' class='btn btn-outline-secondary'><i class='bi bi-chevron-left'></i> 前日</a><a href='{{ url_for('reservation_campus_day', campus=campus, day_str=next_day) }}' class='btn btn-outline-secondary'>翌日 <i class='bi bi-chevron-right'></i></a></div><div class='card mb-4'><div class='card-body'><h5 class='mb-3'>新規予約</h5><p>あなたの本日の総予約時間: {{ my_total_hours }} / {{ max_day_hours }} 時間</p><form method='post' action='{{ url_for('reserve') }}'><input type='hidden' name='campus' value='{{ campus }}'><input type='hidden' name='date' value='{{ day_str }}'><div class='row g-2'><div class='col-md'><select name='room' class='form-select' required><option value='' disabled selected>教室を選択</option>{% for i in range(1, campus_info.rooms + 1) %}<option value='{{ i }}'>教室 {{ i }}</option>{% endfor %}</select></div><div class='col-md'><select name='start' class='form-select' required><option value='' disabled selected>開始時間</option>{% for h in range(open_time, close_time) %}<option value='{{ h }}'>{{ h }}:00</option>{% endfor %}</select></div><div class='col-md'><select name='dur' class='form-select'><option value='1'>1時間</option><option value='2'>2時間</option></select></div><div class='col-md-auto'><button class='btn btn-primary w-100'><i class='bi bi-check2-circle'></i> 予約する</button></div></div></form></div></div><div class='table-responsive'><table class='table table-bordered text-center bg-white'><thead class='table-light'><tr><th>教室</th>{% for h in range(open_time, close_time) %}<th>{{h}}:00</th>{% endfor %}</tr></thead><tbody>{% for room_num in range(1, campus_info.rooms + 1) %}<tr><td class='fw-bold'>Room {{ room_num }}</td>{% for h in range(open_time, close_time) %}{% set res_user = day_reservations.get(room_num|string, {}).get(h|string) %}{% if res_user %}<td class='table-{{ 'success' if res_user == session.user else 'danger' }}'>{{ res_user if res_user == session.user else '予約済' }}{% if res_user == session.user %}<form method='post' action='{{ url_for('cancel') }}' class='d-inline'><input type='hidden' name='campus' value='{{ campus }}'><input type='hidden' name='room' value='{{ room_num }}'><input type='hidden' name='date' value='{{ day_str }}'><input type='hidden' name='hour' value='{{ h }}'><button type='submit' class='btn btn-xs btn-link text-danger p-0 ms-1' title='キャンセル'><i class='bi bi-x-circle-fill'></i></button></form>{% endif %}</td>{% else %}<td></td>{% endif %}{% endfor %}</tr>{% endfor %}</tbody></table></div><a href='{{ url_for('reservation_home') }}' class='btn btn-link mt-3'><i class='bi bi-arrow-left'></i> キャンパス選択に戻る</a>{% endblock %}"
}
app.jinja_loader = ChoiceLoader([app.jinja_loader, DictLoader(ALL_HTMLS)])

# ───────── 5. Manager Instances & Jinja Globals ─────────
um = UserManager()
pm = PostManager()
rs = ReservationSystem()
anm = AnnouncementManager()
schm = ScheduleManager()
app.jinja_env.globals.update(um=um, titles=TITLES, violation_limit=VIOLATION_LIMIT, campuses=CAMPUSES,
                             shop_titles=SHOP_TITLES, themes=PROFILE_THEMES)

# (Decorators and Routes are defined below)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session: flash("ログインが必要です", "warning"); return redirect(url_for("login"))
        user = um.get_user(session["user"])
        if not user or user["status"] == "banned":
            flash("アカウントが利用停止中です", "danger"); session.pop("user", None); return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session or not um.is_admin(session["user"]): abort(403)
        return f(*args, **kwargs)
    return decorated_function

# ───────── Routes ─────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uid, pw = request.form["uid"], request.form["pw"]
        if um.verify(uid, pw):
            if um.get_user(uid)["status"] == "banned": flash("このアカウントは利用停止中です", "danger"); return redirect(url_for("login"))
            session["user"] = uid; return redirect(url_for("index"))
        flash("ユーザIDまたはパスワードが違います", "danger")
    return render_template("login_register.html", title="ログイン")
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if um.register(request.form["uid"], request.form["pw"]):
            flash("登録が完了しました。ログインしてください", "success"); return redirect(url_for("login"))
        flash("そのユーザIDは既に使用されています", "warning")
    return render_template("login_register.html", title="新規登録")
@app.route("/logout")
def logout(): session.pop("user", None); return redirect(url_for("login"))
@app.route("/")
@login_required
def index():
    announcements = anm.get_all()[:3]
    questions = pm.search_questions(request.args.get('keyword', ''), request.args.get('tag', ''))
    return render_template("index.html", questions=questions, announcements=announcements)
@app.route("/ask", methods=["GET", "POST"])
@login_required
def ask():
    if request.method == "POST":
        uid = session["user"]; qid = pm.add_question(uid, request.form["title"], request.form["content"], request.form.get("tags", ""))
        um.add_points(uid, POINT_ON_QUESTION); um.increment_counter(uid, "questions")
        if datetime.now().hour in [2, 3]: um.check_and_award_titles(uid, night_activity=True)
        flash("質問を投稿しました", "success"); return redirect(url_for("question_detail", qid=qid))
    return render_template("ask.html")
@app.route("/question/<qid>")
@login_required
def question_detail(qid):
    question = pm.get_question(qid)
    if not question: abort(404)
    return render_template("question_detail.html", q=question)
@app.route("/answer/<qid>", methods=["POST"])
@login_required
def answer(qid):
    uid = session["user"]
    if pm.add_answer(qid, uid, request.form["content"]):
        um.add_points(uid, POINT_ON_ANSWER); um.increment_counter(uid, "answers")
        if datetime.now().hour in [2, 3]: um.check_and_award_titles(uid, night_activity=True)
        flash("回答を投稿しました", "success")
    return redirect(url_for("question_detail", qid=qid))
@app.route("/best_answer/<qid>/<aid>")
@login_required
def best_answer(qid, aid):
    q = pm.get_question(qid)
    if not q or q["author"] != session["user"] or q['best_answer_id']: abort(403)
    answer_author, self_answered = pm.set_best_answer(qid, aid)
    if answer_author:
        um.add_points(answer_author, POINT_ON_BEST_ANSWER); um.increment_counter(answer_author, "best_answers")
        if self_answered: um.check_and_award_titles(answer_author, self_answered=True)
        flash("ベストアンサーを決定しました", "success")
    return redirect(url_for("question_detail", qid=qid))
@app.route("/reservations")
@login_required
def reservation_home():
    return render_template("reservation_home.html", today=date.today().strftime("%Y-%m-%d"))
@app.route("/reservations/<campus>/<day_str>")
@login_required
def reservation_campus_day(campus, day_str):
    if campus not in CAMPUSES: abort(404)
    try: day_dt = datetime.strptime(day_str, "%Y-%m-%d").date()
    except ValueError: abort(400)
    day_reservations = rs.get_day_reservations(campus, day_str)
    my_total_hours = rs.get_user_reservations_for_day(day_str, session['user'])
    return render_template("reservation_day.html", campus=campus, campus_info=CAMPUSES[campus], day_str=day_str, day_dt=day_dt,
                           day_reservations=day_reservations, my_total_hours=my_total_hours, max_day_hours=MAX_HOURS_PER_DAY,
                           open_time=OPEN_TIME, close_time=CLOSE_TIME,
                           prev_day=(day_dt - timedelta(days=1)).strftime("%Y-%m-%d"),
                           next_day=(day_dt + timedelta(days=1)).strftime("%Y-%m-%d"))
@app.route("/reservations/reserve", methods=["POST"])
@login_required
def reserve():
    f = request.form; ok, msg = rs.reserve(session["user"], f["campus"], f["room"], f["date"], int(f["start"]), int(f["dur"]))
    if ok:
        um.increment_counter(session["user"], "reservations")
        if int(f["start"]) == OPEN_TIME: um.check_and_award_titles(session["user"], early_bird=True)
        flash(msg, "success")
    else: um.adjust_violation(session["user"], 1); flash(msg, "danger")
    return redirect(url_for("reservation_campus_day", campus=f["campus"], day_str=f["date"]))
@app.route("/reservations/cancel", methods=["POST"])
@login_required
def cancel():
    f = request.form
    if rs.cancel(session["user"], f["campus"], f["room"], f["date"], int(f["hour"])):
        flash(f"{f['hour']}:00の予約をキャンセルしました", "success")
    else: flash("キャンセルできませんでした", "danger")
    return redirect(url_for("reservation_campus_day", campus=f["campus"], day_str=f["date"]))
@app.route("/profile/<uid>")
@login_required
def profile(uid):
    user_data = um.get_user(uid)
    if not user_data: abort(404)
    return render_template("profile.html", p_user={"uid": uid, "data": user_data})
@app.route("/admin")
@admin_required
def admin(): return render_template("admin.html", users=um.users, announcements=anm.get_all())
@app.route("/admin/user_action", methods=["POST"])
@admin_required
def admin_user_action():
    uid, act = request.form["uid"], request.form["act"]
    if uid == 'admin': flash("管理者アカウントは操作できません", "danger"); return redirect(url_for("admin"))
    if act == "ban": um.toggle_ban(uid); flash(f"{uid}の状態を変更しました", "info")
    elif act == "vio_add": um.adjust_violation(uid, 1)
    elif act == "vio_sub": um.adjust_violation(uid, -1)
    elif act == "adjust_points": um.add_points(uid, int(request.form.get("points", 0))); flash(f"{uid}のポイントを調整しました", "info")
    return redirect(url_for("admin"))
@app.route("/admin/announcement_action", methods=["POST"])
@admin_required
def admin_announcement_action():
    act = request.form.get("act")
    if act == "add":
        anm.add(request.form["title"], request.form["content"]); flash("お知らせを追加しました", "success")
    elif act == "delete":
        anm.delete(request.form["ann_id"]); flash("お知らせを削除しました", "info")
    return redirect(url_for("admin"))
@app.route("/schedule")
@app.route("/schedule/<ym>")
@login_required
def schedule_month(ym=None):
    if ym is None: ym = date.today().strftime("%Y-%m")
    year, month = map(int, ym.split('-'))
    cal = calendar.Calendar(firstweekday=6); weeks = cal.monthdayscalendar(year, month)
    month_events = schm.get_user_schedule_for_month(session['user'], year, month)
    today = date.today(); prev_dt = (date(year, month, 1) - timedelta(days=1)); next_dt = (date(year, month, 1) + timedelta(days=32)).replace(day=1)
    return render_template("schedule_month.html", year=year, month=month, weeks=weeks,
                           month_events=month_events, today=today, prev_ym=prev_dt.strftime("%Y-%m"), next_ym=next_dt.strftime("%Y-%m"))
@app.route("/schedule/day/<day_str>")
@login_required
def schedule_day(day_str):
    try: day_dt = datetime.strptime(day_str, "%Y-%m-%d").date()
    except ValueError: abort(400)
    events = schm.get_user_schedule_for_day(session['user'], day_str)
    return render_template("schedule_day.html", day_str=day_str, day_dt=day_dt, events=events)
@app.route("/schedule/add", methods=["POST"])
@login_required
def schedule_add():
    d_str, time, title = request.form["date"], request.form["time"], request.form["title"]
    if title: schm.add(session['user'], d_str, time, title)
    return redirect(url_for("schedule_day", day_str=d_str))
@app.route("/schedule/delete", methods=["POST"])
@login_required
def schedule_delete():
    d_str, event_id = request.form["date"], request.form["event_id"]
    schm.delete(session['user'], d_str, event_id)
    return redirect(url_for("schedule_day", day_str=d_str))
@app.route("/shop")
@login_required
def shop():
    current_user = um.get_user(session["user"])
    return render_template("shop.html", current_user=current_user)
@app.route("/purchase", methods=["POST"])
@login_required
def purchase():
    item_id, item_type = request.form.get("item_id"), request.form.get("item_type")
    ok, msg = um.purchase_item(session["user"], item_id, item_type)
    if ok: flash(msg, "success")
    else: flash(msg, "danger")
    return redirect(url_for("shop"))
@app.route("/set_theme", methods=["POST"])
@login_required
def set_theme():
    theme_id = request.form.get("theme_id")
    if um.set_profile_theme(session["user"], theme_id):
        flash("プロフィールテーマを変更しました。", "success")
    else: flash("テーマの変更に失敗しました。", "danger")
    return redirect(url_for("profile", uid=session["user"]))
@app.route("/transfer_points", methods=["POST"])
@login_required
def transfer_points():
    to_uid = request.form.get("to_uid")
    try: amount = int(request.form.get("amount", 0))
    except (ValueError, TypeError):
        flash("無効なポイント数です。", "danger"); return redirect(url_for("profile", uid=session['user']))
    ok, msg = um.transfer_points(session["user"], to_uid, amount)
    if ok: flash(msg, "success")
    else: flash(msg, "danger")
    return redirect(url_for("profile", uid=session['user']))
@app.route("/game_center")
@login_required
def game_center():
    return render_template("game_center.html")
@app.route("/game/tetris")
@login_required
def game_tetris():
    return render_template("game.html")
@app.route("/game/submit_score", methods=["POST"])
@login_required
def game_submit_score():
    data = request.get_json()
    score = data.get("score", 0)
    points_earned = min(500, score // 10)
    if points_earned > 0:
        um.add_points(session['user'], points_earned)
    return jsonify({"status": "success", "points_earned": points_earned})
@app.errorhandler(404)
def page_not_found(e):
    if "user" in session: um.increment_counter(session["user"], "404_count")
    return "<h1>404 - Page Not Found</h1><p>お探しのページは見つかりませんでした。</p><a href='/'>トップに戻る</a>", 404

# ───────── 8. Run App ─────────
if __name__ == "__main__":
    port = 5001
    print(f" * 統合ポータルサーバーv6.1起動: http://127.0.0.1:{port}")
    print(f" * 管理者アカウント: admin / admin")
    app.run(debug=True, host="0.0.0.0", port=port)