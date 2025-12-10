from glint.core.notifier import Notifier
import time

print("Testing notification...")
notifier = Notifier()
notifier.send_notification(
    "Glint Test", 
    "This is a test notification with the Glint logo! 🚀"
)
print("Notification sent! Check your system tray/notification center.")
