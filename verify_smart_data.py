import sys
import os
import json
sys.path.insert(0, r"c:\Users\GOWSICK\Documents\SMART-ATTENDANCE")
from BACKEND.controllers.smart_analytics_controller import (
    get_smart_summary, get_trust_scores, get_late_arrivals,
    get_fraud_alerts, get_attendance_forecast, get_smart_achievements
)
from flask import Flask

app = Flask(__name__)

def test_apis():
    with app.app_context():
        print("--- Testing Smart Summary ---")
        summary = get_smart_summary().get_json()
        print(json.dumps(summary, indent=2))
        
        print("\n--- Testing Trust Scores ---")
        trust = get_trust_scores().get_json()
        print(f"Loaded {len(trust.get('scores', []))} student trust scores.")
        if trust['scores']: print(f"Sample: {trust['scores'][0]}")
        
        print("\n--- Testing Late Arrivals (Monthly) ---")
        late = get_late_arrivals(period='monthly').get_json()
        print(f"Loaded {len(late.get('arrivals', []))} monthly arrivals.")
        
        print("\n--- Testing Fraud Alerts ---")
        fraud = get_fraud_alerts().get_json()
        print(json.dumps(fraud, indent=2))
        
        print("\n--- Testing Achievements ---")
        ach = get_smart_achievements().get_json()
        print(json.dumps(ach, indent=2))

if __name__ == "__main__":
    test_apis()
