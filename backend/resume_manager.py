import os
from datetime import datetime
from mongo_store import load_dataset, save_dataset


class ResumeManager:

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self):

        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        self.resume_data_file = os.path.join(
            base_dir,
            "resume_analysis.json"
        )

    # ============================================================
    # LOAD DATA
    # ============================================================

    def load_resume_data(self):

        try:
            data = load_dataset(self.resume_data_file, [])

            if not isinstance(data, list):
                return []

            return data

        except Exception as e:

            print(
                f"❌ Error loading resume data: {e}"
            )

            return []

    # ============================================================
    # SAVE DATA
    # ============================================================

    def save_resume_data(self, data):

        try:
            save_dataset(self.resume_data_file, data)

            return True

        except Exception as e:

            print(
                f"❌ Error saving resume data: {e}"
            )

            return False

    # ============================================================
    # SAVE COMPLETE RESUME ANALYSIS
    # ============================================================

    def save_analysis(
        self,
        username,
        resume_name,
        detected_name="",
        email="",
        phone="",
        skills=None,
        sections=None,
        strength_score=0,
        ats_score=0,
        analysis=None
    ):

        data = self.load_resume_data()

        if not isinstance(
            data,
            list
        ):
            data = []

        # --------------------------------------------------------
        # COMPLETE ANALYSIS
        # --------------------------------------------------------

        if isinstance(
            analysis,
            dict
        ):

            record = dict(
                analysis
            )

        else:

            record = {}

        # --------------------------------------------------------
        # FORCE SYSTEM FIELDS
        # --------------------------------------------------------

        record["user"] = username

        record["resume_file"] = resume_name

        record["name"] = (
            detected_name
            or
            record.get(
                "name",
                ""
            )
        )

        record["email"] = (
            email
            or
            record.get(
                "email",
                ""
            )
        )

        record["phone"] = (
            phone
            or
            record.get(
                "phone",
                ""
            )
        )

        record["skills"] = (
            skills
            if isinstance(
                skills,
                list
            )
            else record.get(
                "skills",
                []
            )
        )

        record["sections"] = (
            sections
            if isinstance(
                sections,
                list
            )
            else record.get(
                "sections",
                []
            )
        )

        record["resume_strength_score"] = (
            strength_score
            if strength_score is not None
            else record.get(
                "resume_strength_score",
                0
            )
        )

        record["ats_score"] = (
            ats_score
            if ats_score is not None
            else record.get(
                "ats_score",
                0
            )
        )

        # --------------------------------------------------------
        # IMPORTANT CAREER INTELLIGENCE FIELDS
        # --------------------------------------------------------

        record["content_quality"] = record.get(
            "content_quality",
            0
        )

        record["achievement_strength"] = record.get(
            "achievement_strength",
            0
        )

        record["summary"] = record.get(
            "summary",
            ""
        )

        record["profile"] = record.get(
            "profile",
            ""
        )

        record["objective"] = record.get(
            "objective",
            ""
        )

        record["experience"] = record.get(
            "experience",
            ""
        )

        record["education"] = record.get(
            "education",
            ""
        )

        record["linkedin"] = record.get(
            "linkedin",
            ""
        )

        record["github"] = record.get(
            "github",
            ""
        )

        # --------------------------------------------------------
        # TIMESTAMP
        # --------------------------------------------------------

        record["timestamp"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # --------------------------------------------------------
        # SAVE
        # --------------------------------------------------------

        data.append(
            record
        )

        if self.save_resume_data(
            data
        ):

            print(
                "\n✅ Complete resume analysis saved successfully!"
            )

            return True

        return False

    # ============================================================
    # GET USER RESUME HISTORY
    # ============================================================

    def get_user_resume_history(
        self,
        username
    ):

        data = self.load_resume_data()

        user_history = []

        for record in data:

            record_user = str(
                record.get(
                    "user",
                    ""
                )
            ).strip()

            if (
                record_user.lower()
                ==
                str(username).strip().lower()
            ):

                user_history.append(
                    record
                )

        return user_history

    # ============================================================
    # VIEW RESUME HISTORY
    # ============================================================

    def view_resume_history(
        self,
        username
    ):

        history = (
            self.get_user_resume_history(
                username
            )
        )

        print(
            "\n========== RESUME ANALYSIS HISTORY =========="
        )

        if not history:

            print(
                "❌ No resume analysis history found."
            )

            return

        for index, record in enumerate(
            history,
            start=1
        ):

            print(
                "\n----------------------------------------"
            )

            print(
                f"Analysis #{index}"
            )

            print(
                f"Resume File      : "
                f"{record.get('resume_file', '')}"
            )

            print(
                f"Detected Name    : "
                f"{record.get('name', '')}"
            )

            print(
                f"Email            : "
                f"{record.get('email', '')}"
            )

            print(
                f"Phone            : "
                f"{record.get('phone', '')}"
            )

            print(
                f"Skills           : "
                f"{len(record.get('skills', []))}"
            )

            print(
                f"Resume Strength  : "
                f"{record.get('resume_strength_score', 0)}/100"
            )

            print(
                f"ATS Score        : "
                f"{record.get('ats_score', 0)}/100"
            )

            print(
                f"Content Quality  : "
                f"{record.get('content_quality', 0)}/100"
            )

            print(
                f"Achievement      : "
                f"{record.get('achievement_strength', 0)}/100"
            )

            print(
                f"Analyzed On      : "
                f"{record.get('timestamp', '')}"
            )

            print(
                "----------------------------------------"
            )

    # ============================================================
    # LATEST ANALYSIS
    # ============================================================

    def get_latest_analysis(
        self,
        username
    ):

        history = (
            self.get_user_resume_history(
                username
            )
        )

        if not history:
            return None

        return history[-1]