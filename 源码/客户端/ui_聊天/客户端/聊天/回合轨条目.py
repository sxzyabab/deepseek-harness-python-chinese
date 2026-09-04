"""宿主回合大纲与已加载轨道项的视图层联合。

对齐上游 `ui-chat/src/client/chat/turn-rail-items.ts`。公开面仅中文名。
"""

__all__=['合并回合轨条目','空轨条目']#仅中文公开名

空轨条目=()#稳定空元组

def 大纲条目(值):#收窄线大纲条目
    """turn/seq 承重；预览装饰可降级。"""
    if not isinstance(值,dict):#非映射
        return None#丢
    回合=值.get('turn')#回合
    序号=值.get('seq')#序号
    if not isinstance(回合,int) or 回合<0:#turn 无效
        return None#丢
    if not isinstance(序号,int) or 序号<0:#seq 无效
        return None#丢
    提示=值.get('prompt')#提示
    回复=值.get('response')#回复
    return {'turn':回合,'seq':序号,'prompt':提示 if isinstance(提示,str) else '','response':回复 if isinstance(回复,str) else ''}#条目

def 大纲条目们(大纲):#取大纲数组
    """投影缺席或畸形时为空。"""
    return 大纲 if isinstance(大纲,list) else []#数组

def 合并回合轨条目(已加载,大纲):#合并梯子
    """两侧都有的回合保留已加载锚；结果按回合升序。"""
    按回合={}#索引
    for 原始 in 大纲条目们(大纲):#先铺大纲
        条目=大纲条目(原始)#收窄
        if 条目 is None:#坏
            continue#跳
        按回合[条目['turn']]={'turn':条目['turn'],'prompt':条目['prompt'],'response':条目['response'],'anchor':{'kind':'unloaded','seq':条目['seq']}}#未加载
    for 项 in 已加载 or []:#已加载覆盖
        回合=项.get('turn') if isinstance(项,dict) else getattr(项,'turn',None)#回合
        if 回合 is None:#无
            continue#跳
        预览=按回合.get(回合)#大纲预览
        提示=项.get('prompt') if isinstance(项,dict) else getattr(项,'prompt','')#提示
        回复=项.get('response') if isinstance(项,dict) else getattr(项,'response','')#回复
        锚键=项.get('anchorKey') if isinstance(项,dict) else getattr(项,'anchorKey',None)#锚键
        按回合[回合]={'turn':回合,'prompt':提示 if 提示!='' else (预览['prompt'] if 预览 else ''),'response':回复 if 回复!='' else (预览['response'] if 预览 else ''),'anchor':{'kind':'loaded','key':锚键}}#已加载
    if len(按回合)==0:#皆无
        return 空轨条目#空
    return tuple(sorted(按回合.values(),key=lambda 项:项['turn']))#升序
