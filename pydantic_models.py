from pydantic import BaseModel

from models import Driver, Employee, User, Driver


class DriverCreate(BaseModel):
    user: User
    driver: Driver


class EmployeeCreate(BaseModel):
    user: User
    employee: Employee


class AssignDriver(BaseModel):
    driver_id: str
    car_id: str


class EmployeeCarBooking(BaseModel):
    employee_id: str
    car_id: str
    booking_date: str
