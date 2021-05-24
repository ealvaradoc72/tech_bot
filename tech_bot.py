import logging 
import os
import telegram
import sys
import pandas as pd
import pprint
from dateparser.search import search_dates


from telegram.ext import Updater, updater, CommandHandler, MessageHandler,Filters
from transformers import pipeline

#from telegram.ext.messagehandler import MessageHandler

#conf logging
contexto = ""

logging.basicConfig(
    level= logging.INFO, format="%(asctime)s - %(name)s -%(levelname)s - %(message)s,"
)

logger = logging.getLogger()

#Solictar token
TOKEN = os.getenv("TOKEN")
mode = os.getenv("MODE")

if mode == "dev":
    def run(updater):
        updater.start_polling()
        print("BOT CARGADO")
        updater.idle()
elif mode == "prod":
    def run(udpater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        udpater.start_webhook(listen= "0.0.0.0", port= PORT, url_path=TOKEN)
        updater.bot.set_webhook(f"https://{HEROKU_APP_NAME}.herokuapp.com/{TOKEN}")
else:
    logger.info("no se especifico el MODE")
    sys.exit

def getMonth(i):
    meses = ('enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre')
    return meses[i-1]

def start(update, context):
    global contexto
    contexto = None
    logger.info(f"El usuario {update.effective_user['username']}, ha iniciado una conversaciíon")
    name = update.effective_user['first_name']
    update.message.reply_text(f"Hola {name}  yo soy tu bot, te contestaré una pregunta sobre la mañanera, escoge una fecha!")
    print(update)

def echo(update, context):
    #Debo detectar si me estan preguntando por una fecha, para regresar el texto y luego esperar pregunta
   
    user_id = update.effective_user['id']
    logger.info(f"El usuario {user_id}, ha enviado un mensaje")

    text = update.message.text

    #En la variable contexto tengo datos si ya hay una pregunta
    global contexto
    if contexto:
        texto = contexto
        context.bot.sendMessage(
            chat_id = user_id,
            parse_mode = "HTML",
            text = f"<b> Espera estoy investigando .... </b> "
            )

        nlp = pipeline(
            'question-answering', 
    #        model='mrm8488/distill-bert-base-spanish-wwm-cased-finetuned-spa-squad2-es',
            model='mrm8488/electricidad-small-finetuned-squadv1-es',
            tokenizer=(
    #            'mrm8488/distill-bert-base-spanish-wwm-cased-finetuned-spa-squad2-es',  
                'mrm8488/electricidad-small-finetuned-squadv1-es',  
                {"use_fast": False}
            )
        )

        pregunta = text
        respuesta = nlp({'question': pregunta, 'context': texto})
        print(respuesta['answer'])
        context.bot.sendMessage(
            chat_id = user_id,
            parse_mode = "HTML",
            text = f"<b>{pregunta} </b>\n {respuesta['answer']} \n\n Has otra pregunta o <b> /start </b> para empezar de nuevo"
            )
        return 

    encontrada = search_dates(text)
    if (encontrada):
        fecha = encontrada[0][1]
        url = f"https://raw.githubusercontent.com/NOSTRODATA/conferencias_matutinas_amlo/master/{fecha.year}/{fecha.month}-{fecha.year}/{getMonth(fecha.month)}%20{fecha.day}%2C%20{fecha.year}/mananera_{fecha.day}_{fecha.month:02d}_{fecha.year}.csv"
        try:
            df = pd.read_csv(url)
            ind = min(df.index[df.Participante != df.Participante[0]]) - 1
            contexto = "\n".join(df.Texto[:ind])
            print(contexto)
            context.bot.sendMessage(
                chat_id = user_id,
                parse_mode = "HTML",
                text = f"<b>Esto fue lo que encontré </b> \n\n {contexto}\n\n\n  <b> Haz una pregunta sobre este fragmento de texto, (no olvides los signos ¿?) </b> "
                )
        except:
            context.bot.sendMessage(
                chat_id = user_id,
                parse_mode = "HTML",
                text = f"<b>No encontré mañanera ese día, escoge otra fecha </b>"
                )
    else:
        print("No reconocí la fecha")

    #primero voy a clasificar la pregunta sobre las categorias que ya tengo precargadas
    

if __name__ == "__main__":
    #obtener datos del bot
    my_bot = telegram.Bot(token = TOKEN)

    print("Datos del bot" , my_bot.getMe())

    updater = Updater(my_bot.token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, echo))

    run(updater)