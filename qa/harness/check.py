import copy,hashlib,json,pathlib,shutil,subprocess,sys,tempfile
from fixtures import SCRIPT,pair,png,write
source=pathlib.Path.cwd();checks=0
def run(script,args,code,valid=None):
 global checks
 r=subprocess.run([sys.executable,str(script),*map(str,args)],text=True,capture_output=True,timeout=15)
 assert r.returncode==code,(args,r.returncode,r.stdout,r.stderr)
 assert 'Traceback' not in r.stderr
 try:d=json.loads(r.stdout)
 except Exception as e:raise AssertionError(('not JSON',args,r.stdout,r.stderr))from e
 assert isinstance(d,dict)
 if args and args[0]=='compare':
  assert d.get('visual_quality_verified') is False,d
  assert isinstance(d.get('screens'),list) and d.get('limits'),d
  if valid is not None:assert d.get('comparison_contract_valid') is valid,d
  assert d.get('comparable') is (code==0),d
  if code==1:assert d.get('differences'),d
  if code==2:assert d.get('errors') or d.get('error'),d
 checks+=1;return d
with tempfile.TemporaryDirectory(prefix='studio-compare-probe-')as temp:
 t=pathlib.Path(temp);tree=t/'tree';tree.mkdir()
 for f in [SCRIPT,'plugins/app-ui-studio/skills/app-ui-studio/assets/saas-presets.json']:
  q=tree/f;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((source/f).read_bytes())
 subprocess.run(['patch','-p1','--batch','--input',str(source/'fix.patch')],cwd=tree,check=True,capture_output=True)
 script=tree/SCRIPT;subprocess.run([sys.executable,'-c','import ast,sys;ast.parse(open(sys.argv[1]).read())',str(script)],check=True)
 fixture=t/'fixture';fixture.mkdir();(a,ma),(b,mb)=pair(fixture);args=['compare',a/'capture.json',b/'capture.json']
 def reset():write(b/'capture.json',mb);(b/'app.js').write_bytes((a/'app.js').read_bytes());(b/'brand.png').write_bytes((a/'brand.png').read_bytes());(b/'screen.png').write_bytes((a/'screen.png').read_bytes());write(b/'plugin.json',{'version':'1.3.0'})
 snapshot=lambda:{str(p.relative_to(fixture)):hashlib.sha256(p.read_bytes()).hexdigest()for p in fixture.rglob('*')if p.is_file()}
 before=snapshot();d=run(script,args,0,True);assert snapshot()==before,'no-output comparison wrote files';assert d['baseline_version']=='1.1.0'and d['candidate_version']=='1.3.0';assert d['screens'][0]['changed']is False
 (b/'screen.png').write_bytes(png(color=(2,3,4)));d=run(script,args,0,True);assert d['screens'][0]['changed']is True;reset()
 for key,value in [('product','other'),('capture_context',{'locale':'en'}),('screens',[{'id':'else','artifact':'screen.png','viewport':{'width':1,'height':1}}])]:
  m=copy.deepcopy(mb);m[key]=value;write(b/'capture.json',m);run(script,args,1,True);reset()
 (b/'screen.png').write_bytes(png(2,1));m=copy.deepcopy(mb);m['screens'][0]['viewport']['width']=2;write(b/'capture.json',m);run(script,args,1,True);reset()
 for f in ['app.js','brand.png']:(b/f).write_bytes(b'changed');run(script,args,1,True);reset()
 for key in ['business_files','brand_assets']:
  m=copy.deepcopy(mb);original=m[key][0];other='other-'+original;(b/other).write_bytes((b/original).read_bytes());m[key]=[other];write(b/'capture.json',m);run(script,args,1,True);reset()
 invalids=[('schema_version',True),('product',' '),('plugin_version',' '),('capture_context',{}),('business_files',[]),('brand_assets',['brand.png','brand.png']),('screens',[]),('plugin_manifest','../outside.json'),('plugin_manifest',str(a/'plugin.json')),('plugin_manifest','C:\\outside.json')]
 for key,value in invalids:
  m=copy.deepcopy(mb);m[key]=value;write(b/'capture.json',m);run(script,args,2,False);reset()
 write(b/'plugin.json',{'version':'wrong'});run(script,args,2,False);reset()
 for screen in [{'id':'today','artifact':'screen.png','viewport':{'width':True,'height':1}},{'id':'today','artifact':'screen.png','viewport':{'width':2,'height':1}},{'id':'today','artifact':'missing.png','viewport':{'width':1,'height':1}}]:
  m=copy.deepcopy(mb);m['screens']=[screen];write(b/'capture.json',m);run(script,args,2,False);reset()
 m=copy.deepcopy(mb);m['screens']*=2;write(b/'capture.json',m);run(script,args,2,False);reset()
 for data in [b'',b'not an image',b'\x89PNG\r\n\x1a\n',b'\xff\xd8\xff\xc0\x00\x11']:(b/'screen.png').write_bytes(data);run(script,args,2,False);reset()
 m=copy.deepcopy(mb);m['screens'][0]['artifact']='screen.jpg';write(b/'capture.json',m);run(script,args,0,True);reset()
 outside=t/'outside';outside.mkdir();write(outside/'plugin.json',{'version':'1.3.0'});(b/'escape').symlink_to(outside,target_is_directory=True);m=copy.deepcopy(mb);m['plugin_manifest']='escape/plugin.json';write(b/'capture.json',m);run(script,args,2,False);reset()
 (b/'capture.json').write_text('{broken');run(script,args,2,False);reset();(b/'capture.json').write_bytes(b'\xff');run(script,args,2,False);reset()
 report=t/'report.json';d=run(script,[*args,'--output',report],0,True);assert json.loads(report.read_text())==d
 old=report.read_bytes();run(script,[*args,'--output',report],2,False);assert report.read_bytes()==old
 old=(a/'capture.json').read_bytes();run(script,[*args,'--output',a/'capture.json'],2,False);assert(a/'capture.json').read_bytes()==old
 broken=t/'broken.json';broken.symlink_to(t/'nonexistent');run(script,[*args,'--output',broken],2,False);assert broken.is_symlink()and not(t/'nonexistent').exists()
 # Old command smoke, with fixtures copied solely in disposable tree for init/check.
 run(script,['contrast','#000000','#FFFFFF'],0)
 run(script,['preset','saas'],0)
 run(script,['doctor','--project',t],0)
 assets=script.parent.parent/'assets';(assets/'brief-template.md').write_text('brief');write(assets/'delivery-template.json',{'schema_version':1,'project':'q','surface':'product','stages':{k:{'status':'not_executed','evidence':[],'notes':''}for k in ['brief','visuals','code','browser','native_device','editable_design']},'remaining':[]})
 target=t/'init';run(script,['init','--output',target],0);run(script,['check',target/'delivery.json'],0)
 print(f'PASS {checks} CLI contract cases; input snapshots preserved; stdlib fixture image dimensions and compatibility checked')
