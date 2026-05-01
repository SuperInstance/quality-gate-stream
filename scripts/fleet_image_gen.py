#!/usr/bin/env python3
"""Fleet Image Generator — SiliconFlow image gen + vision judge loop"""
import json, urllib.request, os, sys, time

SFKEY = "[SF_KEY_REDACTED]"
SFURL = "https://api.siliconflow.com/v1"

MODELS = {
    "schnell": "black-forest-labs/FLUX.1-schnell",      # fastest, cheapest
    "flux11pro": "black-forest-labs/FLUX-1.1-pro",       # high quality
    "flux2flex": "black-forest-labs/FLUX.2-flex",        # newest
    "qwen-img": "Qwen/Qwen-Image",                       # Qwen image gen
}

def generate(prompt, model="schnell", size="1024x1024"):
    """Generate an image and return URL"""
    body = json.dumps({
        "model": MODELS.get(model, model),
        "prompt": prompt,
        "image_size": size,
        "num_inference_steps": 4 if "schnell" in model else 20,
    }).encode()
    
    req = urllib.request.Request(
        f"{SFURL}/images/generations",
        data=body,
        headers={
            "Authorization": f"Bearer {SFKEY}",
            "Content-Type": "application/json"
        }
    )
    
    resp = urllib.request.urlopen(req, timeout=60)
    data = json.loads(resp.read())
    
    if "images" in data:
        return data["images"][0]["url"]
    elif "data" in data:
        return data["data"][0]["url"]
    return None

def judge(image_url, criteria="Is this suitable as a tech company logo? Rate 1-10 and explain."):
    """Judge an image using Qwen3-VL vision model"""
    body = json.dumps({
        "model": "Qwen/Qwen3-VL-235B-A22B-Instruct",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": criteria}
            ]
        }],
        "max_tokens": 200,
    }).encode()
    
    req = urllib.request.Request(
        f"{SFURL}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {SFKEY}",
            "Content-Type": "application/json"
        }
    )
    
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read())
    
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    return "Judge failed"

def generate_and_judge(prompt, model="schnell", criteria=""):
    """Generate image, judge it, return both"""
    url = generate(prompt, model)
    if not url:
        return None, "Generation failed"
    
    time.sleep(1)
    judgment = judge(url, criteria or f"Rate this image 1-10. Prompt was: {prompt[:100]}")
    return url, judgment

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fleet_image_gen.py <prompt> [model] [size]")
        print(f"Models: {', '.join(MODELS.keys())}")
        sys.exit(1)
    
    prompt = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "schnell"
    size = sys.argv[3] if len(sys.argv) > 3 else "1024x1024"
    
    print(f"Generating with {model}...")
    url, judgment = generate_and_judge(prompt, model)
    
    print(f"\nImage URL: {url}")
    print(f"\nJudge says:\n{judgment}")
