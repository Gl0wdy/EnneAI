from aiogram.fsm.state import State, StatesGroup

class CommandStates(StatesGroup):
    waiting_for_clear = State()
    waiting_for_newsletter = State()


class AdminStates(StatesGroup):
    waiting_for_broadcast = State()


class ProfileStates(StatesGroup):
    waiting_for_confirmation = State()
    waiting_for_username = State()
    waiting_for_typologies = State()
    in_progress = State()