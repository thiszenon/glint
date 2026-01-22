# test_notification.py
from plyer import notification

notification.notify(
    title="Glint Test",
    message="If i see this, notifications are working!",
    app_name="Glint",
    timeout=10
)
print("Notification sent! Check your system .")
