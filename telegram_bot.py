from datetime import datetime
from telegram.ext import Updater,CommandHandler,ConversationHandler,Filters,MessageHandler
from telegram import ReplyKeyboardMarkup, Update
import telegram.ext
import get_stock_info
import twstock as ts
import get_stock_history as gsh
import tools
import Infomation_type as info

updater = Updater(
    token='5725776094:AAHg3YJU6893cTHEq0Wdw7t9BpAeIcKh_L4',use_context=True
)
replay_keyboard = [['輸入/移除追蹤股票','追蹤清單'],['輸入查詢股票'],['結束']]

dispatcher = updater.dispatcher

markup = ReplyKeyboardMarkup(replay_keyboard)

CHOOSING, COMFIRM_STOCK, TYPING_CHOICE, COMFIRM_SEARCH_STOCK, TYPING_SEARCH_CHOICE = range(5)

def stop_telegram(updater:Updater):
    updater.stop()  # 停止推送任務
    print("telegram all stop")
def test(update,context):
    context.bot.send_message(chat_id=update.effective_chat.id,text='歡迎使用WooStockMan!!',reply_markup=markup)
    return CHOOSING
def wrong_command(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text='''
                             不好意思，我不懂你的意思。你可以點選對話框右手邊的選單來與我互動哦！
                             ''',
                             reply_markup=markup)
    return CHOOSING
def check_stock_list(update, context):
    List = get_stock_info.stock_list
    MSG = '你目前追蹤的標的如下：'
    for value in List.values():
        MSG = MSG + '\r\n{} {}'.format(value.number,value.name)
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text=MSG,
                             reply_markup=markup)
def input_stock(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='''
    請輸入你要追蹤股票代碼，若要移除已追蹤股票請在前方加上 - \r\n例如：-AAPL
    （回上一頁請輸入：q）
    ''')
    return TYPING_CHOICE
def input_search_stock(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='''
    請輸入你要查詢股票代碼\r\n
    （回上一頁請輸入：q）
    ''')
    return TYPING_SEARCH_CHOICE
def check_and_store(update:Update, context):
    Msg = update.message.text
    if  ts.codes.__contains__(Msg) == False:
        context.bot.send_message(chat_id=update.effective_chat.id, text='''
        查詢不到你輸入的股票代碼: {} 哦，要不要檢查一下該股票代碼是否有在股市場上市呢？再重新輸入一次吧！（回上一頁請輸入：q）
        '''.format(Msg))
        return TYPING_CHOICE
    stocklist_keyboard = [[Msg]]
    stocklist_markup = ReplyKeyboardMarkup(stocklist_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text='''
                              你查詢的結果如下，請問你想加入的是第幾支標的呢？\r\n（回上一頁請輸入：q）
                              ''',
                             reply_markup=stocklist_markup)
    return COMFIRM_STOCK
def search_check_and_store(update:Update, context):
    Msg = update.message.text
    if  ts.codes.__contains__(Msg) == False:
        context.bot.send_message(chat_id=update.effective_chat.id, text='''
        查詢不到你輸入的股票代碼: {} 哦，要不要檢查一下該股票代碼是否有在股市場上市呢？再重新輸入一次吧！（回上一頁請輸入：q）
        '''.format(Msg))
        return TYPING_SEARCH_CHOICE
    stocklist_keyboard = [[Msg]]
    stocklist_markup = ReplyKeyboardMarkup(stocklist_keyboard, one_time_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text='''
                              你查詢的結果如下，請問你想查詢的是第幾支標的呢？\r\n（回上一頁請輸入：q）
                              ''',
                             reply_markup=stocklist_markup)
    return COMFIRM_SEARCH_STOCK
def stock_added(update:Update, context):
    Msg = update.message.text
    List = get_stock_info.stock_list
    if List.__contains__(Msg):
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                 text='''
                                 你已經有追蹤 {} 囉！\r\n你追蹤的標的如下：\r\n{}
                                 '''.format(Msg, '\r\n'.join(List)),
                                 reply_markup=markup)
        return CHOOSING
    if get_stock_info.Add_stock_info(Msg):
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                text='''
                                已經成功加入 {} 到追蹤清單囉！\r\n請選擇你想查詢的服務🦉
                                '''.format(Msg),
                                reply_markup=markup)
        return CHOOSING
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                text='''
                                加入 {} 到追蹤清單失敗囉！\r\n請選擇你想查詢的服務🦉
                                '''.format(Msg),
                                reply_markup=markup)
        return CHOOSING
def stock_remove(update:Update, context):
    Msg = update.message.text[1:].upper()
    List = get_stock_info.stock_list
    if List.__contains__(Msg) == False:
        MSG = '你已經沒有追蹤 {} 囉！\r\n你追蹤的標的如下：'.format(Msg)
        for value in List.values():
            MSG = MSG + '\r\n{} {}'.format(value.number,value.name)
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                text=MSG,
                                reply_markup=markup)
        return CHOOSING
    if get_stock_info.Delet_stock_info(Msg):
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                text='''
                                已經成功刪除 {} 到追蹤清單囉！\r\n請選擇你想查詢的服務🦉
                                '''.format(Msg),
                                reply_markup=markup)
        return CHOOSING
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                text='''
                                刪除 {} 到追蹤清單失敗囉！\r\n請選擇你想查詢的服務🦉
                                '''.format(Msg),
                                reply_markup=markup)
        return CHOOSING
def stock_searched(update:Update, context):
    Msg = update.message.text
    stock_number = int(Msg)
    stock_info = get_stock_info.ts.codes[Msg]
    date = tools.DateTime2String(datetime.today())
    gsh.Stock_main.number = int(stock_number)
    # gsh.Stock_main.StartDate = tools.backWorkDays(datetime.today(),1)
    Open = gsh.Stock_main.get_PriceByDateAndType(tools.backWorkDays(date,0),info.Price_type.Open)
    High = gsh.Stock_main.get_PriceByDateAndType(tools.backWorkDays(date,0),info.Price_type.High)
    Low = gsh.Stock_main.get_PriceByDateAndType(tools.backWorkDays(date,0),info.Price_type.Low)
    Close = gsh.Stock_main.get_PriceByDateAndType(tools.backWorkDays(date,0),info.Price_type.Close)
    Volume = gsh.Stock_main.get_PriceByDateAndType(tools.backWorkDays(date,0),info.Price_type.Volume)
    context.bot.send_message(chat_id=update.effective_chat.id, 
                                text='''
                                {} {} \r\n OPEN: {} \r\n HIGH: {} \r\n LOW: {} \r\n CLOSE: {} \r\n VOLUME: {}
                                '''.format(Msg,stock_info.name,Open,High,Low,Close,Volume),
                                reply_markup=markup)
    return CHOOSING
def done(update, context):
    user_data = context.user_data
    if 'stock_list' in user_data:
        del user_data['stock_list']

    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text = "再見囉！希望有幫助到你！還需要我的話，請輸入 /test 我就會出現囉")

    user_data.clear()
    return ConversationHandler.END

# BOT互動訊息
test_handler = CommandHandler('test',test)
conv_handler = ConversationHandler(
    entry_points=[test_handler],
    states={
        CHOOSING:[  MessageHandler(Filters.regex('^'+ replay_keyboard[0][0] +'$') & ~(Filters.command | Filters.regex('^'+ replay_keyboard[2][0] +'$')),
                                        input_stock),
                    MessageHandler(Filters.regex('^'+ replay_keyboard[1][0] +'$') & ~(Filters.command | Filters.regex('^'+ replay_keyboard[2][0] +'$')),
                                        input_search_stock),
                    MessageHandler(Filters.regex('^'+ replay_keyboard[0][1] +'$') & ~(Filters.command | Filters.regex('^'+ replay_keyboard[2][0] +'$')),
                                        check_stock_list),
                    MessageHandler(~(Filters.command | Filters.regex('^'+ replay_keyboard[2][0] +'$')),
                                        test)],
        TYPING_CHOICE:[ MessageHandler(Filters.regex('^[A-z0-9]*$') & ~(Filters.command | Filters.regex('^[qQ]$')),
                                check_and_store),
                        MessageHandler(Filters.regex('^-[A-z0-9]*$') & ~(Filters.command | Filters.regex('^[qQ]$')),
                               stock_remove),
                        MessageHandler(Filters.regex('^q$') & ~(Filters.command),
                               test)],
        COMFIRM_STOCK:[ MessageHandler(Filters.regex('^[qQ]$') & ~(Filters.command),
                                test),
                        MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^[qQ]$')),
                               stock_added)],
        TYPING_SEARCH_CHOICE:[  MessageHandler(Filters.regex('^[A-z0-9]*$') & ~(Filters.command | Filters.regex('^[qQ]$')),
                                search_check_and_store),
                                MessageHandler(Filters.regex('^q$') & ~(Filters.command),
                               test)],
        COMFIRM_SEARCH_STOCK:[  MessageHandler(Filters.regex('^[qQ]$') & ~(Filters.command),
                                test),
                                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^[qQ]$')),
                               stock_searched)]
            },
    fallbacks=[MessageHandler(Filters.regex('^結束$'),done)]
    )
dispatcher.add_handler(conv_handler)# 新增推送任務
# 固定時間推送訊息
job = updater.job_queue

def count_time(context:telegram.ext.CallbackContext):
    return
    context.bot.send_message(chat_id=5249905251,text='現在過了{}秒鐘囉！'.format(60))
# 建立時間提醒 JobQueue 並執行
job.run_repeating(count_time, interval=60, first=0)

updater.start_polling()# 開始推送任務