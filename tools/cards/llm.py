"""Shared by the card-builder steps that call a model: one chat call through OpenRouter (temperature 0, minimal reasoning).
The key is read only from the environment variable OPENROUTER_API_KEY and is never printed. Env MC_CARD_MODEL (default
z-ai/glm-5.3-flash, the model of the reported cards; the provider pin of the original run is sent only for the default model) and
OPENROUTER_BASE (default https://openrouter.ai/api/v1)."""
import json
import os
import urllib.request

ROOT = os.environ.get('MC_ROOT') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
WORK = os.path.join(ROOT, 'work', 'cards')
DEFAULT_MODEL = 'z-ai/glm-5.3-flash'
MODEL = os.environ.get('MC_CARD_MODEL') or DEFAULT_MODEL
BASE = os.environ.get('OPENROUTER_BASE', 'https://openrouter.ai/api/v1')


def key():
    k = os.environ.get('OPENROUTER_API_KEY')
    if not k:
        raise SystemExit('OPENROUTER_API_KEY is not set in the environment: nothing was called.')
    return k


def chat(content, max_tokens, timeout=600):
    """Returns (answer text, cost in USD)."""
    body = {'model': MODEL, 'messages': [{'role': 'user', 'content': content}], 'temperature': 0, 'max_tokens': max_tokens,
            'reasoning': {'effort': 'minimal'}}
    if MODEL == DEFAULT_MODEL:
        body['provider'] = {'order': ['relace'], 'allow_fallbacks': False}
    r = urllib.request.Request(BASE.rstrip('/') + '/chat/completions', data=json.dumps(body).encode(),
                               headers={'Authorization': 'Bearer ' + key(), 'Content-Type': 'application/json'})
    j = json.load(urllib.request.urlopen(r, timeout=timeout))
    return j['choices'][0]['message'].get('content') or '', (j.get('usage') or {}).get('cost') or 0
