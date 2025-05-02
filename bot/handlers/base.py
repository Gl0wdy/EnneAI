from aiogram import Router
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.enums import ChatAction, ChatMemberStatus
from aiogram.fsm.context import FSMContext

import bot.database as db
import bot.keyboards as kb
from bot.fsm import ConfirmationState, ReviewState
from ai.completions import Chat
from ai.utils import parse_buttons

import re
from datetime import datetime
import asyncio


base_router = Router(name='main')
chat = Chat()


@base_router.message()
async def catch_all(message: Message):
    if message.chat.type == 'private':
        await message.reply('*❗️ Сервер Наранхо закрыт на тех. обслуживание!* Вот-вот выйдет _обновление..._ Следите за новостями в [канале](https://t.me/typologyAIchannel)')


@base_router.message(CommandStart())
async def start_command(message: Message):
    if message.chat.type == 'private':
        await message.answer(
            text='*Я - Клаудио Наранхо, и я готов помочь тебе с типологиями.* '
                'Я могу:\n1. Типировать что угодно (кроме персонажей, этим занимается [другой бот](https://t.me/fictionalAIbot)\n'
                '2. Рассказать о соционике, эннеаграмме и психософии\n'
                '3. Сравнить 2 и более типа между собой (как по функциям, так и в общем)\n'
                '4. Помочь с изучением типологий\n'
                '5. Провести вас на путь интеграции типа'
                '6. [Работать в группах](https://telegra.ph/Klaudio-Naranho--Vash-pomoshchnik-po-tipologiyam-04-26)\n'
                'Просто напиши мне вопрос или выбери один из предложенных!\n\n'
                '_P.S: Рекомендую прочитать [мануал](https://telegra.ph/Klaudio-Naranho--Vash-pomoshchnik-po-tipologiyam-04-26) по использованию бота, чтобы повысить качество ответов._',
            reply_markup=kb.main_markup
        )
    

@base_router.message(Command(commands='clear'))
async def clear_history(message: Message, state: FSMContext):
    if message.chat.type == 'private':
        await state.set_state(ConfirmationState.confirm)
        await message.answer('❗️ Вы уверены, что хотите стереть историю чата? Это нельзя отменить.',
                            reply_markup=kb.confirm_markup)
        

@base_router.message(Command(commands='cancel'))
async def cancel(message: Message):
    if message.chat.type == 'private':
        await db.set_busy_state(message.from_user.id, is_busy=False)
        await message.answer('✅ Ошибка исправлена, можете отправлять следующий запрос.')


@base_router.message(Command(commands=['settings']))
async def settings(message: Message, state: FSMContext):
    user_id = message.from_user.id
    curr_database = await db.get_collection(user_id)
    markup = kb.set_collection_buttons(user_id, curr_database)
    msg = await message.answer(f'📋 *Пожалуйста, выберите базу знаний:*\n'
                         '- dynamic (BETA) - алгоритм сам решает, какую базу знаний стоит использовать. не всегда работает корректно.\n'
                         '- ennea - база знаний эннеаграммы\n'
                         '- socionics - база знаний соционики\n'
                         '- psychosophy - база знаний психософии\n'
                         '_❗️ Наранхо работает однозначно, понятно и корректно только с типологией, соответствующей выбранной БЗ._',
                         reply_markup=markup)
    await state.set_data({'msg': msg})


@base_router.callback_query(lambda x: x.data.startswith('set'))
async def set_database(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split('__')[-1]
    collection, uid = data.split('_')
    await db.set_collection(int(uid), collection)
    selection_msg = (await state.get_data())['msg']
    markup = kb.set_collection_buttons(uid, collection)
    await selection_msg.edit_text(f'🆕 *Установлена база знаний "{collection}":*\n'
                         '- dynamic (BETA) - алгоритм сам решает, какую базу знаний стоит использовать. не всегда работает корректно.\n'
                         '- ennea - база знаний эннеаграммы\n'
                         '- socionics - база знаний соционики\n'
                         '- psychosophy - база знаний психософии\n'
                         '❗️ Наранхо работает однозначно, понятно и корректно только с типологией, соответствующей выбранной БЗ.',
                         reply_markup=markup)


@base_router.message(ConfirmationState.confirm)
async def confirmation_process(message: Message, state: FSMContext):
    if message.text == '✅Да':
        await db.clear_history(message.from_user.id)
        await message.answer('🗑 История чата успешно удалена. Теперь Наранхо ничего не помнит.',
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
    elif message.text == '❌Нет':
        await message.answer('История чата не была очищена. Можете продолжать диалог.',
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
    else:
        await message.answer('Пожалуйста, выберите действие.')


@base_router.message(Command('floodwait'))
async def set_floodwait(message: Message):
    if message.chat.type == 'supergroup':
        member = await message.bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
        if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
            await message.reply('У вас недостаточно прав для выполнения этой команды.')
            return
        text = message.text.split()
        if len(text) < 2:
            await message.reply('Укажите время в секундах. (/floodwait [время])')
            return
        seconds = text[-1]
        if not seconds.isnumeric():
            await message.answer('Некорректный данные, укажите время в секундах.')
            return
        await db.set_floodwait(message.chat.id, int(seconds))
        await message.reply(f'✅ Параметр успешно обновлён. Теперь ботом могут пользоваться раз в {seconds} секунд.')
    

@base_router.message(lambda x: bool(x.text) | bool(x.caption))
async def message_handler(message: Message):
    text = message.caption if message.caption else message.text
    user_id = message.from_user.id

    if message.chat.type == 'private':
        is_busy = await db.get_busy_state(user_id)
        if is_busy:
            await message.answer('Дождитесь завершения предыдущего запроса.\nЗавис бот? Используй /cancel')
            return
        await db.set_busy_state(user_id, True)
        await db.save_message(user_id, 'user', text)
        chat_history = await db.get_history(user_id)

        selected_collection = await db.get_collection(user_id)
        if selected_collection == 'dynamic':
            collection = await chat.vector_db.classify_search(text)
            status_msg = await message.answer(f'✅ *Запрос принят.* Запрос отнесён к базе знаний "{collection}"\n_Настроить используемую базу знаний - /settings_')
        else:
            collection = selected_collection
            status_msg = await message.answer(f'*✅ Запрос принят.* Используемая база знаний - "{collection}"')
        waiting_msg = await message.answer('⌛️')
        await message.bot.send_chat_action(user_id, ChatAction.TYPING)
        response = await chat.create(
            request=text,
            collections=collection,
            chat_history=chat_history
        )
        await status_msg.delete()
        await waiting_msg.delete()
        cleared_text, buttons_data = parse_buttons(response)
        buttons = kb.create_buttons(buttons_data)

        if len(cleared_text) >= 4096:
            chunked = [cleared_text[:4090] + '...', '...' + cleared_text[4090:]]
            first = await message.answer(chunked[0], parse_mode='Markdown')
            await first.reply(chunked[1], parse_mode='Markdown', reply_markup=buttons)
        else:
            await message.answer(cleared_text, parse_mode='Markdown', reply_markup=buttons)

        await db.save_message(user_id, 'system', cleared_text)
        await db.set_busy_state(user_id, False)
        
    elif message.chat.type == 'supergroup':
        bot = await message.bot.get_me()
        if not re.search(f'^@{bot.username}', message.text):
            await db.save_group_message(
                group_id=message.chat.id,
                username=message.from_user.username,
                role='system',
                content=message.text
            )
            return
        floodwait = await db.get_floodwait(message.chat.id)
        last_message = await db.get_last_request(message.chat.id)
        if last_message:
            now = datetime.now()
            diff = (now - last_message).total_seconds()
            if diff < floodwait:
                await message.reply(f'*❌ Ограничение на всю группу:*\nподождите {int(floodwait - diff)} секунд перед следующим запросом.')
                return
            
        await db.set_last_request(message.chat.id)
        await db.save_group_message(
                group_id=message.chat.id,
                username=message.from_user.username,
                role='user',
                content=message.text
            )
        group_chat_history = await db.get_group_history(message.chat.id)

        if (reply_to := message.reply_to_message):
            reply_to_text = reply_to.caption if reply_to.caption else reply_to.text
            reply_to_context = {
                'role': 'user',
                'content': f'@{reply_to.from_user.username}:\n{reply_to_text}'
            }
            group_chat_history.insert(-2, reply_to_context)

        waiting_msg = await message.reply('⏳')
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

        response = await chat.create(
            request=text.split(maxsplit=1)[-1],
            collections='ennea',
            chat_history=group_chat_history,
            is_group=True
        )
        cleared_text, _ = parse_buttons(response)
        await waiting_msg.delete()
        await db.save_group_message(
            group_id=message.chat.id, 
            username=message.from_user.username,
            role='assistant',
            content=cleared_text
        )
        await message.reply(cleared_text, parse_mode='Markdown')


@base_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_group_adding(message: Message):
    await message.answer(text='*Я - Наранхо, и я могу помочь вам с типированием по эннеаграмме.*\n'
                                'Чтобы обратиться ко мне, просто отметь и задай свой вопрос. '
                                'Например: "@typologyAIbot типируй участников чата".\n'
                                'Также я способен читать историю чата в диапазоне ста сообщений.'
                                'Подробнее обо мне вы можете узнать в [мануале](https://telegra.ph/Klaudio-Naranho--Vash-pomoshchnik-po-tipologiyam-04-26)\n\n'
                                '*❗️ ДЛЯ КОРРЕКТНОЙ РАБОТЫ БОТА ЕМУ НУЖНО ВЫДАТЬ ПРАВА АДМИНА*')