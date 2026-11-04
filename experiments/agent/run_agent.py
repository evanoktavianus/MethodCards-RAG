"""Shared pieces of the Ours arms (agent_cards.py): the document-search service (`VM`, set by run_main.py) and the formatting of a document read."""
import sys
sys.path.insert(0,(__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+'/experiments/baselines')
sys.path.insert(0,(__import__('os').environ.get('MC_ROOT') or __import__('os').path.abspath(__import__('os').path.join(__import__('os').path.dirname(__file__),'..','..')))+'/tools/retrieval')
import run_baselines as rb
import embed_queries as eq
try:from client import VMPool as VMSearch   # the document-search service of the Ours arms of the reported runs (a PostgreSQL service; not distributed)
except ImportError:   # in this repository: the same index served from files (tools/retrieval/local_docs.py; needs the document files, see MC_DOCS_DIR)
    from local_docs import LocalDocsPool as VMSearch
pr=rb.pr;rp=rb.rp
VM=None   # set by run_main.py
def fmt_read(d):
    if 'error' in d:return 'ERROR: '+str(d['error'])
    body='\n\n'.join(f"[chunk {c['chunk_index']}, p.{c['page']}] {c['text']}" for c in d['chunks'])
    return f"{d['title']} (chunks {d['total_chunks']} in total; next start={d.get('next_start_chunk')})\n{body}"
