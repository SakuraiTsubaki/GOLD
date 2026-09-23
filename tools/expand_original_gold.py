#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path

ROM_TARGET=4*1024*1024
ROM_SIZE_CODE_4MIB=0x07
RAM_SIZE_CODE_64KIB=0x05
CART_MBC3_RTC_RAM_BATTERY=0x10
SRAM_32K=0x8000
SRAM_64K=0x10000
RTC_TRAILER=0x2C
BANKSWITCH_SIGNATURE=bytes.fromhex('e0 9f ea 00 20 c9')
EXT_BANK4_OFFSET=0x8000
EXT_BANK_BYTES=0x2000
SAVE_V2_MAGIC=b'GOLDV2\0\0'
SAVE_V2_FORMAT_VERSION=2
SAVE_V2_SCHEMA_VERSION=1
SAVE_V2_HEADER_SIZE=0x20
SAVE_V2_DIRECTORY_OFFSET=0x20
SAVE_V2_DIRECTORY_ENTRY_SIZE=12
SAVE_V2_MON_HIGH_OFFSET=0x100
SAVE_V2_MON_SLOTS=288
SAVE_V2_MON_HIGH_BYTES_PER_SLOT=6
SAVE_V2_MON_HIGH_LENGTH=SAVE_V2_MON_SLOTS*SAVE_V2_MON_HIGH_BYTES_PER_SLOT
SAVE_V2_INV_HIGH_OFFSET=0x800
SAVE_V2_INV_HIGH_LENGTH=20+50+12+25
BLOCK_MON_ID_HIGH=1
BLOCK_INVENTORY_ITEM_HIGH=2
REGISTRY_BANK=0x80
REGISTRY_PHYS=REGISTRY_BANK*0x4000
REGISTRY_MAGIC=b'GOLDREG\0'
REGISTRY_HEADER_SIZE=0x40
REGISTRY_DIRECTORY_OFFSET=0x40
REGISTRY_ENTRY_SIZE=16
REGISTRY_DATA_OFFSET=0x100
REGISTRY_SPECIES=1
REGISTRY_MOVES=2
REGISTRY_ITEMS=3
BASE_DATA_SIZE=251*32
MOVES_DATA_SIZE=251*7
ITEM_DATA_SIZE=256*7

RELEASES={
'8814f1039450a5d3684b1389f588ccd7ee7c3436':{'id':'japan_v0','profile_id':1,'rom_bytes':0x100000,'save_sha1':'ecdd363a4c4e64c956a483547f6b1a5ef1bc8ec4','sram_sha1':'c05322715b9b204590ade3637a471446907afffb'},
'a222402235d484ee8e39f3f31bae57cf13daf585':{'id':'japan_rev_a','profile_id':2,'rom_bytes':0x100000,'save_sha1':'3fc59f3d4bcbbfc1a0ff385a658ef434951289c8','sram_sha1':'290973b7d6561b0d4cc457feaf5b150efd368e62'},
'c0ff3999e1093e1af59ef3eea3f1bfd7c1f18a65':{'id':'korea','profile_id':3,'rom_bytes':0x200000,'save_sha1':'7a00c2f8a10a456ea22262ccd7d150703712d41e','sram_sha1':'a5d57a4236c83e003445b8c401f3e0399816a23d','patches':[{'offset':0x317C,'before':0x04,'after':0x08,'reason':'OpenSRAM bank bound 4->8 for MBC30 SRAM banks'}]},
'd8b8a3600a465308c9953dfa04f0081c05bdcb94':{'id':'usa_europe','profile_id':4,'rom_bytes':0x200000,'save_sha1':'6fbf7312c9c0257857f5a5819325116b5cf7d063','sram_sha1':'04667489b08e8532632a178f2677ac01089a2ff1'},
'9254195d461ea942eaaa08cc4b83de3cf82aea0d':{'id':'germany','profile_id':5,'rom_bytes':0x200000,'save_sha1':'54872724841b6d6bbede97b3315ca4efd2af123a','sram_sha1':'b5ec4a3de2dd37cddbbd182bdd5366ee8ce5de02'},
'c147c0d8c2b71b7628a7233436f5c052b5b17081':{'id':'france','profile_id':6,'rom_bytes':0x200000,'save_sha1':'9d9cf301dbaac80c7903e1bf12295ee9cc3598f9','sram_sha1':'0f316f58fa0b142d8e24a239b0dda487d3cef4dd'},
'032608fe8947b627584a4a0eccc7bf9ad3588426':{'id':'italy','profile_id':7,'rom_bytes':0x200000,'save_sha1':'d7584c6021cebb6b4d5fd100008361cb6b44a11b','sram_sha1':'3b427b3bf452c17d4e4ed081df4307961215f8a5'},
'162ea54c6a3cff374642e6dd842f9bffac847e7b':{'id':'spain','profile_id':8,'rom_bytes':0x200000,'save_sha1':'602be21c5e85f164dc759af576b4cff21cf5082a','sram_sha1':'531ca2fe4e6248e88ffe9518cb74ea41fd28fbca'},
}
SAVE_RELEASES={p['save_sha1']:p for p in RELEASES.values()}
SRAM_RELEASES={p['sram_sha1']:p for p in RELEASES.values()}

def sha1(d): return hashlib.sha1(d).hexdigest()
def sha256(d): return hashlib.sha256(d).hexdigest()
def crc16_ccitt(d:bytes)->int:
    crc=0xffff
    for byte in d:
        crc ^= byte<<8
        for _ in range(8): crc=((crc<<1)^0x1021)&0xffff if crc&0x8000 else (crc<<1)&0xffff
    return crc

def header_checksum(data):
    v=0
    for x in data[0x134:0x14D]: v=(v-x-1)&0xff
    return v

def global_checksum(data): return (sum(data[:0x14E])+sum(data[0x150:]))&0xffff
def validate_header(data):
    if header_checksum(data)!=data[0x14D]: raise ValueError('bad input header checksum')
    if global_checksum(data)!=int.from_bytes(data[0x14E:0x150],'big'): raise ValueError('bad input global checksum')
def fix_checksums(buf):
    buf[0x14D]=header_checksum(buf);buf[0x14E:0x150]=b'\0\0';buf[0x14E:0x150]=global_checksum(buf).to_bytes(2,'big')

def identify_rom(data):
    h=sha1(data)
    if h not in RELEASES: raise ValueError(f'unsupported Gold ROM SHA-1: {h}')
    return dict(RELEASES[h],sha1=h)
def identify_save(data):
    full=sha1(data); sram=sha1(data[:SRAM_32K])
    p=SAVE_RELEASES.get(full) or SRAM_RELEASES.get(sram)
    if not p: raise ValueError(f'unsupported Gold SAVE (full={full}, sram={sram})')
    return p

def make_directory_entry(t,version,offset,length,payload,flags=0):
    return struct.pack('<HHHHHH',t,version,offset,length,crc16_ccitt(payload),flags)

def build_save_v2_extension(profile_id:int, legacy_sram:bytes)->bytes:
    ext=bytearray(0x8000)
    mon=bytes(SAVE_V2_MON_HIGH_LENGTH)
    inv=bytes(SAVE_V2_INV_HIGH_LENGTH)
    ext[SAVE_V2_MON_HIGH_OFFSET:SAVE_V2_MON_HIGH_OFFSET+len(mon)]=mon
    ext[SAVE_V2_INV_HIGH_OFFSET:SAVE_V2_INV_HIGH_OFFSET+len(inv)]=inv
    entries=[
        make_directory_entry(BLOCK_MON_ID_HIGH,1,SAVE_V2_MON_HIGH_OFFSET,len(mon),mon),
        make_directory_entry(BLOCK_INVENTORY_ITEM_HIGH,1,SAVE_V2_INV_HIGH_OFFSET,len(inv),inv),
    ]
    directory=b''.join(entries)
    ext[SAVE_V2_DIRECTORY_OFFSET:SAVE_V2_DIRECTORY_OFFSET+len(directory)]=directory
    struct.pack_into('<8sHHHHHHHH',ext,0,SAVE_V2_MAGIC,SAVE_V2_FORMAT_VERSION,SAVE_V2_SCHEMA_VERSION,
                     profile_id,len(entries),SAVE_V2_DIRECTORY_OFFSET,0x8000,crc16_ccitt(legacy_sram),0)
    hdr=bytearray(ext[:SAVE_V2_HEADER_SIZE]); hdr[22:24]=b'\0\0'
    struct.pack_into('<H',ext,22,crc16_ccitt(hdr))
    return bytes(ext)

def parse_save_v2_extension(ext:bytes)->dict:
    if len(ext)<0x8000: raise ValueError('extension too small')
    magic,fmt,schema,profile,count,diroff,extbytes,legacycrc,hdrcrc=struct.unpack_from('<8sHHHHHHHH',ext,0)
    hdr=bytearray(ext[:SAVE_V2_HEADER_SIZE]); hdr[22:24]=b'\0\0'
    if magic!=SAVE_V2_MAGIC or crc16_ccitt(hdr)!=hdrcrc: raise ValueError('invalid GOLD_SAVE_V2 header')
    entries=[]
    for n in range(count):
        o=diroff+n*SAVE_V2_DIRECTORY_ENTRY_SIZE
        t,v,poff,plen,pcrc,flags=struct.unpack_from('<HHHHHH',ext,o)
        payload=ext[poff:poff+plen]
        entries.append({'type':t,'version':v,'offset':poff,'length':plen,'crc16':pcrc,'crc_ok':crc16_ccitt(payload)==pcrc,'flags':flags})
    return {'format_version':fmt,'schema_version':schema,'profile_id':profile,'directory_count':count,'extension_bytes':extbytes,'legacy_crc16':legacycrc,'header_crc16':hdrcrc,'entries':entries}

def build_registry_seed(source:bytes, profile:dict)->bytes:
    base_prefix=bytes.fromhex('012d31312d414116032d400000')
    move_prefix=bytes([1,0,40,0,255,35,0,2,0,50,1,255,25,0])
    candidates=[]
    for pos in range(len(source)-35):
        ok=True
        for n,price in enumerate((0,1200,10,600,200)):
            if source[pos+n*7:pos+n*7+2] != price.to_bytes(2,'little'):
                ok=False; break
        if ok: candidates.append(pos)
    base=source.find(base_prefix); moves=source.find(move_prefix)
    if base<0 or moves<0 or len(candidates)!=1: raise ValueError('cannot locate legacy registry tables')
    items=candidates[0]
    base_blob=source[base:base+BASE_DATA_SIZE];move_blob=source[moves:moves+MOVES_DATA_SIZE];item_blob=source[items:items+ITEM_DATA_SIZE]
    if sha256(base_blob)!='dccd0f065a1ccba8ee1a1b7dbee960574499262a2739f46f67fa2f7e686654ac': raise ValueError('BaseData hash mismatch')
    if sha256(move_blob)!='e84da1c005921f4352d9bbd83bd5a5885a12b0bbdcfd9ddc14c8ceb50c42670e': raise ValueError('Moves hash mismatch')
    if sha256(item_blob)!='34ef5e76d33d6a92dfc85d55afbefc9bedd5d79c5de4feac1b5001f1d14a74d5': raise ValueError('ItemAttributes hash mismatch')
    bank=bytearray(b'\xff'*0x4000)
    struct.pack_into('<8sHHHHHH',bank,0,REGISTRY_MAGIC,1,profile['profile_id'],3,REGISTRY_DIRECTORY_OFFSET,REGISTRY_DATA_OFFSET,16)
    cursor=REGISTRY_DATA_OFFSET; entries=[]
    for typ,entry_size,count,blob in ((REGISTRY_SPECIES,32,251,base_blob),(REGISTRY_MOVES,7,251,move_blob),(REGISTRY_ITEMS,7,256,item_blob)):
        entries.append((typ,1,entry_size,16,cursor,count,len(blob),0))
        bank[cursor:cursor+len(blob)]=blob; cursor+=len(blob)
    for n,e in enumerate(entries): struct.pack_into('<HHHHHHHH',bank,REGISTRY_DIRECTORY_OFFSET+n*REGISTRY_ENTRY_SIZE,*e)
    return bytes(bank)

def expand_rom(data):
    p=identify_rom(data)
    if len(data)!=p['rom_bytes']: raise ValueError('ROM size differs from fingerprint profile')
    validate_header(data)
    if data[0x147]!=0x10 or data[0x149]!=0x03 or data[0x10:0x16]!=BANKSWITCH_SIGNATURE: raise ValueError('unexpected original header/bankswitch')
    out=bytearray(data);ap=[]
    for patch in p.get('patches',[]):
        if out[patch['offset']]!=patch['before']: raise ValueError(f"patch precondition failed at {patch['offset']:#x}")
        out[patch['offset']]=patch['after'];ap.append(patch)
    out.extend(b'\xff'*(ROM_TARGET-len(out)))
    registry=build_registry_seed(data,p)
    out[REGISTRY_PHYS:REGISTRY_PHYS+0x4000]=registry
    out[0x148]=0x07;out[0x149]=0x05;fix_checksums(out);validate_header(out)
    return bytes(out),{'release':p['id'],'profile_id':p['profile_id'],'input_sha1':p['sha1'],'input_bytes':len(data),'output_bytes':len(out),'output_sha1':sha1(out),'output_sha256':sha256(out),'rom_banks':256,'sram_banks':8,'registry_bank':REGISTRY_BANK,'registry_physical_offset':REGISTRY_PHYS,'registry_magic':REGISTRY_MAGIC.decode('ascii','ignore').rstrip('\0'),'applied_release_patches':ap}

def expand_save(data):
    if len(data) not in (SRAM_32K,SRAM_32K+RTC_TRAILER): raise ValueError(f'expected 0x8000+optional0x2c, got {len(data):#x}')
    p=identify_save(data);legacy=data[:SRAM_32K];trailer=data[SRAM_32K:]
    ext=build_save_v2_extension(p['profile_id'],legacy); parsed=parse_save_v2_extension(ext)
    out=legacy+ext+trailer
    return out,{'release':p['id'],'profile_id':p['profile_id'],'input_bytes':len(data),'output_bytes':len(out),'legacy_sram_bytes_preserved':SRAM_32K,'extension_sram_bytes':len(ext),'rtc_trailer_bytes':len(trailer),'save_v2':parsed,'input_sha1':sha1(data),'output_sha1':sha1(out),'output_sha256':sha256(out)}

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='kind',required=True)
    for kind in ('rom','save'):
        p=sub.add_parser(kind);p.add_argument('input',type=Path);p.add_argument('output',type=Path)
    a=ap.parse_args();d=a.input.read_bytes();out,report=expand_rom(d) if a.kind=='rom' else expand_save(d);a.output.write_bytes(out);print(json.dumps(report,indent=2));return 0
if __name__=='__main__': raise SystemExit(main())
