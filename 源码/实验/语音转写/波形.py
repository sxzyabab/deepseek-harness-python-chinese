__all__=['校验波形']

def 读无符号32(数据,偏移):
    """小端 4 字节。"""
    return int.from_bytes(数据[偏移:偏移+4],'little')

def 读无符号16(数据,偏移):
    """小端 2 字节。"""
    return int.from_bytes(数据[偏移:偏移+2],'little')

def 读ascii(数据,起,止):
    """固定区间 ASCII。"""
    return bytes(数据[起:止]).decode('ascii')

def 校验波形(音频,最长秒):
    """读规范 16 kHz 单声道 PCM16 WAV，长度不一致则拒绝。"""
    数据=bytes(音频)
    if (
        len(数据)<46
        or 读ascii(数据,0,4)!='RIFF'
        or 读ascii(数据,8,12)!='WAVE'
        or 读ascii(数据,12,16)!='fmt '
        or 读无符号32(数据,16)!=16
        or 读无符号16(数据,20)!=1
        or 读无符号16(数据,22)!=1
        or 读无符号32(数据,24)!=16000
        or 读无符号32(数据,28)!=32000
        or 读无符号16(数据,32)!=2
        or 读无符号16(数据,34)!=16
        or 读ascii(数据,36,40)!='data'
        or 读无符号32(数据,4)!=len(数据)-8
        or 读无符号32(数据,40)!=len(数据)-44
        or (len(数据)-44)%2!=0
    ):
        raise RuntimeError('Audio must be a canonical 16 kHz mono PCM16 WAV recording')
    秒=(len(数据)-44)/32000
    if 秒>最长秒:
        raise RuntimeError(f'Audio exceeds {最长秒} seconds')
    return 秒
