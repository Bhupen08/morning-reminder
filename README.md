# Morning Briefing

Every day at 8:30 AM (New York time) your iPhone gets a push notification with:
cybersecurity headlines, the biggest stock gainers and droppers, your own
watchlist, and a physique-training tip.

How it works: GitHub runs `morning.py` for free on its own computers (so your
Mac can be off), and the script sends the message through **ntfy**, a free
push-notification app.

Tap the notification to open the **briefing page**
(https://bhupen08.github.io/morning-reminder/): today's briefing in color at the
top, the last 14 days faded below.

Your private ntfy channel name is stored only as the GitHub secret `NTFY_TOPIC`
(it's not in these files, because this repo is public). Anyone who knows it
can read or send to it, so keep it to yourself.

---

## One-time setup

### 1. Phone (2 min)
1. Install **ntfy** from the App Store (free, by Philipp Heckel).
2. Open it, allow notifications, tap **+**, type your channel name, tap **Subscribe**.

### 2. GitHub (5 min)
1. Go to https://github.com/new. Name: `morning-briefing`. Choose **Private**. Click **Create repository**.
2. On the new page click **uploading an existing file**. Drag in `morning.py`,
   `config.json` and `README.md`. Click **Commit changes**.
3. Click **Add file → Create new file**. In the name box type exactly
   `.github/workflows/morning.yml` (the slashes create folders). Paste in the
   contents of `.github/workflows/morning.yml` from this folder. Click **Commit changes**.
4. Go to **Settings → Secrets and variables → Actions → New repository secret**.
   Name: `NTFY_TOPIC`. Secret: your channel name. Click **Add secret**.
5. Test it: **Actions** tab → **Morning briefing** → **Run workflow** → **Run workflow**.
   Within a minute or two your phone should buzz.

That's it. It will now run every morning by itself.

---

## Changing things later
All edits are done on github.com: open the file, click the pencil ✏️, edit, **Commit changes**.

**Change the time** – two places:
1. In `config.json`, change `"send_time": "08:30"` (24-hour clock, e.g. `"06:45"`, `"19:00"`).
2. In `.github/workflows/morning.yml`, change the cron line. Format is
   `"MINUTE HOUR1,HOUR2 * * *"` in UTC. For New York, HOUR1 = your hour + 4 and
   HOUR2 = your hour + 5 (24-hour clock; subtract 24 if over 23).
   - 6:45 AM → `"45 10,11 * * *"`
   - 7:00 AM → `"0 11,12 * * *"`
   - 8:30 AM → `"30 12,13 * * *"`

**Weekdays only:** change the last `*` in the cron line to `1-5` (e.g. `"30 12,13 * * 1-5"`).

**Change the heading:** edit `"title"` in `config.json`.

**Add/remove stocks:** edit the `"watchlist"` list in `config.json`, e.g.
`["^GSPC", "^IXIC", "SPY", "NVDA", "AMZN", "MSFT"]`. Use Yahoo Finance ticker symbols
(`^GSPC` = S&P 500, `^IXIC` = Nasdaq, `^DJI` = Dow, `BTC-USD` = Bitcoin).

**More/fewer headlines or movers:** change `"cyber_news_count"` or `"movers_count"`.

**Days kept on the page:** change `"history_days"` in `config.json`.

**Training tips:** edit the `TRAINING_TIPS` list near the top of `morning.py`.

**Pause it:** Actions tab → Morning briefing → `...` menu → **Disable workflow**.

---

## Good to know
- GitHub's timer can start 5–20 minutes late at busy times, so expect it around 8:30–8:50.
- Stock numbers are from the previous trading day (the market opens at 9:30 AM).
  This is information only, not financial advice.
- If a news or stock source is down, that section says "(couldn't load today)" and the rest still arrives.
- Check runs: Actions tab shows each day's run; a red ✗ means it failed (GitHub also emails you).

### Test from your Mac (optional)
In Terminal, from this folder:
```bash
python3 morning.py --dry-run
NTFY_TOPIC=your-channel-name python3 morning.py
```
