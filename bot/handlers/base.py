from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, JOIN_TRANSITION, or_f
from aiogram.types import Message, CallbackQuery, MessageEntity
from aiogram.enums import ChatAction, ChatMemberStatus
from aiogram.fsm.context import FSMContext
from aiogram.utils import markdown as md

import bot.database as db
import bot.keyboards as kb
from bot.fsm import ConfirmationState, LongMemState
from ai.completions import Chat
from ai.utils import parse_system_info
from utils.file_reader import BufferTextReader
from config import ADMIN_ID

import re
from datetime import datetime, timedelta
import io
import random

base_router = Router(name='main')
chat = Chat()

reader = BufferTextReader()
SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".fb2", ".epub", ".docx"}


@base_router.message(CommandStart())
async def start_command(message: Message):
    start_args = message.text.split()
    uid = message.from_user.id
    user = await db.get_user(uid)
    if not user:
        await db.save_message(uid, 'system', 'юзер впервые взаимодействует с тобой, поздоровайся.')
    if len(start_args) == 2:
        ref_id = int(start_args[-1])
        ref_user = await db.get_user(ref_id)
        user = await db.get_user(uid)
        if user is None and ref_user.get('ref_count', 0) < 6:
            await db.save_message(uid, 'system', 'это первое сообщение пользователя, поздоровайся и объясни свое предназначение!')
            await message.bot.send_message(ref_id, '*🥳 По вашей реферальной ссылке перешли!*\nВы получаете премиум на 1 день.',
                                           message_effect_id="5046509860389126442")
            await db.set_status(ref_id, premium=True, period=timedelta(days=1))
            await db.inc_ref_count(ref_id)

    if message.chat.type == 'private':
        await message.answer(
            text='*Я - Клаудио Наранхо, и я готов помочь тебе с типологиями.* '
                'Я могу:\n1. Типировать что угодно (кроме персонажей, этим занимается [другой бот](https://t.me/fictionalAIbot)\n'
                '2. Рассказать о соционике, эннеаграмме, психософии и классическом Юнге\n'
                '3. Сравнить 2 и более типа между собой (как по функциям, так и в общем)\n'
                '4. Помочь с изучением типологий\n'
                '5. [Работать в группах](https://telegra.ph/Klaudio-Naranho--Vash-pomoshchnik-po-tipologiyam-04-26)\n'
                '6. Читать твои опросники и разбирать их: просто пришли мне файл в формате txt, pdf, fb2, epub или docx!, '
                'Просто напиши мне вопрос или выбери один из предложенных.\n\n'
                'P.S: Рекомендую прочитать [мануал](https://telegra.ph/Klaudio-Naranho--Vash-pomoshchnik-po-tipologiyam-04-26) по использованию бота, чтобы повысить качество ответов.',
            reply_markup=kb.main_markup
        )
    
@base_router.message(Command(commands='clear'))
async def clear_history(message: Message, state: FSMContext):
    if message.chat.type == 'private':
        await state.set_state(ConfirmationState.confirm)
        await message.answer('❗️ Вы уверены, что хотите стереть историю чата? Это нельзя отменить.',
                            reply_markup=kb.confirm_markup)
    else:
        await db.clear_group_history(message.chat.id)
        await message.reply('История чата очищена. Наранхо забыл всё об этой группе.')


@base_router.message(Command(commands='delete'))
async def delete_user(message: Message):
    if message.chat.type != 'private':
        return
    await db.delete(message.from_user.id)
    await message.answer('Ваша запись полностью удалена из БД.')


@base_router.message(ConfirmationState.confirm)
async def confirmation_process(message: Message, state: FSMContext):
    if message.text == '✅Да':
        await db.clear_history(message.from_user.id)
        await message.answer('🗑 История чата успешно удалена. Теперь Наранхо ничего не помнит.',
                             reply_markup=kb.main_markup)
        await state.clear()
    elif message.text == '❌Нет':
        await message.answer('История чата не была очищена. Можете продолжать диалог.',
                             reply_markup=kb.main_markup)
        await state.clear()
    else:
        await message.answer('Пожалуйста, выберите действие.')
        

@base_router.message(Command(commands='cancel'))
async def cancel(message: Message, state: FSMContext):
    if message.chat.type == 'private':
        await state.clear()
        await db.set_busy_state(message.from_user.id, is_busy=False)
        await message.answer('✅ Ошибка исправлена, можете отправлять следующий запрос.')


@base_router.message(or_f(Command(commands='profile'), F.text == '👤 Профиль'))
async def profile(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    history_length = len(user.get('history', []))
    tags = ','.join(user.get('tags', "не распознаны").split(',')[:3]) + '...'
    await message.reply(text=f'*🫵 Это вы, @{message.from_user.username}:*\n'
                        f'│ 🆔: {md.code(user_id)}\n│ 📋 История: {history_length}/100 сообщений\n'
                        f'│ 📂 База знаний: {user.get('collection')}\n' + 
                        f'│ 🏷️ Теги: _{tags}_\n')


@base_router.message(or_f(Command(commands='settings'), F.text == '⚙️ Настройки'))
async def settings(message: Message, state: FSMContext):
    if message.chat.type == 'private':
        user_id = message.from_user.id
        curr_database = await db.get_collection(user_id)
        long_memory = await db.get_long_memory(user_id)
    else:
        user_id = message.chat.id
        curr_database = await db.get_collection(user_id, group=True)
        long_memory = await db.get_long_memory(user_id, group=True)
    markup = kb.settings_buttons(user_id, curr_database)
    msg = await message.answer('<b>Настройки Наранхо:</b>\n' +
                               f'📂 База знаний - <i>"{curr_database}"</i>\n' +
                               '   <i>Тык на кнопку папки для доп. информации о коллекции.</i>\n' +
                               (f'🧠 Долгая память: <i>{long_memory}</i>' if long_memory else '🧠 Нет записей в долгую память'),
                               reply_markup=markup, parse_mode='HTML')
    await state.set_data({'msg': msg, 'caller': message.from_user.id})


@base_router.callback_query(F.data.startswith('collection'))
async def set_database(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split('__')[-1]
    collection, uid = data.split('_')
    state_data = await state.get_data()
    if state_data['caller'] != callback.from_user.id:
        await callback.answer('Это не твоя кнопка. Брысь.')
        return
    await db.set_collection(int(uid), collection, group=uid.startswith('-100'))
    selection_msg = (await state.get_data())['msg']
    markup = kb.settings_buttons(uid, collection)
    long_memory = await db.get_long_memory(int(uid), group=uid.startswith('-100'))
    await selection_msg.edit_text('<b>Настройки Наранхо:</b>\n' +
                                f'📂 База знаний - <i>"{collection}"</i>\n' +
                                '   <i>Тык на кнопку папки для доп. информации о коллекции.</i>\n' +
                                (f'🧠 Долгая память: <i>{long_memory}</i>' if long_memory else '🧠 Нет записей в долгую память'),
                                reply_markup=markup, parse_mode='HTML')
    

@base_router.callback_query(F.data.startswith('colinfo'))
async def set_database(callback: CallbackQuery):
    collection = callback.data.split('__')[-1]
    data = {
        'dynamic': 'dynamic - динамическая база знаний, которая подстраивается под текущий запрос. Может работать не очень корректно - для долгой беседы рекомендуется ставить конкретную БЗ.',
        'ennea': 'ennea - база знаний эннеаграммы. Основана на учениях Наранхо.',
        'socionics': 'socionics - база знаний соционики. Используется модель А. Информация взята с wikisocion.',
        'psychosophy': 'psychosophy - база знаний психософии. Основана на трудах Афанасьева.',
        'ichazo': 'ichazo - база знаний поинтов Ичазо.'
    }
    await callback.answer(data[collection], show_alert=True)


@base_router.callback_query(F.data.startswith('long_memory'))
async def set_long_memory(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    if state_data['caller'] != callback.from_user.id:
        await callback.answer('Это не твоя кнопка. Брысь.')
        return
    await state.set_state(LongMemState.enter)
    await state.set_data({'uid': callback.from_user.id, 'msg': callback.message})
    await callback.message.edit_text('🧠 Введите новые данные в долгую память.\nДля отмены используйте точку.')


@base_router.callback_query(F.data.startswith('chunks'))
async def show_used_chunks(callback: CallbackQuery):
    message_id = int(callback.data.split('_')[-1])
    chunks = await db.get_chunks(message_id)
    
    text = '📄 <b>Здесь вы можете увидеть куски информации, найденной ботом в векторной базе знаний.</b>\n<a href="https://github.com/Gl0wdy/EnneAI/tree/main/data">👉 Посмотреть всю базу знаний бота</a>\n'
    for n, t in enumerate(chunks, 1):
        t = t.replace('\n\n', '\n')
        text += f'{n}. <blockquote expandable>{t[:300]}...</blockquote>\n'
    
    await callback.message.answer(text, parse_mode='HTML')
    await callback.answer()


@base_router.callback_query(F.data.startswith('star'))
async def handle_rate(callback: CallbackQuery, bot: Bot):
    stars = callback.data.split('_')[-1]
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f'Бота оценили на {stars} звёзд.'
    )
    await callback.message.answer('🌟')
    await callback.message.answer('Свои пожелания и предложения вы всегда можете высказать в нашем канале: @typologyAIchannel')
    await callback.message.delete()


@base_router.message(LongMemState.enter)
async def write_long_memory(message: Message, state: FSMContext):
    data = await state.get_data()
    collection = await db.get_collection(message.from_user.id)
    markup = kb.settings_buttons(message.from_user.id, collection)
    if data['uid'] != message.from_user.id:
        return
    if message.text != '.':
        if message.chat.type == 'private':
            await db.set_long_memory(message.from_user.id, message.text[:200])
        else:
            await db.set_long_memory(message.chat.id, message.text[:200], True)
    await data['msg'].delete()
    await message.reply('<b>Настройки Наранхо:</b>\n' +
                        f'📂 База знаний - <i>"{collection}"</i>\n' +
                        '   <i>Тык на кнопку папки для доп. информации о коллекции.</i>\n' +
                        f'🧠 Долгая память: <i>{message.text}</i>',
                        reply_markup=markup, parse_mode='HTML')
    await message.delete()
    await state.clear()
    await state.set_data(**data)


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


@base_router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    if message.chat.type != 'private':
        return
    caption = message.caption
    doc = message.document
    filename = doc.file_name or ""
    ext = filename.rsplit(".", 1)[-1].lower()

    if f".{ext}" not in SUPPORTED_EXTENSIONS:
        await message.answer(f"Неподдерживаемый формат. Отправьте: {', '.join(SUPPORTED_EXTENSIONS)}")
        return

    status_msg = await message.answer("*Читаю файл...*\n(1/3)")
    waiting_msg = await message.answer('📁')

    buffer = io.BytesIO()
    await bot.download(doc, destination=buffer)

    try:
        text = await reader.read(buffer, filename)
        text = f'{caption}:\n {text}'
    except Exception as e:
        await message.answer(f"Ошибка при чтении файла: {e}")
        return

    if not text.strip():
        await message.answer("Файл пустой или не удалось извлечь текст.")
        return
    
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        user = await db.save_message(user_id, 'system', 'юзер впервые взаимодействует с тобой, поздоровайся.')
    is_busy = user.get('busy')

    if is_busy:
        await message.answer('Дождитесь завершения предыдущего запроса.\nЗавис бот? Используй /cancel')
        return
    await db.set_busy_state(user_id, True)
    await db.save_message(user_id, 'user', text)
    chat_history = await db.get_history(user_id)

    selected_collection = user.get('collection')
    collection = selected_collection

    if collection == 'ichazo':
            await message.answer('Бу. Доступ к ичазо пока закрыт. Скоро этот режим будет доработан, о чем вы будете оповещены в канале: @typologyAIchannel')
            return
    
    await status_msg.edit_text(f'*Опросник принят.*\nПишу запрос к базе знаний... (2/3)')
    await waiting_msg.edit_text('✍️')

    rewritten_query = await chat.rewrite_query(text, chat_history)

    await status_msg.edit_text(f'*Готово*.\nИщу информацию в базе знаний по запросу: _{rewritten_query}_ (3/3)')
    await waiting_msg.edit_text('🔍')

    await message.bot.send_chat_action(user_id, ChatAction.TYPING)
    tags = user.get('tags', '')
    long_memory = user.get('long_memory', '')
    response, used_chunks = await chat.create(
        request=rewritten_query,
        collection=collection,
        chat_history=[{'role': 'system',
                        'content': f'ПОСТОЯННОЕ ХРАНИЛИЩЕ. ЗДЕСЬ ПОСТОЯННАЯ ИНФОРМАЦИЯ, ЗАПИСАННАЯ САМИМ ПОЛЬЗОВАТЕЛЕМ: {long_memory}'}] + chat_history,
        tags=tags
    )
    await status_msg.delete()
    await waiting_msg.delete()
    cleared = parse_system_info(response)
    await db.set_tags(user_id, cleared['tags'])

    if len(cleared['text']) >= 4096:
        chunked = [cleared['text'][:4090] + '...', '...' + cleared['text'][4090:]]
        first = await message.reply(chunked[0], parse_mode='Markdown')
        sent = await first.reply(chunked[1], parse_mode='Markdown')
    else:
        sent = await message.answer(cleared['text'], parse_mode='Markdown')

    await db.save_chunks(user_id, sent.message_id, used_chunks)
    await sent.edit_reply_markup(reply_markup=kb.ai_response_markup(sent.message_id))
    await db.save_message(user_id, 'system', cleared['text'])
    await db.set_busy_state(user_id, False)


@base_router.message(F.text | F.caption)
async def message_handler(message: Message):
    text = message.caption if message.caption else message.text
    if message.chat.type == 'private':
        user_id = message.from_user.id
        user = await db.get_user(user_id)
        if not user:
            user = await db.save_message(user_id, 'system', 'юзер впервые взаимодействует с тобой, поздоровайся.')
        is_busy = user.get('busy')

        if is_busy:
            await message.answer('Дождитесь завершения предыдущего запроса.\nЗавис бот? Используй /cancel')
            return
        await db.set_busy_state(user_id, True)
        await db.save_message(user_id, 'user', text)
        chat_history = await db.get_history(user_id)

        collection = user.get('collection')
        if collection == 'ichazo':
            await message.answer('Бу. Доступ к ичазо пока закрыт. Скоро этот режим будет доработан, о чем вы будете оповещены в канале: @typologyAIchannel')
            return

        hear_u = ['Запрос принят.', 'Услышал.', 'Интересно.', 'Хмм...']
        status_msg = await message.answer(f'*{random.choice(hear_u)}*\nПишу запрос к базе знаний, чтобы найти _лучшие_ результаты... (1/2)')
        await message.bot.send_chat_action(user_id, ChatAction.TYPING)
        waiting_msg = await message.answer('✍️')
        rewritten_query = await chat.rewrite_query(text, chat_history)
        if rewritten_query == 'None':
            await status_msg.edit_text(f'*Готово.* Дополнительной информации не требуется. (2/2)')
            await waiting_msg.edit_text('🤔')  
        else:
            await status_msg.edit_text(f'*Готово.*\nИщу информацию в базе знаний *{collection}* по запросу: _{rewritten_query}_... (2/2)') 
            await waiting_msg.edit_text('🔍')  
        await message.bot.send_chat_action(user_id, ChatAction.TYPING)
        
        tags = user.get('tags', '')
        long_memory = user.get('long_memory', '')
        response, used_chunks = await chat.create(
            request=rewritten_query,
            collection=collection,
            chat_history=[{'role': 'system',
                           'content': f'ПОСТОЯННОЕ ХРАНИЛИЩЕ. ЗДЕСЬ ПОСТОЯННАЯ ИНФОРМАЦИЯ, ЗАПИСАННАЯ САМИМ ПОЛЬЗОВАТЕЛЕМ: {long_memory}'}] + chat_history,
            tags=tags
        )
        await status_msg.delete()
        await waiting_msg.delete()
        cleared = parse_system_info(response)
        buttons = kb.create_buttons(cleared['buttons'])
        await db.set_tags(user_id, cleared['tags'])

        if len(cleared['text']) >= 4096:
            chunked = [cleared['text'][:4090] + '...', '...' + cleared['text'][4090:]]
            first = await message.reply(chunked[0], parse_mode='Markdown')
            sent = await first.reply(chunked[1], parse_mode='Markdown')
        else:
            sent = await message.answer(cleared['text'], parse_mode='Markdown')

        if rewritten_query != 'None':
            await sent.edit_reply_markup(reply_markup=kb.ai_response_markup(sent.message_id))
        await db.save_chunks(user_id, sent.message_id, used_chunks)
        await db.save_message(user_id, 'assistant', cleared['text'])
        await db.set_busy_state(user_id, False)

        last_review = user.get('last_review')
        if len(chat_history) + 1 == 20 and (not last_review or (datetime.now() - last_review) > timedelta(days=15)):
            await message.answer('🌟 *Привет! Предлагаю тебе оценить работу бота.*', 
                                 reply_markup=kb.rate_markup)
            await db.set_last_review(user_id)

        
    elif message.chat.type == 'supergroup':
        group_id = message.chat.id
        group = await db.get_group(group_id)
        bot = await message.bot.get_me()
        if not re.search(f'^@{bot.username}', message.text):
            await db.save_group_message(
                group_id=message.chat.id,
                username=f'{message.from_user.username} ({message.from_user.full_name})',
                role='system',
                content=message.text
            )
            return
        floodwait = group.get('floodwait', 10)
        last_request = await db.get_last_request(message.chat.id)
        if last_request:
            now = datetime.now()
            diff = (now - last_request).total_seconds()
            if diff < floodwait:
                await message.reply(f'*❌ Ограничение на всю группу:*\nподождите {int(floodwait - diff)} секунд перед следующим запросом.')
                return
            
        await db.set_last_request(message.chat.id)
        await db.save_group_message(
            group_id=message.chat.id,
            username=f'{message.from_user.username} ({message.from_user.full_name})',
            role='user',
            content=message.text
        )
        group_chat_history = await db.get_group_history(group_id)

        if (reply_to := message.reply_to_message):
            reply_to_text = reply_to.caption if reply_to.caption else reply_to.text
            reply_to_context = {
                'role': 'user',
                'content': f'[НА ЭТО СООБЩЕНИЕ ССЫЛАЕТСЯ ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ]\n@{reply_to.from_user.username}:\n{reply_to_text}'
            }
            group_chat_history.insert(-2, reply_to_context)

        waiting_msg = await message.reply('⏳')
        await message.bot.send_chat_action(chat_id=message.chat.id,
                                           action=ChatAction.TYPING,
                                           message_thread_id=message.message_thread_id)
        selected_collection = await db.get_collection(group_id, group=True)
        long_memory = group.get('long_memory', '')
        response, used_chunks = await chat.create(
            request=text.split(maxsplit=1)[-1],
            collection=selected_collection,
            chat_history=[{'role': 'system',
                           'content': f'ПОСТОЯННОЕ ХРАНИЛИЩЕ. ЗДЕСЬ ПОСТОЯННАЯ ИНФОРМАЦИЯ, ЗАПИСАННАЯ САМИМ ПОЛЬЗОВАТЕЛЕМ: {long_memory}'}] + group_chat_history,
            is_group=True
        )
        cleared = parse_system_info(response)
        await waiting_msg.delete()
        await db.save_group_message(
            group_id=message.chat.id, 
            username='typologyAIbot (you)',
            role='assistant',
            content=cleared['text']
        )
        await message.reply(f'<blockquote expandable>{cleared['text']}</blockquote>', parse_mode='HTML')


@base_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_group_adding(message: Message):
    await message.answer(text='*Я - Наранхо, и я могу помочь вам с типированием по эннеаграмме.*\n'
                                'Чтобы обратиться ко мне, просто отметь и задай свой вопрос. '
                                'Например: "@typologyAIbot типируй участников чата".\n'
                                'Также я способен читать историю чата в диапазоне ста сообщений.'
                                'Подробнее обо мне вы можете узнать в [мануале](https://telegra.ph/Klaudio-Naranho--Vash-pomoshchnik-po-tipologiyam-04-26)\n\n'
                                '*❗️ ДЛЯ КОРРЕКТНОЙ РАБОТЫ БОТА ЕМУ НУЖНО ВЫДАТЬ ПРАВА АДМИНА*')