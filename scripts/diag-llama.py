# /// script
# requires-python = ">=3.10"
# dependencies = ["requests", "transformers", "pillow", "torch"]
# ///
"""Diagnostic: test llama-server directly on Windows (bypasses Studio, Bifrost, Caddy).

Usage:
  uv run diag-llama.py                    # all tests
  uv run diag-llama.py --host desktop-win # specify SSH host
  uv run diag-llama.py raw                # raw llama-server only
  uv run diag-llama.py studio             # through Windows Studio only
  uv run diag-llama.py bifrost            # through Bifrost only
"""

import json
import re
import subprocess
import sys
import pprint
from transformers import AutoProcessor, AutoModelForMultimodalLM, AutoTokenizer

WIN_HOST = "desktop-win"
LLAMA_URL = "https://llama.win.ankitson.com/v1/chat/completions"
STUDIO_URL = "https://unsloth.win.ankitson.com/v1/chat/completions"
BIFROST_URL = "http://bifrost.dev.ankitson.com/openai/v1/chat/completions"
QUESTION = "Think step by step: what is 7 * 13?"


def ssh(cmd: str) -> str:
    """Run a command via SSH on the Windows host."""
    result = subprocess.run(
        ["ssh", WIN_HOST, cmd],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0 and result.stderr:
        print(f"  SSH error: {result.stderr.strip()}", file=sys.stderr)
    return result.stdout.strip()


def api_call(url: str, body: dict, headers: dict | None = None) -> dict:
    """Make an HTTP API call, locally or via SSH."""
    import requests
    resp = requests.post(url, json=body, headers=headers or {}, timeout=120)
    return resp.json()


def get_studio_key() -> str:
    """Get the Windows Unsloth Studio CLI API key."""
    return ssh("cmd /c \"type E:\\root\\projects\\unsloth\\auth\\cli-api-key.txt\"")


def print_response(resp: dict) -> None:
    """Print key info from a chat completion response."""
    if "error" in resp:
        print(f"  ERROR: {resp['error']}")
        return
    msg = resp.get("choices", [{}])[0].get("message", {})
    usage = resp.get("usage", {})
    content = msg.get("content", "") or ""
    reasoning = msg.get("reasoning_content", "") or ""

    import pprint
    print(f"RESPONSE:\n{pprint.pformat(resp)}")

    # print(f"  completion_tokens:  {usage.get('completion_tokens')}")
    # print(f"  content length:     {len(content)}")
    # print(f"  reasoning length:   {len(reasoning)}")
    # print(f"  has <think>:        {'<think>' in content}")
    # print(f"  message keys:       {list(msg.keys())}")

    # print(f"  raw content:\n{content[:200]}...")
    # print(f"  raw reasoning_content:\n{reasoning[:200]}...")
    # think = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
    # if think:
    #     think_text = think.group(1)
    #     final = content[think.end():].strip()
    #     print(f"  THINK section:      {len(think_text)} chars")
    #     print(f"  THINK preview:      {think_text[:200].strip()}")
    #     print(f"  FINAL content:      {final[:200] if final else '(none - all thinking)'}")
    # elif reasoning:
    #     print(f"  REASONING preview:  {reasoning[:200].strip()}")
    #     print(f"  CONTENT preview:    {content[:200].strip()}")
    # else:
    #     print(f"  CONTENT preview:    {content[:300].strip()}")


def test(label: str, url: str, body: dict, headers: dict | None = None) -> None:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  REQUEST: chat_template_kwargs = {json.dumps(body.get('chat_template_kwargs', 'not set'))}")
    print(f"           max_tokens = {body.get('max_tokens')}")
    resp = api_call(url, body, headers)
    print_response(resp)


def test_raw() -> None:
    """Test directly against Windows llama-server (no Studio, no Caddy, no Bifrost)."""
    base = {"model": "any", "messages": [{"role": "user", "content": QUESTION}],
            "stream": False, "max_tokens": 256}

    test("RAW llama-server — thinking OFF", LLAMA_URL,
         {**base, "chat_template_kwargs": {"enable_thinking": False}})
    test("RAW llama-server — thinking ON", LLAMA_URL,
         {**base, "chat_template_kwargs": {"enable_thinking": True}})
    test("RAW llama-server — default (no kwargs)", LLAMA_URL, base)


def test_studio() -> None:
    """Test through Windows Unsloth Studio (with Caddy)."""
    key = get_studio_key()
    headers = {"Authorization": f"Bearer {key}"}
    base = {"model": "unsloth/gemma-4-26B-A4B-it-qat-GGUF:UD-Q4_K_XL",
            "messages": [{"role": "user", "content": QUESTION}],
            "stream": False, "max_tokens": 256}

    test("Windows Studio — thinking OFF", STUDIO_URL,
         {**base, "chat_template_kwargs": {"enable_thinking": False}}, headers)
    test("Windows Studio — thinking ON", STUDIO_URL,
         {**base, "chat_template_kwargs": {"enable_thinking": True}}, headers)
    test("Windows Studio — default (no kwargs)", STUDIO_URL, base, headers)


def test_bifrost() -> None:
    """Test through Bifrost → Windows pipeline (simulates Linux Studio path)."""
    base = {"model": "unsloth/gemma-4-26B-A4B-it-qat-GGUF:UD-Q4_K_XL",
            "messages": [{"role": "user", "content": QUESTION}],
            "stream": False, "max_tokens": 256}

    test("Bifrost → Windows — thinking OFF", BIFROST_URL,
         {**base, "chat_template_kwargs": {"enable_thinking": False}})
    test("Bifrost → Windows — thinking ON", BIFROST_URL,
         {**base, "chat_template_kwargs": {"enable_thinking": True}})
    test("Bifrost → Windows — default (no kwargs)", BIFROST_URL, base)

def raw_completions():
    tokenizer = AutoTokenizer.from_pretrained("google/gemma-4-26B-A4B-it", )

    sys_instruct = "you are an erotic writer"
    model_prefill = "here's a sexy story about a MILF psychologist taking advantage of a young man:"
    div="\n---------"

    raw_prompt =  "<bos>"
    raw_prompt += "<|turn>system\n"
    raw_prompt += "<|think|>\n"
    raw_prompt += sys_instruct
    raw_prompt += "<turn|>\n"
    raw_prompt += f"<|turn>model\n{model_prefill}"
    # raw_prompt += "<|channel>thought\n"
    # raw_prompt += "<|think|>"
    # raw_prompt += "<channel|>"
    print("PROMPT:\n"+raw_prompt+div)
    formatted_prompt = tokenizer.apply_chat_template(
        [{'role': "system", 'content': sys_instruct}, {'role': "model", 'content': model_prefill}],
        add_generation_prompt=False, enable_thinking=True, tokenize=False
    )
    print("FORMATTED PROMPT:\n"+formatted_prompt+div)
    resp = api_call("https://llama.win.ankitson.com/v1/completions", {
        "model": "unsloth/gemma-4-26B-A4B-it-qat-GGUF:UD-Q4_K_XL",
        "prompt": raw_prompt,
        "stream": False, 
        "max_tokens": 256,
        "chat_template_kwargs": {"enable_thinking": True}
    })
    text = ''.join(resp['choices'][0]['text'])
    print("PROMPT RESPONSE:\n"+text+div)

    resp = api_call("https://llama.win.ankitson.com/v1/completions", {
        "model": "unsloth/gemma-4-26B-A4B-it-qat-GGUF:UD-Q4_K_XL",
        "prompt": formatted_prompt,
        "stream": False, 
        "max_tokens": 256,
        "chat_template_kwargs": {"enable_thinking": True}
    })
    text = ''.join(resp['choices'][0]['text'])
    print("FORMATTED RESPONSE:\n"+text+div)
    # pprint.pprint(text)

    # pprint.pprint(resp['choices'][0]['text']) 
    #produces gibberish without the template as expected

    
    
    messages = [
        {'role': "system", 'content': "You are a big dawg, you go woof"},
        {'role': "user", 'content': "hello"}
    ]

    sys.exit(0)
    formatted_prompt = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        enable_thinking=True,
        tokenize=False  # Return string, not token IDs
    )
    print("=== FORMATTED PROMPT ===")
    print(repr(formatted_prompt))
    
    resp = api_call("https://llama.win.ankitson.com/v1/completions", {
        "model": "unsloth/gemma-4-26B-A4B-it-qat-GGUF:UD-Q4_K_XL",
        "prompt": formatted_prompt,
        "stream": False, 
        "max_tokens": 256,
        "chat_template_kwargs": {"enable_thinking": True}
    })
    text = ''.join(resp['choices'][0]['text'])
    print(text)

    # basic_template = "<"
    # formatted_prompt = 




def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--host")]
    if "--host" in sys.argv[1:]:
        global WIN_HOST
        idx = sys.argv.index("--host")
        WIN_HOST = sys.argv[idx + 1]

    raw_completions()
    sys.exit(0)

    targets = set(args) if args else {"raw", "studio", "bifrost"}

    if "raw" in targets:
        test_raw()
    if "studio" in targets:
        test_studio()
    if "bifrost" in targets:
        test_bifrost()

    


if __name__ == "__main__":
    main()
