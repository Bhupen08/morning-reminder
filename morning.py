#!/usr/bin/env python3
"""Morning briefing: builds a short digest and pushes it to your phone via ntfy.

Usage:
  NTFY_TOPIC=your-topic python3 morning.py           # build and send now
  python3 morning.py --dry-run                       # just print it, send nothing
  NTFY_TOPIC=your-topic python3 morning.py --scheduled   # only send if it's send_time (used by GitHub)

Uses only the Python standard library, so there is nothing to install.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 (morning-briefing)"}

TRAINING_TIPS = [
    "Progressive overload: add 1 rep or a little weight to one lift this week.",
    "Aim for ~0.7-1 g of protein per lb of goal bodyweight, spread over 3-5 meals.",
    "Control the lowering part of each rep for 2-3 seconds - more growth, fewer injuries.",
    "Sleep 7-9 hours. Muscle is built while you recover, not while you train.",
    "Train each muscle group about twice a week for steady gains.",
    "Leave 1-2 reps in the tank on most sets; go to failure only on the last set.",
    "Warm up with 2-3 lighter ramp-up sets before your first heavy lift.",
    "Drink water early: a big glass now, and aim for pale-yellow urine all day.",
    "Compound lifts first (squat, bench, row, deadlift), isolation work after.",
    "Walk 8-10k steps a day - easy fat loss without hurting recovery.",
    "Track your lifts. If a number hasn't moved in 3 weeks, change reps or exercise.",
    "Pull as much as you push: match every pressing set with a rowing set.",
    "Creatine monohydrate (3-5 g daily) is the most researched, cheapest supplement.",
    "Keep rest at 2-3 min for heavy compound sets, 60-90 s for isolation.",
    "Take a deload (lighter week) every 6-8 weeks to come back stronger.",
    "Full range of motion beats heavier partial reps for muscle growth.",
    "Eat a protein + carb meal 1-3 hours before training for better sessions.",
    "Brace your core like you're about to be punched before every heavy rep.",
    "Shoulders look wider with side raises - try 3 sets of 15 slow reps today.",
    "Mobility: 5 minutes of hip and thoracic stretching after your workout.",
    "Cutting? Lose ~0.5-1% of bodyweight per week to keep your muscle.",
    "Bulking? Gain ~0.25-0.5% of bodyweight per month to stay lean.",
    "Film a set of your main lift and check your form once a week.",
    "Mind-muscle connection: slow down and feel the target muscle working.",
    "Consistency beats intensity. A good workout done is better than a perfect one skipped.",
    "Fiber + veggies at most meals keep you full on a cut.",
    "Do a short finisher today: 3 rounds of push-ups and planks.",
    "Grip weak? Add farmer's carries - 3 walks of 30-40 m with heavy dumbbells.",
    "Keep training sessions under ~75 minutes; focus beats volume.",
    "Weigh yourself daily and watch the weekly average, not single days.",
]


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def cyber_news(cfg):
    items = []
    for feed in cfg["cyber_feeds"]:
        try:
            root = ET.fromstring(fetch(feed))
        except Exception as e:
            print(f"[warn] feed failed {feed}: {e}", file=sys.stderr)
            continue
        for it in root.iter("item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            try:
                when = parsedate_to_datetime(it.findtext("pubDate"))
            except Exception:
                when = datetime.min.replace(tzinfo=ZoneInfo("UTC"))
            if title:
                items.append((when, title, link))
    items.sort(reverse=True)
    seen, out = set(), []
    for _, title, link in items:
        if title.lower() in seen:
            continue
        seen.add(title.lower())
        out.append({"text": title, "link": link})
        if len(out) >= cfg["cyber_news_count"]:
            break
    return out


def movers(screen, count):
    url = ("https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?"
           + urllib.parse.urlencode({"scrIds": screen, "count": count}))
    quotes = json.loads(fetch(url))["finance"]["result"][0]["quotes"]
    return [{"text": f"{q['symbol']} {q['regularMarketChangePercent']:+.1f}% "
                     f"(${q['regularMarketPrice']:.2f}) {q.get('shortName', '')}",
             "change": round(q["regularMarketChangePercent"], 2)}
            for q in quotes[:count]]


def watchlist(symbols):
    out = []
    for sym in symbols:
        try:
            url = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
                   f"{urllib.parse.quote(sym)}?range=5d&interval=1d")
            res = json.loads(fetch(url))["chart"]["result"][0]
            closes = [c for c in res["indicators"]["quote"][0]["close"] if c is not None]
            last, prev = closes[-1], closes[-2]
            name = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^DJI": "Dow"}.get(sym, sym)
            pct = (last / prev - 1) * 100
            out.append({"text": f"{name} {last:,.2f} ({pct:+.1f}%)", "change": round(pct, 2)})
        except Exception as e:
            print(f"[warn] watchlist {sym}: {e}", file=sys.stderr)
    return out


def section(heading, build):
    try:
        items = build()
    except Exception as e:
        print(f"[warn] {heading}: {e}", file=sys.stderr)
        items = []
    return {"heading": heading, "items": items}


def build_briefing(cfg, now):
    tip = TRAINING_TIPS[now.timetuple().tm_yday % len(TRAINING_TIPS)]
    return [
        section("🛡️ CYBERSECURITY", lambda: cyber_news(cfg)),
        section("📈 BIGGEST GAINERS (last session)",
                lambda: movers("day_gainers", cfg["movers_count"])),
        section("📉 BIGGEST DROPPERS (last session)",
                lambda: movers("day_losers", cfg["movers_count"])),
        section("👀 MY WATCHLIST", lambda: watchlist(cfg["watchlist"])),
        {"heading": "💪 TRAINING TIP", "items": [{"text": tip}]},
    ]


def render_text(sections):
    parts = []
    for sec in sections:
        lines = []
        for it in sec["items"]:
            if "change" in it:
                dot = "🟢" if it["change"] > 0 else "🔴" if it["change"] < 0 else "⚪"
                lines.append(f"{dot} {it['text']}")
            elif "link" in it:
                lines.append(f"🔹 {it['text']}\n   {it['link']}")
            else:
                lines.append(it["text"])
        parts.append(sec["heading"] + "\n" + ("\n".join(lines) or "(couldn't load today)"))
    msg = "\n\n".join(parts)
    # ntfy turns messages over 4096 bytes into attachments; keep it inline.
    while len(msg.encode()) > 4000:
        msg = msg[:-200]
    return msg


def save_history(cfg, now, sections):
    """Add today's briefing to docs/history.json, which the web page reads."""
    path = HERE / "docs" / "history.json"
    history = json.loads(path.read_text()) if path.exists() else []
    history = [h for h in history if h["date"] != now.strftime("%Y-%m-%d")]
    history.insert(0, {"date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M"),
                       "sections": sections})
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(history[:cfg["history_days"]], ensure_ascii=False, indent=1))


def is_send_time(cfg, now):
    # GitHub runs us twice (to cover daylight saving) and may start late;
    # send only on the run that lands in the hour after send_time.
    h, m = map(int, cfg["send_time"].split(":"))
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return target <= now < target + timedelta(hours=1)


def send(topic, title, msg, page_url):
    headers = {"Title": title.encode().decode("latin-1", "ignore"),
               "Priority": "high", "Tags": "sunrise"}
    if page_url:
        headers["Click"] = page_url  # tapping the notification opens the page
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}", data=msg.encode(), method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        print(f"sent: HTTP {r.status}")


def main():
    cfg = json.loads((HERE / "config.json").read_text())
    now = datetime.now(ZoneInfo(cfg["timezone"]))
    if "--scheduled" in sys.argv and not is_send_time(cfg, now):
        print(f"Not send time yet ({now:%H:%M} {cfg['timezone']}); skipping.")
        return
    sections = build_briefing(cfg, now)
    msg = render_text(sections)
    print(msg)
    if "--dry-run" in sys.argv:
        return
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        sys.exit("NTFY_TOPIC is not set")
    save_history(cfg, now, sections)
    send(topic, cfg["title"], msg, cfg.get("page_url"))


if __name__ == "__main__":
    main()
