from ...异常 import 表格预览错误
from ..远程过程调用 import 宿主文件
from .格式 import excel格式
from .转换 import 转换excel

__all__=['表格正文','处理表格正文']


def _格文(格):
    '单元格展示串；空单元格为空串'
    if not isinstance(格,dict):
        return ''
    值=格.get('v')
    if not isinstance(值,dict):
        return ''
    显示=值.get('m')
    if isinstance(显示,str):
        return 显示
    原=值.get('v')
    return '' if 原 is None else str(原)


def _有公式(表):
    '工作表是否含已存公式'
    for 表页 in 表:
        格表=表页.get('celldata') if isinstance(表页,dict) else None
        if not isinstance(格表,list):
            continue
        for 格 in 格表:
            值=格.get('v') if isinstance(格,dict) else None
            if isinstance(值,dict) and 'f' in 值 and 值['f'] is not None:
                return True
    return False


def 处理表格正文(window,属性):
    '按字节画出当前工作表，失败可重试。有 parent 就挂上去'
    文档=window.document
    组件=属性['组件']
    根=文档.createElement('div')
    根.className='excel'
    内容=属性['content'] if 'content' in 属性 else None
    地址=属性['resourceAddress'] if 'resourceAddress' in 属性 else ''
    def 收尾():
        '有 parent 就挂上这一份表'
        if 'parent' in 属性:
            属性['parent'].appendChild(根)
        return 根
    if not isinstance(内容,dict) or 内容.get('kind')!='bytes':
        签=文档.createElement('div')
        签.textContent=组件._翻译('invalid')
        根.appendChild(签)
        return 收尾()
    数据=内容.get('data')
    if isinstance(数据,bytearray):
        数据=bytes(数据)
    if not isinstance(数据,bytes):
        签=文档.createElement('div')
        签.textContent=组件._翻译('invalid')
        根.appendChild(签)
        return 收尾()
    路径=宿主文件(地址)['path'] if isinstance(地址,str) else ''
    try:
        格式=excel格式(路径)
    except 表格预览错误:
        签=文档.createElement('div')
        签.textContent=组件._翻译('invalid')
        根.appendChild(签)
        return 收尾()
    组件._解析(数据,格式)
    if 组件.错误 is not None:
        签=文档.createElement('div')
        签.textContent=组件._翻译(组件.错误)
        根.appendChild(签)
        def 重试(事件):
            '丢掉解析结果再读一次'
            组件.缓存键=None
            组件.渲染()
        钮=文档.createElement('button')
        钮.type='button'
        钮.textContent=组件._翻译('retry')
        钮.addEventListener('click',重试)
        根.appendChild(钮)
        return 收尾()
    簿=组件.结果 if isinstance(组件.结果,dict) else {}
    表列=簿['sheets'] if isinstance(簿.get('sheets'),list) else []
    if len(表列)==0:
        签=文档.createElement('div')
        签.textContent=组件._翻译('invalid')
        根.appendChild(签)
        return 收尾()
    特性=簿['unsupportedFeatures'] if isinstance(簿.get('unsupportedFeatures'),list) else []
    if len(特性)>0:
        名表=[组件._翻译(项) for 项 in 特性 if isinstance(项,str)]
        签=文档.createElement('div')
        签.textContent=组件._翻译('unsupportedNotice',{'features':组件._翻译('featureSeparator').join(名表)})
        根.appendChild(签)
    if _有公式(表列):
        警=文档.createElement('span')
        警.setAttribute('aria-label',组件._翻译('formulaWarning'))
        警.setAttribute('title',组件._翻译('formulaWarning'))
        警.textContent='warning'
        根.appendChild(警)
    if len(表列)>1:
        def 换表(序号):
            '切换当前工作表'
            def 点(事件,号=序号):
                组件.表号=号
                组件.渲染()
            return 点
        排=文档.createElement('div')
        for 序号,表页 in enumerate(表列):
            名=表页.get('name') if isinstance(表页,dict) else str(序号+1)
            钮=文档.createElement('button')
            钮.type='button'
            钮.textContent=名 if isinstance(名,str) and 名!='' else str(序号+1)
            钮.addEventListener('click',换表(序号))
            排.appendChild(钮)
        根.appendChild(排)
    号=组件.表号 if 0<=组件.表号<len(表列) else 0
    表页=表列[号] if isinstance(表列[号],dict) else {}
    格表=表页.get('celldata') if isinstance(表页.get('celldata'),list) else []
    网格={}
    for 格 in 格表:
        if not isinstance(格,dict):
            continue
        行=格.get('r')
        列=格.get('c')
        if not isinstance(行,int) or not isinstance(列,int) or 行<0 or 列<0:
            continue
        网格[(行,列)]=_格文(格)
    if len(网格)==0:
        return 收尾()
    行号=sorted({行 for 行,_列 in 网格})
    列号=sorted({列 for _行,列 in 网格})
    表=文档.createElement('table')
    for 行 in 行号:
        横=文档.createElement('tr')
        for 列 in 列号:
            格=文档.createElement('td')
            格.textContent=网格[(行,列)] if (行,列) in 网格 else ''
            横.appendChild(格)
        表.appendChild(横)
    根.appendChild(表)
    return 收尾()


class 表格正文:
    '只读工作表：表标签、单元格展示值、公式与不支持特性提示'

    def __init__(自身,属性):
        '记下文档席 props。有 window 且有内容才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.缓存键=None
        自身.结果=None
        自身.错误=None
        自身.表号=0
        自身.根=None
        if isinstance(自身.属性,dict) and 'window' in 自身.属性 and 'content' in 自身.属性:
            自身.渲染()

    def _翻译(自身,键,参数=None):
        '缺文案钩子时返回键'
        翻译=自身.属性['t'] if 't' in 自身.属性 else None
        if 翻译 is None:
            return 键
        if 参数 is None:
            return 翻译(键)
        return 翻译(键,参数)

    def _解析(自身,数据,格式):
        '同一份字节只解析一次'
        键=(id(数据),格式)
        if 自身.缓存键==键:
            return
        自身.缓存键=键
        自身.结果=None
        自身.错误=None
        自身.表号=0
        上限=自身.属性['limits'] if 'limits' in 自身.属性 else None
        if not isinstance(上限,dict):
            自身.错误='invalid'
            return
        try:
            自身.结果=转换excel(数据,格式,上限)
        except 表格预览错误 as 错:
            码=错.code if 错.code in ('tooLarge','timeout','encoding') else 'invalid'
            自身.错误=码

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '拆掉旧表，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        if 'window' not in 自身.属性:
            自身.根=None
            return None
        绘制=dict(自身.属性)
        绘制['组件']=自身
        自身.根=处理表格正文(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
            自身.缓存键=None
        return 自身.渲染()
