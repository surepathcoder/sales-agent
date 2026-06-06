/**
 * WhatsApp Web.js sidecar service for Kijani AI.
 * One session per tenant_id. Communicates with FastAPI backend via HTTP.
 */
const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const QRCode = require('qrcode');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 8001;
const SESSION_PATH = process.env.SESSION_PATH || './sessions';

const clients = new Map();
const qrCodes = new Map();
const statuses = new Map();

function getClient(tenantId) {
  if (clients.has(tenantId)) return clients.get(tenantId);

  const client = new Client({
    authStrategy: new LocalAuth({ clientId: tenantId, dataPath: SESSION_PATH }),
    puppeteer: { headless: true, args: ['--no-sandbox'] },
  });

  client.on('qr', async (qr) => {
    qrCodes.set(tenantId, await QRCode.toDataURL(qr));
    statuses.set(tenantId, 'qr_required');
  });

  client.on('ready', () => {
    statuses.set(tenantId, 'connected');
    qrCodes.delete(tenantId);
  });

  client.on('message', async (msg) => {
    const backendUrl = process.env.BACKEND_WEBHOOK_URL || 'http://backend:8000/api/v1/webhooks/whatsapp';
    try {
      await fetch(backendUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: tenantId,
          from_number: msg.from.replace('@c.us', ''),
          message: msg.body,
          message_id: msg.id?.id,
        }),
      });
    } catch (err) {
      console.error('Inbound webhook forward failed:', err.message);
    }
  });

  client.on('disconnected', () => {
    statuses.set(tenantId, 'disconnected');
    clients.delete(tenantId);
  });

  client.initialize().catch((err) => {
    console.error(`WhatsApp init failed for ${tenantId}:`, err);
    statuses.set(tenantId, 'error');
  });

  clients.set(tenantId, client);
  statuses.set(tenantId, 'initializing');
  return client;
}

app.get('/health', (_, res) => res.json({ status: 'ok' }));

app.get('/status/:tenantId', (req, res) => {
  const { tenantId } = req.params;
  res.json({ tenant_id: tenantId, status: statuses.get(tenantId) || 'not_initialized' });
});

app.get('/qr/:tenantId', (req, res) => {
  const { tenantId } = req.params;
  getClient(tenantId);
  res.json({ qr: qrCodes.get(tenantId) || null, status: statuses.get(tenantId) });
});

app.post('/send', async (req, res) => {
  const { tenant_id, to, message } = req.body;
  if (!tenant_id || !to || !message) {
    return res.status(400).json({ error: 'tenant_id, to, message required' });
  }

  const client = getClient(tenant_id);
  if (statuses.get(tenant_id) !== 'connected') {
    return res.json({ status: 'queued', id: `pending-${Date.now()}`, mock: true });
  }

  try {
    const chatId = to.includes('@') ? to : `${to.replace(/\D/g, '')}@c.us`;
    const result = await client.sendMessage(chatId, message);
    res.json({ status: 'sent', id: result.id.id });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => console.log(`WhatsApp service on :${PORT}`));
