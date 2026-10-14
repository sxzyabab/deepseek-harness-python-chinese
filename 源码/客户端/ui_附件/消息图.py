from nicegui import ui as 界面
from .原图灯箱 import 原图灯箱
from .异常 import 叠页面失败,页面失败文案

__all__=['消息图','图库','单图适配']#仅中文公开名

def 单图适配(附件):#单图显示盒
    '长边 240px，宽高比夹在 [0.25,4]，不放大超过自然尺寸'
    if 附件 is None:#无附件
        宽=1#缺附件当 1
        高=1#缺附件当 1
    else:#有附件 dict
        宽=附件['width'] if 'width' in 附件 and 附件['width'] is not None else 1#缺键当 1
        高=附件['height'] if 'height' in 附件 and 附件['height'] is not None else 1#缺键当 1
    自然=宽/高#自然比
    比例=min(4,max(0.25,自然))#夹紧比
    if 比例>=1:#横图
        盒宽,盒高=240,240/比例#盒
    else:#竖图
        盒宽,盒高=240*比例,240#盒
    缩放=min(1,宽/盒宽,高/盒高)#不放大
    物位='center top' if 自然<0.25 else ('left center' if 自然>4 else 'center')#锚点
    return {#适配
        'width':max(1,round(盒宽*缩放)),#宽
        'height':max(1,round(盒高*缩放)),#高
        'objectPosition':物位,#物位
    }#适配结束

class 消息图:#历史缩略图
    '可重试加载与单击原图预览'
    def __init__(自身,属性):#构造
        '记下 props 并首载'
        自身.属性=属性#合成 props
        自身.源=None#已解析 URL
        自身.错误=False#失败
        自身.打开中=False#灯箱
        自身.尝试=0#重试计数
        自身.存活=True#存活
        自身.灯箱=None#内嵌灯箱
        自身.画面失败=None
        自身.加载失败文=None
        自身.加载()#首载

    def 更新(自身,属性):#props 变更
        '附件或加载器变则重载'
        旧附=自身.属性['attachment'] if 'attachment' in 自身.属性 else None#旧
        旧载=自身.属性['load'] if 'load' in 自身.属性 else None#旧载
        自身.属性=属性#最新
        新附=自身.属性['attachment'] if 'attachment' in 自身.属性 else None#新
        新载=自身.属性['load'] if 'load' in 自身.属性 else None#新载
        if 新附 is not 旧附 or 新载 is not 旧载:#引用变
            自身.加载()#重载

    def 卸载(自身):#卸载
        '标死'
        自身.存活=False#死
        if 自身.灯箱 is not None:#有灯箱
            自身.灯箱.卸载()#拆

    def 加载(自身):#拉取 URL
        '同一存活守卫下加载。ImageLoader 已是同步，返回 URL'
        自身.错误=False#清错
        自身.源=None#清源
        自身.加载失败文=None
        加载器=自身.属性['load'] if 'load' in 自身.属性 else None#加载器
        附件=自身.属性['attachment'] if 'attachment' in 自身.属性 else None#附件
        try:#加载
            地址=加载器(附件) if 加载器 is not None else None#同步 URL
        except Exception as 错误:#加载器异常契约未定，故不能换成更窄的 except
            if 自身.存活:#仍活
                自身.错误=True#失败
                自身.加载失败文=页面失败文案(错误)
            return
        if not 自身.存活:#已死
            return#丢弃
        自身.源=地址#记下

    def 重试(自身):#失败后重试
        '抬尝试计数并再载'
        自身.尝试+=1#计数
        自身.加载()#再载

    def 打开(自身):#开灯箱
        '有源才开'
        if 自身.源 is None:#无源
            return
        自身.打开中=True#打开
        文案=自身.属性['labels'] if 'labels' in 自身.属性 and 自身.属性['labels'] is not None else {}#文案
        附件=自身.属性['attachment'] if 'attachment' in 自身.属性 and 自身.属性['attachment'] is not None else {}#附件
        if 'name' in 附件 and 附件['name'] is not None:#?? 空串保留
            名=附件['name']#显示名
        else:#无 name
            名=文案['image'] if 'image' in 文案 else None#回退文案
        灯箱文案=文案['lightbox'] if 'lightbox' in 文案 and 文案['lightbox'] is not None else {}#灯箱文案
        自身.灯箱=原图灯箱({#灯箱 props
            'src':自身.源,#URL
            'alt':名,#替代
            'labels':灯箱文案,#灯箱文案
            'onClose':自身.关闭灯箱,#关闭
        })#铸造

    def 关闭灯箱(自身):#关灯箱
        '关掉'
        自身.打开中=False#关
        if 自身.灯箱 is not None:#有
            自身.灯箱.卸载()#拆
            自身.灯箱=None#清

    def 视图(自身):#读视图模型
        '投影缩略或重试钮'
        文案=自身.属性['labels'] if 'labels' in 自身.属性 and 自身.属性['labels'] is not None else {}#文案
        附件=自身.属性['attachment'] if 'attachment' in 自身.属性 and 自身.属性['attachment'] is not None else {}#附件
        变体=自身.属性['variant'] if 'variant' in 自身.属性 and 自身.属性['variant'] is not None else 'tile'#变体
        if 'name' in 附件 and 附件['name'] is not None:#?? 空串保留
            名=附件['name']#显示名
        else:#无 name
            名=文案['image'] if 'image' in 文案 else None#回退文案
        开名=文案['openNamed'] if 'openNamed' in 文案 else None#命名打开
        if 开名 is not None:#有函数
            无障碍=开名(名)#调用
        else:#缺席
            无障碍=名#退回
        if 自身.错误:#失败
            return {'status':'error','variant':变体,'retryLabel':文案['loadFailed'] if 'loadFailed' in 文案 else None}#重试
        适配=单图适配(附件) if 变体=='single' else None#单图适配
        结果={#就绪视图
            'status':'ready',#状态
            'variant':变体,#变体
            'src':自身.源,#URL
            'alt':名,#替代
            'title':文案['open'] if 'open' in 文案 else None,#提示
            'aria':无障碍,#无障碍
            'loading':文案['loading'] if 自身.源 is None and 'loading' in 文案 else None,#加载中
            'fit':适配,#适配
            'lightbox':自身.灯箱.视图() if 自身.打开中 and 自身.灯箱 is not None else None,#灯箱
        }#结果结束
        return 结果#返回

    def 图样式(自身,视):
        '单图用适配盒，方砖 64，缩略 48'
        变体=视['variant'] if 'variant' in 视 else 'tile'#变体
        if 变体=='thumbnail':#缩略
            return 'width:48px;height:48px;object-fit:contain'#缩略盒
        if 变体=='tile':#方砖
            return 'width:64px;height:64px;object-fit:cover'#方砖盒
        适配=视['fit'] if 'fit' in 视 else None#单图适配
        if not isinstance(适配,dict):#无适配
            return ''#默认
        宽=适配['width'] if 'width' in 适配 else None#宽
        高=适配['height'] if 'height' in 适配 else None#高
        物位=适配['objectPosition'] if 'objectPosition' in 适配 else None#锚点
        段=[]#样式段
        if isinstance(宽,(int,float)) and not isinstance(宽,bool) and isinstance(高,(int,float)) and not isinstance(高,bool):#有尺寸
            段.append('width:'+str(int(宽))+'px')#宽
            段.append('height:'+str(int(高))+'px')#高
            段.append('object-fit:cover')#裁切
        if isinstance(物位,str) and 物位!='':#有锚点
            段.append('object-position:'+物位)#锚点
        return ';'.join(段)#拼起来

    def 渲染(自身):
        '失败给重试；有地址则出图，点击开灯箱'
        视=自身.视图()
        旧=getattr(自身,'根',None)
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:
                自身.根=None
                自身.画面失败=叠页面失败(自身.画面失败,错误)
        if getattr(自身,'根',None) is None:
            自身.根=界面.column().classes('message-image')
        with 自身.根:
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            if 视['status']=='error':
                if isinstance(自身.加载失败文,str) and 自身.加载失败文!='':
                    界面.label(自身.加载失败文)
                文=视['retryLabel'] if isinstance(视['retryLabel'],str) else ''
                def 点重试():
                    '再载缩略图'
                    自身.重试()
                    自身.渲染()
                if 视['variant']=='thumbnail':
                    钮=界面.button(on_click=点重试).props('icon=refresh flat round')
                    if 文!='':
                        钮.tooltip(文)
                else:
                    界面.button(文,on_click=点重试).props('flat no-caps')
            else:
                if 视['variant']=='thumbnail' and 视['src'] is None:
                    界面.spinner(size='16px')
                elif isinstance(视['loading'],str) and 视['loading']!='' and 视['src'] is None:
                    界面.label(视['loading'])
                if isinstance(视['src'],str) and 视['src']!='':
                    def 点开():
                        '打开原图'
                        自身.打开()
                        自身.渲染()
                    图=界面.image(视['src'])
                    样式=自身.图样式(视)
                    if 样式!='':
                        图.style(样式)
                    if isinstance(视['title'],str) and 视['title']!='':
                        图.tooltip(视['title'])
                    图.on('click',lambda _e:点开())
            if 自身.打开中 is True and 自身.灯箱 is not None:
                自身.灯箱.渲染()

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 组件调用'
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()

class 图库:#消息图组
    '单图大显，多图方砖'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性#合成 props
        自身.子图=[]#子消息图
        自身.画面失败=None
        自身.重建子图()#首建

    def 重建子图(自身):#按 images 重建
        '变体随条数变'
        图列=自身.属性['images'] if 'images' in 自身.属性 and 自身.属性['images'] is not None else []#图列；空列表保留
        缩略=自身.属性['thumbnail'] is True if 'thumbnail' in 自身.属性 else False#列表缩略
        紧凑=自身.属性['compact'] is True if 'compact' in 自身.属性 else False#紧凑方砖
        if 缩略:#缩略图
            变体='thumbnail'#缩略
        elif 紧凑 or len(图列)!=1:#多图或要求紧凑
            变体='tile'#方砖
        else:#独图
            变体='single'#大图
        加载=自身.属性['load'] if 'load' in 自身.属性 else None#加载器
        文案=自身.属性['labels'] if 'labels' in 自身.属性 else None#文案
        自身.子图=[消息图({#子图
            'attachment':图['attachment'] if 'attachment' in 图 else None,#附件
            'load':加载,#加载
            'variant':变体,#变体
            'labels':文案,#文案
        }) for 图 in 图列]#铸造

    def 更新(自身,属性):#props 变更
        '刷新并重建'
        自身.属性=属性#最新
        for 子 in 自身.子图:#旧子
            子.卸载()#拆
        自身.重建子图()#重建

    def 卸载(自身):#卸载
        '拆子图'
        for 子 in 自身.子图:#每个
            子.卸载()#拆
        自身.子图=[]#清

    def 视图(自身):#读视图模型
        '空图列返回 None'
        图列=自身.属性['images'] if 'images' in 自身.属性 and 自身.属性['images'] is not None else []#图列；空列表保留
        if len(图列)==0:#空；判的是 length
            return None#不渲染
        return {#视图
            'align':自身.属性['align'] if 'align' in 自身.属性 else None,#对齐
            'images':[子.视图() for 子 in 自身.子图],#子视图
        }#视图结束

    def 渲染(自身):
        '先有一行；空图列藏起，有图则逐张交给消息图'
        视=自身.视图()
        旧=getattr(自身,'根',None)
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:
                自身.根=None
                自身.画面失败=叠页面失败(自身.画面失败,错误)
        if getattr(自身,'根',None) is None:
            自身.根=界面.row().classes('message-images')
        失败文=自身.画面失败 if isinstance(自身.画面失败,str) and 自身.画面失败!='' else None
        if 视 is None and 失败文 is None:
            自身.根.set_visibility(False)
            return
        自身.根.set_visibility(True)
        if 视 is not None:
            对齐=视['align'] if 'align' in 视 else None
            if 对齐=='end':
                自身.根.style('justify-content:flex-end;flex-wrap:wrap;gap:8px')
            else:
                自身.根.style('justify-content:flex-start;flex-wrap:wrap;gap:8px')
        with 自身.根:
            if 失败文 is not None:
                界面.label(失败文)
            if 视 is None:
                return
            for 子 in 自身.子图:
                子.渲染()

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 组件调用'
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()
