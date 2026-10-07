class Person:

    def __init__(self):
        self.__name = ""

    def set_name(self, name):
        if name.replace(" ", "").isalpha():
            self.__name = name
        else:
            print("❌ Invalid Name!")

    def get_name(self):
        return self.__name

    def welcome_user(self):
        print(f"\nWelcome, {self.__name}")