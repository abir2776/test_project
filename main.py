import aioredis
from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from redis import asyncio as aioredis
from redis.asyncio.client import Redis

from models import *
from pydantic_models import (
    AssignDriver,
    DriverCreate,
    EmployeeCarBooking,
    EmployeeCreate,
)

app = FastAPI()


async def init():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    app.state.redis = await aioredis.from_url(
        "redis://localhost:6379", decode_responses=True
    )
    database = client.my_database
    await init_beanie(
        database,
        document_models=[User, Employee, Car, CarBooking, Driver, DriverAssignment],
    )


def get_redis() -> Redis:
    return app.state.redis


@app.on_event("startup")
async def on_startup():
    await init()


@app.get("/")
def index():
    return {"message": "Hello World!"}


@app.post("/add_cars")
async def add_cars(car_data: Car):
    car = Car(
        registration_number=car_data.registration_number,
        model=car_data.model,
        manufacturer=car_data.manufacturer,
        year=car_data.year,
    )
    await car.insert()
    return {"status": "success"}


@app.get("/cars", response_model=list[Car])
async def get_all_cars():
    cars = await Car.find_all().to_list()
    return cars


@app.post("/add_drivers")
async def add_driver(data: DriverCreate):
    user = User(
        username=data.user.username, email=data.user.email, password=data.user.password
    )
    await user.insert()

    driver = Driver(
        user_id=str(user.id),
        license_number=data.driver.license_number,
    )
    await driver.insert()

    return {"status": "success"}


@app.post("/add_employees")
async def add_employee(data: EmployeeCreate):
    user = User(
        username=data.user.username, email=data.user.email, password=data.user.password
    )
    await user.insert()

    employee = Employee(
        user_id=str(user.id),
        position=data.employee.position,
        salary=data.employee.salary,
        hire_date=data.employee.hire_date,
    )
    await employee.insert()

    return {"status": "success"}


@app.post("/assign_drivers")
async def assign_driver(data: AssignDriver):
    cache = get_redis()
    is_car_assigned = await cache.get(f"is_car_assigned_{data.car_id}")
    is_driver_assigned = await cache.get(f"is_driver_assigned_{data.driver_id}")

    if is_car_assigned == "True" and is_driver_assigned == "True":
        return {"status": "Car and driver are already assigned."}

    if is_car_assigned == "True":
        return {"status": "Car is already assigned to a driver."}

    if is_driver_assigned == "True":
        return {"status": "Driver is already assigned to a car."}

    assigned_driver = DriverAssignment(driver_id=data.driver_id, car_id=data.car_id)

    await assigned_driver.insert()

    await cache.set(f"is_car_assigned_{data.car_id}", "True")
    await cache.set(f"is_driver_assigned_{data.driver_id}", "True")

    return {"status": "Driver assigned successfully."}


@app.post("/car_booking")
async def car_booking(data: EmployeeCarBooking):
    cache = get_redis()
    is_car_booked = await cache.get(f"is_car_booked_{data.car_id}")
    is_employee_booked_car = await cache.get(
        f"is_employee_booked_car_{data.employee_id}_{data.booking_date}"
    )
    if is_car_booked == "True" and is_employee_booked_car == "True":
        return {
            "status": "Car is already booked and employee is also booked a car for the given date."
        }
    if is_car_booked == "True":
        return {"status": "Car is already booked."}
    if is_employee_booked_car == "True":
        return {"status": "Employee is already booked a car for the given date."}

    car_booking = CarBooking(
        employee_id=data.employee_id, car_id=data.car_id, booking_date=data.booking_date
    )
    await car_booking.insert()
    await cache.set(f"is_car_booked_{data.car_id}", "True")
    await cache.set(
        f"is_employee_booked_car_{data.employee_id}_{data.booking_date}", "True"
    )

    return {"status": "Car booking successful."}


@app.get("/car_booking/{booking_id}")
async def get_car_booking(booking_id: str):
    car_booking = await CarBooking.get(booking_id)

    if not car_booking:
        return {"status": "Car booking not found."}

    return car_booking


@app.put("/car_booking/{booking_id}")
async def update_car_booking(booking_id: str, data: EmployeeCarBooking):
    car_booking = await CarBooking.get(booking_id)

    if not car_booking:
        return {"status": "Car booking not found."}

    car_booking.employee_id = data.employee_id
    car_booking.car_id = data.car_id
    car_booking.booking_date = data.booking_date
    await car_booking.save()
    cache = get_redis()
    await cache.set(f"is_car_booked_{data.car_id}", "True")
    await cache.set(
        f"is_employee_booked_car_{data.employee_id}_{data.booking_date}", "True"
    )

    return {"status": "Car booking updated successfully."}


@app.delete("/car_booking/{booking_id}")
async def delete_car_booking(booking_id: str):
    car_booking = await CarBooking.get(booking_id)

    if not car_booking:
        return {"status": "Car booking not found."}
    await car_booking.delete()

    cache = get_redis()
    await cache.delete(f"is_car_booked_{car_booking.car_id}")
    await cache.delete(
        f"is_employee_booked_car_{car_booking.employee_id}_{car_booking.booking_date}"
    )

    return {"status": "Car booking deleted successfully."}
