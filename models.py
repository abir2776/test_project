from datetime import datetime,date
from typing import Optional

from beanie import Document


class User(Document):
    username: str
    email: str
    password: str

    class Settings:
        collection = "users"


class Employee(Document):
    user_id: Optional[str] = None
    position: str
    salary: float
    hire_date: str
    is_active: bool = True

    class Settings:
        collection = "employees"


class Car(Document):
    registration_number: str
    model: str
    manufacturer: str
    year: int
    is_active: bool = True

    class Settings:
        collection = "cars"


class Driver(Document):
    user_id: Optional[str] = None
    license_number: str
    is_active: bool = True

    class Settings:
        collection = "drivers"


class DriverAssignment(Document):
    driver_id: Optional[str] = None
    car_id: Optional[str]
    assigned_at: datetime = datetime.now()
    unassigned_at: datetime = None
    is_active: bool = True

    class Settings:
        collection = "driver_assignments"
        indexes = [
            [("car_id", 1), ("driver_id", 1)],
        ]


class CarBooking(Document):
    employee_id: Optional[str] = None
    car_id: Optional[str] = None
    booking_date: date
    created_at: datetime = datetime.now()

    class Settings:
        collection = "car_bookings"
        indexes = [[("car_id", 1), ("employee_id", 1), ("booking_date", 1)]]
