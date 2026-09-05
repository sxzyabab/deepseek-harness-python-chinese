# temporary generator — delete after use
import json, re, os
ROOT=r'A:\code\py\lib\dsh'
SUB=r'A:\code\py\lib\dsh\dsh-python-chinese\源码\子智能体'
with open(os.path.join(ROOT,r'.文档\翻译\翻译.json'),encoding='utf-8') as f:
    MAIN=json.load(f)
with open(os.path.join(ROOT,r'.文档\翻译\翻译特例.json'),encoding='utf-8') as f:
    SPEC=json.load(f)
TRANS={**MAIN,**SPEC}
VALUES=sorted(set(TRANS.values()),key=len,reverse=True)
ID_PAT=re.compile(
    r'(?:^|[\s,=(\[])'
    r'([\u4e00-\u9fff][\u4e00-\u9fff\w]*)'
    r'(?=[\s,)=:\[\].]|$)'
)
DEF_PAT=re.compile(r'^\s*(?:def|class)\s+([\u4e00-\u9fff][\u4e00-\u9fff\w]*)')
ASSIGN_PAT=re.compile(r'^\s*([\u4e00-\u9fff][\u4e00-\u9fff\w]*)\s*=')
SKIP=re.compile(r'[\u4e00-\u9fff]')

def extract_ids(text):
    ids=set()
    for line in text.splitlines():
        m=DEF_PAT.match(line)
        if m:
            ids.add(m.group(1))
        m=ASSIGN_PAT.match(line)
        if m:
            ids.add(m.group(1))
        for m in ID_PAT.finditer(line.split('#')[0]):
            s=m.group(1)
            if SKIP.search(s):
                ids.add(s)
    return ids

def build_map(text):
    ids=extract_ids(text)
    if not ids:
        return None
    blob=''.join(ids)
    if not SKIP.search(blob):
        return None
    out={}
    for eng,zh in TRANS.items():
        if zh and zh in blob:
            out[eng]=zh
    return out if out else None

created=skipped_existing=skipped_empty=skipped_english=0
for dirpath,_,files in os.walk(SUB):
    if os.path.basename(dirpath).endswith('.translatemap.json'):
        continue
    for fn in files:
        if not fn.endswith('.py'):
            continue
        if fn=='_build_translatemaps.py':
            continue
        py_path=os.path.join(dirpath,fn)
        map_path=py_path+'.translatemap.json'
        if os.path.isfile(map_path):
            skipped_existing+=1
            continue
        with open(py_path,encoding='utf-8') as f:
            text=f.read()
        ids=extract_ids(text)
        if not ids or not any(SKIP.search(i) for i in ids):
            skipped_english+=1
            continue
        m=build_map(text)
        if not m:
            skipped_empty+=1
            continue
        with open(map_path,'w',encoding='utf-8') as f:
            json.dump(m,f,ensure_ascii=False,indent=4)
            f.write('\n')
        created+=1
print(json.dumps({
    'created':created,
    'skipped_existing':skipped_existing,
    'skipped_empty':skipped_empty,
    'skipped_english':skipped_english,
},ensure_ascii=False))
