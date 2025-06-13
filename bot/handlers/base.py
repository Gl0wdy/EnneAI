from aiogram import Router, F
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, JOIN_TRANSITION, or_f
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatAction, ChatMemberStatus
from aiogram.fsm.context import FSMContext
from aiogram.utils import markdown as md

import bot.database as db
import bot.keyboards as kb
from bot.fsm import ConfirmationState, LongMemState
from ai.completions import Chat
from ai.utils import parse_system_info

import re
from datetime import datetime, timedelta
from io import BytesIO
import fitz
import whisper
from pydub import AudioSegment
import asyncio
import ffmpeg
import numpy as np

model = whisper.load_model("base")
base_router = Router(name='main')
chat = Chat()


@base_router.message(CommandStart())
async def start_command(message: Message):
    start_args = message.text.split()
    uid = message.from_user.id
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
                'Просто напиши мне вопрос или выбери один из предложенных!\n\n'
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
    is_premium = await db.get_status(user_id)
    tags = ','.join(user.get('tags', "не распознаны").split(',')[:3]) + '...'
    end_date = user.get('end_date')
    days_left = (end_date - datetime.now()).days if is_premium else 0
    await message.reply(text=f'*🫵 Это вы, @{message.from_user.username}:*\n'
                        f'│ 🆔: {md.code(user_id)}\n│ 📋 История: {history_length}/{"160" if is_premium else "80"} сообщений\n'
                        f'│ 📂 База знаний: {user.get('collection')}\n' + 
                        f'│ 🏷️ Теги: _{tags}_\n' +
                        (f'│ 👑 VIP до {end_date.strftime('%d.%m.%Y')} ({days_left + 1} д.)' if is_premium else ''),
                        reply_markup=kb.premium_markup)


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
        'psychosophy': 'psychosophy - база знаний психософии. Основана на трудах Афанасьева.'
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


@base_router.callback_query(F.data.startswith('watch'))
async def watch_menu(callback: CallbackQuery):
    menu = callback.data.split('__')[-1]
    user = await db.get_user(callback.from_user.id)
    ref_count = user.get("ref_count", 5)
    menus = {
        'premium': '*👑 Премиум подписка открывает многие возможности:*\n' +
                '1. Расширение лимитов - _лимит истории сообщений увеличен с 80 до 160_\n' +
                '2. Чтение опросников - _позволяет отправлять pdf-файлы с опросниками без лимита на количество символов. ' +
                'Сам опросник сохраняется в вашей истории, благодаря чему его можно обсудить еще глубже._\n' +
                '3. Распознавание голосовых сообщений - _тут объяснять нечего..._\n' +
                '4. Функция "вне очереди" - _позволяет "пройти" через очередь даже во время нагрузок на бота. Ответ бота гарантирован._\n' +
                'Помимо всего прочего, новые функции будут доступны премиум юзерам _сразу_ после их выхода.\n' +
                'Из интересного: в будущем для VIP-юзеров планируется добавить типирование по [семантике речи](https://vk.com/@e.vasilevs-shpargalka-po-semantike-rechi-dlya-opredeleniya-sociotipa)...\n\n' +
                '*💸 Текущая цена на подписку: 250₽/месяц.* Купить можно через [бусти](https://boosty.to/enneai/donate) - [оформление через ЛС](https://t.me/m/KCKTEdqAM2Iy)',

        'ref':  '*👥 Реферальная программа позволяет получить премиум на 1 день за каждого приглашенного пользователя.*\n' +
                f'Ваша ссылка: `t.me/typologyAIbot?start={callback.from_user.id}` - отправьте её другу!\n' +
                'Учтите, что премиум вы получите только за _новых пользователей_, никогда не пользовавшихся ботом.\n' +
                (f'\n*Переходов осталось: {5 - ref_count}*') if ref_count else 'Вы исчерпали максимальное кол-во реферальных переходов.'
    }

    await callback.message.edit_text(menus[menu], reply_markup=kb.premium_markup)


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


@base_router.message(F.text | F.caption | F.document)
async def message_handler(message: Message):
    text = message.caption if message.caption else message.text
    if message.chat.type == 'private':
        user_id = message.from_user.id
        user = await db.get_user(user_id)
        if not user:
            user = await db.save_message(user_id, 'system', 'юзер впервые взаимодействует с тобой, поздоровайся.')
            print(user)
        is_busy = user.get('busy')
        is_premium = await db.get_status(user_id)
        doc = message.document
        if doc and not is_premium:
            await message.answer('🔒 Чтение файлов доступно только с премиум подпиской.')
            return
        if doc:
            file_id = message.document.file_id
            file = await message.bot.download(file_id)
            buffer = BytesIO(file.read())
            with fitz.open(stream=buffer.read(), filetype="pdf") as doc:
                text = message.caption + ':\n\n'
                for page in doc:
                    text += page.get_text()

        if is_busy:
            await message.answer('Дождитесь завершения предыдущего запроса.\nЗавис бот? Используй /cancel')
            return
        await db.set_busy_state(user_id, True)
        await db.save_message(user_id, 'user', text, is_premium)
        chat_history = await db.get_history(user_id)

        selected_collection = user.get('collection')
        if selected_collection == 'dynamic':
            collection = await chat.vector_db.classify_search(text)
            status_msg = await message.answer(f'✅ *Запрос принят.* Запрос отнесён к базе знаний "{collection}"\n_Настроить используемую базу знаний - /settings_')
        else:
            collection = selected_collection
            status_msg = await message.answer(f'*✅ Запрос принят.* Используемая база знаний - "{collection}"')
        waiting_msg = await message.answer('⌛️')
        await message.bot.send_chat_action(user_id, ChatAction.TYPING)
        tags = user.get('tags', '')
        long_memory = user.get('long_memory', '')
        response = await chat.create(
            request=text,
            collection=collection,
            chat_history=[{'role': 'system',
                           'content': f'ПОСТОЯННОЕ ХРАНИЛИЩЕ. ЗДЕСЬ ПОСТОЯННАЯ ИНФОРМАЦИЯ, ЗАПИСАННАЯ САМИМ ПОЛЬЗОВАТЕЛЕМ: {long_memory}'}] + chat_history,
            premium=is_premium,
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
            await first.reply(chunked[1], parse_mode='Markdown', reply_markup=buttons)
        else:
            await message.answer(cleared['text'], parse_mode='Markdown', reply_markup=buttons)

        await db.save_message(user_id, 'system', cleared['text'], is_premium)
        await db.set_busy_state(user_id, False)
        
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
        response = await chat.create(
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


@base_router.message(F.voice)
async def speesh_recognize(message: Message):
    if message.chat.type != 'private':
        return
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    is_premium = user.get('premium')
    if not is_premium:
        await message.answer('🔒 Голосовые сообщения доступны только с премиум подпиской.')
        return
    await db.set_busy_state(user_id, True)

    status = await message.answer('*🗣 Распознаю голос...*')
    voice = message.voice
    file = await message.bot.download(voice.file_id)
    ogg_data = BytesIO(file.read())

    def convert_and_transcribe(ogg_data: BytesIO) -> str:
        ogg_data.seek(0)
        audio = AudioSegment.from_file(ogg_data, format="ogg")
        wav_io = BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)

        out, _ = (
            ffmpeg
            .input('pipe:0')
            .output('pipe:1', format='s16le', acodec='pcm_s16le', ac=1, ar='16000')
            .run(input=wav_io.read(), capture_stdout=True, capture_stderr=True)
        )
        audio_data = np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0

        result = model.transcribe(audio_data, language="ru")
        return result["text"]

    result_text = await asyncio.to_thread(convert_and_transcribe, ogg_data)
    sandglasses = await message.answer('⏳')
    await db.save_message(user_id, 'user', result_text, is_premium)

    collection = user.get('collection')
    if collection == 'dynamic':
        collection = await chat.vector_db.classify_search(message.text)
        status = await status.edit_text(f'<b>✅ Запрос распознан как:</b>\n<blockquote>{result_text}</blockquote>\nЗапрос отнесён к базе знаний "{collection}"\n<i>Настроить используемую базу знаний - /settings</i>',
                                      parse_mode='HTML')
    else:
        collection = collection
        status = await status.edit_text(f'<b>✅ Запрос распознан как:</b>\n<blockquote>{result_text}</blockquote>\nИспользуемая база знаний - "{collection}"',
                                      parse_mode='HTML')
    chat_history = await db.get_history(user_id)

    response = await chat.create(result_text, collection, chat_history, False, is_premium)
    cleared = parse_system_info(response)
    buttons = kb.create_buttons(buttons)

    await sandglasses.delete()
    await status.delete()
    if len(cleared['text']) >= 4096:
        chunked = [cleared['text'][:4090] + '...', '...' + cleared['text'][4090:]]
        first = await message.reply(chunked[0], parse_mode='Markdown')
        await first.reply(chunked[1], parse_mode='Markdown', reply_markup=buttons)
    else:
        await message.answer(cleared['text'], parse_mode='Markdown', reply_markup=buttons)
    await db.set_busy_state(user_id, False)


@base_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_group_adding(message: Message):
    await message.answer(text='*Я - Наранхо, и я могу помочь вам с типированием по эннеаграмме.*\n'
                                'Чтобы обратиться ко мне, просто отметь и задай свой вопрос. '
                                'Например: "@typologyAIbot типируй участников чата".\n'
                                'Также я способен читать историю чата в диапазоне ста сообщений.'
                                'Подробнее обо мне вы можете узнать в [мануале](https://telegra.ph/Klaudio-Naranho--Vash-pomoshchnik-po-tipologiyam-04-26)\n\n'
                                '*❗️ ДЛЯ КОРРЕКТНОЙ РАБОТЫ БОТА ЕМУ НУЖНО ВЫДАТЬ ПРАВА АДМИНА*')