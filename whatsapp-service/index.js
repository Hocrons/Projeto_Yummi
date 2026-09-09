/**
 * Microsserviço local de envio de mensagens WhatsApp.
 */
const express = require("express");
const qrcode = require("qrcode-terminal");
const { Client, LocalAuth } = require("whatsapp-web.js");

const app = express();
app.use(express.json());

let conectado = false;

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: "./sessao" }),
  // Força uma versão estável do WhatsApp Web do RemoteAuth para evitar 'ProtocolError'
  webVersionCache: {
    type: "remote",
    remotePath:
      "https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2412.54.html",
  },
  puppeteer: {
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-accelerated-2d-canvas",
      "--no-first-run",
      "--no-zygote",
      "--disable-gpu",
    ],
  },
});

client.on("qr", (qr) => {
  console.log("\n=== Escaneie este QR Code com o WhatsApp do número 11959913833 ===");
  console.log("(Configurações > Aparelhos conectados > Conectar um aparelho)\n");
  qrcode.generate(qr, { small: true });
});

client.on("ready", () => {
  conectado = true;
  console.log("\n✅ WhatsApp conectado! Pronto para enviar códigos de verificação.\n");
});

client.on("disconnected", (motivo) => {
  conectado = false;
  console.log("\n⚠️  WhatsApp desconectado:", motivo, "\n");
});

client.initialize();

// ---------------------------------------------------------------
// API HTTP local, consumida pelo Flask
// ---------------------------------------------------------------
app.get("/status", (req, res) => {
  res.json({ conectado });
});

app.post("/enviar", async (req, res) => {
  if (!conectado) {
    return res.status(503).json({
      ok: false,
      erro: "WhatsApp ainda não conectado. Escaneie o QR Code exibido no terminal deste processo.",
    });
  }

  const { numero, mensagem } = req.body || {};
  if (!numero || !mensagem) {
    return res.status(400).json({ ok: false, erro: "Parâmetros 'numero' e 'mensagem' são obrigatórios." });
  }

  try {
    const chatId = `${numero}@c.us`;
    await client.sendMessage(chatId, mensagem);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ ok: false, erro: e.message });
  }
});

const PORTA = process.env.PORT || 3001;
app.listen(PORTA, () => {
  console.log(`Microsserviço de WhatsApp rodando em http://localhost:${PORTA}`);
});