"""共享文件/目录打开器：默认动作、应用菜单、手势反馈。"""
from .打开失败提示 import 使用打开失败提示#失败横幅

__all__=['使用打开目标手势','应用图标','打开目标按钮','样式表']#仅中文公开名

样式表='''#对齐 OpenTargetButton.module.css
.menuAnchor{display:inline-flex;flex:none;align-self:center}
.split{display:inline-flex;align-items:stretch;box-sizing:border-box;height:24px;overflow:hidden;border:0.5px solid var(--dsw-alias-border-l4);border-radius:var(--dsw-radius-sm);font-family:var(--dsw-font-family)}
.main,.chevron{display:inline-flex;align-items:center;justify-content:center;border:0;background:none;color:var(--dsw-alias-label-primary);font-size:11px;line-height:16px;white-space:nowrap;cursor:pointer}
.main{gap:4px;padding:3px 5px}
.chevron{padding:3px 4px 3px 3px;border-left:0.5px solid var(--dsw-alias-border-l4);color:var(--dsw-alias-label-secondary)}
.main:hover:not(:disabled),.main:focus-visible,.chevron:hover:not(:disabled),.chevron:focus-visible{background:var(--dsw-alias-interactive-bg-hover)}
.main:disabled,.chevron:disabled{cursor:default}
.appIcon{object-fit:contain}
.split[data-size="large"]{height:36px;border-radius:var(--dsw-radius-md);border-color:var(--dsw-alias-border-l2)}
.split[data-size="large"] .main{gap:6px;padding:6px 14px;font-size:14px}
.split[data-size="large"] .chevron{padding:6px 10px}
.skeleton{display:inline-block;flex:none;border-radius:var(--dsw-radius-xs);background:var(--dsw-alias-interactive-bg-hover)}
'''#样式表结束

def 使用打开目标手势(执行,翻译):
    """串行化手势，失败经发起控件的 toast 宣告。
    执行为目标适配器，返回失败键或 None；翻译为本地化文案。
    返回 pending、toast 与受守卫的 act。
    """
    提示=使用打开失败提示()#横幅
    箱={'pending':False,'inFlight':False}#态
    def 行动(操作):
        """在飞时忽略；结束后清 pending。"""
        if 箱['inFlight']:#在飞
            return#忽略
        箱['inFlight']=True#占位
        箱['pending']=True#忙碌
        失败=执行(操作)#跑
        if hasattr(失败,'等待'):#异步面
            失败=失败.等待()#等
        if 失败 is not None:#失败
            提示['show'](翻译(f'path.{失败}'))#宣告
        箱['inFlight']=False#结束
        箱['pending']=False#闲
    return {'pending':lambda:箱['pending'],'toast':提示['toast'],'act':行动,'state':箱}#面

class 应用图标:#主钮与菜单共用
    """一条应用图；失败落到通用右上箭头占位。"""

    def __init__(自身,源,尺寸=14):
        """记下图标 URL 与边长。"""
        自身.源=源#URL 或 None
        自身.尺寸=尺寸#边长
        自身.已失败=False#本图失败

    def 标记失败(自身):
        """onError。"""
        自身.已失败=True#切占位

    def 渲染(自身):
        """真图或占位图标名。"""
        if 自身.源 is None or 自身.已失败:#占位
            return {'type':'icon','name':'IconRightUpOutlineRegular','size':自身.尺寸}#占位
        return {#真图
            'type':'img','src':自身.源,'width':自身.尺寸,'height':自身.尺寸,
            'className':'appIcon','alt':'','draggable':False,'onError':自身.标记失败,
        }#真图结束

class 打开目标按钮:#文件与目录同一分体按钮
    """文件揭示恒在末项；仅无已登记应用时揭示才作默认。"""

    def __init__(自身,属性):
        """记下 props 与本地态。"""
        自身.属性=属性 if 属性 is not None else {}#props
        自身.菜单开=False#菜单
        自身.手势=使用打开目标手势(自身.属性['execute'],自身.属性['t'])#手势

    def 更新(自身,属性):
        """刷新 props 并重建手势面。"""
        自身.属性=属性 if 属性 is not None else {}#最新
        自身.手势=使用打开目标手势(自身.属性['execute'],自身.属性['t'])#重建

    def _偏好(自身):
        """文件优先 Host 默认标记，否则壳偏好序首项；目录仅认默认标记。"""
        属性=自身.属性#props
        应用表=属性['applications'] if 'applications' in 属性 else []#应用
        默认标识=属性['defaultId'] if 'defaultId' in 属性 else None#默认 id
        种类=属性['kind']#file|directory
        命中=None#偏好
        for 应用 in 应用表:#找默认
            if 应用['id']==默认标识:#命中
                命中=应用#记下
                break#止
        if 种类=='file':#文件
            return 命中 if 命中 is not None else (应用表[0] if len(应用表)>0 else None)#回落首项
        return 命中#目录无默认则为空

    def _跑(自身,操作):
        """关菜单后行动。"""
        自身.菜单开=False#关
        自身.手势['act'](操作)#行动

    def _主钮(自身):
        """主钮点击。"""
        属性=自身.属性#props
        偏好=自身._偏好()#偏好
        加载中=属性['loading'] is True if 'loading' in 属性 else False#加载
        揭示默认=属性['kind']=='file' and 偏好 is None and not 加载中#无应用则揭示
        if 揭示默认:#揭示
            自身._跑({'kind':'reveal'})#揭示
            return#止
        默认标识=属性['defaultId'] if 'defaultId' in 属性 else None#默认
        if 偏好 is not None and 偏好['id']!=默认标识:#无 Host 默认标记
            自身._跑({'kind':'application','id':偏好['id']})#点名应用
            return#止
        自身._跑({'kind':'default'})#默认

    def _菜单选定(自身,标识):
        """菜单项 id → 操作。"""
        if 标识=='reveal':#揭示
            自身._跑({'kind':'reveal'})#揭示
            return#止
        自身._跑({'kind':'application','id':标识[4:]})#app: 前缀后为 id

    def 切换菜单(自身):
        """箭头；打开前可选刷新。"""
        if not 自身.菜单开:#将开
            刷新=自身.属性['refresh'] if 'refresh' in 自身.属性 else None#刷新
            if 刷新 is not None:#有
                刷新()#刷新联想
        自身.菜单开=not 自身.菜单开#翻

    def 渲染(自身):
        """分体按钮与瞬态失败反馈。"""
        属性=自身.属性#props
        翻译=属性['t']#文案
        应用表=属性['applications'] if 'applications' in 属性 else []#应用
        种类=属性['kind']#种类
        偏好=自身._偏好()#偏好
        待定=自身.手势['pending']()#手势待定
        忙碌=属性['busy'] is True if 'busy' in 属性 else False#忙碌
        加载中=属性['loading'] is True if 'loading' in 属性 else False#加载
        禁用=待定 or 忙碌 or 加载中#禁用
        失败=属性['failed'] is True if 'failed' in 属性 else False#失败
        突出=属性['prominent'] is True if 'prominent' in 属性 else False#大钮
        有菜单=加载中 or 失败 or (len(应用表)+(1 if 种类=='file' else 0)>1)#菜单
        揭示默认=种类=='file' and 偏好 is None and not 加载中#揭示默认
        主标签=翻译('path.reveal') if 偏好 is None else 翻译('open.title',{'app':偏好['name']})#主文案
        图标尺寸=18 if 突出 else 13#图标边
        if 加载中 and 偏好 is None:#骨架
            图标={'type':'span','className':'skeleton','props':{'data-open-target-skeleton':True,'aria-hidden':True,'style':{'width':图标尺寸,'height':图标尺寸}}}#骨架
        elif 揭示默认:#文件夹
            图标={'type':'icon','name':'IconFolderOpenOutlineRegular','size':图标尺寸}#文件夹
        else:#应用图
            图标源=偏好['icon'] if 偏好 is not None and 'icon' in 偏好 else None#源
            图标=应用图标(图标源,图标尺寸).渲染()#图
        快捷=属性['shortcut'] if 'shortcut' in 属性 else None#快捷键
        菜单项=[]#项
        for 应用 in 应用表:#逐应用
            标签=翻译('path.appDefault',{'app':应用['name']}) if 偏好 is not None and 应用['id']==偏好['id'] else 应用['name']#标签
            菜单项.append({'id':f"app:{应用['id']}",'icon':应用图标(应用['icon'] if 'icon' in 应用 else None).渲染(),'label':标签})#项
        if 失败:#不可用行
            菜单项.append({'id':'unavailable','label':翻译('path.appsError'),'disabled':True})#禁用行
        页脚=[]#页脚
        if 种类=='file':#文件有揭示
            揭示标签=翻译('path.appDefault',{'app':翻译('path.reveal')}) if 揭示默认 else 翻译('path.reveal')#标签
            页脚.append({'id':'reveal','icon':{'type':'icon','name':'IconFolderOpenOutlineRegular'},'label':揭示标签})#揭示
        主文=翻译('path.reveal') if 揭示默认 else 翻译('path.open')#突出主文
        return {#视图
            'type':'open-target-button',#种类
            'kind':种类,#file|directory
            'menuOpen':自身.菜单开 and (not 禁用) and 有菜单,#菜单
            'disabled':禁用,#禁用
            'hasMenu':有菜单,#有菜单
            'primaryLabel':主标签,#主文案
            'prominent':突出,#大钮
            'icon':图标,#图标
            'primaryText':主文 if 突出 else None,#大钮文
            'shortcut':快捷,#快捷
            'items':菜单项,#菜单项
            'footer':页脚,#页脚
            'toast':自身.手势['toast'](),#失败条
            'styleSheet':样式表,#样式
            'onPrimary':自身._主钮,#主钮
            'onToggle':自身.切换菜单,#箭头
            'onClose':lambda:setattr(自身,'菜单开',False),#关菜单
            'onSelect':自身._菜单选定,#选定
        }#视图结束

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
