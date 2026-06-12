from DATABASE.connection.db_connection import execute_query, execute_insert
from flask import jsonify, request
from datetime import datetime, date, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

def get_smart_summary():
    """Live Attendance Command Center & Overview"""
    today = date.today()
    
    # 5. Live Attendance Command Center (Real-time updates)
    stats = execute_query("""
        SELECT 
            COUNT(*) FILTER (WHERE status = 'present') as total_present,
            COUNT(*) FILTER (WHERE status = 'absent') as total_absent,
            COUNT(*) FILTER (WHERE face_match_status = 'success' OR face_match_status = 'Matched') as face_verified,
            COUNT(*) FILTER (WHERE location_valid = true OR boundary = 'inside') as inside_boundary,
            COUNT(*) FILTER (WHERE location_valid = false OR boundary = 'outside') as outside_boundary
        FROM attendance
        WHERE date = %s
    """, (today,), fetch="one") or {"total_present":0, "total_absent":0, "face_verified":0, "inside_boundary":0, "outside_boundary":0}

    # 6. Classroom Occupancy Monitor
    occupancy = execute_query("""
        SELECT s.department, s.class_name as section,
               COUNT(*) FILTER (WHERE a.status = 'present') as present_count,
               COUNT(*) as total_students
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id AND a.date = %s
        WHERE s.role NOT IN ('creator', 'admin') AND s.is_active = 1
        GROUP BY s.department, s.class_name
        ORDER BY s.department, s.class_name
    """, (today,), fetch="all") or []

    return jsonify({
        "success": True,
        "stats": stats,
        "occupancy": occupancy
    })

def get_trust_scores():
    """1. Smart Attendance Trust Score (0-100)"""
    # Calculate scores based on historical data
    # High Trust: >90, Medium Risk: 70-89, Suspicious: <70
    results = execute_query("""
        WITH Stats AS (
            SELECT 
                student_id,
                COUNT(*) as total_days,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_days,
                SUM(CASE WHEN face_match_status IN ('success', 'Matched') THEN 1 ELSE 0 END) as face_matches,
                SUM(CASE WHEN location_valid = true OR boundary = 'inside' THEN 1 ELSE 0 END) as inside_checks
            FROM attendance
            GROUP BY student_id
        )
        SELECT s.student_id, s.name, s.department, s.class_name as section,
               st.total_days, st.present_days,
               ROUND(
                   ( (st.present_days::numeric / NULLIF(st.total_days, 0)) * 40 +
                     (st.face_matches::numeric / NULLIF(st.present_days, 0)) * 30 +
                     (st.inside_checks::numeric / NULLIF(st.present_days, 0)) * 30
                   ), 1
               ) as trust_score
        FROM students s
        JOIN Stats st ON s.student_id = st.student_id
        WHERE s.role NOT IN ('creator', 'admin')
        ORDER BY trust_score ASC
    """, fetch="all") or []

    for r in results:
        score = float(r.get("trust_score") or 0)
        if score >= 90: r["category"] = "High Trust"
        elif score >= 70: r["category"] = "Medium Risk"
        else: r["category"] = "Suspicious Activity"

    return jsonify({"success": True, "scores": results})

def get_late_arrivals(period='daily'):
    """2. Late Arrival Intelligence"""
    # Thresholds: On Time (<5m), Late (5-15m), Very Late (>15m)
    # Reference: 09:00:00
    ref_time = "09:00:00"
    
    query = """
        SELECT a.student_id, s.name, a.date, a.time,
               EXTRACT(EPOCH FROM (a.time::time - %s::time))/60 as diff_minutes
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.status = 'present'
    """
    params = [ref_time]
    
    if period == 'daily':
        query += " AND a.date = CURRENT_DATE"
    elif period == 'weekly':
        query += " AND a.date >= CURRENT_DATE - INTERVAL '7 days'"
    
    records = execute_query(query, tuple(params), fetch="all") or []
    
    results = []
    for r in records:
        diff = float(r.get("diff_minutes") or 0)
        if diff <= 5: cat = "On Time"
        elif diff <= 15: cat = "Late"
        else: cat = "Very Late"
        
        results.append({
            "student_id": r["student_id"],
            "name": r["name"],
            "date": str(r["date"]),
            "time": r["time"],
            "delay": round(diff, 1),
            "category": cat
        })
        
    return jsonify({"success": True, "arrivals": results})

def get_fraud_alerts():
    """3. Attendance Fraud Detection"""
    # Detect suspicious patterns: Repeated failed face, Spikes in distance
    alerts = []
    
    # Check failed face attempts in last 3 days
    failed_faces = execute_query("""
        SELECT student_id, COUNT(*) as fail_count
        FROM attendance
        WHERE (face_match_status = 'failed' OR face_match_status = 'Not Matched')
          AND date >= CURRENT_DATE - INTERVAL '3 days'
        GROUP BY student_id
        HAVING COUNT(*) >= 2
    """, fetch="all") or []
    
    for f in failed_faces:
        alerts.append({
            "type": "Repeated Face Match Failure",
            "student_id": f["student_id"],
            "severity": "Medium",
            "details": f"Failed match {f['fail_count']} times in 3 days."
        })

    # Check outside boundary present markings
    outside_present = execute_query("""
        SELECT student_id, COUNT(*) as out_count
        FROM attendance
        WHERE status = 'present' AND (location_valid = false OR boundary = 'outside')
          AND date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY student_id
        HAVING COUNT(*) >= 3
    """, fetch="all") or []

    for o in outside_present:
        alerts.append({
            "type": "Suspicious GPS Pattern",
            "student_id": o["student_id"],
            "severity": "High",
            "details": f"Marked present outside boundary {o['out_count']} times in a week."
        })

    return jsonify({"success": True, "alerts": alerts})

def get_attendance_forecast(student_id):
    """4. Attendance Forecast Engine"""
    stats = execute_query("""
        SELECT 
            COUNT(*) as total_days,
            SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_days
        FROM attendance
        WHERE student_id = %s
    """, (student_id,), fetch="one")
    
    if not stats or not stats["total_days"]:
        return jsonify({"success": False, "message": "No data for student"})

    total = stats["total_days"]
    present = stats["present_days"]
    current_pct = (present / total) * 100
    
    # Forecast for next 10 days
    scenario_10p = ((present + 10) / (total + 10)) * 100
    scenario_10a = (present / (total + 10)) * 100
    
    return jsonify({
        "success": True,
        "current_percentage": round(current_pct, 2),
        "forecast_10_days_present": round(scenario_10p, 2),
        "forecast_10_days_absent": round(scenario_10a, 2)
    })

def ask_ai_assistant():
    """9. AI Attendance Assistant (Admin Query Hub)"""
    q = request.args.get("q", "").lower()
    
    if "lowest attendance" in q:
        # Which department has lowest attendance?
        res = execute_query("""
            SELECT department, ROUND(AVG(CASE WHEN status = 'present' THEN 1 ELSE 0 END)*100, 2) as avg_att
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            GROUP BY department
            ORDER BY avg_att ASC
            LIMIT 3
        """, fetch="all")
        return jsonify({"success": True, "answer": f"The departments with the lowest attendance are: " + ", ".join([f"{r['department']} ({r['avg_att']}%)" for r in res])})
    
    if "below 75" in q:
        # Show students below 75%
        res = execute_query("""
            SELECT name, student_id, ROUND((present_days::numeric / total_days)*100, 2) as pct
            FROM (
                SELECT s.name, s.student_id, COUNT(*) as total_days, SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_days
                FROM attendance a JOIN students s ON a.student_id = s.student_id
                GROUP BY s.name, s.student_id
            ) t
            WHERE (present_days::numeric / total_days) < 0.75
            LIMIT 10
        """, fetch="all")
        if not res: return jsonify({"success": True, "answer": "No students found below 75%."})
        return jsonify({"success": True, "answer": "Students below 75% at risk: " + ", ".join([f"{r['name']} ({r['pct']}%)" for r in res])})

    if "exam eligibility" in q or "at risk" in q:
        # Simple risk model
        res = execute_query("""
            SELECT name, student_id
            FROM (
                SELECT s.name, s.student_id, COUNT(*) as total_days, SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_days
                FROM attendance a JOIN students s ON a.student_id = s.student_id
                GROUP BY s.name, s.student_id
            ) t
            WHERE (present_days::numeric / total_days) < 0.60
        """, fetch="all")
        if not res: return jsonify({"success": True, "answer": "All students are currently eligible."})
        return jsonify({"success": True, "answer": f"There are {len(res)} students currently at high risk for exam eligibility."})
    
    return jsonify({"success": True, "answer": "I'm sorry, I don't have enough data to answer that specific query yet. Try asking about 'lowest attendance', 'students below 75%', or 'exam eligibility'."})
