"""Identical supplementary real PNG/JPEG contract checks for all four retained outputs.
Does not alter frozen k=1 inputs, replay agents, or assert image authenticity/quality.
"""
import hashlib,json,pathlib,shutil,subprocess,sys,tempfile
SCRIPT='plugins/app-ui-studio/skills/app-ui-studio/scripts/studio.py'
project=pathlib.Path(__file__).resolve().parents[2]
run='24e4c378711f489888725ac7'
images=[('today.jpg',project/'examples/qike/v1.1.0/screenshots/today.jpg',390,844),('tech-kv.png',project/'examples/qike/v1.2.0/assets/tech-kv.png',2048,1152)]
input_hashes={str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest()for _,p,_,_ in images}
results={}
for label in ['baseline','general','domain','composed']:
 workspace=project/'.harness2/runs'/run/'workspaces'/label
 with tempfile.TemporaryDirectory(prefix='studio-real-images-supplement-')as tmp:
  t=pathlib.Path(tmp);tree=t/'tree';tree.mkdir()
  for n in [SCRIPT,'plugins/app-ui-studio/skills/app-ui-studio/assets/saas-presets.json']:
   q=tree/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((workspace/n).read_bytes())
  subprocess.run(['patch','-p1','--batch','--input',str(workspace/'fix.patch')],cwd=tree,check=True,capture_output=True)
  captures=[]
  for side,version in [('base','1.1.0'),('next','1.3.0')]:
   p=t/side;p.mkdir();(p/'business.js').write_text('same frozen business fixture\n');(p/'plugin.json').write_text(json.dumps({'version':version}))
   for name,source,_,_ in images:shutil.copyfile(source,p/name)
   m={'schema_version':1,'product':'栖刻','plugin_version':version,'plugin_manifest':'plugin.json','capture_context':{'fixture':'same','locale':'zh-CN','state':'ready'},'business_files':['business.js'],'brand_assets':['tech-kv.png'],'screens':[{'id':name,'artifact':name,'viewport':{'width':w,'height':h}}for name,_,w,h in images]}
   (p/'capture.json').write_text(json.dumps(m,ensure_ascii=False));captures.append((p,m))
  (a,ma),(b,mb)=captures
  args=[sys.executable,str(tree/SCRIPT),'compare',str(a/'capture.json'),str(b/'capture.json')]
  r=subprocess.run(args,text=True,capture_output=True);d=json.loads(r.stdout)
  assert r.returncode==0 and d['comparison_contract_valid']is True and d['comparable']is True and d['visual_quality_verified']is False,(label,r.stdout,r.stderr)
  assert len(d['screens'])==2 and all(s['changed']is False for s in d['screens'])
  mb['screens'][0]['viewport']['width']=391;(b/'capture.json').write_text(json.dumps(mb))
  r2=subprocess.run(args,text=True,capture_output=True);e=json.loads(r2.stdout)
  assert r2.returncode==2 and e['comparison_contract_valid']is False and e['visual_quality_verified']is False,(label,r2.stdout,r2.stderr)
  mb['screens'][0]['viewport']['width']=390;mb['capture_context']['state']='paused';(b/'capture.json').write_text(json.dumps(mb))
  r3=subprocess.run(args,text=True,capture_output=True);f=json.loads(r3.stdout)
  assert r3.returncode==1 and f['comparison_contract_valid']is True and f['comparable']is False and f['visual_quality_verified']is False,(label,r3.stdout,r3.stderr)
  results[label]={'real_jpeg_and_png_exit':r.returncode,'dimension_mismatch_exit':r2.returncode,'context_mismatch_exit':r3.returncode}
assert input_hashes=={str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest()for _,p,_,_ in images},'supplement source images changed'
print(json.dumps({'supplement_valid':True,'input_hashes':input_hashes,'results':results,'limits':'Same real source files across outputs; verifies header/dimensions and three-state contract only. Does not replace frozen k=1 inputs or establish image authenticity/visual quality.'},ensure_ascii=False,indent=2))
