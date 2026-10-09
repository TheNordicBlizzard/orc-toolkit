import os, sys, json, subprocess, time
BLENDER=r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
HERE=os.path.dirname(os.path.abspath(__file__))
BUILDER=os.path.join(HERE,"build_library.py")
CHUNKDIR=os.path.join(HERE,"_chunks"); os.makedirs(CHUNKDIR,exist_ok=True)
COUNTER=[0]; BAD=[]
def build(chunk, depth=0):
    if not chunk: return
    COUNTER[0]+=1; idx=COUNTER[0]
    out=os.path.join(CHUNKDIR,f"part_{idx:03d}.blend")
    man=os.path.join(CHUNKDIR,f"_man_{idx:03d}.json")
    json.dump(chunk, open(man,"w",encoding="utf-8"))
    r=subprocess.run([BLENDER,"--background","--factory-startup","--python",BUILDER,"--",man,out],
                     capture_output=True,text=True)
    try: os.remove(man)
    except: pass
    if os.path.exists(out) and os.path.getsize(out)>200:
        print(f"  part_{idx:03d}: OK ({len(chunk)} models, {os.path.getsize(out)//1024//1024} MB)",flush=True); return
    if len(chunk)==1:
        BAD.append(chunk[0][1]); print(f"  SKIP bad: {chunk[0][1]}",flush=True); return
    mid=len(chunk)//2
    print(f"  part_{idx:03d} FAILED ({len(chunk)}) -> split",flush=True)
    build(chunk[:mid],depth+1); build(chunk[mid:],depth+1)
def main():
    cs=int(sys.argv[1]) if len(sys.argv)>1 else 300
    items=json.load(open(os.path.join(HERE,"_all_manifest.json"),encoding="utf-8"))
    chunks=[items[i:i+cs] for i in range(0,len(items),cs)]
    print(f"{len(items)} models -> {len(chunks)} chunks of {cs}",flush=True)
    t0=time.time()
    for ci,ch in enumerate(chunks):
        print(f"[chunk {ci+1}/{len(chunks)}]",flush=True); build(ch)
    json.dump(BAD, open(os.path.join(HERE,"_bad_models.json"),"w"))
    print(f"DONE in {time.time()-t0:.0f}s; bad: {len(BAD)}",flush=True)
if __name__=="__main__": main()
