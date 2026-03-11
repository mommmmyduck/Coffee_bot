from aiogram import Bot
from services.user_service import get_staff_users
from services.order_service import get_order_by_id  # 👈 ДОБАВЛЯЕМ ИМПОРТ
from config import BOT_TOKEN

# services/notification_service.py

async def notify_staff_new_order(order):
    """
    Уведомить всех баристов и админов о новом заказе
    """
    bot = Bot(token=BOT_TOKEN)
    
    # Получаем свежий объект заказа
    from services.order_service import get_order_by_id
    fresh_order = await get_order_by_id(order.id)
    if not fresh_order:
        print(f"❌ Заказ {order.id} не найден в БД")
        await bot.session.close()
        return
    
    # Получаем всех сотрудников
    from services.user_service import get_staff_users
    staff_users = await get_staff_users()
    
    if not staff_users:
        await bot.session.close()
        return
    
    # Формируем сообщение
    text = "🔔 <b>Новый заказ!</b>\n\n"
    text += f"🆔 Заказ №{fresh_order.id}\n"
    text += f"💰 Сумма: {fresh_order.total_price} ₽\n\n"
    text += "📋 Состав:\n"
    
    for item in fresh_order.items:
        text += f"  • {item.product.name} x{item.quantity}\n"
        
        # Показываем кастомизацию если есть
        if item.customization:
            c = item.customization
            customizations = []
            
            if c.milk_type and c.milk_type != "regular":
                milk_names = {
                    "almond": "🌰 миндальное",
                    "coconut": "🥥 кокосовое",
                    "soy": "🌱 соевое",
                    "lactose_free": "🚫 безлактозное"
                }
                customizations.append(milk_names.get(c.milk_type, c.milk_type))
            
            if c.sugar_count > 0:
                sugar_emoji = {1: "🍬", 2: "🍬🍬", 3: "🍬🍬🍬"}
                customizations.append(f"{sugar_emoji.get(c.sugar_count, '🍬')} сахар {c.sugar_count}")
            
            if c.temperature:
                temp_names = {
                    "cold": "❄️ айс",
                    "warm": "🔥 тёплый",
                    "hot": "☕️ горячий"
                }
                customizations.append(temp_names.get(c.temperature, c.temperature))
            
            toppings = []
            if c.whipped_cream:
                toppings.append("🥛 сливки")
            if c.cinnamon:
                toppings.append("⚜️ корица")
            if c.cocoa:
                toppings.append("🍫 какао")
            if c.caramel_syrup:
                toppings.append("🍯 карамель")
            if c.vanilla_syrup:
                toppings.append("🌿 ваниль")
            
            if toppings:
                customizations.append("➕ " + ", ".join(toppings))
            
            if customizations:
                text += f"    <i>({', '.join(customizations)})</i>\n"
    
    
    # Отправляем уведомление каждому сотруднику
    for staff in staff_users:
        try:
            await bot.send_message(
                chat_id=staff.telegram_id,
                text=text,
                parse_mode="HTML"
            )
            print(f"✅ Уведомление отправлено сотруднику {staff.telegram_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления {staff.telegram_id}: {e}")
    
    await bot.session.close()


async def notify_staff_order_cancelled(order, cancelled_by_user=True):
    """
    Уведомить баристов об отмене заказа
    """
    bot = Bot(token=BOT_TOKEN)
    
    from services.order_service import get_order_by_id
    fresh_order = await get_order_by_id(order.id)
    if not fresh_order:
        print(f"❌ Заказ {order.id} не найден в БД")
        await bot.session.close()
        return
    
    from services.user_service import get_staff_users
    staff_users = await get_staff_users()
    
    if not staff_users:
        await bot.session.close()
        return
    
    who = "клиентом" if cancelled_by_user else "системой"
    
    text = f"❌ <b>Заказ №{fresh_order.id} отменён {who}</b>\n\n"
    text += f"💰 Сумма была: {fresh_order.total_price} ₽\n\n"
    text += "📋 Состав:\n"
    
    for item in fresh_order.items:
        text += f"  • {item.product.name} x{item.quantity}\n"
    
    # 👇 УБИРАЕМ информацию о клиенте
    
    for staff in staff_users:
        try:
            await bot.send_message(
                chat_id=staff.telegram_id,
                text=text,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления {staff.telegram_id}: {e}")
    
    await bot.session.close()