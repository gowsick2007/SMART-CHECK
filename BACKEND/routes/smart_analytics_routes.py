from flask import Blueprint
from BACKEND.controllers.smart_analytics_controller import (
    get_smart_summary, get_trust_scores, get_late_arrivals,
    get_fraud_alerts, get_attendance_forecast, ask_ai_assistant
)
from BACKEND.middleware.auth_middleware import require_role

smart_analytics_bp = Blueprint('smart_analytics', __name__)

@smart_analytics_bp.route('/api/smart/summary', methods=['GET'])
@require_role(['admin', 'creator'])
def api_smart_summary(current_student=None):
    return get_smart_summary()

@smart_analytics_bp.route('/api/smart/trust-scores', methods=['GET'])
@require_role(['admin', 'creator'])
def api_trust_scores(current_student=None):
    return get_trust_scores()

@smart_analytics_bp.route('/api/smart/late-arrivals', methods=['GET'])
@require_role(['admin', 'creator'])
def api_late_arrivals(current_student=None):
    import flask
    period = flask.request.args.get('period', 'daily')
    return get_late_arrivals(period)

@smart_analytics_bp.route('/api/smart/fraud-alerts', methods=['GET'])
@require_role(['admin', 'creator'])
def api_fraud_alerts(current_student=None):
    return get_fraud_alerts()

@smart_analytics_bp.route('/api/smart/forecast/<student_id>', methods=['GET'])
@require_role(['admin', 'creator'])
def api_attendance_forecast(student_id, current_student=None):
    return get_attendance_forecast(student_id)

@smart_analytics_bp.route('/api/smart/ai-assistant', methods=['GET'])
@require_role(['admin', 'creator'])
def api_ai_assistant(current_student=None):
    return ask_ai_assistant()
