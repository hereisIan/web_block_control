import sys
import platform
import subprocess
from datetime import datetime, timedelta
import os
import time
import threading


class FocusBlocker:
    def __init__(self):
        self.hosts_path = "/etc/hosts"  # macOS path
        self.redirect_ip = "127.0.0.1"
        self.focus_timer = None
        self.common_distractions = [
            "facebook.com",
            "instagram.com",
            "youtube.com",
            "threads.net"
        ]
        self.youtube_exceptions = [
            "music.youtube.com"
        ]
        self.end_time = datetime.now().replace(hour=17, minute=0, second=0, microsecond=0)
        # If current time is past 5 PM, set end time to tomorrow 5 PM
        if datetime.now() >= self.end_time:
            self.end_time += timedelta(days=1)

    def is_admin(self):
        """Check if script has root privileges."""
        return os.geteuid() == 0

    def calculate_remaining_time(self):
        """Calculate minutes until 5 PM."""
        now = datetime.now()
        remaining = self.end_time - now
        return max(0, remaining.total_seconds() / 60)

    def display_countdown(self, total_minutes):
        """Display a countdown timer until unblock time."""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=total_minutes)

        try:
            while datetime.now() < end_time:
                remaining = end_time - datetime.now()
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                print(f"\rTime remaining: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}",
                      end="", flush=True)
                time.sleep(1)

                # Clear the line for clean updates
                print("\r" + " " * 40 + "\r", end="", flush=True)
        except KeyboardInterrupt:
            print("\nCountdown interrupted, but websites will still unblock at 5 PM")

    def block_websites(self, websites, duration=None):
        """Block specified websites until 5 PM."""
        if not self.is_admin():
            print("Error: This script requires root privileges!")
            print("Please run with sudo")
            return False

        try:
            with open(self.hosts_path, 'r') as file:
                content = file.read()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content += f"\n\n# Focus Mode activated on {timestamp}\n"

            for website in websites:
                if website not in content:
                    if website == "youtube.com":
                        for exception in self.youtube_exceptions:
                            content += f"\n# Keeping access to {exception}\n"
                            content += f"{self.redirect_ip} youtube.com\n"
                            content += f"{self.redirect_ip} www.youtube.com\n"
                            content += f"# End YouTube block\n"
                    else:
                        content += f"{self.redirect_ip} {website}\n"
                        content += f"{self.redirect_ip} www.{website}\n"
                    print(f"Blocking: {website}")

            with open(self.hosts_path, 'w') as file:
                file.write(content)

            print("\nFocus Mode activated! Websites blocked until 5 PM")
            print(f"Current time: {datetime.now().strftime('%H:%M')}")
            print(f"Will unblock at: {self.end_time.strftime('%H:%M')}")

            # Calculate remaining time until 5 PM
            remaining_minutes = self.calculate_remaining_time()

            # Start countdown in a separate thread
            timer_thread = threading.Thread(target=self.display_countdown,
                                            args=(remaining_minutes,))
            timer_thread.daemon = True  # Allow the script to exit even if thread is running
            timer_thread.start()

            # Schedule unblock
            self.focus_timer = threading.Timer(remaining_minutes * 60,
                                               self.unblock_websites,
                                               [websites])
            self.focus_timer.start()

            # Keep main thread alive until timer expires
            try:
                time.sleep(remaining_minutes * 60)
            except KeyboardInterrupt:
                print("\nScript interrupted, but unblock timer will continue in background")

            return True

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return False

    def unblock_websites(self, websites):
        """Remove specified websites from the hosts file."""
        if not self.is_admin():
            print("Error: This script requires root privileges!")
            print("Please run with sudo")
            return False

        try:
            with open(self.hosts_path, 'r') as file:
                lines = file.readlines()

            new_lines = []
            for line in lines:
                if not any(website in line for website in websites):
                    new_lines.append(line)

            with open(self.hosts_path, 'w') as file:
                file.writelines(new_lines)

            print("\nFocus session completed! Websites have been unblocked.")
            print(f"Session ended at: {datetime.now().strftime('%H:%M')}")
            return True

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return False

    def start_focus_session(self):
        """Start a focus session until 5 PM."""
        print("\nStarting focus session until 5 PM...")
        remaining_minutes = self.calculate_remaining_time()

        if remaining_minutes <= 0:
            print("It's already past 5 PM! Setting timer for tomorrow at 5 PM")
            self.end_time += timedelta(days=1)
            remaining_minutes = self.calculate_remaining_time()

        print(f"Blocking distracting websites for {int(remaining_minutes)} minutes")
        self.block_websites(self.common_distractions, remaining_minutes)


if __name__ == "__main__":
    blocker = FocusBlocker()

    if len(sys.argv) > 1:
        action = sys.argv[1].lower()

        if action == "start":
            blocker.start_focus_session()
        elif action == "unblock":
            blocker.unblock_websites(blocker.common_distractions)
        else:
            print("Invalid action. Use 'start' or 'unblock'")
    else:
        print("\nFocus Blocker Usage:")
        print("1. Start focus session until 5 PM:")
        print("   sudo python3 focus_blocker.py start")
        print("\n2. Manually unblock all websites:")
        print("   sudo python3 focus_blocker.py unblock")