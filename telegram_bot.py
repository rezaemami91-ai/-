import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import json
import logging
from scanner import OptionScanner

class TelegramBot:
    def __init__(self, config_path='config.json'):
        self.load_config(config_path)
        self.scanner = OptionScanner(config_path)
        self.setup_bot()
    
    def load_config(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.token = self.config['telegram']['token']
        self.chat_id = self.config['telegram']['chat_id']
    
    def setup_bot(self):
        self.bot = telegram.Bot(token=self.token)
        self.updater = Updater(token=self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CommandHandler("scan", self.scan_now))
        self.dispatcher.add_handler(CommandHandler("status", self.status))
        
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                           level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start(self, update, context):
        welcome_message = """
        🤖 ربات تحلیل فرصت‌های آپشن
        
        دستورات موجود:
        /start - نمایش این پیام
        /scan - اجرای اسکن فوری
        /status - وضعیت ربات
        
        ربات به طور خودکار هر ۵ دقیقه بازار را اسکن می‌کند و فرصت‌های معاملاتی را گزارش می‌دهد.
        """
        update.message.reply_text(welcome_message)
    
    def scan_now(self, update, context):
        update.message.reply_text("🔍 در حال اسکن بازار...")
        
        try:
            options_data = self.scanner.scan_all_sites()
            opportunities = self.scanner.analyze_opportunities(options_data)
            
            if opportunities:
                message = "🎯 فرصت‌های شناسایی شده:\n\n"
                for i, opp in enumerate(opportunities[:5], 1):
                    option = opp['option']
                    message += f"{i}. {option.get('symbol', 'N/A')}\n"
                    message += f"   نوع: {option.get('type', 'N/A')}\n"
                    message += f"   قیمت: {option.get('price', 'N/A')}\n"
                    message += f"   حجم: {option.get('volume', 'N/A')}\n"
                    message += f"   امتیاز: {opp['score']}/5\n"
                    message += f"   سیگنال‌ها: {', '.join(opp['signals'])}\n\n"
                
                update.message.reply_text(message)
                self.scanner.save_results(opportunities)
            else:
                update.message.reply_text("⚠️ هیچ فرصت معاملاتی شناسایی نشد.")
                
        except Exception as e:
            update.message.reply_text(f"❌ خطا در اسکن: {str(e)}")
    
    def status(self, update, context):
        status_msg = """
        📊 وضعیت ربات:
        
        ✅ فعال
        🔄 اسکن خودکار: هر ۵ دقیقه
        📡 تعداد سایت‌های تحت نظارت: ۵
        ⏰ آخرین بروزرسانی: در حال اجرا
        """
        update.message.reply_text(status_msg)
  def send_alert(self, message):
        try:
            self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
            return False
    
    def start_polling(self):
        self.updater.start_polling()
        self.updater.idle()
