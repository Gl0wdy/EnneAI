from aiogram.fsm.state import State, StatesGroup

class CommandStates(StatesGroup):
    waiting_for_clear = State()
    waiting_for_mode = State()

class ProfileStates(StatesGroup):
    waiting_for_confirmation = State()
    waiting_for_username = State()
    waiting_for_typologies = State()