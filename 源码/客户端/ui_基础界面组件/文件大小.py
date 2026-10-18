__all__=['文件大小文本']

def 文件大小文本(字节):
    '紧凑字节数：不足 1024 用 B，否则 KB、MB、GB。不足 10 个单位保留一位小数'
    if 字节<1024:
        return str(字节)+'B'
    千=字节/1024
    if 千<1024:
        if 千<10:
            return format(千,'.1f')+'KB'
        return str(round(千))+'KB'
    兆=千/1024
    if 兆<1024:
        if 兆<10:
            return format(兆,'.1f')+'MB'
        return str(round(兆))+'MB'
    吉=兆/1024
    if 吉<10:
        return format(吉,'.1f')+'GB'
    return str(round(吉))+'GB'
