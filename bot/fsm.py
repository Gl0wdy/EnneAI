from aiogram.fsm.state import StatesGroup, State


class SendingState(StatesGroup):
    enter_content = State()

class ConfirmationState(StatesGroup):
    confirm = State()

class ReviewState(StatesGroup):
    review = State()