from faker import Faker
import random
from typing import Literal as _Literal

from aplustools.security.passwords import SpecificPasswordGenerator, big_reducer_3

# Extra functionalities derived from the faker module
# This is also a wrapper for the default faker.Faker
# class for ease of use.


class FakerPro(Faker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._families = []
        self._remaining_family_members = []

    def _generate_family(self):
        family_name = self.last_name()
        # Create parents
        father = self._create_identity(gender='male', last_name=family_name)
        mother = self._create_identity(gender='female', last_name=family_name)
        family = [father, mother]

        # Create children
        num_children = random.randint(1, 3)
        for _ in range(num_children):
            child = self._create_identity(gender=random.choice(['male', 'female']), last_name=family_name)
            family.append(child)

        self._families.append(family)
        self._remaining_family_members.extend(family)

    def _create_identity(self, gender=None, last_name=None):
        first_name = self.first_name_male() if gender == 'male' else self.first_name_female()
        if last_name is None:
            last_name = self.last_name()
        full_name = f"{first_name} {last_name}"
        email = self.email_relational_name(first_name, last_name)
        return {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
            'gender': gender,
            'email': email,
            'address': self.address(),
            'phone_number': self.phone_number(),
            'birth_date': self.date_of_birth()
        }

    def generate_person(self):
        # Decide whether to generate a new person or return a family member
        if self._remaining_family_members and random.random() < 0.5:
            return self._remaining_family_members.pop()
        else:
            if random.random() < 0.3:  # 30% chance to generate a new family
                self._generate_family()
                return self._remaining_family_members.pop()
            else:  # Generate a single person not part of a family
                return self._create_identity(gender=random.choice(['male', 'female']))

    def gender_relational_name(self, gender: _Literal["male", "female", "other"], include_last_name=False):
        first_name = self.first_name_male() if gender.lower() == 'male' else self.first_name_female()
        if include_last_name:
            last_name = self.last_name()
            return f"{first_name} {last_name}"
        return first_name

    def email_relational_name(self, first_name, last_name):
        ranges = [range(48, 57), range(65, 90), range(97, 122), range(43, 43), range(45, 45), range(95, 95), range(126, 126)]
        last_name = big_reducer_3(SpecificPasswordGenerator().basic_secure_password(last_name, passes=1, expand=False), ranges)
        first_name = big_reducer_3(SpecificPasswordGenerator().basic_secure_password(first_name, passes=1, expand=False), ranges)
        email = f"{first_name}{random.choice(('.', '+', '_', '-', '', '~'))}{last_name}@{self.domain_name()}"
        return email

    def generate_family(self, family_name=None):
        if family_name is None:
            family_name = self.last_name()

        self._generate_family()
        family = self._families[-1]
        return family


def local_test():
    """Test the module"""
    try:
        fake_pro = FakerPro("de-DE")

        # Generate multiple random people, some of which may belong to families
        print("Generating random people:")
        for _ in range(10):
            person = fake_pro.generate_person()
            print(person)

        # Generate a specific family
        family_name = "Smith"
        family = fake_pro.generate_family(family_name)
        print(f"\nGenerated family {family_name}:")
        for member in family:
            print(member)

        # Generate gender relational names with and without last names
        male_name_with_last = fake_pro.gender_relational_name('male', include_last_name=True)
        female_name_without_last = fake_pro.gender_relational_name('female', include_last_name=False)
        print(f"\nMale name with last name: {male_name_with_last}")
        print(f"Female name without last name: {female_name_without_last}")

        # Generate email relational to name
        email = fake_pro.email_relational_name("John", "Doe")
        print(f"\nRelational email: {email}")
    except Exception as e:
        print(f"Error occurred: {e}")
        return False
    return True


if __name__ == "__main__":
    local_test()
