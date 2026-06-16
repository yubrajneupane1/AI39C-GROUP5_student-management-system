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
# MARK SINGLE NOTIFICATION AS READ
# ============================================

@notification_bp.route("/notifications/mark-read/<int:notification_id>", methods=["POST"])
def mark_notification_read(notification_id):
    """Mark a single notification as read"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    db = Database()
    
    # Verify notification belongs to user
    notification = db.fetchone(
        "SELECT id FROM notifications WHERE id=%s AND user_id=%s",
        (notification_id, session["user_id"])
    )
    
    if not notification:
        db.close()
        return jsonify({"error": "Notification not found"}), 404
    
    db.execute("""
        UPDATE notifications 
        SET is_read = TRUE, read_at = NOW()
        WHERE id = %s
    """, (notification_id,))
    
    db.close()
    
    return jsonify({"success": True, "message": "Notification marked as read"})


# ============================================
# MARK ALL NOTIFICATIONS AS READ
# ============================================

@notification_bp.route("/notifications/mark-all-read", methods=["POST"])
def mark_all_notifications_read():
    """Mark all notifications as read for the current user"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    db = Database()
    
    db.execute("""
        UPDATE notifications 
        SET is_read = TRUE, read_at = NOW()
        WHERE user_id = %s AND is_read = FALSE
    """, (session["user_id"],))
    
    db.close()
    
    return jsonify({"success": True, "message": "All notifications marked as read"})


# ============================================
# NOTIFICATION PREFERENCES
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
# ADMIN - NOTIFICATION MANAGEMENT
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
        flash("No users found.", "error")
        db.close()
        return redirect(url_for("notification.admin_notifications"))
    
    # Send to all users
    sent_count = 0
    for user in users:
        db.execute("""
            INSERT INTO notifications (user_id, type, title, message, link)
            VALUES (%s, %s, %s, %s, %s)
        """, (user['id'], notification_type, title, message, link))
        sent_count += 1
    
    db.close()
    
    flash(f"✅ Notification sent to ALL {sent_count} user(s).", "success")
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
        flash("No users found for the selected type.", "error")
        db.close()
        return redirect(url_for("notification.admin_notifications"))
    
    # Send to selected users
    sent_count = 0
    for user in users:
        db.execute("""
            INSERT INTO notifications (user_id, type, title, message, link)
            VALUES (%s, %s, %s, %s, %s)
        """, (user['id'], notification_type, title, message, link))
        sent_count += 1
    
    db.close()
    
    flash(f"✅ Notification sent to {sent_count} user(s).", "success")
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