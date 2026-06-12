from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8952868227:AAHe4EIyhZhj_hpTuen7RAzNf7DPUYUcGxA"
ADMIN_ID = 545632565

PRICE_PER_GB = 15000
MIN_GB = 20

orders = {}
custom_mode = {}
awaiting_config = {}   # برای ارسال کانفیگ توسط ادمین


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 خرید سرویس", callback_data="buy")],
        [InlineKeyboardButton("🎧 پشتیبانی", callback_data="support")]
    ]

    await update.message.reply_text(
        "به ربات فروش VPN خوش آمدید 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- CALLBACK ----------------
async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    data = query.data

    if data == "buy":
        keyboard = [
            [InlineKeyboardButton("20", callback_data="20"),
             InlineKeyboardButton("50", callback_data="50")],
            [InlineKeyboardButton("100", callback_data="100")],
            [InlineKeyboardButton("✏️ دلخواه", callback_data="custom")]
        ]
        await query.message.reply_text("حجم رو انتخاب کن 👇", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "support":
        await query.message.reply_text("📞 @netgateconfig")

    elif data in ["20", "50", "100"]:
        gb = int(data)
        price = gb * PRICE_PER_GB
        orders[uid] = {"gb": gb, "price": price}
        await query.message.reply_text(
            f"📦 {gb} گیگ\n💰 {price:,} تومان\n\n"
            "💳 کارت: 6037-9972-6658-2635\n\n"
            "بعد از پرداخت رسید رو بفرست 📷"
        )

    elif data == "custom":
        custom_mode[uid] = True
        await query.message.reply_text("عدد گیگ رو بفرست (حداقل 20)")

    # تایید ادمین
    elif data.startswith("approve_"):
        if uid != ADMIN_ID:
            await query.message.reply_text("❌ دسترسی نداری")
            return

        target_uid = int(data.split("_")[1])
        order = orders.get(target_uid)

        if not order:
            await query.message.reply_text("❌ سفارش پیدا نشد")
            return

        gb = order["gb"]
        price = order["price"]

        await query.message.reply_text(
            f"✅ سفارش تایید شد\n\n"
            f"👤 کاربر: {target_uid}\n"
            f"📦 حجم: {gb} گیگ\n"
            f"💰 مبلغ: {price:,} تومان\n"
            f"💳 کارت: 6037-9972-6658-2635\n\n"
            "🔹 حالا کانفیگ رو بفرست (هر متنی که بفرستی دقیقاً همون به کاربر ارسال میشه):"
        )

        awaiting_config[ADMIN_ID] = target_uid

        await context.bot.send_message(
            chat_id=target_uid,
            text="🎉 پرداخت شما با موفقیت تایید شد!\n\n🔐 کانفیگ به‌زودی برای شما ارسال خواهد شد."
        )

        orders.pop(target_uid, None)


# ---------------- TEXT MESSAGES ----------------
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    # حالت حجم دلخواه
    if custom_mode.get(uid):
        try:
            gb = int(text)
            if gb < MIN_GB:
                await update.message.reply_text("❌ حداقل 20 گیگ")
                return
            price = gb * PRICE_PER_GB
            orders[uid] = {"gb": gb, "price": price}
            custom_mode.pop(uid)

            await update.message.reply_text(
                f"📦 {gb} گیگ\n💰 {price:,} تومان\n\n"
                "💳 کارت: 6037-9972-6658-2635\n\n"
                "بعد از پرداخت رسید رو بفرست 📷"
            )
        except:
            await update.message.reply_text("❌ فقط عدد بفرست")
        return

    # ارسال کانفیگ توسط ادمین (بدون هیچ متن اضافی)
    if uid == ADMIN_ID and ADMIN_ID in awaiting_config:
        target_uid = awaiting_config[ADMIN_ID]
        
        # حالا دقیقاً همون متنی که ادمین می‌فرسته به کاربر ارسال میشه
        await context.bot.send_message(chat_id=target_uid, text=text)
        
        await update.message.reply_text("✅ کانفیگ با موفقیت به کاربر ارسال شد.")
        awaiting_config.pop(ADMIN_ID)
        return


# ---------------- PHOTO (رسید) ----------------
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in orders:
        await update.message.reply_text("❌ اول یک سفارش ثبت کن")
        return

    gb = orders[uid]["gb"]
    price = orders[uid]["price"]

    await update.message.reply_text("📥 رسید دریافت شد\n⏳ منتظر تایید ادمین باشید")

    keyboard = [[InlineKeyboardButton("✅ تایید", callback_data=f"approve_{uid}")]]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"🧾 رسید جدید\n👤 کاربر: {uid}\n📦 {gb} گیگ\n💰 {price:,} تومان",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- RUN ----------------
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callback_router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
app.add_handler(MessageHandler(filters.PHOTO, photo))

app.run_polling()

