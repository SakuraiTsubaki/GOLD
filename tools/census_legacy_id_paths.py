#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

BASE_PATTERN=[0xC5,0xD5,0xE5,0xF0,None,0xF5,0x3E,None,0xD7,0xFA,None,None,0xFE,0xFD,0x28,None,0x3D,0x01,0x20,0x00,0x21,None,None,0xCD,None,None,0x11,None,None,0x01,0x20,0x00,0xCD,None,None]
ITEM_ACCESS_PATTERN=[0xE5,0xC5,0x21,None,None,0x4F,0x06,0x00,0x09,0xAF,0xEA,None,None,0xFA,None,None,0x3D,0x4F,0x3E,0x07,0xCD,None,None,0x3E,0x01,0xCD,None,None,0xC1,0xE1,0xC9]
MOVE_PREFIX=bytes([1,0,40,0,255,35,0,2,0,50,1,255,25,0])
ITEM_PRICE_PATTERN=[None]*35
for n,price in enumerate((0,1200,10,600,200)):
    ITEM_PRICE_PATTERN[n*7]=price&0xff;ITEM_PRICE_PATTERN[n*7+1]=(price>>8)&0xff
SUPPORTED={
'8814f1039450a5d3684b1389f588ccd7ee7c3436':'japan_v0','a222402235d484ee8e39f3f31bae57cf13daf585':'japan_rev_a','c0ff3999e1093e1af59ef3eea3f1bfd7c1f18a65':'korea','d8b8a3600a465308c9953dfa04f0081c05bdcb94':'usa_europe','9254195d461ea942eaaa08cc4b83de3cf82aea0d':'germany','c147c0d8c2b71b7628a7233436f5c052b5b17081':'france','032608fe8947b627584a4a0eccc7bf9ad3588426':'italy','162ea54c6a3cff374642e6dd842f9bffac847e7b':'spain'}

def sha1(d):return hashlib.sha1(d).hexdigest()
def sha256(d):return hashlib.sha256(d).hexdigest()
def find_wild(buf,pat):
    return [i for i in range(len(buf)-len(pat)+1) if all(x is None or buf[i+j]==x for j,x in enumerate(pat))]
def bank_addr(phys):return phys//0x4000,0x4000+(phys%0x4000)
def ldhl_refs(buf,addr):
    sig=bytes((0x21,addr&0xff,(addr>>8)&0xff));out=[];p=0
    while True:
        i=buf.find(sig,p)
        if i<0:return out
        out.append(i);p=i+1
def ref_matrix(buf,addr,width):
    return [{'rom_offset':o,'field_offset':f} for f in range(width) for o in ldhl_refs(buf,addr+f)]
def physical(bank,addr):return bank*0x4000+(addr-0x4000)

def analyze(path):
    b=path.read_bytes();h=sha1(b)
    if h not in SUPPORTED:raise ValueError(f'unsupported ROM {path.name}: {h}')
    base_hits=find_wild(b,BASE_PATTERN);item_hits=find_wild(b,ITEM_ACCESS_PATTERN);price_hits=find_wild(b,ITEM_PRICE_PATTERN)
    if len(base_hits)!=1 or len(item_hits)!=1 or len(price_hits)!=1:raise ValueError(f'non-unique signatures in {path.name}')
    gb=base_hits[0];ga=item_hits[0]
    base_bank=b[gb+7];base_addr=b[gb+21]|b[gb+22]<<8;base_phys=physical(base_bank,base_addr)
    move_phys=b.find(MOVE_PREFIX)
    if move_phys<0:raise ValueError('Moves prefix not found')
    move_bank,move_addr=bank_addr(move_phys)
    item_phys=price_hits[0];item_bank,item_addr=bank_addr(item_phys)
    return {'id':SUPPORTED[h],'rom_sha1':h,'rom_sha256':sha256(b),'get_base_data_offset':gb,'w_cur_species_address':b[gb+10]|b[gb+11]<<8,'base_data':{'bank':base_bank,'address':base_addr,'physical_offset':base_phys,'entry_size':32,'entry_count':251,'sha256':sha256(b[base_phys:base_phys+251*32]),'direct_ld_hl_refs':sorted(ref_matrix(b,base_addr,32),key=lambda x:x['rom_offset'])},'moves':{'bank':move_bank,'address':move_addr,'physical_offset':move_phys,'entry_size':7,'entry_count':251,'sha256':sha256(b[move_phys:move_phys+251*7]),'direct_ld_hl_refs':sorted(ref_matrix(b,move_addr,7),key=lambda x:x['rom_offset'])},'get_item_attr_offset':ga,'w_cur_item_address':b[ga+14]|b[ga+15]<<8,'item_attributes':{'bank':item_bank,'address':item_addr,'physical_offset':item_phys,'entry_size':7,'entry_count':256,'sha256':sha256(b[item_phys:item_phys+256*7]),'direct_ld_hl_refs':sorted(ref_matrix(b,item_addr,7),key=lambda x:x['rom_offset'])}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('roms',nargs='+',type=Path);ap.add_argument('-o','--output',type=Path);a=ap.parse_args()
    rows=sorted((analyze(p) for p in a.roms),key=lambda x:x['id'])
    result={'schema_version':1,'release_count':len(rows),'legacy_struct':{'boxmon_bytes':32,'species_offset':0,'item_offset':1,'move_offsets':[2,3,4,5],'id_width_bits':8},'shared_table_hashes':{'base_data':sorted({r['base_data']['sha256'] for r in rows}),'moves':sorted({r['moves']['sha256'] for r in rows}),'item_attributes':sorted({r['item_attributes']['sha256'] for r in rows})},'releases':rows}
    text=json.dumps(result,indent=2)+"\n"
    if a.output:a.output.write_text(text,encoding='utf-8')
    else:print(text,end='')
    return 0
if __name__=='__main__':raise SystemExit(main())
