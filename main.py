

from collections import UserDict
from datetime import datetime, timedelta

# ==========================================
# 1. КЛАСИ МОДЕЛЕЙ ДАНИХ (з ДЗ 6 + Birthday)
# ==========================================

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value: str):
        if not value:
            raise ValueError("Name cannot be empty.")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value: str):
        # Валідація: перевірка чи в номері рівно 10 цифр
        if not (value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str):
        try:
            # Перетворюємо рядок у об'єкт datetime.date та валідуємо формат
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number: str) -> None:
        phone = Phone(phone_number)
        self.phones.append(phone)

    def remove_phone(self, phone_number: str) -> None:
        phone_to_remove = self.find_phone(phone_number)
        if phone_to_remove is None:
            raise ValueError(f"Phone number {phone_number} not found.")
        self.phones.remove(phone_to_remove)

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        phone_obj = self.find_phone(old_phone)
        if not phone_obj:
            raise ValueError(f"Phone number {old_phone} not found.")

        new_phone_obj = Phone(new_phone)
        index = self.phones.index(phone_obj)
        self.phones[index] = new_phone_obj

    def find_phone(self, phone_number: str):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def add_birthday(self, birthday_str: str) -> None:
        self.birthday = Birthday(birthday_str)

    def __str__(self):
        phones_str = "; ".join(p.value for p in self.phones) if self.phones else "No phones"
        birthday_str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"


class AddressBook(UserDict):
    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name)

    def delete(self, name: str) -> None:
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self) -> list:
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if not record.birthday:
                continue

            bday = record.birthday.value

            # Безпечна обробка для 29 лютого у невисокосні роки
            try:
                bday_this_year = bday.replace(year=today.year)
            except ValueError:
                bday_this_year = datetime(today.year, 3, 1).date()

            # Якщо день народження цього року вже минув
            if bday_this_year < today:
                try:
                    bday_this_year = bday.replace(year=today.year + 1)
                except ValueError:
                    bday_this_year = datetime(today.year + 1, 3, 1).date()

            delta_days = (bday_this_year - today).days

            # Перевірка на найближчі 7 днів (включаючи сьогодні)
            if 0 <= delta_days <= 7:
                congratulation_date = bday_this_year

                # Перенесення з вихідних на понеділок
                if congratulation_date.weekday() == 5:    # Субота
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:  # Неділя
                    congratulation_date += timedelta(days=1)

                upcoming_birthdays.append({
                    "name": record.name.value,
                    "birthday": congratulation_date.strftime("%d.%m.%Y")
                })

        return upcoming_birthdays

    def __str__(self):
        if not self.data:
            return "Address book is empty."
        return "\n".join(str(record) for record in self.data.values())


# ==========================================
# 2. ДЕКОРАТОР ТА ХЕНДЛЕРИ КОМАНД
# ==========================================

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Enter all required arguments for the command."
        except KeyError:
            return "Contact not found."
    return inner


def parse_input(user_input: str):
    if not user_input.strip():
        return "", []
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        return "Contact not found."
    record.edit_phone(old_phone, new_phone)
    return "Phone number updated."


@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        return "Contact not found."
    if not record.phones:
        return f"No phone numbers found for {name}."
    return f"{name}: {'; '.join(p.value for p in record.phones)}"


@input_error
def show_all(book: AddressBook):
    return str(book)


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday_str, *_ = args
    record = book.find(name)
    if record is None:
        return "Contact not found."
    record.add_birthday(birthday_str)
    return f"Birthday added for {name}."


@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        return "Contact not found."
    if record.birthday is None:
        return f"No birthday set for {name}."
    return f"{name}'s birthday: {record.birthday}"


@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays in the next 7 days."
    
    result = ["Upcoming birthdays:"]
    for entry in upcoming:
        result.append(f"{entry['name']}: {entry['birthday']}")
    return "\n".join(result)


# ==========================================
# 3. ОСНОВНИЙ ЦИКЛ БОТА
# ==========================================

def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")
    
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()