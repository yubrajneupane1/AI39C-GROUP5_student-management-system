from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from app.models.database import Database
from app.models.notification_model import NotificationModel
from datetime import datetime

notification_bp = Blueprint("notification", __name__)

def admin_required():
    return "role" not in session or session["role"] != "admin"

# ============================================
# VIEW NOTIFICATIONS (All Users)
# ============================================

@notification_bp.route("/notifications")
def view_notifications():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    db = Database()
    notifications = db.fetch("""
        SELECT * FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 50
    """, (session["user_id"],))
    
    unread_count = db.fetchone(
        "SELECT COUNT(*) as count FROM notifications WHERE user_id=%s AND is_read=FALSE",
        (session["user_id"],)
    )
    
    db.close()
    
    return render_template(
        "notifications.html",
        username=session["username"],
        role=session["role"],
        notifications=notifications,
        unread_count=unread_count["count"] if unread_count else 0
    )

# ============================================
# GET UNREAD COUNT (AJAX)
# ============================================

@notification_bp.route("/notifications/unread-count")
def get_unread_count():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    db = Database()
    result = db.fetchone(
        "SELECT COUNT(*) as count FROM notifications WHERE user_id=%s AND is_read=FALSE",
        (session["user_id"],)
    )
    db.close()
    
    return jsonify({"unread": result["count"] if result else 0})

# ============================================
# USER NOTIFICATION PREFERENCES
# ============================================

@notification_bp.route("/notifications/preferences", methods=["GET", "POST"])
def notification_preferences():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    notification_model = NotificationModel()
    
    if request.method == "POST":
        preferences = {
            'attendance_alerts': request.form.get("attendance_alerts") == "on",
            'fee_alerts': request.form.get("fee_alerts") == "on",
            'system_alerts': request.form.get("system_alerts") == "on",
            'grade_alerts': request.form.get("grade_alerts") == "on",
            'task_alerts': request.form.get("task_alerts") == "on",
            'email_notifications': request.form.get("email_notifications") == "on",
            'attendance_threshold': int(request.form.get("attendance_threshold", 75))
        }
        
        notification_model.update_preferences(session["user_id"], preferences)
        flash("Notification preferences updated successfully.", "success")
    
    preferences = notification_model.get_preferences(session["user_id"])
    notification_model.close()
    
    return render_template(
        "notification_preferences.html",
        username=session["username"],
        role=session["role"],
        preferences=preferences
    )


# ============================================
# ADMIN - SEND CUSTOM NOTIFICATION TO ALL
# ============================================

@notification_bp.route("/admin/notifications")
def admin_notifications():
    if admin_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    
    # Get all notifications with user info
    notifications = db.fetch("""
        SELECT n.*, u.fullname as user_name, u.role as user_role
        FROM notifications n
        JOIN users u ON n.user_id = u.id
        ORDER BY n.created_at DESC
        LIMIT 100
    """)
    
    # Summary
    summary = db.fetchone("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_read = FALSE THEN 1 ELSE 0 END) as unread
        FROM notifications
    """)
    
    # Get all users for dropdown
    users = db.fetch("SELECT id, fullname, username, role FROM users ORDER BY role, fullname")
    
    db.close()
    
    return render_template(
        "admin/notifications.html",
        username=session["username"],
        role=session["role"],
        notifications=notifications,
        summary=summary,
        users=users
    )

@notification_bp.route("/admin/notifications/send-all", methods=["POST"])
def admin_send_to_all():
    if admin_required():
        return redirect(url_for("auth.login"))
    
    title = request.form.get("title")
    message = request.form.get("message")
    notification_type = request.form.get("notification_type", "system")
    link = request.form.get("link", "")
    
    if not all([title, message]):
        flash("Title and message are required.", "error")
        return redirect(url_for("notification.admin_notifications"))
    
    db = Database()
    
    # Get ALL active users
    users = db.fetch("SELECT id FROM users WHERE is_active = TRUE")
    
    if not users:
        flash("No users found to send notification.", "error")
        db.close()
        return redirect(url_for("notification.admin_notifications"))
    
    # Send notification to all users
    sent_count = 0
    for user in users:
        db.execute("""
            INSERT INTO notifications (user_id, type, title, message, link)
            VALUES (%s, %s, %s, %s, %s)
        """, (user['id'], notification_type, title, message, link))
        sent_count += 1
    
    db.close()
    
    flash(f"✅ Custom notification sent to ALL {sent_count} user(s).", "success")
    return redirect(url_for("notification.admin_notifications"))

@notification_bp.route("/admin/notifications/send-selected", methods=["POST"])
def admin_send_selected():
    if admin_required():
        return redirect(url_for("auth.login"))
    
    title = request.form.get("title")
    message = request.form.get("message")
    recipient_type = request.form.get("recipient_type", "all")
    notification_type = request.form.get("notification_type", "system")
    link = request.form.get("link", "")
    
    if not all([title, message]):
        flash("Title and message are required.", "error")
        return redirect(url_for("notification.admin_notifications"))
    
    db = Database()
    
    # Get users based on recipient type
    if recipient_type == "all":
        users = db.fetch("SELECT id FROM users WHERE is_active = TRUE")
    elif recipient_type == "teachers":
        users = db.fetch("SELECT id FROM users WHERE role = 'teacher' AND is_active = TRUE")
    elif recipient_type == "students":
        users = db.fetch("SELECT id FROM users WHERE role = 'student' AND is_active = TRUE")
    elif recipient_type == "specific":
        user_id = request.form.get("user_id")
        if user_id:
            users = db.fetch("SELECT id FROM users WHERE id = %s AND is_active = TRUE", (user_id,))
        else:
            flash("Please select a user.", "error")
            db.close()
            return redirect(url_for("notification.admin_notifications"))
    else:
        flash("Invalid recipient type.", "error")
        db.close()
        return redirect(url_for("notification.admin_notifications"))
    
    if not users:
        flash("No users found for the selected recipient type.", "error")
        db.close()
        return redirect(url_for("notification.admin_notifications"))
    
    # Send notification to selected users
    sent_count = 0
    for user in users:
        db.execute("""
            INSERT INTO notifications (user_id, type, title, message, link)
            VALUES (%s, %s, %s, %s, %s)
        """, (user['id'], notification_type, title, message, link))
        sent_count += 1
    
    db.close()
    
    flash(f"✅ Custom notification sent to {sent_count} user(s).", "success")
    return redirect(url_for("notification.admin_notifications"))

@notification_bp.route("/admin/notifications/delete/<int:notification_id>", methods=["POST"])
def admin_delete_notification(notification_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    
    db = Database()
    db.execute("DELETE FROM notifications WHERE id=%s", (notification_id,))
    db.close()
    
    flash("Notification deleted.", "success")
    return redirect(url_for("notification.admin_notifications"))


# ============================================
# ADMIN - USER PREFERENCES CONTROL
# ============================================

@notification_bp.route("/admin/preferences/update/<int:user_id>", methods=["POST"])
def admin_update_user_preferences(user_id):
    if admin_required():
        return redirect(url_for("auth.login"))
    
    preferences = {
        'attendance_alerts': request.form.get("attendance_alerts") == "on",
        'fee_alerts': request.form.get("fee_alerts") == "on",
        'system_alerts': request.form.get("system_alerts") == "on",
        'grade_alerts': request.form.get("grade_alerts") == "on",
        'task_alerts': request.form.get("task_alerts") == "on",
        'email_notifications': request.form.get("email_notifications") == "on",
        'attendance_threshold': int(request.form.get("attendance_threshold", 75))
    }
    
    db = Database()
    
    existing = db.fetchone(
        "SELECT id FROM notification_preferences WHERE user_id = %s",
        (user_id,)
    )
    
    if existing:
        db.execute("""
            UPDATE notification_preferences 
            SET attendance_alerts=%s, fee_alerts=%s, system_alerts=%s,
                grade_alerts=%s, task_alerts=%s, email_notifications=%s,
                attendance_threshold=%s, updated_at=NOW()
            WHERE user_id=%s
        """, (
            preferences['attendance_alerts'],
            preferences['fee_alerts'],
            preferences['system_alerts'],
            preferences['grade_alerts'],
            preferences['task_alerts'],
            preferences['email_notifications'],
            preferences['attendance_threshold'],
            user_id
        ))
    else:
        db.execute("""
            INSERT INTO notification_preferences 
            (user_id, attendance_alerts, fee_alerts, system_alerts, grade_alerts, 
             task_alerts, email_notifications, attendance_threshold)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            preferences['attendance_alerts'],
            preferences['fee_alerts'],
            preferences['system_alerts'],
            preferences['grade_alerts'],
            preferences['task_alerts'],
            preferences['email_notifications'],
            preferences['attendance_threshold']
        ))
    
    db.close()
    
    flash("User preferences updated successfully.", "success")
    return redirect(url_for("notification.admin_notifications"))

@notification_bp.route("/admin/preferences/toggle-all", methods=["POST"])
def admin_toggle_all_preferences():
    if admin_required():
        return redirect(url_for("auth.login"))
    
    preference_type = request.form.get("preference_type")
    value = request.form.get("value") == "true"
    role_filter = request.form.get("role_filter", "all")
    
    if not preference_type:
        flash("Preference type is required.", "error")
        return redirect(url_for("notification.admin_notifications"))
    
    db = Database()
    
    query = """
        UPDATE notification_preferences np
        JOIN users u ON np.user_id = u.id
        SET np.{} = %s, np.updated_at = NOW()
        WHERE u.is_active = TRUE
    """.format(preference_type)
    
    params = [value]
    
    if role_filter != "all":
        query += " AND u.role = %s"
        params.append(role_filter)
    
    db.execute(query, tuple(params))
    db.close()
    
    flash(f"✅ {preference_type.replace('_', ' ').title()} toggled for all {role_filter} users.", "success")
    return redirect(url_for("notification.admin_notifications"))