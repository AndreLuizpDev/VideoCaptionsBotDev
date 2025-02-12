import telebot
import pika
import configparser
import i18n

config = configparser.ConfigParser()
config.read('bot.conf')
TOKEN = config['TELEGRAM']['BOT_TOKEN']
RABBITCONNECT = config['RABBITMQ']['CONNECTION_STRING']

bot = telebot.TeleBot(TOKEN)

def get_text(message, arg):
    i18n.load_path.append("i18n")
    i18n.set("fallback", "en-us")
    user_lang = message.from_user.language_code.lower()
    return i18n.t(arg, locale=user_lang)

def add_to_line(message):
    rabbitmq_con = pika.BlockingConnection(pika.URLParameters(RABBITCONNECT))
    rabbit = rabbitmq_con.channel()
    rabbit.queue_declare(queue='VideoCaptionsBot', durable=True)
    rabbit.basic_publish(
        exchange='',
        routing_key='VideoCaptionsBot',
        body=str(message),
        properties=pika.BasicProperties(
            delivery_mode = pika.spec.PERSISTENT_DELIVERY_MODE
        )
    )
    rabbitmq_con.close()

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(
        message.from_user.id,
        get_text(message, 'bot.cmd_start'),
        parse_mode='HTML'
    )

@bot.message_handler(content_types=['video', 'document', 'video_note'])
def get_video(message):
    add_to_line(message)
    bot.send_message(
        message.from_user.id,
        get_text(message, 'bot.please_wait')
    )

if __name__ == "__main__":
    bot.infinity_polling()
