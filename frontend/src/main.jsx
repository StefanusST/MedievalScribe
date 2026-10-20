import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';
import { topics, generateLine } from './samples';

function App() {
  const [text,setText] = useState(() => generateLine(topics[0]));
  const mode = 'shakespeare';
  const [lastSamples,setLastSamples] = useState({});
  const [address,setAddress] = useState('singular');
  const [result,setResult] = useState(null);
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const [copied,setCopied] = useState(false);
  const [filter,setFilter] = useState(false);
  async function translate(e) {
    e.preventDefault(); setBusy(true); setError(''); setCopied(false); setResult(null);
    const controller = new AbortController();
    const timeout = setTimeout(()=>controller.abort(),30000);
    try {
      const response = await fetch('/api/translate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,address,mode}),signal:controller.signal});
      if(!response.ok) throw new Error(response.status === 422 ? 'Please enter between 1 and 10,000 characters.' : 'The Python server could not complete this request. Check the server logs.');
      setResult(await response.json());
    } catch(e) {setError(e.name==='AbortError'?'The request timed out. Please try again.':e.message==='Failed to fetch'?'Cannot reach the Python API. Start the backend and try again.':e.message);}
    finally {clearTimeout(timeout);setBusy(false);}
  }
  async function copy() {
    try {await navigator.clipboard.writeText(result.translation);setCopied(true);} catch {setError('Clipboard unavailable. Select the translated text to copy it.');}
  }
  const rows = result?.tokens.filter(t=>!filter || t.changed) || [];
  return <main>
    <nav><span className="brand">✦ &nbsp; MEDIEVAL SCRIBE</span><span className="pill">A PYTHON + REACT EXPERIMENT</span></nav>
    <header><span className="eyebrow">OLD WORDS. NEW POSSIBILITIES.</span><h1>A little less modern.<br/><em>A little more timeless.</em></h1><p>Turn everyday English into readable, Shakespeare-inspired prose.<br/>Then look beneath the parchment to see the NLP at work.</p></header>
    <form onSubmit={translate}>
      <div className="workspace">
        <section className="panel"><div className="panel-head"><h2><span>01</span> The present</h2><span>MODERN ENGLISH</span></div>
          <label className="sr-only" htmlFor="source">Modern English text</label>
          <textarea id="source" value={text} disabled={busy} maxLength={10000} onChange={e=>{setText(e.target.value);setResult(null);}} placeholder="Write your tale here…"/>
          <div className="input-foot"><span>{text.length.toLocaleString()} / 10,000</span><button type="button" className="text-button" disabled={busy} onClick={()=>{setText('');setResult(null);setError('');}}>Clear</button></div>
        </section>
        <section className="panel parchment" aria-live="polite"><div className="panel-head"><h2><span>02</span> The past</h2><span>SHAKESPEARE STYLE</span></div>
          <div className={'output '+(!result?'muted':'')}>{busy?'The scribe is at work…':result?.translation || 'Thy words await their transformation.'}</div>
          <div className="input-foot"><span>{result?`${result.stats.changed} tokens transformed`:'A new voice for your words'}</span><button type="button" className="text-button" disabled={!result||busy} onClick={copy}>{copied?'Copied ✓':'Copy text'}</button></div>
        </section>
      </div>
      <div className="controls"><span className="pill">Mode: Shakespeare</span><label>Who is “you”? <select value={address} disabled={busy} onChange={e=>{setAddress(e.target.value);setResult(null);}}><option value="singular">One person · thou / thee</option><option value="plural">Several people · ye / you</option></select></label><button className="primary" disabled={busy||!text.trim()}>{busy?'Translating…':'Translate thy words'} <span>→</span></button></div>
    </form>
    <div className="samples"><span>TRY A LINE</span>{topics.map(topic=><button key={topic.name} type="button" disabled={busy} onClick={()=>{const next = generateLine(topic, lastSamples[topic.name] || text);setLastSamples(prev=>({...prev,[topic.name]:next}));setText(next);setResult(null);setError('');setCopied(false);}} title={`Generate another ${topic.name.toLowerCase()} example`}>{topic.name} ↻</button>)}</div>
    {error && <p role="alert" className="error">{error}</p>}
    <section className="analysis"><div className="section-title"><div><span className="eyebrow">BENEATH THE PARCHMENT</span><h2>The anatomy of a sentence</h2></div><span className="pill">EXPLAINABLE NLP</span></div>
      <div className="steps">{[['01','Tokenize','Split sentences and words.'],['02','POS tag','Identify grammatical roles.'],['03','Stem + lemmatize','Compare roots and base forms.'],['04','Transform','Apply vocabulary and grammar rules.']].map(([n,t,d])=><div key={n}><span>{n}</span><h3>{t}</h3><p>{d}</p></div>)}</div>
      {result ? <><div className="table-toolbar"><span>{result.stats.sentences} sentences · {result.stats.tokens} tokens · {result.stats.phrases} phrase matches</span><label><input type="checkbox" checked={filter} onChange={e=>setFilter(e.target.checked)}/> Changed only</label></div><div className="table-wrap"><table><caption className="sr-only">NLP analysis of the normalized input</caption><thead><tr>{['Token','POS','Stem','Lemma','Output','Rule'].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{rows.map((t,i)=><tr key={i} className={t.changed?'changed':''}><td>{t.token}</td><td><code>{t.pos}</code></td><td>{t.stem}</td><td>{t.lemma}</td><td title={t.phrase ? `Phrase output: ${t.phrase.output}` : undefined}>{t.phrase && !t.phrase.first ? "↳ part of phrase" : t.replacement}</td><td>{t.rule}</td></tr>)}</tbody></table>{!rows.length&&<p>No changed tokens.</p>}</div><details><summary>View normalized text and raw API response</summary><p>{result.normalized}</p><pre>{JSON.stringify(result,null,2)}</pre></details></>:<p className="empty">Translate a passage to explore each token, its root, and the rule behind its transformation.</p>}
    </section>
    {result && <section className="analysis"><h2>Shakespeare dialogue examples</h2><p>Related dialogue retrieved from train.csv by word overlap. These are character replies, NOT translations of the modern dialogue or your input.</p>{result.corpus_examples.length ? result.corpus_examples.map(e=><details key={e.id}><summary>{e.id} · {e.matched_terms} matching words</summary><p><strong>Modern dialogue:</strong> {e.modern_dialogue}</p><p><strong>Shakespeare reply:</strong> {e.shakespeare_reply}</p></details>) : <p>No matching dialogue found.</p>}</section>}
    <footer><strong>A note from the scribe.</strong> Shakespeare mode uses vocabulary and grammar rules, with related dialogue from the uploaded Shakespeare corpus. It does not train a translation model. Example lines are randomly combined from local templates. Complex grammar may need editing. Stems are shown for learning; lemmas and POS tags guide conversion.</footer>
  </main>;
}
createRoot(document.getElementById('root')).render(<App/>);
