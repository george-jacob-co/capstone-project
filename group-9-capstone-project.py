import telegram.ext
import pandas as pd
import requests
from bs4 import BeautifulSoup
from forex_python.converter import CurrencyRates

#API key is the token to the telegram bot
API_KEY = '5572195495:AAELnUKso6pj6foVmAc_KZocCfbXMQqCEAs'

updater = telegram.ext.Updater(API_KEY, use_context=True)
disp = updater.dispatcher

#this function is to obtain the text from an html website
def getdata(url):
    r = requests.get(url)
    return r.text

htmldata = getdata(
    'https://autotraveler.ru/en/spravka/fuel-price-in-europe.html#.Yt4j4egzaUk'
)
#Beautiful Soup pulls data from the html, turning them into string
soup = BeautifulSoup(htmldata, 'html.parser')\

# Declare string var and list
mydatastr = ''
result = []

# searching all tr in the html data, storing as a string
for table in soup.find_all('tr'):
    mydatastr += table.get_text()
#preparing the data by placing them into a list
mydatastr = mydatastr[1:]
itemlist = mydatastr.split('\n\n')

#-46 removes all the unnecessary data from the website
for item in itemlist[:-46]:
    result.append(item.split('\n'))

df = pd.DataFrame(result[1:])
#removes an extra column that was the numbering of the website
df.drop(0, inplace=True, axis=1)
df.columns = ['Country', 'E5', 'E5 Super Plus', 'B7 Diesel']

#some data sets from the website were empty
def empty(x):
    if x == " ":
        return "Unavailable"
    else:
        return x
df["E5"]= df["E5"].apply(empty)
df["E5 Super Plus"]= df["E5 Super Plus"].apply(empty)
df["B7 Diesel"]= df["B7 Diesel"].apply(empty)

#adds an extra column for currency shortcuts
def converter(x):
    Currency= { 'Austria': 'EUR', 'Azerbaijan': 'EUR', 'Albania':'EUR', 'Andorra':'EUR', 'Armenia':'EUR', 'Belarus':'EUR', 'Belgium':'EUR', 'Bulgaria':'BGN', 'Bosnia andHerzegovina':'EUR', 
               'Great Britain': 'GBP','Hungary':'HUF','Germany':'EUR', 'Greece': 'EUR', 'Georgia':'EUR', 'Denmark':'DKK', 'Ireland':'EUR', 'Iceland':'ISK', 'Spain':'EUR', 'Italy':'EUR', 'Cyprus':'EUR',
               'Latvia':'EUR', 'Lithuania':'EUR', 'Luxembourg':'EUR','NorthMacedonia': 'EUR', 'Malta':'EUR', 'Moldova': 'EUR', 'Netherlands' :'EUR', 'Norway':'NOK', 'Poland':'PLN', 'Portugal':'EUR', 'Romania':'RON',
               'Serbia': 'EUR', 'Slovakia':'EUR', 'Slovenia':'EUR', 'Turkey': 'TRY', 'Ukraine':'EUR', 'Finland':'EUR', 'France':'EUR', 'Croatia': 'HRK', 'Montenegro':'EUR', 'CzechRepublic':'CZK', 'Switzerland':'CHF',
               'Sweden': 'SEK', 'Estonia':'EUR', 'Russia':'EUR'
              }
    return Currency[x]

df['Currency']= df['Country'].apply(converter)

#removes spaces. This will be useful later once we use .split
df["Country"]=df["Country"].replace("Great Britain", "GreatBritain", regex=True)
df["Country"]=df["Country"].replace("Bosnia andHerzegovina", "BosniaandHerzegovina", regex=True)
#creates start button for bot to introduce itself
def start(update, context):
    update.message.reply_text("Hello! This is GasDaddy. \U00002764\n\nHere, I will be helping you retrieve the latest information on gas prices in the EU.\n\nTo get started, try using ""/help"" in order to find what you're looking for\U00002755")
#help button that introduces all the commands possible
def help(update, context):
  update.message.reply_text("Here are the gas types that are available: \n\n E5, E5 Super Plus, B7 Diesel \n\n Here are the list of functions you need to know: \n\n /start ---> Greetings \n /help  ---> This message \n\nTo choose what EU country and gas type:\n\nSimply type either both the country and the gas type or just the country.\n\nExample: France E5 or France\U00002714 \n\nTo convert chosen gas type to domestic currency:\n\nSimply type convert with both the country and gas type.\n\n Example: convert Germany E5\U00002714\n\n However, please note that some countries are in Euro as their local currency can not be converted.\U00002764 \n\n Gas Up!\U00002b50")
# send price determines what country/type of gas user is looking for
def send_price(update, context):
  #splits message to determine what the use is looking for
  a = update.message.text.split(" ")
  #just the country, relays all fuel prices
  if len(a)== 1:
    if a[0] in list(df["Country"]):
      #locates the entire row, showing all prices
      response= df.loc[df["Country"] == a[0]]
      #removes unnecessary data such as other numbers and spaces, and types of fuel not asked for by the user
      b= response.to_string(header=False).split(" ",4)
      reply=b[4]
      update.message.reply_text(f"Here are the gas prices for {a[0]}\n\n Types of Gas: E5, E5 Super Plus, B7 Diesel\n\n {reply}\n\n Feel free to keep messaging Gas Daddy for more fuel updates\U00002728 ")
  #country and type of fuel, relays a particular price for the fuel type in that country
  if len(a)>= 2:
    #split(" ",1) ensures that longer fuels still work
    z= update.message.text.split(" ",1)
    if z[0] in list(df["Country"]) and z[1] in list(df.columns):
      #locates the entire row, showing all prices
      response2 = df.loc[df["Country"] == z[0], [z[1]]]
      b =response2.to_string(header=False).split(" ",2)
      #shows the prices just for the selected gas type
      reply= b[2]
      update.message.reply_text(f"Here is the price of {a[1]}  in {a[0]} \n\n {reply} \n\n Feel free to keep messaging Gas Daddy for more fuel updates\U00002728 ")
  #for the converter
  if a[0] == 'convert':
     #split(" ",2) ensures that longer fuels still work
    y= update.message.text.split(" ",2)
    #locates specific price for the country, and gas type
    response3 = df.loc[df["Country"] == y[1], [y[2]]]
    b =response3.to_string(header=False).split(" ",2)
    reply= b[2]
    #some data sets are unavailable
    if reply == 'Unavailable':
      update.message.reply_text("No Data")
    if reply != 'Unavailable':
      response4 = df.loc[df["Country"] == y[1], ["Currency"]]
      #removes unnecessary informtion
      c= response4.to_string(header=False).split(" ", 2)
      acronym= c[2]
      #filters reply (reduces multiple prices for the 3 gas types to just 1 price)
      rate= CurrencyRates().get_rate('EUR', acronym) 
      #makes it just a number so that we can multiply it
      d=reply.split(" ")
      value= float(rate)*float(d[1])
      update.message.reply_text(f"Here is the final price of {a[2]} in {a[1]} for the local currency\n\n {value} {acronym}\n\n Feel free to keep messaging Gas Daddy for more fuel updates\U00002728")
#handlers are what make the bots respond. CommandHandler needs /, MessageHandler does not
disp.add_handler(telegram.ext.CommandHandler("start", start))
disp.add_handler(telegram.ext.CommandHandler("help", help))

disp.add_handler(
    telegram.ext.MessageHandler(telegram.ext.Filters.text, send_price))

#polling keeps refreshing the messages to see if any of the handlers are called
updater.start_polling()
updater.idle()
