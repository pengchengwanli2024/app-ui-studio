"""Independent final behavioral validation: extra boundaries and user-file preservation."""
import ast,base64,copy,json,pathlib,subprocess,sys,tempfile
from fixtures import SCRIPT,pair,png,write
root=pathlib.Path.cwd();count=0
with tempfile.TemporaryDirectory(prefix='studio-compare-final-')as tmp:
 t=pathlib.Path(tmp);tree=t/'code';tree.mkdir()
 for n in [SCRIPT,'plugins/app-ui-studio/skills/app-ui-studio/assets/saas-presets.json']:
  q=tree/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((root/n).read_bytes())
 subprocess.run(['patch','-p1','--batch','--input',str(root/'fix.patch')],cwd=tree,check=True,capture_output=True)
 script=tree/SCRIPT
 oldast=ast.parse((root/SCRIPT).read_text());newast=ast.parse(script.read_text());newdefs={n.name for n in newast.body if isinstance(n,ast.FunctionDef)};assert all(n.name in newdefs for n in oldast.body if isinstance(n,ast.FunctionDef)),'old public helpers removed'
 f=t/'data';f.mkdir();(a,ma),(b,mb)=pair(f)
 def invoke(code=0,*extra):
  global count
  r=subprocess.run([sys.executable,str(script),'compare',str(a/'capture.json'),str(b/'capture.json'),*map(str,extra)],capture_output=True,text=True,timeout=15)
  assert r.returncode==code,(code,r.returncode,r.stdout,r.stderr)
  d=json.loads(r.stdout);assert isinstance(d,dict)and d.get('visual_quality_verified')is False
  assert d.get('comparison_contract_valid')is(code!=2)and d.get('comparable')is(code==0),d
  assert 'Traceback'not in r.stderr
  count+=1;return d
 def restore():write(a/'capture.json',ma);write(b/'capture.json',mb);write(b/'plugin.json',{'version':'1.3.0'});(b/'screen.png').write_bytes(png())
 # Reordering both screen and hash-bearing file lists changes no semantic contract.
 for p,m in [(a,ma),(b,mb)]:
  (p/'second.js').write_text('same');(p/'other.png').write_bytes(png());m['business_files'].append('second.js');m['screens'].append({'id':'focus','artifact':'screen.jpg','viewport':{'width':1,'height':1}});write(p/'capture.json',m)
 m=copy.deepcopy(mb);m['screens'].reverse();m['business_files'].reverse();write(b/'capture.json',m);d=invoke();assert {x['id']for x in d['screens']}=={'today','focus'};restore()
 m=copy.deepcopy(mb);m['screens'][0]['artifact']='other.png';write(b/'capture.json',m);d=invoke();assert all(x['changed']is False for x in d['screens']);restore()
 # Both sides must validate before semantic comparison, even if product already differs.
 m=copy.deepcopy(mb);m['product']='other';m['screens'][0]['artifact']='missing.png';write(b/'capture.json',m);invoke(2);restore()
 for value in [[],None,True,{'schema_version':1}]:write(b/'capture.json',value);invoke(2);restore()
 for field,value in [('schema_version',1.0),('plugin_version',3),('business_files','app.js'),('brand_assets',[42]),('capture_context',[])]:
  m=copy.deepcopy(mb);m[field]=value;write(b/'capture.json',m);invoke(2);restore()
 for bad in ['{"schema_version":1,"schema_version":1}',json.dumps(mb).replace('"ready"','NaN')]:
  (b/'capture.json').write_text(bad);invoke(2);restore()
 for value in [[],{'version':None},{'version':'1.3.0','x':float('inf')}]:write(b/'plugin.json',value);invoke(2);restore()
 m=copy.deepcopy(mb);m['screens'][0]['viewport']['height']=0;write(b/'capture.json',m);invoke(2);restore()
 m=copy.deepcopy(mb);m['screens'][0]['id']=' ';write(b/'capture.json',m);invoke(2);restore()
 # PNG IHDR CRC corrupt, and file with dimensions but no image chunks; reject malformed header.
 img=bytearray(png());img[29]^=1;(b/'screen.png').write_bytes(img);invoke(2);restore()
 (b/'screen.png').write_bytes(png()[:24]);invoke(2);restore()
 # Distinct escape through image symlink, and a directory in place of a business file.
 ext=t/'private.png';ext.write_bytes(png());(b/'external.png').symlink_to(ext);m=copy.deepcopy(mb);m['screens'][0]['artifact']='external.png';write(b/'capture.json',m);invoke(2);restore()
 (b/'directory').mkdir();m=copy.deepcopy(mb);m['business_files']=['directory'];write(b/'capture.json',m);invoke(2);restore()
 # New report for a valid but incomparable pair retains exit1 and full evidence JSON.
 m=copy.deepcopy(mb);m['capture_context']['state']='paused';write(b/'capture.json',m);out=t/'different.json';d=invoke(1,'--output',out);assert json.loads(out.read_text())==d;restore()
 # Existing regular files, symlink-to-file, directory, missing parent are rejected without damage.
 original=t/'keep.json';original.write_bytes(b'KEEP USER BYTES');link=t/'alias.json';link.symlink_to(original)
 for path in [original,link,t,t/'missing-parent'/'report.json']:invoke(2,'--output',path);assert original.read_bytes()==b'KEEP USER BYTES'
 assert not(t/'missing-parent').exists()
 for extra in [['compare'],['compare',str(a/'capture.json')],['compare',str(a/'capture.json'),str(b/'capture.json'),'--unknown-option']]:
  r=subprocess.run([sys.executable,str(script),*extra],text=True,capture_output=True);assert r.returncode==2;d=json.loads(r.stdout);assert d.get('comparison_contract_valid')is False and d.get('visual_quality_verified')is False;count+=1
 # Existing init destination is never overwritten; legacy contrast invalid remains JSON exit2.
 occupied=t/'occupied';occupied.mkdir();(occupied/'user.txt').write_text('preserve')
 for args,code in [(['init','--output',str(occupied)],2),(['contrast','invalid','#000000'],2),(['preset','saas','--tone','calm','--surface','product'],0)]:
  r=subprocess.run([sys.executable,str(script),*args],text=True,capture_output=True);assert r.returncode==code;json.loads(r.stdout);count+=1
 assert(occupied/'user.txt').read_text()=='preserve'
 print(f'PASS independent validation: {count} extra boundary/compatibility/user-file checks')
 print('LIMIT: metadata comparability only; no screenshot authenticity, visual quality, browser or publication acceptance')
