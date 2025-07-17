const express = require('express');
const TelegramBot = require('node-telegram-bot-api');
const app = express();

app.use(express.static('.'));

// Токен бота (лучше использовать process.env.BOT_TOKEN)
const token = '7876336865:AAFO4jpGefQ9xF-oOq9x1kT3k1nXZNfaTRs';
const bot = new TelegramBot(token, { polling: true });

bot.on('message', (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(chatId, `Привет! Я @ukraine_cryptocoin_bot. Твой счёт пока не обновлён.`);
});

bot.on('webhook_data', (data) => {
  if (data.data) {
    const score = JSON.parse(data.data).score;
    bot.sendMessage(data.chat_id || data.from.id, `Твой счёт: ${score}!`);
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Сервер запущен на порту ${PORT}`);
});
