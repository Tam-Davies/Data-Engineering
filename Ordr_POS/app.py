"""
ORDR Restaurant POS — Flask Backend (PostgreSQL Edition)
"""
from flask import (Flask, jsonify, request, render_template,
                   redirect, url_for, session, send_file)
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from sqlalchemy import text
from functools import wraps
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import csv, io, os, uuid, logging, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline.config import DATABASE_URL
from pipeline.db import (
    Base, Staff, RestaurantTable, MenuCategory, MenuItem,
    Order, OrderItem, SalesDaily, SalesWeekly, SalesMonthly,
    AlertLog, PipelineRun, get_db, create_tables
)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "ordr-change-in-production")
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
TAX_RATE = 0.075


# Auth helpers
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "staff_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("staff_role") not in ("Manager", "Admin"):
            return jsonify({"error": "Manager access required"}), 403
        return f(*args, **kwargs)
    return decorated

def _f(v):
    return float(v) if isinstance(v, Decimal) else (float(v) if v else 0.0)

def _staff_safe(s):
    return {"id": s.id, "name": s.name, "role": s.role, "active": s.active}

def _order_dict(o, db):
    items = db.query(OrderItem).filter_by(order_id=o.id).all()
    item_list = [{"id": it.menu_item_id or "", "name": it.name,
                  "price": _f(it.price), "qty": it.qty, "emoji": ""} for it in items]
    sub = sum(i["price"] * i["qty"] for i in item_list)
    tax = round(sub * TAX_RATE, 2)
    return {
        "id": o.id, "table_id": o.table_id or "",
        "table_no": str(o.table.number) if o.table else "T/A",
        "staff_id": o.staff_id or "",
        "staff_name": o.staff_member.name if o.staff_member else "Unknown",
        "items": item_list, "status": o.status, "note": o.note or "",
        "subtotal": sub, "tax": tax, "total": round(sub + tax, 2),
        "created_at": o.created_at.isoformat() if o.created_at else "",
        "updated_at": o.updated_at.isoformat() if o.updated_at else "",
    }


# Pages
@app.route("/login")
def login_page():
    if "staff_id" in session:
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/monitor")
@login_required
def monitor_page():
    return render_template("monitor.html")


# Auth API
@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.json or {}
    with get_db() as db:
        s = db.query(Staff).filter_by(name=data.get("name"), active=True).first()
        if not s or not bcrypt.check_password_hash(s.pin_hash, data.get("pin", "")):
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
        session["staff_id"]   = s.id
        session["staff_name"] = s.name
        session["staff_role"] = s.role
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=12)
        return jsonify({"success": True, "staff": _staff_safe(s)})

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/auth/me")
def api_me():
    if "staff_id" not in session:
        return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "staff": {
        "id": session["staff_id"], "name": session["staff_name"], "role": session["staff_role"]}})

@app.route("/api/staff/login", methods=["POST"])
def staff_pin_login():
    return api_login()


# Menu API
@app.route("/api/menu")
def get_menu():
    with get_db() as db:
        cats = db.query(MenuCategory).order_by(MenuCategory.sort_order).all()
        result = {}
        for cat in cats:
            items = db.query(MenuItem).filter_by(category_id=cat.id, active=True).all()
            result[cat.name] = [{"id": i.id, "name": i.name,
                                  "price": _f(i.price), "emoji": i.emoji} for i in items]
        return jsonify({"menu": result})

@app.route("/api/menu/item", methods=["POST"])
@login_required
def add_menu_item():
    data = request.json
    with get_db() as db:
        cat = db.query(MenuCategory).filter_by(name=data.get("category", "Mains")).first()
        if not cat:
            return jsonify({"error": "Category not found"}), 404
        item = MenuItem(id="m"+str(uuid.uuid4())[:6], category_id=cat.id,
                        name=data["name"], price=float(data["price"]),
                        emoji=data.get("emoji", ""))
        db.add(item)
        db.flush()
        return jsonify({"success": True, "item": {"id": item.id, "name": item.name,
                         "price": _f(item.price), "emoji": item.emoji}}), 201

@app.route("/api/menu/item/<item_id>", methods=["DELETE"])
@login_required
@manager_required
def delete_menu_item(item_id):
    with get_db() as db:
        item = db.query(MenuItem).filter_by(id=item_id).first()
        if not item:
            return jsonify({"error": "Not found"}), 404
        item.active = False
    return jsonify({"success": True})


# Tables API
@app.route("/api/tables")
def get_tables():
    with get_db() as db:
        tables = db.query(RestaurantTable).order_by(RestaurantTable.number).all()
        return jsonify({"tables": [{"id": t.id, "number": t.number,
                                     "seats": t.seats, "status": t.status} for t in tables]})

@app.route("/api/tables/<tid>/status", methods=["PUT"])
@login_required
def update_table_status(tid):
    with get_db() as db:
        t = db.query(RestaurantTable).filter_by(id=tid).first()
        if not t:
            return jsonify({"error": "Not found"}), 404
        t.status = request.json.get("status", "available")
        t.updated_at = datetime.now(timezone.utc)
    return jsonify({"success": True})


# Staff API
@app.route("/api/staff")
@login_required
def get_staff():
    with get_db() as db:
        staff = db.query(Staff).filter_by(active=True).all()
        return jsonify({"staff": [_staff_safe(s) for s in staff]})

@app.route("/api/staff", methods=["POST"])
@login_required
@manager_required
def create_staff():
    data = request.json
    with get_db() as db:
        s = Staff(id="s"+str(uuid.uuid4())[:6], name=data["name"],
                  role=data.get("role","Waiter"),
                  pin_hash=bcrypt.generate_password_hash(data["pin"]).decode())
        db.add(s)
        db.flush()
        return jsonify({"success": True, "staff": _staff_safe(s)}), 201


# Orders API
@app.route("/api/orders")
@login_required
def get_orders():
    status = request.args.get("status")
    with get_db() as db:
        q = db.query(Order)
        if status:
            q = q.filter_by(status=status)
        orders = q.order_by(Order.created_at.desc()).limit(200).all()
        return jsonify({"orders": [_order_dict(o, db) for o in orders]})

@app.route("/api/orders", methods=["POST"])
@login_required
def create_order():
    data = request.json
    with get_db() as db:
        items   = data.get("items", [])
        sub     = sum(float(i["price"]) * int(i["qty"]) for i in items)
        tax     = round(sub * TAX_RATE, 2)
        oid     = "ORD-" + str(uuid.uuid4())[:6].upper()
        order   = Order(id=oid, table_id=data.get("table_id") or None,
                        staff_id=data.get("staff_id") or session.get("staff_id"),
                        status="pending", note=data.get("note",""),
                        subtotal=sub, tax=tax, total=round(sub+tax,2))
        db.add(order)
        db.flush()
        for item in items:
            db.add(OrderItem(order_id=order.id, menu_item_id=item.get("id") or None,
                             name=item["name"], price=float(item["price"]), qty=int(item["qty"])))
        if data.get("table_id"):
            t = db.query(RestaurantTable).filter_by(id=data["table_id"]).first()
            if t: t.status = "occupied"
        db.flush()
        return jsonify({"success": True, "order": _order_dict(order, db)}), 201

@app.route("/api/orders/<oid>")
@login_required
def get_order(oid):
    with get_db() as db:
        o = db.query(Order).filter_by(id=oid).first()
        if not o: return jsonify({"error": "Not found"}), 404
        return jsonify(_order_dict(o, db))

@app.route("/api/orders/<oid>/status", methods=["PUT"])
@login_required
def update_order_status(oid):
    with get_db() as db:
        o = db.query(Order).filter_by(id=oid).first()
        if not o: return jsonify({"error": "Not found"}), 404
        o.status = request.json.get("status")
        o.updated_at = datetime.now(timezone.utc)
        if o.status == "paid" and o.table_id:
            t = db.query(RestaurantTable).filter_by(id=o.table_id).first()
            if t: t.status = "available"
        db.flush()
        return jsonify({"success": True, "order": _order_dict(o, db)})


# Analytics API
@app.route("/api/analytics/summary")
@login_required
def analytics_summary():
    with get_db() as db:
        today = datetime.now(timezone.utc).date()
        ws    = today - timedelta(days=today.weekday())
        def qr(where, params={}):
            r = db.execute(text(
                f"SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders WHERE status='paid' AND {where}"),
                params).fetchone()
            return int(r[0]), float(r[1])
        t_c,t_r = qr("DATE(created_at)=:d", {"d": today})
        w_c,w_r = qr("DATE(created_at)>=:s", {"s": ws})
        m_c,m_r = qr("EXTRACT(MONTH FROM created_at)=EXTRACT(MONTH FROM NOW()) AND EXTRACT(YEAR FROM created_at)=EXTRACT(YEAR FROM NOW())")
        a_c,a_r = qr("1=1")
        pending = db.query(Order).filter_by(status="pending").count()
        active  = db.query(RestaurantTable).filter_by(status="occupied").count()
        top     = db.execute(text(
            "SELECT oi.name,SUM(oi.qty) as t FROM order_items oi "
            "JOIN orders o ON o.id=oi.order_id WHERE o.status='paid' "
            "GROUP BY oi.name ORDER BY t DESC LIMIT 5")).fetchall()
        return jsonify({
            "today":{"orders":t_c,"revenue":t_r},"week":{"orders":w_c,"revenue":w_r},
            "month":{"orders":m_c,"revenue":m_r},"total":{"orders":a_c,"revenue":a_r},
            "pending":pending,"active_tables":active,
            "top_items":[[r[0],int(r[1])] for r in top],
        })


# Export API
def _csv_response(rows, headers, filename):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(headers)
    for r in rows: w.writerow(r)
    out.seek(0)
    return send_file(io.BytesIO(out.getvalue().encode()), mimetype="text/csv",
                     as_attachment=True, download_name=filename)

@app.route("/api/export/orders")
@login_required
def export_orders():
    from_d = request.args.get("from_date",""); to_d = request.args.get("to_date","")
    fmt    = request.args.get("format","csv")
    with get_db() as db:
        q = ("SELECT o.id,o.created_at,o.status,o.total,o.subtotal,o.tax,o.note,"
             "t.number,s.name FROM orders o "
             "LEFT JOIN restaurant_tables t ON t.id=o.table_id "
             "LEFT JOIN staff s ON s.id=o.staff_id WHERE o.status='paid'")
        params = {}
        if from_d: q += " AND DATE(o.created_at)>=:fd"; params["fd"]=from_d
        if to_d:   q += " AND DATE(o.created_at)<=:td"; params["td"]=to_d
        rows = db.execute(text(q+" ORDER BY o.created_at DESC"), params).fetchall()
    if fmt=="json": return jsonify([list(r) for r in rows])
    return _csv_response(
        [[r[0],str(r[1])[:19],r[2],f"{_f(r[3]):.2f}",f"{_f(r[4]):.2f}",
          f"{_f(r[5]):.2f}",r[6] or "",r[7] or "T/A",r[8] or ""] for r in rows],
        ["Order ID","Date","Status","Total","Subtotal","Tax","Note","Table","Staff"],
        f"ordr_orders_{datetime.now().strftime('%Y%m%d')}.csv")

@app.route("/api/export/items")
@login_required
def export_items():
    fmt = request.args.get("format","csv")
    with get_db() as db:
        rows = db.execute(text(
            "SELECT o.id,o.created_at,oi.name,oi.price,oi.qty,oi.price*oi.qty,"
            "mc.name,t.number,s.name FROM order_items oi "
            "JOIN orders o ON o.id=oi.order_id "
            "LEFT JOIN menu_items mi ON mi.id=oi.menu_item_id "
            "LEFT JOIN menu_categories mc ON mc.id=mi.category_id "
            "LEFT JOIN restaurant_tables t ON t.id=o.table_id "
            "LEFT JOIN staff s ON s.id=o.staff_id "
            "WHERE o.status='paid' ORDER BY o.created_at DESC")).fetchall()
    if fmt=="json": return jsonify([list(r) for r in rows])
    return _csv_response(
        [[r[0],str(r[1])[:19],r[2],f"{_f(r[3]):.2f}",r[4],f"{_f(r[5]):.2f}",
          r[6] or "Uncategorized",r[7] or "T/A",r[8] or ""] for r in rows],
        ["Order ID","Date","Item","Price","Qty","Line Total","Category","Table","Staff"],
        f"ordr_items_{datetime.now().strftime('%Y%m%d')}.csv")

@app.route("/api/export/daily-summary")
@login_required
def export_daily():
    fmt = request.args.get("format","csv")
    with get_db() as db:
        rows = db.query(SalesDaily).order_by(SalesDaily.date.desc()).all()
    if fmt=="json":
        return jsonify([{"date":str(r.date),"orders":r.total_orders,
            "revenue":_f(r.total_revenue),"avg":_f(r.avg_order_val),"top_item":r.top_item} for r in rows])
    return _csv_response(
        [[r.date,r.total_orders,f"{_f(r.total_revenue):.2f}",
          f"{_f(r.avg_order_val):.2f}",r.top_item or ""] for r in rows],
        ["Date","Orders","Revenue","Avg Order Value","Top Item"],
        f"ordr_daily_{datetime.now().strftime('%Y%m%d')}.csv")

@app.route("/api/export/weekly-summary")
@login_required
def export_weekly():
    fmt = request.args.get("format","csv")
    with get_db() as db:
        rows = db.query(SalesWeekly).order_by(SalesWeekly.week_start.desc()).all()
    if fmt=="json":
        return jsonify([{"week_start":str(r.week_start),"week_end":str(r.week_end),
            "orders":r.total_orders,"revenue":_f(r.total_revenue),"wow_pct":_f(r.wow_change_pct)} for r in rows])
    return _csv_response(
        [[r.week_start,r.week_end,r.total_orders,f"{_f(r.total_revenue):.2f}",
          f"{_f(r.wow_change_pct):+.1f}%" if r.wow_change_pct else "N/A"] for r in rows],
        ["Week Start","Week End","Orders","Revenue","WoW Change %"],
        f"ordr_weekly_{datetime.now().strftime('%Y%m%d')}.csv")

@app.route("/api/export/monthly-summary")
@login_required
def export_monthly():
    fmt = request.args.get("format","csv")
    with get_db() as db:
        rows = db.query(SalesMonthly).order_by(
            SalesMonthly.year.desc(), SalesMonthly.month.desc()).all()
    if fmt=="json":
        return jsonify([{"year":r.year,"month":r.month,"orders":r.total_orders,
            "revenue":_f(r.total_revenue),"mom_pct":_f(r.mom_change_pct)} for r in rows])
    return _csv_response(
        [[r.year,r.month,r.total_orders,f"{_f(r.total_revenue):.2f}",
          f"{_f(r.mom_change_pct):+.1f}%" if r.mom_change_pct else "N/A"] for r in rows],
        ["Year","Month","Orders","Revenue","MoM Change %"],
        f"ordr_monthly_{datetime.now().strftime('%Y%m%d')}.csv")


# Monitor API
@app.route("/api/monitor/pipeline-runs")
@login_required
def monitor_runs():
    with get_db() as db:
        runs = db.query(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(50).all()
        return jsonify({"runs": [{
            "id":r.id,"run_type":r.run_type,"status":r.status,
            "records_processed":r.records_processed,"error_message":r.error_message,
            "started_at":r.started_at.isoformat() if r.started_at else "",
            "finished_at":r.finished_at.isoformat() if r.finished_at else "",
            "duration_s":round((r.finished_at-r.started_at).total_seconds(),1)
                         if r.finished_at and r.started_at else None,
        } for r in runs]})

@app.route("/api/monitor/alerts")
@login_required
def monitor_alerts():
    with get_db() as db:
        alerts = db.query(AlertLog).order_by(AlertLog.sent_at.desc()).limit(100).all()
        return jsonify({"alerts": [{
            "id":a.id,"alert_type":a.alert_type,"period":a.period,
            "current_val":_f(a.current_val),"previous_val":_f(a.previous_val),
            "change_pct":_f(a.change_pct),"message":a.message,
            "sent_at":a.sent_at.isoformat() if a.sent_at else "",
            "channels":a.channels or [],
        } for a in alerts]})

@app.route("/api/monitor/stats")
@login_required
def monitor_stats():
    with get_db() as db:
        total  = db.query(PipelineRun).count()
        failed = db.query(PipelineRun).filter_by(status="failed").count()
        last   = db.query(PipelineRun).filter_by(status="success").order_by(
            PipelineRun.finished_at.desc()).first()
        return jsonify({
            "total_runs":total,"failed_runs":failed,
            "success_rate":round((total-failed)/total*100,1) if total else 100.0,
            "last_success":last.finished_at.isoformat() if last and last.finished_at else None,
            "total_alerts":db.query(AlertLog).count(),
            "total_orders_synced":db.query(Order).filter_by(status="paid").count(),
        })


# Seed & boot
def seed_database():
    try:
        with get_db() as db:
            if db.query(Staff).count() > 0:
                print("Already seeded, skipping.")
                return
            for name, role, pin in [
                ("Amara Osei", "Cashier", "1234"),
                ("Kofi Mensah", "Waiter", "5678"),
                ("Fatima Bello", "Manager", "9999"),
                ("Chidi Eze", "Waiter", "4321")
            ]:
                db.add(Staff(
                    id="s"+str(uuid.uuid4())[:6],
                    name=name, role=role,
                    pin_hash=bcrypt.generate_password_hash(pin).decode()
                ))
            menu_data = [
                ("Starters", [("Spring Rolls",4.50),("Chicken Wings",7.00),("Garlic Bread",3.50),("Soup of the Day",5.00)]),
                ("Mains",    [("Grilled Salmon",18.00),("Beef Burger",14.50),("Pasta Carbonara",13.00),("Jollof Rice",12.00),("Grilled Chicken",15.00)]),
                ("Sides",    [("French Fries",4.00),("Coleslaw",2.50),("Steamed Veggies",3.00)]),
                ("Drinks",   [("Soft Drink",2.50),("Fresh Juice",4.00),("Water Bottle",1.50),("Cocktail",9.00)]),
                ("Desserts", [("Chocolate Cake",6.00),("Ice Cream",4.50),("Fruit Salad",5.00)]),
            ]
            for idx, (cat_name, items) in enumerate(menu_data):
                cat = db.query(MenuCategory).filter_by(name=cat_name).first()
                if not cat:
                    cat = MenuCategory(name=cat_name, sort_order=idx+1)
                    db.add(cat)
                    db.flush()
                for n, p in items:
                    db.add(MenuItem(
                        id="m"+str(uuid.uuid4())[:6],
                        category_id=cat.id, name=n, emoji="", price=p
                    ))
            if db.query(RestaurantTable).count() == 0:
                for i in range(1, 13):
                    db.add(RestaurantTable(id=str(i), number=i, seats=4 if i<=6 else 2))
            print("Database seeded successfully.")
    except Exception as e:
        print(f"Seed error (non-fatal): {e}")


# Runs for both python app.py and gunicorn
import threading

def startup():
    try:
        create_tables()
        print("Tables created/verified.")
    except Exception as e:
        print(f"Table creation error: {e}")
    try:
        seed_database()
    except Exception as e:
        print(f"Seed error: {e}")

# Run startup in background so gunicorn boots immediately
threading.Thread(target=startup, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))