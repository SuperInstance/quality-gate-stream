/**
 * Fleet Widget v1.0 — Embeddable Cocapn Fleet Client
 * Drop into any website to add live MUD exploration + tile submission.
 * Usage: <script src="http://147.224.38.131:4060/fleet.js"></script>
 *        <div id="fleet-widget"></div>
 */
(function() {
  const MUD = 'http://147.224.38.131:4042';
  const PLATO = 'http://147.224.38.131:8847';
  const TERMINAL = 'http://147.224.38.131:4060';
  
  // State
  let agent = null;
  let currentRoom = null;
  let history = [];
  let connected = false;

  // Fetch helper
  async function api(url) {
    try {
      const r = await fetch(url);
      return await r.json();
    } catch(e) {
      return { error: e.message };
    }
  }

  // Connect
  async function connect(name, job) {
    agent = name || 'web-user-' + Math.random().toString(36).slice(2,6);
    const data = await api(`${MUD}/connect?agent=${agent}&job=${job||'scholar'}`);
    if (data.room) {
      currentRoom = data.room;
      connected = true;
      addOutput('system', `Connected as ${agent} in ${data.room}`);
      if (data.description) addOutput('response', data.description);
      if (data.exits) addOutput('system', `Exits: ${data.exits.join(', ')}`);
      if (data.objects) addOutput('system', `Objects: ${data.objects.join(', ')}`);
    }
    return data;
  }

  // Look
  async function look() {
    if (!connected) return addOutput('error', 'Not connected. Type /connect first.');
    const data = await api(`${MUD}/look?agent=${agent}`);
    if (data.description) addOutput('response', data.description);
    if (data.exits) addOutput('system', `Exits: ${data.exits.join(', ')}`);
    if (data.objects) addOutput('system', `Objects: ${data.objects.join(', ')}`);
    return data;
  }

  // Move
  async function move(room) {
    if (!connected) return addOutput('error', 'Not connected.');
    const data = await api(`${MUD}/move?agent=${agent}&room=${room}`);
    if (data.room) {
      currentRoom = data.room;
      addOutput('cmd', `→ ${room}`);
      if (data.description) addOutput('response', data.description);
      if (data.exits) addOutput('system', `Exits: ${data.exits.join(', ')}`);
    } else {
      addOutput('error', data.error || `Can't move to ${room}`);
    }
    return data;
  }

  // Examine
  async function examine(obj) {
    if (!connected) return addOutput('error', 'Not connected.');
    const data = await api(`${MUD}/examine?agent=${agent}&object=${obj}`);
    if (data.description) addOutput('response', data.description);
    if (data.task) addOutput('agent', `Task: ${data.task}`);
    return data;
  }

  // Submit tile
  async function submitTile(domain, question, answer) {
    const data = await api(`${MUD}/submit/tile?agent=${agent}&domain=${domain}&question=${encodeURIComponent(question)}&answer=${encodeURIComponent(answer)}`);
    if (data.status === 'ok') addOutput('system', `✅ Tile submitted to ${domain}`);
    else addOutput('error', data.error || 'Tile submission failed');
    return data;
  }

  // Output
  function addOutput(type, text) {
    history.push({ type, text, time: Date.now() });
    if (widget.onOutput) widget.onOutput(type, text);
    const el = document.getElementById('fleet-output');
    if (el) {
      const div = document.createElement('div');
      div.className = 'fleet-line fleet-' + type;
      div.textContent = text;
      el.appendChild(div);
      el.scrollTop = el.scrollHeight;
    }
  }

  // Process command
  async function exec(input) {
    const cmd = input.trim();
    if (!cmd) return;
    addOutput('cmd', `> ${cmd}`);
    
    if (cmd === '/connect') return await connect();
    if (cmd.startsWith('/connect ')) return await connect(cmd.slice(9));
    if (cmd === '/look' || cmd === 'look') return await look();
    if (cmd === '/help') return addOutput('system', 'Commands: /connect [name], /look, move <room>, examine <obj>, /tasks, /status, /rooms');
    if (cmd === '/tasks') {
      if (!connected) return addOutput('error', 'Not connected.');
      const data = await api(`${MUD}/tasks?agent=${agent}`);
      if (data.tasks) data.tasks.forEach(t => addOutput('agent', `📋 ${t}`));
      return data;
    }
    if (cmd === '/status') {
      if (!connected) return addOutput('error', 'Not connected.');
      return addOutput('system', `Agent: ${agent} | Room: ${currentRoom} | History: ${history.length} entries`);
    }
    if (cmd === '/rooms') {
      const data = await api(`${MUD}/rooms`);
      if (data.rooms) data.rooms.forEach(r => addOutput('system', `  ${r}`));
      return data;
    }
    
    // Natural language: move/examine/look
    const moveMatch = cmd.match(/^(go|move|walk|enter)\s+(to\s+)?(.+)/i);
    if (moveMatch) return await move(moveMatch[3].trim());
    
    const examMatch = cmd.match(/^(examine|look at|inspect|check|study)\s+(.+)/i);
    if (examMatch) return await examine(examMatch[2].trim());
    
    if (cmd.match(/^(look around|look|l)$/i)) return await look();
    
    // Default: try examine
    return await examine(cmd);
  }

  // The widget object
  const widget = {
    connect, look, move, examine, submitTile, exec,
    getAgent: () => agent,
    getRoom: () => currentRoom,
    getHistory: () => history,
    onOutput: null,
    
    // Auto-mount to #fleet-widget
    mount(selector) {
      const container = document.querySelector(selector || '#fleet-widget');
      if (!container) return;
      
      container.innerHTML = `
        <div id="fleet-container" style="font-family:'Courier New',monospace;background:#0a0a0f;border:1px solid #1a1a2e;border-radius:8px;overflow:hidden;max-width:700px">
          <div style="background:#0d0d15;padding:.5em 1em;border-bottom:1px solid #1a1a2e;display:flex;justify-content:space-between;align-items:center">
            <span style="color:#7b1fa2;font-weight:700;font-size:.9em">🔮 Fleet Terminal</span>
            <span id="fleet-status" style="color:#666;font-size:.75em">Not connected</span>
          </div>
          <div id="fleet-output" style="padding:.8em 1em;height:300px;overflow-y:auto;font-size:.85em;line-height:1.6;color:#e0e0e0"></div>
          <div style="display:flex;gap:.4em;padding:.5em;border-top:1px solid #1a1a2e;background:#0d0d15">
            <input id="fleet-input" type="text" placeholder="Type a command..." style="flex:1;background:#12121a;border:1px solid #1a1a2e;color:#e0e0e0;padding:.4em .6em;font-family:inherit;font-size:.85em;border-radius:4px;outline:none">
            <button id="fleet-send" style="background:#7b1fa2;color:#0a0a0f;border:none;padding:.4em 1em;border-radius:4px;cursor:pointer;font-family:inherit;font-weight:600;font-size:.85em">Send</button>
          </div>
          <div style="display:flex;gap:.3em;padding:.3em .5em;flex-wrap:wrap;background:#0d0d15">
            <button class="fleet-quick" data-cmd="/connect">Connect</button>
            <button class="fleet-quick" data-cmd="/look">Look</button>
            <button class="fleet-quick" data-cmd="move forge">⚒️ Forge</button>
            <button class="fleet-quick" data-cmd="move bridge">🎛️ Bridge</button>
            <button class="fleet-quick" data-cmd="move arena-hall">🏟️ Arena</button>
            <button class="fleet-quick" data-cmd="move observatory">🔭 Observatory</button>
            <button class="fleet-quick" data-cmd="/help">Help</button>
          </div>
        </div>
      `;
      
      // Style quick buttons
      container.querySelectorAll('.fleet-quick').forEach(btn => {
        Object.assign(btn.style, {
          background:'#12121a', border:'1px solid #1a1a2e', color:'#888',
          padding:'.2em .5em', borderRadius:'3px', cursor:'pointer',
          fontFamily:'inherit', fontSize:'.75em'
        });
        btn.addEventListener('click', () => {
          const cmd = btn.dataset.cmd;
          document.getElementById('fleet-input').value = '';
          exec(cmd);
        });
      });
      
      // Input handling
      const input = document.getElementById('fleet-input');
      input.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
          exec(input.value);
          input.value = '';
        }
      });
      document.getElementById('fleet-send').addEventListener('click', () => {
        exec(input.value);
        input.value = '';
      });
      
      // Status updates
      widget.onOutput = () => {
        const s = document.getElementById('fleet-status');
        if (s) s.textContent = connected ? `${agent} @ ${currentRoom}` : 'Not connected';
      };
      
      addOutput('system', 'Welcome to the Cocapn Fleet Terminal. Type /connect to start exploring.');
    }
  };

  // Auto-mount
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => widget.mount());
  } else {
    // Don't auto-mount — let user call fleet.mount()
  }

  window.fleet = widget;
})();
