import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import time

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SELECT_RECIPIENTS, ENTER_MESSAGE, ENTER_COUNT, CONFIRMATION = range(4)

class MailingBot:
    def __init__(self, token):
        self.token = token
        self.recipients = []
        self.message = ""
        self.count = 1
        self.delay = 1

    def start(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text("Отправь список получателей (username или ID через пробел):")
        return SELECT_RECIPIENTS

    def select_recipients(self, update: Update, context: CallbackContext) -> int:
        self.recipients = update.message.text.split()
        update.message.reply_text("Теперь отправь текст сообщения для рассылки:")
        return ENTER_MESSAGE

    def enter_message(self, update: Update, context: CallbackContext) -> int:
        self.message = update.message.text
        update.message.reply_text("Сколько раз отправить это сообщение каждому получателю?")
        return ENTER_COUNT

    def enter_count(self, update: Update, context: CallbackContext) -> int:
        try:
            self.count = int(update.message.text)
            if self.count <= 0:
                update.message.reply_text("Число должно быть положительным.")
                return ENTER_COUNT
            
            update.message.reply_text(f"Настройки:\nПолучатели: {', '.join(self.recipients)}\nСообщение: {self.message}\nКоличество: {self.count}\n\nОтправляем? (да/нет)")
            return CONFIRMATION
        except ValueError:
            update.message.reply_text("Введи число.")
            return ENTER_COUNT

    def confirmation(self, update: Update, context: CallbackContext) -> int:
        if update.message.text.lower() == 'да':
            update.message.reply_text("Начинаю рассылку...")
            self.start_mailing(update, context)
            return ConversationHandler.END
        else:
            update.message.reply_text("Отменено. /start - начать заново.")
            return ConversationHandler.END

    def start_mailing(self, update: Update, context: CallbackContext):
        sent = 0
        errors = 0
        
        for recipient in self.recipients:
            for _ in range(self.count):
                try:
                    context.bot.send_message(chat_id=recipient, text=self.message)
                    sent += 1
                    time.sleep(self.delay)
                except Exception as e:
                    errors += 1
                    logger.error(f"Ошибка: {e}")
        
        update.message.reply_text(f"Готово!\nУспешно: {sent}\nОшибок: {errors}")

    def cancel(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('Отменено. /start - начать заново.')
        return ConversationHandler.END

    def run(self):
        updater = Updater(self.token)
        dispatcher = updater.dispatcher

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                SELECT_RECIPIENTS: [MessageHandler(Filters.text & ~Filters.command, self.select_recipients)],
                ENTER_MESSAGE: [MessageHandler(Filters.text & ~Filters.command, self.enter_message)],
                ENTER_COUNT: [MessageHandler(Filters.text & ~Filters.command, self.enter_count)],
                CONFIRMATION: [MessageHandler(Filters.text & ~Filters.command, self.confirmation)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )

        dispatcher.add_handler(conv_handler)
        updater.start_polling()
        updater.idle()


if __name__ == '__main__':
    TOKEN = "ВАШ_ТОКЕН_БОТА"
    bot = MailingBot(TOKEN)
    bot.run()
