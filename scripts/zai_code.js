const https = require('https');
const fs = require('fs');

const API_KEY = '80f38677d324450589c6d83c6d12fbbf.2zS6rTOyLCA1dqub';
const MODEL = 'glm-5.1';
const PATH = '/api/coding/paas/v4/chat/completions';

function chat(model, prompt, maxTokens = 4096) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({
            model,
            messages: [{ role: 'user', content: prompt }],
            max_tokens: maxTokens
        });
        const options = {
            hostname: 'api.z.ai', port: 443, path: PATH, method: 'POST',
            headers: { 'Authorization': `Bearer ${API_KEY}`, 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
        };
        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', c => body += c);
            res.on('end', () => {
                try {
                    const r = JSON.parse(body);
                    if (r.error) { reject(new Error(r.error.message)); return; }
                    const msg = r.choices[0].message;
                    resolve({ content: msg.content || '', reasoning: msg.reasoning_content || '', raw: r });
                } catch(e) { reject(new Error(body)); }
            });
        });
        req.on('error', reject);
        req.setTimeout(180000, () => { req.destroy(); reject(new Error('timeout')); });
        req.write(data);
        req.end();
    });
}

async function main() {
    const args = process.argv.slice(2);
    let task = args.join(' ');
    let savePath = null;
    
    if (args.includes('--file')) {
        const idx = args.indexOf('--file');
        savePath = args[idx + 1];
        task = args.slice(0, idx).join(' ');
    }
    
    if (!task) {
        console.error('Usage: node zai_code.js "<task>" [--file <path>]');
        process.exit(1);
    }
    
    const result = await chat(MODEL, task);
    const output = result.content || result.reasoning;
    
    if (savePath && output) {
        fs.writeFileSync(savePath, output);
        console.log(`Saved to ${savePath} (${output.length} chars)`);
    } else {
        console.log(output);
    }
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });