import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.db.models import Q

router = Router()


# --- Перевірка доступу ---


def is_admin_or_teacher(chat_id):
    allowed = os.getenv("TELEGRAM_ADMIN_CHAT_IDS", "")
    return str(chat_id) in [x.strip() for x in allowed.split(",") if x.strip()]


# --- Допоміжні функції ---


@sync_to_async
def find_student_by_username(username):
    from students.models import Student

    clean = username.lstrip("@")
    return Student.objects.filter(
        Q(telegram_username__iexact=clean) | Q(telegram_username__iexact=f"@{clean}")
    ).first()


@sync_to_async
def update_chat_id(student, chat_id):
    student.telegram_chat_id = chat_id
    student.save(update_fields=["telegram_chat_id"])


@sync_to_async
def get_debtors_list():
    from notifications.services import get_bot_debtors_text

    return get_bot_debtors_text()


@sync_to_async
def get_formatted_group_info(group_name):
    from schedule.models import Group

    try:
        group = (
            Group.objects.select_related("teacher")
            .prefetch_related("schedule_entries", "students")
            .get(name__iexact=group_name)
        )
        teacher = group.teacher.get_full_name() if group.teacher else "Не призначено"
        schedule = (
            "\n".join(
                f"  {s.get_weekday_display()} {s.start_time.strftime('%H:%M')}-{s.end_time.strftime('%H:%M')}"
                for s in group.schedule_entries.all()
            )
            or "Розклад не заповнений"
        )
        students = "\n".join(f"  {s.full_name}" for s in group.students.all()) or "Студентів немає"
        return (
            f"Група: {group.name}\n"
            f"Викладач: {teacher}\n\n"
            f"Розклад:\n{schedule}\n\n"
            f"Студенти:\n{students}"
        )
    except Group.DoesNotExist:
        return None


@sync_to_async
def create_student(data):
    from students.models import Course, Student

    course = Course.objects.filter(name__iexact=data["course"]).first()
    return Student.objects.create(
        full_name=data["full_name"],
        phone=data["phone"],
        course=course,
        status=data["status"],
    )


@sync_to_async
def do_remind():
    from notifications.services import remind_debtors_telegram

    return remind_debtors_telegram()


@sync_to_async
def do_broadcast(group_name, text):
    from notifications.services import broadcast_to_group
    from schedule.models import Group

    try:
        group = Group.objects.get(name__iexact=group_name)
        return broadcast_to_group(group.id, text)
    except Group.DoesNotExist:
        return None


# --- FSM для /add_student ---


class AddStudentForm(StatesGroup):
    full_name = State()
    phone = State()
    course = State()
    status = State()


# --- Хендлери ---


@router.message(Command("start"))
async def cmd_start(message: Message):
    username = message.from_user.username
    if username:
        student = await find_student_by_username(username)
        if student:
            await update_chat_id(student, message.chat.id)
            await message.answer(f"Привіт, {student.full_name}! Твій акаунт підключено до системи.")
            return
    await message.answer(
        "Привіт! Я бот ITLEO Academy.\n\n"
        "Команди:\n"
        "/add_student — додати студента\n"
        "/debtors — список боржників\n"
        "/group <назва> — інфо про групу\n"
        "/remind — нагадати про оплату\n"
        "/broadcast <група> | <текст> — розсилка групі"
    )


@router.message(Command("add_student"))
async def cmd_add_student(message: Message, state: FSMContext):
    if not is_admin_or_teacher(message.chat.id):
        await message.answer("⛔ Ця команда доступна лише адміністраторам.")
        return
    await state.set_state(AddStudentForm.full_name)
    await message.answer("Введіть повне ім'я студента:")


@router.message(AddStudentForm.full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(AddStudentForm.phone)
    await message.answer("Введіть телефон:")


@router.message(AddStudentForm.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(AddStudentForm.course)
    await message.answer("Введіть назву курсу (наприклад: Python Junior):")


@router.message(AddStudentForm.course)
async def process_course(message: Message, state: FSMContext):
    await state.update_data(course=message.text)
    await state.set_state(AddStudentForm.status)
    await message.answer("Введіть статус:\nlead / studying / finished / frozen")


@router.message(AddStudentForm.status)
async def process_status(message: Message, state: FSMContext):
    valid_statuses = ["lead", "studying", "finished", "frozen"]
    if message.text.lower() not in valid_statuses:
        await message.answer("Невірний статус. Введіть: lead / studying / finished / frozen")
        return
    await state.update_data(status=message.text.lower())
    data = await state.get_data()
    student = await create_student(data)
    await state.clear()
    await message.answer(f"Студента {student.full_name} успішно додано!")


@router.message(Command("debtors"))
async def cmd_debtors(message: Message):
    if not is_admin_or_teacher(message.chat.id):
        await message.answer("⛔ Ця команда доступна лише адміністраторам.")
        return
    text = await get_debtors_list()
    await message.answer(text)


@router.message(Command("group"))
async def cmd_group(message: Message):
    if not is_admin_or_teacher(message.chat.id):
        await message.answer("⛔ Ця команда доступна лише адміністраторам.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Використання: /group <назва групи>")
        return
    text_response = await get_formatted_group_info(args[1])
    if not text_response:
        await message.answer(f"Група '{args[1]}' не знайдена.")
        return
    await message.answer(text_response)


@router.message(Command("remind"))
async def cmd_remind(message: Message):
    if not is_admin_or_teacher(message.chat.id):
        await message.answer("⛔ Ця команда доступна лише адміністраторам.")
        return
    sent, skipped = await do_remind()
    await message.answer(f"Нагадування надіслано: {sent}\nПропущено (немає Telegram): {skipped}")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin_or_teacher(message.chat.id):
        await message.answer("⛔ Ця команда доступна лише адміністраторам.")
        return
    parts = message.text.split("|", maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Використання: /broadcast <назва групи> | <текст>\n"
            "Приклад: /broadcast Python Pro | Привіт, група!"
        )
        return
    group_name = parts[0].replace("/broadcast", "").strip()
    text = parts[1].strip()
    result = await do_broadcast(group_name, text)
    if result is None:
        await message.answer(f"Група '{group_name}' не знайдена.")
        return
    sent, skipped = result
    await message.answer(
        f"Розсилка по групі '{group_name}':\nНадіслано: {sent}\nПропущено: {skipped}"
    )
