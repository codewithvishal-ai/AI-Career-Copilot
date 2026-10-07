import logging


class InvalidNameError(Exception):
    pass


class InvalidCareerError(Exception):
    pass


logging.basicConfig(
    filename="careercopilot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_user_name():

    while True:

        try:
            name = input("Enter your name: ").strip()

            if not name:
                raise InvalidNameError("Name cannot be empty.")

            if not name.replace(" ", "").isalpha():
                raise InvalidNameError("Name should contain only alphabets.")

            logging.info(f"User entered name: {name}")

            return name

        except InvalidNameError as e:
            logging.error(str(e))
            print(f"❌ {e}")
            
def get_career_interest():

    career_alias = {
        "artificial intelligence": "ai",
        "web development": "web",
        "python programming": "python",
        "datascience": "data science"
    }

    valid_careers = [
        "ai",
        "artificial intelligence",
        "web",
        "web development",
        "python",
        "python programming",
        "data science",
        "datascience",
    ]

    while True:

        try:

            interest = input("Enter your career interest: ").strip().lower()

            if not interest:
                raise InvalidCareerError("Career interest cannot be empty.")

            if interest not in valid_careers:
                raise InvalidCareerError("Invalid career! Choose AI, Web, Python or Data Science.")
            logging.info(f"Career selected: {interest}")
            return career_alias.get(interest, interest)

        except InvalidCareerError as e:
            print(f"enter correctly {e}")