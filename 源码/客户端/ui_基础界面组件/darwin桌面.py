__all__=['是否darwin桌面']#仅中文公开名

def 是否darwin桌面():
    """客户端是否跑在 macOS Electron 壳：读 html 的 data-platform。"""
    文档=globals().get('document')#document
    if 文档 is None:#无 DOM
        return False#非桌面壳
    根=getattr(文档,'documentElement',None)#html
    if 根 is None:#无根
        return False#非
    集=getattr(根,'dataset',None)#dataset
    if 集 is None:#无
        return False#非
    return getattr(集,'platform',None)=='darwin'#darwin 标记
