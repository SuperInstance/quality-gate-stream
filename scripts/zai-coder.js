#!/usr/bin/env node
/**
 * zai-coder — Direct z.ai GLM coding agent
 * Usage: node zai-coder.js "<task>" [model]
 * 
 * Uses z.ai prepaid plan API (api.z.ai/api/coding/paas/v4)
 * Models: glm-4.5, glm-4.6, glm-4.7, glm-5, glm-5-turbo, glm-5.1
 */
const https = require('https');

const API_KEY = '80f38677d324450589c6d83c6d12fbbf.2zS6rTOyLCA1dqub';
const BASE_URL = 'api.z.ai';
const PATH = '/api/coding/paas/v4/chat/completions';

function chat(model, prompt, maxTokens = 4096) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({
            model,
            messages: [{ role: 'user', content: prompt }],
            max_tokens: maxTokens
        });

        const options = {
            hostname: BASE_URL,
            port: 443,
            path: PATH,
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${API_KEY}`,
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                try {
                    const result = JSON.parse(body);
                    if (result.error) {
                        reject(new Error(result.error.message || JSON.stringify(result.error)));
                        return;
                    }
                    const content = result.choices[0].message.content || '';
                    const reasoning = result.choices[0].message.reasoning_content || '';
                    resolve({ content, reasoning, raw: result });
                } catch (e) {
                    reject(new Error(body));
                }
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
    let model = 'glm-5.1';
    let task = '';
    
    // Parse --model flag
    const modelIdx = args.indexOf('--model');
    if (modelIdx !== -1 && args[modelIdx + 1]) {
        model = args[modelIdx + 1];
        args.splice(modelIdx, 2);
    }
    
    task = args.join(' ') || 'say hello in 2 words';
    
    try {
        const result = await chat(model, task);
        console.log(result.content);
        if (result.reasoning && process.argv.includes('--debug')) {
            console.error('\n--- Reasoning ---');
            console.error(result.reasoning);
        }
    } catch (e) {
        console.error('Error:', e.message);
        process.exit(1);
    }
}

main();