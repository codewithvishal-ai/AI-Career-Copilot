import logging
import csv
import os

from datetime import datetime
from dotenv import load_dotenv

from person import Person
from career_features import CareerFeatures
from utils import get_user_name, get_career_interest
from resume_analyzer import ResumeAnalyzer


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

load_dotenv(os.path.join(BASE_DIR, ".env"))

from werkzeug.security import check_password_hash, generate_password_hash
from mongo_store import (
    create_user,
    find_user,
    load_dataset,
    save_dataset,
    update_user_password,
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "career_data.json"
)

BACKUP_FILE = os.path.join(
    BASE_DIR,
    "career_data_backup.json"
)

CSV_FILE = os.path.join(
    BASE_DIR,
    "career_history.csv"
)

TXT_FILE = os.path.join(
    BASE_DIR,
    "career_report.txt"
)


# ============================================================
# LOGGING
# ============================================================

LOG_FILE = os.path.join(
    BASE_DIR,
    "careercopilot.log"
)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# CAREER ROADMAPS
# ============================================================

ROADMAPS = {

    "ai": [
        "Learn Python",
        "Learn Machine Learning",
        "Build AI Projects"
    ],

    "web": [
        "Learn HTML",
        "Learn CSS",
        "Learn JavaScript"
    ],

    "python": [
        "Learn Python Basics",
        "Learn Object-Oriented Programming",
        "Build Python Projects"
    ],

    "data science": [
        "Learn Python",
        "Learn Pandas",
        "Learn SQL"
    ]
}


# ============================================================
# CAREER COPILOT
# ============================================================

class CareerCopilot(Person, CareerFeatures):

    def __init__(self):
        super().__init__()
        self.current_user = None
        self.resume_analyzer = ResumeAnalyzer()

    # ========================================================
    # GET ROADMAP
    # ========================================================

    def get_roadmap(self, interest):

        return ROADMAPS.get(
            interest.lower(),
            []
        )

    # ========================================================
    # WELCOME
    # ========================================================

    def welcome(self):

        print("=" * 40)
        print("        AI Career Copilot")
        print("=" * 40)

    def welcome_user(self):

        print("\n" + "=" * 40)

        super().welcome_user()

        print(
            "Let's build your career together! 🚀"
        )

        print("=" * 40)

    # ========================================================
    # DATA HELPERS
    # ========================================================

    def load_career_data(self):

        try:
            data = load_dataset(DATA_FILE, [])

            if not isinstance(data, list):
                return []

            return data

        except Exception as e:

            logging.error(
                f"Error loading career data: {e}"
            )

            return []

    def save_career_data(self, careers):

        try:
            save_dataset(DATA_FILE, careers)

        except Exception as e:

            logging.error(
                f"Error saving career data: {e}"
            )

            print(
                f"❌ Unable to save career data: {e}"
            )

    # ========================================================
    # CLEAN / MIGRATE OLD DATA
    # ========================================================

    def clean_duplicate_records(self):

        careers = self.load_career_data()

        if not careers:
            return

        record_map = {}

        for record in careers:

            name = record.get(
                "name",
                ""
            ).strip()

            career = record.get(
                "career",
                ""
            ).strip().lower()

            if not name or not career:
                continue

            user = record.get(
                "user",
                name
            )

            record["user"] = user

            try:

                record["progress"] = int(
                    record.get(
                        "progress",
                        0
                    )
                )

            except (ValueError, TypeError):

                record["progress"] = 0

            record["favorite"] = bool(
                record.get(
                    "favorite",
                    False
                )
            )

            record["completed_steps"] = record.get(
                "completed_steps",
                []
            )

            if not isinstance(
                record["completed_steps"],
                list
            ):

                record["completed_steps"] = []

            key = (
                str(user).lower(),
                career
            )

            if key not in record_map:

                record_map[key] = record

            else:

                existing = record_map[key]

                existing["progress"] = max(
                    int(
                        existing.get(
                            "progress",
                            0
                        )
                    ),
                    int(
                        record.get(
                            "progress",
                            0
                        )
                    )
                )

                existing_steps = set(
                    existing.get(
                        "completed_steps",
                        []
                    )
                )

                new_steps = set(
                    record.get(
                        "completed_steps",
                        []
                    )
                )

                existing["completed_steps"] = list(
                    existing_steps | new_steps
                )

                existing["favorite"] = (
                    existing.get(
                        "favorite",
                        False
                    )
                    or
                    record.get(
                        "favorite",
                        False
                    )
                )

                if not existing.get("timestamp"):

                    existing["timestamp"] = record.get(
                        "timestamp"
                    )

        cleaned = list(
            record_map.values()
        )

        self.save_career_data(
            cleaned
        )

        logging.info(
            "Career duplicate cleanup completed."
        )

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    def register_user(self):

        username = input(
            "Create Username: "
        ).strip()

        password = input(
            "Create Password: "
        ).strip()

        if not username or not password:

            print(
                "❌ Username and password cannot be empty!"
            )

            return False

        try:
            if not create_user(username, generate_password_hash(password)):
                print("❌ Username already exists!")
                return False

        except Exception as e:

            print(
                f"❌ Registration failed: {e}"
            )

            return False

        print(
            "✅ Registration Successful!"
        )

        logging.info(
            f"New user registered: {username}"
        )

        return True

    # ========================================================
    # LOGIN
    # ========================================================

    def login_user(self):

        username = input(
            "Username: "
        ).strip()

        password = input(
            "Password: "
        ).strip()

        try:
            user = find_user(username)
        except Exception as error:
            print(f"❌ Unable to read users from MongoDB: {error}")
            return False

        if user:

            saved_password = str(user.get("password", ""))
            password_matches = (
                check_password_hash(saved_password, password)
                if saved_password.startswith(("scrypt:", "pbkdf2:", "argon2:"))
                else saved_password == password
            )

            if user.get("name", "").lower() == username.lower() and password_matches:
                if not saved_password.startswith(("scrypt:", "pbkdf2:", "argon2:")):
                    update_user_password(
                        username,
                        generate_password_hash(password),
                    )

                self.set_name(
                    username
                )

                self.current_user = username

                print(
                    f"\n✅ Welcome back, {username}!"
                )

                logging.info(
                    f"{username} logged in."
                )

                self.clean_duplicate_records()

                return True

        print(
            "❌ Invalid Username or Password!"
        )

        logging.warning(
            f"Failed login attempt: {username}"
        )

        return False

    # ========================================================
    # AUTHENTICATION MENU
    # ========================================================

    def authentication_menu(self):

        while True:

            print(
                "\n========== Authentication =========="
            )

            print("1. Register")
            print("2. Login")
            print("3. Exit")

            choice = input(
                "Enter your choice: "
            ).strip()

            if choice == "1":

                self.register_user()

            elif choice == "2":

                if self.login_user():
                    return True

            elif choice == "3":

                print(
                    "\nThank you for using "
                    "AI Career Copilot!"
                )

                return False

            else:

                print(
                    "\n❌ Invalid choice! "
                    "Please select 1 to 3."
                )

    # ========================================================
    # MAIN MENU
    # ========================================================

    def show_menu(self):

        print(
            "\n========== MAIN MENU =========="
        )

        print("1. Career Roadmap")
        print("2. Resume Analysis")
        print("3. ATS Score")
        print("4. Interview Preparation")
        print("5. Career History")
        print("6. Export Career History to CSV")
        print("7. Search Career Record")
        print("8. Update Career Record")
        print("9. Delete Career Record")
        print("10. Dashboard")
        print("11. Export Career Report (TXT)")
        print("12. Mark Favorite Career")
        print("13. View Favorite Careers")
        print("14. Backup Career Data")
        print("15. Restore Backup")
        print("16. Update Roadmap Progress")
        print("17. Complete Roadmap Step")
        print("18. Exit")

        return input(
            "Enter your choice: "
        ).strip()

    # ========================================================
    # PROCESS CHOICE
    # ========================================================

    def process_choice(self, choice):

        if choice == "1":
            self.select_career()

        elif choice == "2":
            self.resume_analysis()

        elif choice == "3":
            self.ats_score()

        elif choice == "4":
            self.interview_preparation()

        elif choice == "5":
            self.career_history()

        elif choice == "6":
            self.export_to_csv()

        elif choice == "7":
            self.search_career()

        elif choice == "8":
            self.update_career()

        elif choice == "9":
            self.delete_career()

        elif choice == "10":
            self.dashboard()

        elif choice == "11":
            self.export_to_txt()

        elif choice == "12":
            self.mark_favorite()

        elif choice == "13":
            self.view_favorites()

        elif choice == "14":
            self.backup_data()

        elif choice == "15":
            self.restore_data()

        elif choice == "16":
            self.update_progress()

        elif choice == "17":
            self.complete_roadmap_step()

        elif choice == "18":

            print(
                "\nThank you for using "
                "AI Career Copilot!"
            )

            return False

        else:

            print(
                "\n❌ Invalid choice! "
                "Please select 1 to 18."
            )

        return True

    # ========================================================
    # SELECT CAREER
    # ========================================================

    def select_career(self):

        interest = get_career_interest()

        if not interest:

            print(
                "❌ Invalid career."
            )

            return

        interest = interest.lower().strip()

        if interest not in ROADMAPS:

            print(
                "❌ Career roadmap not available."
            )

            return

        careers = self.load_career_data()

        current_user = self.current_user.lower()

        existing_record = None

        for record in careers:

            record_user = record.get(
                "user",
                record.get(
                    "name",
                    ""
                )
            )

            if (
                record_user
                and
                record_user.lower()
                ==
                current_user
            ):

                existing_record = record
                break

        # ====================================================
        # EXISTING USER
        # ====================================================

        if existing_record:

            old_career = existing_record.get(
                "career",
                ""
            ).lower()

            if old_career == interest:

                print(
                    "\n⚠ You already selected this career!"
                )

                print(
                    f"Career   : {interest.title()}"
                )

                print(
                    f"Progress : "
                    f"{existing_record.get('progress', 0)}%"
                )

                print(
                    "Using your existing career record."
                )

            else:

                print(
                    "\n🔄 Changing career:"
                )

                print(
                    f"Old Career : {old_career.title()}"
                )

                print(
                    f"New Career : {interest.title()}"
                )

                existing_record["career"] = interest
                existing_record["progress"] = 0
                existing_record["completed_steps"] = []

                existing_record["favorite"] = (
                    existing_record.get(
                        "favorite",
                        False
                    )
                )

                existing_record["user"] = (
                    self.current_user
                )

                existing_record["name"] = (
                    self.get_name()
                )

                existing_record["timestamp"] = (
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

                self.save_career_data(
                    careers
                )

                print(
                    "\n✅ Career updated successfully!"
                )

                print(
                    f"New Career : {interest.title()}"
                )

                print(
                    "Progress reset to 0%."
                )

                logging.info(
                    f"Career changed from "
                    f"{old_career} to "
                    f"{interest} "
                    f"for {self.current_user}"
                )

        # ====================================================
        # NEW USER
        # ====================================================

        else:

            new_record = {

                "name": self.get_name(),

                "career": interest,

                "user": self.current_user,

                "progress": 0,

                "favorite": False,

                "completed_steps": [],

                "timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }

            careers.append(
                new_record
            )

            self.save_career_data(
                careers
            )

            print(
                "\n✅ Career saved successfully!"
            )

            logging.info(
                f"New career selected: {interest}"
            )

        self.show_career_roadmap(
            interest
        )

    # ========================================================
    # SHOW ROADMAP
    # ========================================================

    def show_career_roadmap(self, interest):

        roadmap = self.get_roadmap(
            interest
        )

        print(
            "\n========== Career Roadmap =========="
        )

        if not roadmap:

            print(
                "❌ No roadmap available "
                "for this career."
            )

            print("=" * 35)

            return

        completed_steps = []

        for record in self.load_career_data():

            if (
                record.get(
                    "user",
                    ""
                ).lower()
                ==
                self.current_user.lower()
            ):

                completed_steps = record.get(
                    "completed_steps",
                    []
                )

                break

        for index, step in enumerate(
            roadmap,
            start=1
        ):

            if step in completed_steps:

                print(
                    f"{index}. {step} ✅"
                )

            else:

                print(
                    f"{index}. {step} ⬜"
                )

        total_steps = len(
            roadmap
        )

        completed_count = len(
            completed_steps
        )

        remaining_steps = (
            total_steps
            -
            completed_count
        )

        if total_steps > 0:

            progress = int(
                (
                    completed_count
                    /
                    total_steps
                )
                *
                100
            )

        else:

            progress = 0

        bar_length = 20

        filled = int(
            (
                progress
                /
                100
            )
            *
            bar_length
        )

        progress_bar = (
            "█" * filled
            +
            "░" * (
                bar_length - filled
            )
        )

        print(
            f"\n📈 Progress: {progress}%"
        )

        print(
            f"[{progress_bar}]"
        )

        print(
            "\n📊 Roadmap Summary"
        )

        print(
            f"Total Steps     : {total_steps}"
        )

        print(
            f"Completed Steps : {completed_count}"
        )

        print(
            f"Remaining Steps : {remaining_steps}"
        )

        print(
            f"Progress        : {progress}%"
        )

        if progress == 100:

            print(
                "\n🏆 Roadmap Completed!"
            )

        elif progress > 0:

            print(
                "\n🚀 Roadmap In Progress!"
            )

        else:

            print(
                "\n⏳ Roadmap Not Started."
            )

        print("=" * 35)

    # ========================================================
    # SEARCH CAREER
    # ========================================================

    def search_career(self):

        search_name = input(
            "Enter name to search: "
        ).strip().lower()

        careers = self.load_career_data()

        found = False

        for record in careers:

            user = record.get(
                "user",
                record.get(
                    "name",
                    ""
                )
            )

            if (
                user.lower()
                !=
                self.current_user.lower()
            ):
                continue

            if (
                search_name
                in
                record.get(
                    "name",
                    ""
                ).lower()
            ):

                print(
                    "\n========== Record Found =========="
                )

                print(
                    f"Name       : "
                    f"{record.get('name')}"
                )

                print(
                    f"Career     : "
                    f"{record.get('career')}"
                )

                print(
                    f"Progress   : "
                    f"{record.get('progress', 0)}%"
                )

                if record.get("timestamp"):

                    print(
                        f"Created On : "
                        f"{record['timestamp']}"
                    )

                if record.get(
                    "favorite",
                    False
                ):

                    print(
                        "⭐ Favorite"
                    )

                print("=" * 35)

                found = True

        if not found:

            print(
                "❌ No record found."
            )

    # ========================================================
    # UPDATE CAREER
    # ========================================================

    def update_career(self):

        careers = self.load_career_data()

        user_records = [
            record
            for record in careers
            if record.get(
                "user",
                record.get(
                    "name",
                    ""
                )
            ).lower()
            ==
            self.current_user.lower()
        ]

        if not user_records:

            print(
                "❌ No career records found."
            )

            return

        print(
            "\n========== YOUR CAREERS =========="
        )

        for index, record in enumerate(
            user_records,
            start=1
        ):

            print(
                f"{index}. "
                f"{record['career'].title()} "
                f"({record.get('progress', 0)}%)"
            )

        choice = input(
            "\nSelect career number to update: "
        ).strip()

        if not choice.isdigit():

            print(
                "❌ Invalid choice."
            )

            return

        index = int(choice)

        if (
            index < 1
            or
            index > len(user_records)
        ):

            print(
                "❌ Invalid career number."
            )

            return

        selected = user_records[
            index - 1
        ]

        old_career = selected[
            "career"
        ]

        new_career = get_career_interest()

        if not new_career:
            return

        new_career = new_career.lower().strip()

        if new_career not in ROADMAPS:

            print(
                "❌ Invalid career."
            )

            return

        for record in careers:

            if record is selected:
                continue

            if (
                record.get(
                    "user",
                    ""
                ).lower()
                ==
                self.current_user.lower()
                and
                record.get(
                    "career",
                    ""
                ).lower()
                ==
                new_career
            ):

                print(
                    "\n⚠ You already have "
                    f"{new_career.title()}."
                )

                print(
                    "Update cancelled to "
                    "prevent duplicate records."
                )

                return

        selected["career"] = new_career
        selected["progress"] = 0
        selected["completed_steps"] = []

        self.save_career_data(
            careers
        )

        print(
            "\n✅ Career updated successfully!"
        )

        print(
            f"{old_career.title()} → "
            f"{new_career.title()}"
        )

    # ========================================================
    # DELETE CAREER
    # ========================================================

    def delete_career(self):

        careers = self.load_career_data()

        user_records = [
            record
            for record in careers
            if record.get(
                "user",
                record.get(
                    "name",
                    ""
                )
            ).lower()
            ==
            self.current_user.lower()
        ]

        if not user_records:

            print(
                "❌ No career records found."
            )

            return

        print(
            "\n========== YOUR CAREERS =========="
        )

        for index, record in enumerate(
            user_records,
            start=1
        ):

            print(
                f"{index}. "
                f"{record['career'].title()}"
            )

        choice = input(
            "\nSelect career number to delete: "
        ).strip()

        if not choice.isdigit():

            print(
                "❌ Invalid choice."
            )

            return

        index = int(choice)

        if (
            index < 1
            or
            index > len(user_records)
        ):

            print(
                "❌ Invalid career number."
            )

            return

        selected = user_records[
            index - 1
        ]

        careers.remove(
            selected
        )

        self.save_career_data(
            careers
        )

        print(
            "✅ Career record deleted successfully!"
        )

    # ========================================================
    # DASHBOARD
    # ========================================================

    def dashboard(self):

        self.clean_duplicate_records()

        careers = self.load_career_data()

        user_records = []

        for record in careers:

            user = record.get(
                "user",
                record.get(
                    "name",
                    ""
                )
            )

            if (
                user.lower()
                ==
                self.current_user.lower()
            ):

                user_records.append(
                    record
                )

        if not user_records:

            print(
                "\n❌ No career records found."
            )

            return

        total_records = len(
            user_records
        )

        career_count = {}

        total_progress = 0

        total_completed_steps = 0

        print(
            "\n========== DASHBOARD =========="
        )

        print(
            f"👤 User : {self.current_user}"
        )

        current_record = user_records[-1]

        current_career = current_record.get(
            "career",
            "Unknown"
        ).title()

        current_progress = int(
            current_record.get(
                "progress",
                0
            )
        )

        current_completed_steps = current_record.get(
            "completed_steps",
            []
        )

        roadmap = self.get_roadmap(
            current_record.get(
                "career",
                ""
            )
        )

        total_steps = len(
            roadmap
        )

        completed_count = len(
            current_completed_steps
        )

        remaining_steps = max(
            0,
            total_steps - completed_count
        )

        if current_progress == 100:

            career_status = "🏆 Completed"

        elif current_progress > 0:

            career_status = "🚀 In Progress"

        else:

            career_status = "⏳ Not Started"

        if current_record.get(
            "favorite",
            False
        ):

            favorite_status = "⭐ Favorite"

        else:

            favorite_status = "☆ Not Favorite"

        print(
            "\n========== CURRENT CAREER =========="
        )

        print(
            f"🎯 Career : {current_career}"
        )

        print(
            f"📈 Progress : {current_progress}%"
        )

        bar_length = 20

        filled_length = int(
            bar_length
            *
            current_progress
            /
            100
        )

        progress_bar = (
            "█" * filled_length
            +
            "░" * (
                bar_length
                -
                filled_length
            )
        )

        print(
            f"[{progress_bar}]"
        )

        print(
            f"✅ Completed Steps : "
            f"{completed_count}/{total_steps}"
        )

        print(
            f"⏳ Remaining Steps : "
            f"{remaining_steps}"
        )

        print(
            f"📌 Status : {career_status}"
        )

        print(
            f"Favorite : {favorite_status}"
        )

        for record in user_records:

            career = record.get(
                "career",
                ""
            ).lower()

            career_count[career] = (
                career_count.get(
                    career,
                    0
                )
                +
                1
            )

            progress = int(
                record.get(
                    "progress",
                    0
                )
            )

            total_progress += progress

            completed_steps = record.get(
                "completed_steps",
                []
            )

            total_completed_steps += len(
                completed_steps
            )

        average_progress = (
            total_progress
            /
            total_records
        )

        print(
            "\n========== OVERALL STATISTICS =========="
        )

        print(
            f"📁 Total Career Records : "
            f"{total_records}"
        )

        print(
            f"📈 Average Progress : "
            f"{average_progress:.2f}%"
        )

        print(
            f"✅ Total Completed Steps : "
            f"{total_completed_steps}"
        )

        print(
            "\n========== CAREER STATISTICS =========="
        )

        for career, count in career_count.items():

            percentage = (
                count
                /
                total_records
            ) * 100

            print(
                f"• {career.title()} : "
                f"{count} record(s) "
                f"({percentage:.2f}%)"
            )

        if career_count:

            popular_career = max(
                career_count,
                key=career_count.get
            )

            print(
                "\n🏆 Most Popular Career : "
                f"{popular_career.title()}"
            )

        print(
            "\n========== ALL CAREER PROGRESS =========="
        )

        for record in user_records:

            career = record.get(
                "career",
                "Unknown"
            ).title()

            progress = int(
                record.get(
                    "progress",
                    0
                )
            )

            completed_steps = record.get(
                "completed_steps",
                []
            )

            roadmap = self.get_roadmap(
                record.get(
                    "career",
                    ""
                )
            )

            total_steps = len(
                roadmap
            )

            completed_count = len(
                completed_steps
            )

            remaining_steps = max(
                0,
                total_steps - completed_count
            )

            bar_length = 20

            filled_length = int(
                bar_length
                *
                progress
                /
                100
            )

            progress_bar = (
                "█" * filled_length
                +
                "░" * (
                    bar_length
                    -
                    filled_length
                )
            )

            if progress == 100:

                status = "🏆 Completed"

            elif progress > 0:

                status = "🚀 In Progress"

            else:

                status = "⏳ Not Started"

            if record.get(
                "favorite",
                False
            ):

                favorite = "⭐ Favorite"

            else:

                favorite = "☆ Not Favorite"

            print(
                f"\n🎯 {career}"
            )

            print(
                f"Progress : {progress}%"
            )

            print(
                f"[{progress_bar}]"
            )

            print(
                f"Completed : "
                f"{completed_count}/{total_steps}"
            )

            print(
                f"Remaining : "
                f"{remaining_steps}"
            )

            print(
                f"Status : {status}"
            )

            print(
                f"Favorite : {favorite}"
            )

        print(
            "\n" + "=" * 45
        )

    # ========================================================
    # MARK FAVORITE
    # ========================================================

    def mark_favorite(self):

        careers = self.load_career_data()

        user_records = [
            record
            for record in careers
            if record.get(
                "user",
                record.get(
                    "name",
                    ""
                )
            ).lower()
            ==
            self.current_user.lower()
        ]

        if not user_records:

            print(
                "❌ No career records found."
            )

            return

        print(
            "\n========== YOUR CAREERS =========="
        )

        for index, record in enumerate(
            user_records,
            start=1
        ):

            print(
                f"{index}. "
                f"{record['career'].title()}"
            )

        choice = input(
            "\nSelect career number: "
        ).strip()

        if not choice.isdigit():

            print(
                "❌ Invalid choice."
            )

            return

        index = int(choice)

        if (
            index < 1
            or
            index > len(user_records)
        ):

            print(
                "❌ Invalid career number."
            )

            return

        selected = user_records[
            index - 1
        ]

        selected["favorite"] = True

        self.save_career_data(
            careers
        )

        print(
            "⭐ Career marked as Favorite!"
        )

    # ========================================================
    # VIEW FAVORITES
    # ========================================================

    def view_favorites(self):

        careers = self.load_career_data()

        found = False

        print(
            "\n========== Favorite Careers =========="
        )

        for record in careers:

            user = record.get(
                "user",
                record.get(
                    "name",
                    ""
                )
            )

            if (
                user.lower()
                !=
                self.current_user.lower()
            ):

                continue

            if record.get(
                "favorite",
                False
            ):

                print(
                    f"\nName       : "
                    f"{record.get('name')}"
                )

                print(
                    f"Career     : "
                    f"{record.get('career')}"
                )

                print(
                    f"Progress   : "
                    f"{record.get('progress', 0)}%"
                )

                print(
                    "⭐ Favorite"
                )

                found = True

        if not found:

            print(
                "No favorite careers found."
            )

    # ========================================================
    # CAREER HISTORY
    # ========================================================

    def career_history(self):

        careers = self.load_career_data()

        found = False

        print(
            "\n========== Career History =========="
        )

        for record in careers:

            user = record.get(
                "user",
                record.get(
                    "name",
                    ""
                )
            )

            if (
                user.lower()
                !=
                self.current_user.lower()
            ):

                continue

            career = record.get(
                "career",
                ""
            ).lower()

            roadmap = self.get_roadmap(
                career
            )

            completed_steps = record.get(
                "completed_steps",
                []
            )

            total_steps = len(
                roadmap
            )

            completed_count = len(
                completed_steps
            )

            remaining_steps = max(
                0,
                total_steps - completed_count
            )

            if total_steps > 0:

                progress = int(
                    (
                        completed_count
                        /
                        total_steps
                    )
                    *
                    100
                )

            else:

                progress = record.get(
                    "progress",
                    0
                )

            bar_length = 20

            filled = int(
                (
                    progress
                    /
                    100
                )
                *
                bar_length
            )

            progress_bar = (
                "█" * filled
                +
                "░" * (
                    bar_length - filled
                )
            )

            if total_steps > 0:

                if progress == 100:

                    status = "🏆 Completed"

                elif progress > 0:

                    status = "🚀 In Progress"

                else:

                    status = "⏳ Not Started"

            else:

                status = "❓ No Roadmap"

            print(
                "\n------------------------------"
            )

            print(
                f"Name       : "
                f"{record.get('name')}"
            )

            print(
                f"Career     : "
                f"{record.get('career')}"
            )

            print(
                f"Progress   : "
                f"{progress}%"
            )

            print(
                f"[{progress_bar}]"
            )

            print(
                f"Completed  : "
                f"{completed_count}/"
                f"{total_steps}"
            )

            print(
                f"Remaining  : "
                f"{remaining_steps}"
            )

            print(
                f"Status     : "
                f"{status}"
            )

            if record.get("timestamp"):

                print(
                    f"Created On : "
                    f"{record['timestamp']}"
                )

            if record.get(
                "favorite",
                False
            ):

                print(
                    "⭐ Favorite"
                )

            print(
                "------------------------------"
            )

            found = True

        if not found:

            print(
                "No career history found."
            )

    # ========================================================
    # EXPORT CSV
    # ========================================================

    def export_to_csv(self):

        try:

            careers = self.load_career_data()

            with open(
                CSV_FILE,
                "w",
                newline=""
            ) as file:

                writer = csv.writer(
                    file
                )

                writer.writerow(
                    [
                        "Name",
                        "Career",
                        "Progress",
                        "Favorite",
                        "Timestamp"
                    ]
                )

                for record in careers:

                    writer.writerow(
                        [
                            record.get(
                                "name",
                                ""
                            ),

                            record.get(
                                "career",
                                ""
                            ),

                            record.get(
                                "progress",
                                0
                            ),

                            record.get(
                                "favorite",
                                False
                            ),

                            record.get(
                                "timestamp",
                                ""
                            )
                        ]
                    )

            print(
                "✅ Career history exported!"
            )

            print(
                f"File: {CSV_FILE}"
            )

        except Exception as e:

            logging.error(
                str(e)
            )

            print(
                f"❌ {e}"
            )

    # ========================================================
    # EXPORT TXT
    # ========================================================

    def export_to_txt(self):

        try:

            careers = self.load_career_data()

            with open(
                TXT_FILE,
                "w"
            ) as report:

                report.write(
                    "========== "
                    "AI Career Copilot Report "
                    "==========\n\n"
                )

                for record in careers:

                    report.write(
                        f"Name       : "
                        f"{record.get('name', '')}\n"
                    )

                    report.write(
                        f"Career     : "
                        f"{record.get('career', '')}\n"
                    )

                    report.write(
                        f"Progress   : "
                        f"{record.get('progress', 0)}%\n"
                    )

                    report.write(
                        f"Favorite   : "
                        f"{record.get('favorite', False)}\n"
                    )

                    if record.get("timestamp"):

                        report.write(
                            f"Created On : "
                            f"{record['timestamp']}\n"
                        )

                    report.write(
                        "-" * 40
                        + "\n"
                    )

            print(
                "✅ Career report exported successfully!"
            )

            print(
                f"File: {TXT_FILE}"
            )

        except Exception as e:

            logging.error(
                str(e)
            )

            print(
                f"❌ {e}"
            )

    # ========================================================
    # BACKUP
    # ========================================================

    def backup_data(self):

        try:
            save_dataset(BACKUP_FILE, self.load_career_data())

            print(
                "✅ Backup created successfully!"
            )

        except Exception as e:

            logging.error(
                str(e)
            )

            print(
                f"❌ {e}"
            )

    # ========================================================
    # RESTORE
    # ========================================================

    def restore_data(self):

        try:
            careers = load_dataset(BACKUP_FILE, None)
            if not isinstance(careers, list):

                print(
                    "❌ MongoDB career backup not found."
                )

                return

            self.save_career_data(careers)

            print(
                "✅ Data restored successfully!"
            )

            self.clean_duplicate_records()

        except Exception as e:

            logging.error(
                str(e)
            )

            print(
                f"❌ {e}"
            )

    # ========================================================
    # UPDATE PROGRESS
    # ========================================================

    def update_progress(self):

        careers = self.load_career_data()

        user_records = [
            record
            for record in careers
            if record.get(
                "user",
                record.get(
                    "name",
                    ""
                )
            ).lower()
            ==
            self.current_user.lower()
        ]

        if not user_records:

            print(
                "\n❌ No career records found."
            )

            return

        print(
            "\n========== YOUR CAREERS =========="
        )

        for index, record in enumerate(
            user_records,
            start=1
        ):

            print(
                f"{index}. "
                f"{record['career'].title()} "
                f"({record.get('progress', 0)}%)"
            )

        choice = input(
            "\nSelect career number: "
        ).strip()

        if not choice.isdigit():

            print(
                "❌ Invalid choice."
            )

            return

        index = int(choice)

        if (
            index < 1
            or
            index > len(user_records)
        ):

            print(
                "❌ Invalid career number."
            )

            return

        selected = user_records[
            index - 1
        ]

        career = selected[
            "career"
        ].lower()

        roadmap_steps = self.get_roadmap(
            career
        )

        if not roadmap_steps:

            print(
                "❌ Roadmap not available "
                "for this career."
            )

            return

        completed_steps = selected.get(
            "completed_steps",
            []
        )

        selected[
            "completed_steps"
        ] = completed_steps

        progress = int(
            (
                len(completed_steps)
                /
                len(roadmap_steps)
            )
            *
            100
        )

        selected[
            "progress"
        ] = progress

        self.save_career_data(
            careers
        )

        print(
            "\n========== ROADMAP PROGRESS =========="
        )

        for step in roadmap_steps:

            if step in completed_steps:

                print(
                    f"✅ {step}"
                )

            else:

                print(
                    f"⬜ {step}"
                )

        print(
            f"\n📈 Progress: {progress}%"
        )

        print(
            f"✅ Completed Steps: "
            f"{len(completed_steps)}/"
            f"{len(roadmap_steps)}"
        )

        if progress == 100:

            print(
                "\n🏆 Roadmap Completed!"
            )

        elif progress > 0:

            print(
                "\n🚀 Roadmap In Progress!"
            )

        else:

            print(
                "\n⏳ Roadmap Not Started."
            )

    # ========================================================
    # COMPLETE ROADMAP STEP
    # ========================================================

    def complete_roadmap_step(self):

        careers = self.load_career_data()

        user_records = [
            record
            for record in careers
            if record.get(
                "user",
                record.get(
                    "name",
                    ""
                )
            ).lower()
            ==
            self.current_user.lower()
        ]

        if not user_records:

            print(
                "\n❌ No career records found."
            )

            return

        print(
            "\n========== YOUR CAREERS =========="
        )

        for index, record in enumerate(
            user_records,
            start=1
        ):

            print(
                f"{index}. "
                f"{record['career'].title()} "
                f"- "
                f"{record.get('progress', 0)}%"
            )

        choice = input(
            "\nSelect career number: "
        ).strip()

        if not choice.isdigit():

            print(
                "❌ Please enter a valid number."
            )

            return

        career_index = int(
            choice
        )

        if (
            career_index < 1
            or
            career_index > len(user_records)
        ):

            print(
                "❌ Invalid career number."
            )

            return

        selected_record = user_records[
            career_index - 1
        ]

        career = selected_record[
            "career"
        ].lower()

        steps = self.get_roadmap(
            career
        )

        if not steps:

            print(
                "❌ Roadmap not available."
            )

            return

        completed_steps = selected_record.get(
            "completed_steps",
            []
        )

        print(
            "\n========== ROADMAP =========="
        )

        for index, step in enumerate(
            steps,
            start=1
        ):

            if step in completed_steps:

                print(
                    f"{index}. "
                    f"{step} ✅"
                )

            else:

                print(
                    f"{index}. "
                    f"{step} ⬜"
                )

        step_choice = input(
            "\nEnter step number to complete: "
        ).strip()

        if not step_choice.isdigit():

            print(
                "❌ Please enter a valid number."
            )

            return

        step_index = int(
            step_choice
        )

        if (
            step_index < 1
            or
            step_index > len(steps)
        ):

            print(
                "❌ Invalid step number."
            )

            return

        selected_step = steps[
            step_index - 1
        ]

        if selected_step in completed_steps:

            print(
                "⚠ This step is already completed!"
            )

            return

        completed_steps.append(
            selected_step
        )

        selected_record[
            "completed_steps"
        ] = completed_steps

        progress = int(
            (
                len(completed_steps)
                /
                len(steps)
            )
            *
            100
        )

        selected_record[
            "progress"
        ] = progress

        self.save_career_data(
            careers
        )

        print(
            "\n✅ Roadmap step completed!"
        )

        print(
            f"Completed: {selected_step}"
        )

        print(
            f"Progress: {progress}%"
        )

        if progress == 100:

            print(
                "\n🎉 Congratulations!"
            )

            print(
                "🏆 Career roadmap completed!"
            )

        logging.info(
            f"Roadmap step completed: "
            f"{selected_step}"
        )


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    copilot = CareerCopilot()

    copilot.welcome()

    if copilot.authentication_menu():

        copilot.welcome_user()

        while True:

            choice = copilot.show_menu()

            if not copilot.process_choice(
                choice
            ):

                break