from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.utils.decorators import admin_required
from bot.states.broadcast_states import BroadcastStates
from services.broadcast_service import broadcast_promotion

router = Router()

# -----------------------
# Главное меню рассылки
# -----------------------

@router.message(F.text == "📢 Рассылка")
@admin_required
async def show_broadcast_menu(message: Message):
    """Меню рассылки акций"""
    text = "📢 <b>Рассылка акций</b>\n\n"
    text += "Отправьте акцию всем покупателям с картинкой и текстом.\n"
    text += "Например: 'Покажи это сообщение на кассе — получи скидку 20%!'"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✉️ Создать рассылку",
            callback_data="broadcast_start"
        )],
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "broadcast_start")
@admin_required
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Начать создание рассылки"""
    text = "📝 <b>Шаг 1/3: Текст акции</b>\n\n"
    text += "Введите текст, который увидят клиенты:\n\n"
    text += "Пример:\n"
    text += "<i>🎉 Специальное предложение!\n"
    text += "Покажи это сообщение на кассе и получи скидку 20% на любой кофе!\n"
    text += "Акция действует до конца дня.</i>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")]
    ])
    
    await state.set_state(BroadcastStates.enter_text)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.message(BroadcastStates.enter_text)
@admin_required
async def broadcast_enter_text(message: Message, state: FSMContext):
    """Сохранить текст и запросить картинку"""
    text = message.text.strip()
    
    if len(text) < 10:
        await message.answer("❌ Текст слишком короткий. Введите хотя бы 10 символов:")
        return
    
    await state.update_data(broadcast_text=text)
    await state.set_state(BroadcastStates.upload_image)
    
    response_text = "✅ Текст сохранён!\n\n"
    response_text += "📸 <b>Шаг 2/3: Картинка</b>\n\n"
    response_text += "Отправьте картинку для акции\n"
    response_text += "(или отправьте '—' чтобы пропустить):"
    
    await message.answer(response_text, parse_mode="HTML")


@router.message(BroadcastStates.upload_image, F.photo)
@admin_required
async def broadcast_upload_image(message: Message, state: FSMContext):
    """Сохранить картинку и показать превью"""
    photo_id = message.photo[-1].file_id
    
    await state.update_data(broadcast_image=photo_id)
    
    # Переход к подтверждению
    await show_broadcast_preview(message, state)


@router.message(BroadcastStates.upload_image, F.text)
@admin_required
async def broadcast_skip_image(message: Message, state: FSMContext):
    """Пропустить картинку"""
    if message.text.strip() == "—":
        await state.update_data(broadcast_image=None)
        await show_broadcast_preview(message, state)
    else:
        await message.answer("📸 Отправьте картинку или '—' для пропуска:")


async def show_broadcast_preview(message: Message, state: FSMContext):
    """Показать превью рассылки"""
    data = await state.get_data()
    text = data['broadcast_text']
    image_id = data.get('broadcast_image')
    
    await state.set_state(BroadcastStates.confirm)
    
    preview_text = "👀 <b>Шаг 3/3: Подтверждение</b>\n\n"
    preview_text += "Так будет выглядеть ваша рассылка:\n\n"
    preview_text += "━━━━━━━━━━━━━━━━━━━━\n"
    preview_text += text
    preview_text += "\n━━━━━━━━━━━━━━━━━━━━\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Отправить всем",
            callback_data="broadcast_confirm"
        )],
        [InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="broadcast_cancel"
        )],
    ])
    
    if image_id:
        await message.answer_photo(
            photo=image_id,
            caption=preview_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text=preview_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@router.callback_query(F.data == "broadcast_confirm")
@admin_required
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтвердить и отправить рассылку"""
    data = await state.get_data()
    text = data['broadcast_text']
    image_id = data.get('broadcast_image')
    
    await callback.answer("📤 Отправляю рассылку...")
    
    # Отправляем рассылку
    stats = await broadcast_promotion(text, image_id)
    
    result_text = "✅ <b>Рассылка завершена!</b>\n\n"
    result_text += f"📊 Статистика:\n"
    result_text += f"✅ Успешно: {stats['success']}\n"
    result_text += f"❌ Ошибок: {stats['errors']}\n"
    result_text += f"📊 Всего пользователей: {stats['total']}"
    
    await callback.message.answer(result_text, parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data == "broadcast_cancel")
@admin_required
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Отменить рассылку"""
    await state.clear()
    await callback.message.edit_text("❌ Рассылка отменена")
    await callback.answer()