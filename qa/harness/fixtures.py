"""Owned tiny image fixtures; PNG generated from pixels; JPEG from same 1px test pixel via sips."""
import base64,copy,json,pathlib,struct,zlib
SCRIPT='plugins/app-ui-studio/skills/app-ui-studio/scripts/studio.py'
JPEG='/9j/4AAQSkZJRgABAQAASABIAAD/4QBMRXhpZgAATU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAAaADAAQAAAABAAAAAQAAAAD/7QA4UGhvdG9zaG9wIDMuMAA4QklNBAQAAAAAAAA4QklNBCUAAAAAABDUHYzZjwCyBOmACZjs+EJ+/8AAEQgAAQABAwEiAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+v/EAB8BAAMBAQEBAQEBAQEAAAAAAAABAgMEBQYHCAkKC//EALURAAIBAgQEAwQHBQQEAAECdwABAgMRBAUhMQYSQVEHYXETIjKBCBRCkaGxwQkjM1LwFWJy0QoWJDThJfEXGBkaJicoKSo1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoKDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uLj5OXm5+jp6vLz9PX29/j5+v/bAEMAAgICAgICAwICAwUDAwMFBgUFBQUGCAYGBgYGCAoICAgICAgKCgoKCgoKCgwMDAwMDA4ODg4ODw8PDw8PDw8PD//bAEMBAgICBAQEBwQEBxALCQsQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEP/dAAQAAf/aAAwDAQACEQMRAD8A5uiiiviz8PP/2Q=='
def png(w=1,h=1,color=(80,144,96)):
 def chunk(k,d):return struct.pack('>I',len(d))+k+d+struct.pack('>I',zlib.crc32(k+d)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+bytes(color)*w)*h))+chunk(b'IEND',b'')
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data),encoding='utf8')
def pair(base):
 result=[]
 for name,version in [('base','1.1.0'),('next','1.3.0')]:
  p=base/name;p.mkdir();(p/'app.js').write_text('same business\n');(p/'brand.png').write_bytes(png());(p/'screen.png').write_bytes(png());(p/'screen.jpg').write_bytes(base64.b64decode(JPEG));write(p/'plugin.json',{'version':version})
  m={'schema_version':1,'product':'栖刻','plugin_version':version,'plugin_manifest':'plugin.json','capture_context':{'locale':'zh-CN','fixture':'same','state':'ready'},'business_files':['app.js'],'brand_assets':['brand.png'],'screens':[{'id':'today','artifact':'screen.png','viewport':{'width':1,'height':1}}]};write(p/'capture.json',m);result.append((p,m))
 return result
