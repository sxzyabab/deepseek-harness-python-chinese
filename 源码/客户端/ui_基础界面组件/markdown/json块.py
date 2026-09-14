import json#美化

__all__=['json块','最大字节','默认截断标签']#仅中文公开名

最大字节=20000#UTF-8 字节封顶

def 默认截断标签(总计):
    """超出封顶时的脚。"""
    return '… 已截断，共 '+str(总计)+' 字节'#文案

def 按字节截(串,上限):
    """UTF-8 字节截断，切点落在字符边界。"""
    编码=串.encode('utf-8')#字节
    if len(编码)<=上限:#未超；判 length
        return 串#全
    切=编码[:上限]#截
    while len(切)>0:#回退到字符边界；判 length
        try:#解码
            return 切.decode('utf-8')#成
        except UnicodeDecodeError:#半字符
            切=切[:-1]#退一字节
    return ''#空

class json块:#可折叠 JSON
    """打开时 stringify；超封顶截断。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已打开=自身.属性['defaultOpen'] is True if 'defaultOpen' in 自身.属性 else False#默认开

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 切换(自身):
        """开合。"""
        自身.已打开=not 自身.已打开#翻

    def 渲染(自身):
        """产出 toggle+可选 body。"""
        属性=自身.属性#props
        截断标=属性['truncatedLabel'] if 'truncatedLabel' in 属性 else 默认截断标签#脚格式
        体=''#体
        if 自身.已打开 is True:#开
            载荷=属性['payload'] if 'payload' in 属性 else None#载荷
            try:#stringify
                串=json.dumps(载荷,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2)#美化
            except (TypeError,ValueError):#不可序列
                串=str(载荷)#回退
            字节=串.encode('utf-8')#字节
            if len(字节)>最大字节:#超；判 length
                脚=截断标(len(字节))#脚按字节总计
                体=按字节截(串,最大字节)+'\n'+脚#截
            else:#全
                体=串#全
        标签=属性['label'] if 'label' in 属性 and 属性['label'] is not None else ''#标签
        return {#视图
            'type':'json-block',#类型
            'label':标签,#标签
            'open':自身.已打开,#开
            'body':体,#体
            'onToggle':自身.切换,#切换
            'cssModule':'json块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
