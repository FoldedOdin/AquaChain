// Quick WebSocket connection test
const WebSocket = require('ws');

const wsUrl = 'wss://nnznduptme.execute-api.ap-south-1.amazonaws.com/dev?topic=test';

console.log('Attempting to connect to:', wsUrl);

const ws = new WebSocket(wsUrl);

ws.on('open', () => {
  console.log('✅ Connected successfully!');
  ws.send(JSON.stringify({ type: 'ping' }));
});

ws.on('message', (data) => {
  console.log('📨 Received:', data.toString());
});

ws.on('error', (error) => {
  console.error('❌ Error:', error.message);
});

ws.on('close', (code, reason) => {
  console.log(`🔌 Closed: ${code} - ${reason}`);
});

setTimeout(() => {
  if (ws.readyState !== WebSocket.OPEN) {
    console.log('⏱️ Connection timeout - closing');
    ws.close();
  }
}, 5000);
