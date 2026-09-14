#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scene_db.py (V3) —— 虚拟屏 UI 自动化「场景缓存」数据库（三表混合结构）

设计（方案 C）：
  screens       界面表：某 App 的某个界面(Activity)  唯一键(package_name, activity)
  elements      元素表：某界面上的可点元素 + 比例坐标  唯一键(screen_id, label)
  actions       操作表：一个"操作"（可跨界面）
  action_steps  步骤表：操作的第N步 = 在<某界面>点<某元素>

旧表 scenes / scene_targets 仍保留（作备份），但不再作为主结构。

常用命令（Ubuntu 终端）：
  python3 scene_db.py init
  python3 scene_db.py add-screen --app 拼多多 --pkg com.xunmeng.pinduoduo --act "首页" --desc "底部导航5项"
  python3 scene_db.py add-element --pkg com.xunmeng.pinduoduo --act "首页" --label "个人中心" --xy "901,983"
  python3 scene_db.py add-action --name "拼多多查物流" --steps "pkg|act|label; pkg|act|label"
  python3 scene_db.py query-action --name "再来一单"
  python3 scene_db.py query-screen --pkg com.xunmeng.pinduoduo --act "首页"
  python3 scene_db.py list
  python3 scene_db.py export --out scenes_v3_backup.json
  python3 scene_db.py add ...（兼容旧命令，自动拆解到三表）

默认库路径：/sdcard/Download/Operit/skills/virtual_screen_auto/data/scenes.db
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import date

DEFAULT_DB = "/sdcard/Download/Operit/skills/virtual_screen_auto/data/scenes.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS screens (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name      TEXT NOT NULL,
    package_name  TEXT NOT NULL,
    activity      TEXT NOT NULL,
    screen_desc   TEXT,
    resolution_w  INTEGER DEFAULT 1264,
    resolution_h  INTEGER DEFAULT 2704,
    verified_date TEXT,
    created_at    TEXT,
    updated_at    TEXT,
    UNIQUE(package_name, activity)
);
CREATE TABLE IF NOT EXISTS elements (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    screen_id    INTEGER NOT NULL,
    label        TEXT NOT NULL,
    x_ratio      INTEGER NOT NULL,
    y_ratio      INTEGER NOT NULL,
    element_desc TEXT,
    verified_date TEXT,
    hit_count    INTEGER DEFAULT 0,
    fail_count   INTEGER DEFAULT 0,
    created_at   TEXT,
    updated_at   TEXT,
    UNIQUE(screen_id, label),
    FOREIGN KEY(screen_id) REFERENCES screens(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS actions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    action_name TEXT NOT NULL UNIQUE,
    action_desc TEXT,
    updated_at  TEXT
);
CREATE TABLE IF NOT EXISTS action_steps (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id  INTEGER NOT NULL,
    step_order INTEGER NOT NULL,
    screen_id  INTEGER NOT NULL,
    element_id INTEGER NOT NULL,
    note       TEXT,
    FOREIGN KEY(action_id)  REFERENCES actions(id)  ON DELETE CASCADE,
    FOREIGN KEY(screen_id)  REFERENCES screens(id)  ON DELETE CASCADE,
    FOREIGN KEY(element_id) REFERENCES elements(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_elem_screen ON elements(screen_id);
CREATE INDEX IF NOT EXISTS idx_step_action ON action_steps(action_id);
CREATE INDEX IF NOT EXISTS idx_screen_pkg ON screens(package_name);
CREATE TABLE IF NOT EXISTS scenes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name      TEXT NOT NULL,
    package_name  TEXT NOT NULL,
    activity      TEXT NOT NULL,
    action        TEXT NOT NULL,
    context_desc  TEXT,
    resolution_w  INTEGER,
    resolution_h  INTEGER,
    verified_date TEXT,
    hit_count     INTEGER DEFAULT 0,
    fail_count    INTEGER DEFAULT 0,
    created_at    TEXT,
    updated_at    TEXT,
    UNIQUE(package_name, activity, action)
);
CREATE TABLE IF NOT EXISTS scene_targets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_id     INTEGER NOT NULL,
    step_order   INTEGER NOT NULL DEFAULT 1,
    target_label TEXT NOT NULL,
    x_ratio      INTEGER NOT NULL,
    y_ratio      INTEGER NOT NULL,
    note         TEXT,
    FOREIGN KEY(scene_id) REFERENCES scenes(id) ON DELETE CASCADE
);
"""


def connect(db_path):
    d = os.path.dirname(db_path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def today():
    return date.today().isoformat()


def upsert_screen(cur, app, pkg, act, desc=None, w=1264, h=2704):
    row = cur.execute("SELECT id FROM screens WHERE package_name=? AND activity=?",
                      (pkg, act)).fetchone()
    if row:
        sid = row[0]
        cur.execute("UPDATE screens SET app_name=?, screen_desc=COALESCE(?,screen_desc), "
                    "resolution_w=?, resolution_h=?, verified_date=?, updated_at=? WHERE id=?",
                    (app, desc, w, h, today(), today(), sid))
        return sid
    cur.execute("""INSERT INTO screens(app_name,package_name,activity,screen_desc,
                   resolution_w,resolution_h,verified_date,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (app, pkg, act, desc, w, h, today(), today(), today()))
    return cur.lastrowid


def upsert_element(cur, screen_id, label, x, y, desc=None):
    row = cur.execute("SELECT id FROM elements WHERE screen_id=? AND label=?",
                      (screen_id, label)).fetchone()
    if row:
        eid = row[0]
        cur.execute("UPDATE elements SET x_ratio=?, y_ratio=?, element_desc=COALESCE(?,element_desc),"
                    " verified_date=?, updated_at=? WHERE id=?",
                    (x, y, desc, today(), today(), eid))
        return eid
    cur.execute("""INSERT INTO elements(screen_id,label,x_ratio,y_ratio,element_desc,
                   verified_date,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)""",
                (screen_id, label, x, y, desc, today(), today(), today()))
    return cur.lastrowid


def cmd_init(args):
    conn = connect(args.db); conn.executescript(SCHEMA); conn.commit()
    ns = conn.execute("SELECT COUNT(*) FROM screens").fetchone()[0]
    ne = conn.execute("SELECT COUNT(*) FROM elements").fetchone()[0]
    na = conn.execute("SELECT COUNT(*) FROM actions").fetchone()[0]
    print("OK 数据库已就绪(V3三表):", args.db)
    print("   screens=%d  elements=%d  actions=%d" % (ns, ne, na))
    conn.close()


def cmd_add_screen(args):
    conn = connect(args.db); conn.executescript(SCHEMA); cur = conn.cursor()
    sid = upsert_screen(cur, args.app, args.pkg, args.act, args.desc, args.w or 1264, args.h or 2704)
    conn.commit(); conn.close()
    print("OK screen_id=%d  %s(%s) / %s" % (sid, args.app, args.pkg, args.act))


def cmd_add_element(args):
    conn = connect(args.db); conn.executescript(SCHEMA); cur = conn.cursor()
    sid = upsert_screen(cur, args.app or "", args.pkg, args.act, None)
    x, y = [int(v) for v in args.xy.split(",")]
    eid = upsert_element(cur, sid, args.label, x, y, args.desc)
    conn.commit(); conn.close()
    print("OK element_id=%d  screen=%s/%s  %s -> [%d,%d]" % (eid, args.pkg, args.act, args.label, x, y))


def _parse_steps(steps_str):
    out = []
    for part in steps_str.split(";"):
        part = part.strip()
        if not part:
            continue
        seg = [s.strip() for s in part.split("|")]
        if len(seg) != 3:
            sys.exit("错误：步骤格式应为 'pkg|act|label'，实际: %s" % part)
        out.append(seg)
    return out


def cmd_add_action(args):
    conn = connect(args.db); conn.executescript(SCHEMA); cur = conn.cursor()
    steps = _parse_steps(args.steps)
    if not steps:
        sys.exit("错误：--steps 不能为空")
    row = cur.execute("SELECT id FROM actions WHERE action_name=?", (args.name,)).fetchone()
    if row:
        aid = row[0]
        cur.execute("UPDATE actions SET action_desc=?, updated_at=? WHERE id=?",
                    (args.desc, today(), aid))
        cur.execute("DELETE FROM action_steps WHERE action_id=?", (aid,))
        print("更新操作 id=%d" % aid)
    else:
        cur.execute("INSERT INTO actions(action_name,action_desc,updated_at) VALUES(?,?,?)",
                    (args.name, args.desc, today()))
        aid = cur.lastrowid
        print("新增操作 id=%d" % aid)
    for i, (pkg, act, label) in enumerate(steps, 1):
        sid_row = cur.execute("SELECT id FROM screens WHERE package_name=? AND activity=?",
                              (pkg, act)).fetchone()
        if not sid_row:
            sys.exit("错误：界面不存在 %s/%s（请先 add-screen/add-element）" % (pkg, act))
        sid = sid_row[0]
        eid_row = cur.execute("SELECT id FROM elements WHERE screen_id=? AND label=?",
                              (sid, label)).fetchone()
        if not eid_row:
            sys.exit("错误：元素不存在 %s（界面 %s/%s）" % (label, pkg, act))
        cur.execute("INSERT INTO action_steps(action_id,step_order,screen_id,element_id) VALUES(?,?,?,?)",
                    (aid, i, sid, eid_row[0]))
    conn.commit(); conn.close()
    print("OK 写入 %d 个步骤" % len(steps))


def cmd_query_action(args):
    conn = connect(args.db)
    sql = "SELECT id,action_name,action_desc FROM actions WHERE 1=1"
    p = []
    if args.name:
        sql += " AND action_name LIKE ?"; p.append("%" + args.name + "%")
    rows = conn.execute(sql, p).fetchall()
    if not rows:
        print("MISS 未命中操作缓存"); conn.close(); return
    for r in rows:
        aid = r[0]
        print("HIT action_id=%d  %s" % (aid, r[1]))
        if r[2]:
            print("  说明: %s" % r[2])
        steps = conn.execute("""
            SELECT s.step_order, sc.app_name, sc.package_name, sc.activity,
                   e.label, e.x_ratio, e.y_ratio, e.id
            FROM action_steps s
            JOIN screens sc ON sc.id=s.screen_id
            JOIN elements e ON e.id=s.element_id
            WHERE s.action_id=? ORDER BY s.step_order""", (aid,)).fetchall()
        for t in steps:
            print("  第%d步 | %s(%s)/%s | 点「%s」-> [%d, %d]" %
                  (t[0], t[1], t[2], t[3], t[4], t[5], t[6]))
            conn.execute("UPDATE elements SET hit_count=hit_count+1, updated_at=? WHERE id=?",
                         (today(), t[7]))
    conn.commit(); conn.close()


def cmd_query_screen(args):
    conn = connect(args.db)
    sql = "SELECT id,app_name,package_name,activity,screen_desc FROM screens WHERE 1=1"
    p = []
    if args.pkg:
        sql += " AND package_name=?"; p.append(args.pkg)
    if args.act:
        sql += " AND activity LIKE ?"; p.append("%" + args.act + "%")
    if args.app:
        sql += " AND app_name LIKE ?"; p.append("%" + args.app + "%")
    rows = conn.execute(sql, p).fetchall()
    if not rows:
        print("MISS 未命中界面"); conn.close(); return
    for r in rows:
        print("HIT screen_id=%d  %s(%s)/%s" % (r[0], r[1], r[2], r[3]))
        if r[4]:
            print("  描述: %s" % r[4])
        els = conn.execute("SELECT label,x_ratio,y_ratio,hit_count,fail_count FROM elements "
                           "WHERE screen_id=? ORDER BY id", (r[0],)).fetchall()
        for e in els:
            print("    「%s」-> [%d, %d]  (命中%d/失败%d)" % (e[0], e[1], e[2], e[3], e[4]))
    conn.close()


def cmd_add(args):
    conn = connect(args.db); conn.executescript(SCHEMA); cur = conn.cursor()
    targets = [t.strip() for t in (args.targets or "").split(";") if t.strip()]
    labels = [s.strip() for s in (args.labels or "").split(";") if s.strip()]
    if not targets:
        sys.exit("错误：至少需要一个 --targets")
    if len(labels) < len(targets):
        labels += ["步骤%d" % (i + 1) for i in range(len(labels), len(targets))]
    w, h = (args.w or 1264), (args.h or 2704)
    sid = upsert_screen(cur, args.app, args.pkg, args.act, args.ctx, w, h)
    for i, t in enumerate(targets, 1):
        x, y = [int(v.strip()) for v in t.split(",")]
        upsert_element(cur, sid, labels[i - 1], x, y, None)
    row = cur.execute("SELECT id FROM scenes WHERE package_name=? AND activity=? AND action=?",
                      (args.pkg, args.act, args.action)).fetchone()
    if row:
        sid_old = row[0]
        cur.execute("UPDATE scenes SET app_name=?, context_desc=?, verified_date=?, updated_at=? WHERE id=?",
                    (args.app, args.ctx, today(), today(), sid_old))
        cur.execute("DELETE FROM scene_targets WHERE scene_id=?", (sid_old,))
    else:
        cur.execute("""INSERT INTO scenes(app_name,package_name,activity,action,context_desc,
                       resolution_w,resolution_h,verified_date,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (args.app, args.pkg, args.act, args.action, args.ctx, w, h, today(), today(), today()))
        sid_old = cur.lastrowid
    for i, t in enumerate(targets, 1):
        x, y = [int(v.strip()) for v in t.split(",")]
        cur.execute("INSERT INTO scene_targets(scene_id,step_order,target_label,x_ratio,y_ratio) VALUES(?,?,?,?,?)",
                    (sid_old, i, labels[i - 1], x, y))
    conn.commit(); conn.close()
    print("OK 兼容写入：screen_id=%d, 元素 %d 个" % (sid, len(targets)))


def cmd_list(args):
    conn = connect(args.db)
    print("=== screens ===")
    for r in conn.execute("SELECT id,app_name,package_name,activity,screen_desc FROM screens ORDER BY id"):
        print("  screen%d | %s(%s) | %s | %s" % (r[0], r[1], r[2], r[3], r[4] or ""))
    print("=== elements ===")
    for r in conn.execute("""SELECT e.id,sc.activity,e.label,e.x_ratio,e.y_ratio FROM elements e
                             JOIN screens sc ON sc.id=e.screen_id ORDER BY e.screen_id,e.id"""):
        print("  elem%d | %s | 「%s」[%d,%d]" % (r[0], r[1], r[2], r[3], r[4]))
    print("=== actions ===")
    for r in conn.execute("SELECT id,action_name,action_desc FROM actions ORDER BY id"):
        print("  action%d | %s | %s" % (r[0], r[1], r[2] or ""))
    print("=== action_steps ===")
    for r in conn.execute("""SELECT st.action_id,a.action_name,st.step_order,sc.activity,e.label
                             FROM action_steps st JOIN actions a ON a.id=st.action_id
                             JOIN screens sc ON sc.id=st.screen_id
                             JOIN elements e ON e.id=st.element_id
                             ORDER BY st.action_id,st.step_order"""):
        print("  [%s] 第%d步: %s -> 「%s」" % (r[1], r[2], r[3], r[4]))
    ns = conn.execute("SELECT COUNT(*) FROM screens").fetchone()[0]
    ne = conn.execute("SELECT COUNT(*) FROM elements").fetchone()[0]
    na = conn.execute("SELECT COUNT(*) FROM actions").fetchone()[0]
    print("--- 共 %d 界面 / %d 元素 / %d 操作 ---" % (ns, ne, na))
    conn.close()


def cmd_export(args):
    conn = connect(args.db)
    out = {}
    for tbl in ("screens", "elements", "actions", "action_steps"):
        rows = conn.execute("SELECT * FROM %s" % tbl).fetchall()
        cols = [d[0] for d in conn.execute("SELECT * FROM %s LIMIT 1" % tbl).description]
        out[tbl] = [dict(zip(cols, r)) for r in rows]
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    conn.close()
    print("OK 已导出到 %s（screens=%d elements=%d actions=%d steps=%d）" %
          (args.out, len(out["screens"]), len(out["elements"]), len(out["actions"]), len(out["action_steps"])))


def cmd_fail(args):
    conn = connect(args.db)
    conn.execute("UPDATE elements SET fail_count=fail_count+1, updated_at=? WHERE id=?",
                 (today(), args.id))
    r = conn.execute("SELECT fail_count FROM elements WHERE id=?", (args.id,)).fetchone()
    conn.commit(); conn.close()
    if r:
        print("OK element_id=%d fail_count=%d %s" % (args.id, r[0], "(>=3 建议重验)" if r[0] >= 3 else ""))


def main():
    ap = argparse.ArgumentParser(description="虚拟屏场景缓存数据库 V3（三表）")
    ap.add_argument("--db", default=DEFAULT_DB)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="建库/升级表结构").set_defaults(func=cmd_init)

    s = sub.add_parser("add-screen", help="新增界面")
    s.add_argument("--app", default=""); s.add_argument("--pkg", required=True)
    s.add_argument("--act", required=True); s.add_argument("--desc", default="")
    s.add_argument("--w", type=int, default=None); s.add_argument("--h", type=int, default=None)
    s.set_defaults(func=cmd_add_screen)

    e = sub.add_parser("add-element", help="新增元素")
    e.add_argument("--app", default=""); e.add_argument("--pkg", required=True)
    e.add_argument("--act", required=True); e.add_argument("--label", required=True)
    e.add_argument("--xy", required=True); e.add_argument("--desc", default="")
    e.set_defaults(func=cmd_add_element)

    a = sub.add_parser("add-action", help="新增操作")
    a.add_argument("--name", required=True); a.add_argument("--desc", default="")
    a.add_argument("--steps", required=True, help="pkg|act|label ; ...")
    a.set_defaults(func=cmd_add_action)

    qa = sub.add_parser("query-action", help="按操作查询")
    qa.add_argument("--name"); qa.set_defaults(func=cmd_query_action)

    qs = sub.add_parser("query-screen", help="按界面查询")
    qs.add_argument("--pkg"); qs.add_argument("--act"); qs.add_argument("--app")
    qs.set_defaults(func=cmd_query_screen)

    old = sub.add_parser("add", help="兼容旧命令")
    old.add_argument("--app", required=True); old.add_argument("--pkg", required=True)
    old.add_argument("--act", required=True); old.add_argument("--action", required=True)
    old.add_argument("--ctx", default=""); old.add_argument("--targets", required=True)
    old.add_argument("--labels", default=""); old.add_argument("--w", type=int, default=None)
    old.add_argument("--h", type=int, default=None)
    old.set_defaults(func=cmd_add)

    sub.add_parser("list", help="列出全部").set_defaults(func=cmd_list)

    ex = sub.add_parser("export", help="导出 JSON")
    ex.add_argument("--out", default="scenes_v3_backup.json"); ex.set_defaults(func=cmd_export)

    fa = sub.add_parser("fail", help="记录元素失败")
    fa.add_argument("--id", type=int, required=True); fa.set_defaults(func=cmd_fail)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()