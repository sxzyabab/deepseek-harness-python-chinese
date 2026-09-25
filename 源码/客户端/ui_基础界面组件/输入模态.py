"""文档级输入模态：工具提示跟上次输入；焦点环跟导航键或按键后换控件。
模块级监听与文档同寿；无 window 时整段惰性跳过。
"""
__all__=['输入模态值','输入模态属性','指针模态']#仅中文公开名

输入模态值={'pointer':'pointer','keyboard':'keyboard'}#指针 / 键盘
输入模态属性='data-input-modality'#根元素属性

焦点导航=frozenset(('Tab','Home','End','PageUp','PageDown'))#方向键另用 startsWith Arrow

_指针=False#上次输入是否来自指针（给工具提示）
_指针占焦=False#焦点环是否仍按指针态隐藏
_按键源=None#keydown 时的真实目标

def _发布():
    """把当前焦点环归属写到 documentElement。"""
    文档=globals().get('document')#document
    if 文档 is None:#无 DOM
        return#停
    根=getattr(文档,'documentElement',None)#html
    if 根 is None:#无根
        return#停
    值=输入模态值['pointer'] if _指针占焦 else 输入模态值['keyboard']#模态
    根.setAttribute(输入模态属性,值)#写根属性

def 指针模态():
    """上次输入是否来自指针，与焦点环是否显示无关。"""
    return _指针#上次是否指针

窗口=globals().get('window')#window
if 窗口 is not None:#浏览器才挂监听
    def _指针按下(_事件=None):
        """指针按下：指针拥有输入与焦点环。"""
        global _指针,_指针占焦,_按键源#写
        _指针=True#工具提示跟指针
        _指针占焦=True#环保持安静
        _按键源=None#清按键源
        _发布()#刷新
    def _按键(事件):
        """按键：工具提示切键盘；导航键才亮环。"""
        global _指针,_指针占焦,_按键源#写
        _指针=False#工具提示改跟键盘
        if getattr(事件,'isComposing',False):#IME 合成中不算导航
            _按键源=None#清源
            return#不改焦点环
        取路径=getattr(事件,'composedPath',None)#composedPath
        if callable(取路径):#有路径
            链=取路径()#合成路径
            _按键源=链[0] if len(链)>0 else getattr(事件,'target',None)#按键源
        else:#无
            _按键源=getattr(事件,'target',None)#回落 target
        键=getattr(事件,'key',None)#键名
        if 键 not in 焦点导航 and not (isinstance(键,str) and 键.startswith('Arrow')):#非导航
            return#环仍安静
        _指针占焦=False#导航键：亮键盘环
        _发布()#刷新
    def _焦点入(事件):
        """按键后焦点落到别的控件 → 亮环。"""
        global _指针占焦,_按键源#写
        if _按键源 is None:#无按键源
            return#无关
        取路径=getattr(事件,'composedPath',None)#composedPath
        if callable(取路径):#有路径
            链=取路径()#合成路径
            当前=链[0] if len(链)>0 else getattr(事件,'target',None)#当前
        else:#无
            当前=getattr(事件,'target',None)#回落
        if 当前 is _按键源:#同源再聚焦
            return#不算换控件
        _按键源=None#用过即清
        if not _指针占焦:#已是键盘环
            return#无需再发
        _指针占焦=False#切到键盘环
        _发布()#刷新
    def _失焦(_事件=None):
        """窗口失焦清按键源。"""
        global _按键源#写
        _按键源=None#清
    窗口.addEventListener('pointerdown',_指针按下,True)#指针捕获
    窗口.addEventListener('keydown',_按键,True)#按键捕获
    窗口.addEventListener('focusin',_焦点入,True)#焦点入捕获
    窗口.addEventListener('blur',_失焦)#窗失焦
