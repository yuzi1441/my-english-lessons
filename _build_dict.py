# Rebuild dictionary with full WordNet extraction (synonyms, antonyms, examples)
import json, re, zipfile, os, sys
from pathlib import Path

# find wordnet dir
wn_dir = None
for candidate in [r'C:\Users\whatn\AppData\Local\Temp\wordnet\wordnet', '/tmp/wordnet/wordnet']:
    if Path(candidate, 'index.noun').exists():
        wn_dir = Path(candidate)
        break
if not wn_dir:
    z = zipfile.ZipFile(r'C:\Users\whatn\AppData\Local\Temp\wordnet.zip')
    z.extractall(r'C:\Users\whatn\AppData\Local\Temp\wordnet')
    wn_dir = Path(r'C:\Users\whatn\AppData\Local\Temp\wordnet\wordnet')

print('wordnet dir:', wn_dir)
words = set(Path(r'C:\Users\whatn\AppData\Local\Temp\words.txt').read_text(encoding='utf-8').splitlines())

POS_LABEL = {'n': 'n.名', 'v': 'v.动', 'a': 'adj.形', 's': 'adj.形', 'r': 'adv.副'}

lemma_index = {}  # lemma -> [(pos, offset_str)]
glosses = {}      # (pos, offset_str) -> {gloss, examples}
synset_words = {} # (pos, offset_str) -> [words]
synset_antos = {} # (pos, offset_str) -> [antonym words]

def parse_index_file(path, pos):
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        if not line or line[0] == ' ': continue
        toks = line.split()
        if len(toks) < 4: continue
        lemma = toks[0].replace('_', ' ')
        # toks[1]=pos, toks[2]=synset_cnt, toks[3]=p_cnt, then p_cnt ptr symbols, then sense_cnt, tagsense_cnt, offsets...
        synset_cnt = int(toks[2])
        p_cnt = int(toks[3])
        base = 4 + p_cnt  # skip lemma,pos,cnt,cnt + ptr symbols
        # offsets start after sense_cnt and tagsense_cnt
        offsets = toks[base + 2:]
        for off in offsets:
            lemma_index.setdefault(lemma, []).append((pos, off))

def parse_data_file(path, pos):
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        if not line or line[0] == ' ': continue
        pipe_pos = line.find('|')
        if pipe_pos < 0: continue
        head = line[:pipe_pos].strip()
        gloss_raw = line[pipe_pos+1:].strip() if pipe_pos + 1 < len(line) else ''
        toks = head.split()
        if len(toks) < 4: continue
        offset = toks[0]
        key = (pos, offset)
        # extract gloss and examples
        examples = re.findall(r'"([^"]+)"', gloss_raw)
        gloss = re.split(r';\s*"', gloss_raw)[0].strip().rstrip(';').strip()
        gloss = re.sub(r'\([^)]*\)\s*$', '', gloss).strip()
        glosses[key] = {'g': gloss, 'ex': examples}
        # parse words and pointers from head
        w_cnt = int(toks[3])
        syn_words = []
        for i in range(4, 4 + w_cnt * 2, 2):
            if i < len(toks):
                syn_words.append(toks[i].replace('_', ' '))
        synset_words[key] = syn_words
        # antonyms from ! pointers
        antos = []
        p_cnt2 = int(toks[4 + w_cnt * 2]) if 4 + w_cnt * 2 < len(toks) else 0
        pbase = 5 + w_cnt * 2
        for j in range(p_cnt2):
            idx2 = pbase + j * 4
            if idx2 + 3 < len(toks) and toks[idx2] == '!':
                aw = toks[idx2 + 3].replace('_', ' ') if idx2 + 3 < len(toks) else ''
                if aw: antos.append(aw)
        if antos:
            synset_antos[key] = antos

for pos, idx_f, data_f in [('n','index.noun','data.noun'), ('v','index.verb','data.verb'),
                            ('a','index.adj','data.adj'), ('r','index.adv','data.adv')]:
    parse_index_file(wn_dir / idx_f, pos)
    parse_data_file(wn_dir / data_f, pos)

print('lemma index:', len(lemma_index), '| glosses:', len(glosses))

# build enhanced dictionary
final = {}
norm = lambda s: re.sub(r'\s+', ' ', s.strip().lower().rstrip('.!?'))

# course meanings (Chinese, hand-authored - priority)
course = json.loads(Path('examples/courses/speaking-vocab/vocabulary-month/month.json').read_text(encoding='utf-8'))
for day in course['days']:
    for g in day['groups']:
        for item in g['items']:
            w = norm(item['term'])
            if not w: continue
            e = final.setdefault(w, {'p':'','pos':'','d':'','t':'','syn':[],'ant':[],'ex':[]})
            e['t'] = item['meaning']
            ex = item.get('example', '')
            if ex and ex not in e['ex']:
                e['ex'].insert(0, ex)
                e['ex'] = e['ex'][:2]

# WordNet extraction for all content words
for w in sorted(words):
    entries = lemma_index.get(w) or lemma_index.get(w.replace(' ', '_')) or []
    if not entries:
        cands = []
        if w.endswith('s'): cands += [w[:-1], w[:-2]]
        if w.endswith('es'): cands += [w[:-2]]
        if w.endswith('ed'): cands += [w[:-1], w[:-2]]
        if w.endswith('ing'): cands += [w[:-3], w[:-3] + 'e']
        if w.endswith('ly'): cands += [w[:-2]]
        for c in cands:
            if lemma_index.get(c):
                entries = lemma_index[c][:2]
                break
    if not entries: continue

    e = final.setdefault(w, {'p':'','pos':'','d':'','t':'','syn':[],'ant':[],'ex':[]})
    pos_set = set()
    all_syn = set()
    all_ant = set()
    all_ex = list(e.get('ex', []))
    defs = []
    seen = set()

    for pos, off in entries[:5]:
        key = (pos, off)
        g = glosses.get(key)
        if not g: continue
        gloss = g.get('g', '')
        if gloss and gloss not in seen:
            seen.add(gloss)
            pl = POS_LABEL.get(pos, pos)
            pos_set.add(pl)
            defs.append(f'[{pl}] {gloss}')
        for ex in g.get('ex', []):
            if ex not in all_ex and len(all_ex) < 2: all_ex.append(ex)
        for sw in synset_words.get(key, []):
            swl = sw.lower()
            if swl != w and swl not in all_syn: all_syn.add(swl)
        for aw in synset_antos.get(key, []):
            awl = aw.lower()
            if awl != w: all_ant.add(awl)

    if defs: e['d'] = ' ｜ '.join(defs[:3])
    if pos_set and not e['pos']: e['pos'] = ' / '.join(sorted(pos_set))
    if all_syn: e['syn'] = sorted(all_syn)[:6]
    if all_ant: e['ant'] = sorted(all_ant)[:4]
    if all_ex: e['ex'] = all_ex[:2]

# IPA
try:
    from eng_to_ipa import ipa_list
    for w in final:
        try:
            r = ipa_list([w])[0]
            if r: final[w]['p'] = '/' + r[0] + '/'
        except: pass
except: pass

# stats
has_zh = sum(1 for e in final.values() if e.get('t'))
has_syn = sum(1 for e in final.values() if e.get('syn'))
has_ant = sum(1 for e in final.values() if e.get('ant'))
has_ex = sum(1 for e in final.values() if e.get('ex'))
has_d = sum(1 for e in final.values() if e.get('d'))
print(f'final: {len(final)} words | zh:{has_zh} | syn:{has_syn} | ant:{has_ant} | ex:{has_ex} | en-def:{has_d}')

out = Path('examples/courses/speaking-vocab/dictionary.json')
out.write_text(json.dumps(final, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print('size KB:', out.stat().st_size // 1024)
