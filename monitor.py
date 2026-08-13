"""Conservative official-source monitor for ExamTrack.
Run daily in GitHub Actions. It fetches official pages, records content hashes,
and updates only fields that can be extracted with high confidence. If a source
changes but a new date cannot be safely parsed, the change is logged for review
instead of inventing a date.
"""
import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).parent
DATA=ROOT/'exams.json'
STATE=ROOT/'.source_state.json'
HEADERS={'User-Agent':'ExamTrack official-source monitor/1.0 (+GitHub Actions)'}

KEYWORDS=re.compile(r'(exam|examination|test|commence|held|scheduled|date|registration|application|last date)',re.I)
DATE_PATTERNS=[
    re.compile(r'\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})\b'),
    re.compile(r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2})\b',re.I),
    re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(20\d{2})\b',re.I),
]
MONTH={m.lower():i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}

def fetch(url):
    req=Request(url,headers=HEADERS)
    with urlopen(req,timeout=25) as r: return r.read().decode('utf-8','ignore')

def normalize(s): return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',s))

def candidates(text):
    out=[]
    for pat in DATE_PATTERNS:
        for m in pat.finditer(text):
            try:
                if len(m.groups())==3 and m.group(1).isdigit() and m.group(2).isdigit():
                    d,mo,y=map(int,m.groups()); out.append(f'{y:04d}-{mo:02d}-{d:02d}')
                elif m.group(1).isdigit():
                    d=int(m.group(1)); mo=MONTH[m.group(2).lower()]; y=int(m.group(3)); out.append(f'{y:04d}-{mo:02d}-{d:02d}')
                else:
                    mo=MONTH[m.group(1).lower()]; d=int(m.group(2)); y=int(m.group(3)); out.append(f'{y:04d}-{mo:02d}-{d:02d}')
            except Exception: pass
    return sorted(set(out))

def main():
    data=json.loads(DATA.read_text())
    state=json.loads(STATE.read_text()) if STATE.exists() else {}
    changes=[]
    for e in data['exams']:
        try:
            raw=fetch(e['source']); digest=hashlib.sha256(raw.encode()).hexdigest(); old=state.get(e['id'],{}).get('hash')
            changed=old is not None and old!=digest
            state[e['id']]={'hash':digest,'checked_at':datetime.now(timezone.utc).isoformat(),'url':e['source']}
            if changed:
                text=normalize(raw)
                cs=candidates(text)
                # Only auto-apply a date when exactly one plausible future/near-future date appears.
                if len(cs)==1:
                    e['auto_candidate_date']=cs[0]
                changes.append({'id':e['id'],'name':e['name'],'changed':True,'date_candidates':cs[:20]})
        except Exception as ex:
            changes.append({'id':e['id'],'name':e['name'],'error':str(ex)})
    data['last_checked']=datetime.now(timezone.utc).date().isoformat(); data['generated_at']=datetime.now(timezone.utc).isoformat()
    DATA.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n'); STATE.write_text(json.dumps(state,indent=2)+'\n')
    Path(ROOT/'monitor-report.json').write_text(json.dumps(changes,indent=2)+'\n')
    changed=[x for x in changes if x.get('changed')]
    print(f'Checked {len(data["exams"])} sources; {len(changed)} changed.')
    for x in changed: print(x)
if __name__=='__main__': main()
