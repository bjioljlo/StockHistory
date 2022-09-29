from telegram.ext import Updater,CommandHandler,ConversationHandler,Filters,MessageHandler
from telegram import ReplyKeyboardMarkup
import telegram.ext

updater = Updater(
    token='5725776094:AAHg3YJU6893cTHEq0Wdw7t9BpAeIcKh_L4',use_context=True
)
replay_keyboard = [['追蹤清單'],['查詢線圖'],['結束']]

dispatcher = updater.dispatcher

markup = ReplyKeyboardMarkup(replay_keyboard)
CHOOSING, COMFIRM_STOCK, TYPING_CHOICE = range(3)

def test(update,context):
    context.bot.send_message(chat_id=update.effective_chat.id,text='歡迎使用WooStockMan!!',reply_markup=markup)
    return CHOOSING
def done(update, context):
    user_data = context.user_data
    if 'stock_list' in user_data:
        del user_data['stock_list']

    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text = "再見囉！希望有幫助到你！還需要我的話，請輸入 /test 我就會出現囉")

    user_data.clear()
    return ConversationHandler.END

test_handler = CommandHandler('test',test)
conv_handler = ConversationHandler(entry_points=[test_handler],states={
    CHOOSING:[],
    TYPING_CHOICE:[],
    COMFIRM_STOCK:[],},fallbacks=[MessageHandler(Filters.regex('^結束$'),done)])

test_handler = CommandHandler('test',test)
dispatcher.add_handler(conv_handler)

# updater.stop()  # 停止推送任務

job = updater.job_queue
conttimes = 0
def count_time(context:telegram.ext.CallbackContext):
    global conttimes
    conttimes += 5
    context.bot.send_message(chat_id=5249905251,text='現在過了{}秒鐘囉！'.format(conttimes))
# 建立時間提醒 JobQueue 並執行
job_count_minute = job.run_repeating(count_time, interval=5, first=0)    


updater.start_polling()# 開始推送任務