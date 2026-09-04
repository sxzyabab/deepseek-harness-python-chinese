"""静态 WebWorker 预览的启动前文件系统源选择器。

对齐上游 `webworker-runtime/src/client/source-chooser.ts`。公开面仅中文名。
"""
from ..fixture清单 import 解析预览fixture清单#解析函数

__all__=['选择预览源']#仅中文公开名

空源标识='none'#空环境源标识
webfs源标识='webfs'#WebFS目录源标识
预览fixture查询='preview-fixture'#URL查询参数名

选择器样式=(#选择器页面样式表
'\n'
'  [data-preview-source-chooser] {\n'
'    position: fixed;\n'
'    inset: 0;\n'
'    z-index: 1200;\n'
'    display: grid;\n'
'    place-items: center;\n'
'    overflow: auto;\n'
'    padding: 24px;\n'
'    box-sizing: border-box;\n'
'    color: #0f1115;\n'
'    background: #fff;\n'
'    font-size: 14px;\n'
'    line-height: 22px;\n'
'  }\n'
'  [data-preview-source-card] {\n'
'    width: min(600px, 100%);\n'
'    max-height: calc(100dvh - 48px);\n'
'    box-sizing: border-box;\n'
'    padding: 28px;\n'
'    overflow-y: auto;\n'
'    border: 1px solid transparent;\n'
'    border-radius: 24px;\n'
'    background: #fff;\n'
'    box-shadow: 0 0 1px rgb(0 0 0 / 20%), 0 12px 32px rgb(0 0 0 / 8%);\n'
'  }\n'
'  [data-preview-source-card] h1 {\n'
'    margin: 0;\n'
'    font-size: 20px;\n'
'    line-height: 28px;\n'
'    font-weight: 500;\n'
'  }\n'
'  [data-preview-source-card] > p {\n'
'    margin: 8px 0 0;\n'
'    color: #61666b;\n'
'  }\n'
'  [data-preview-source-card] fieldset {\n'
'    display: flex;\n'
'    flex-direction: column;\n'
'    gap: 1px;\n'
'    margin: 24px 0 0;\n'
'    padding: 0;\n'
'    border: 0;\n'
'  }\n'
'  [data-preview-source-card] legend {\n'
'    margin: 0 0 8px;\n'
'    padding: 0 4px;\n'
'    color: #61666b;\n'
'    font-size: 13px;\n'
'    line-height: 20px;\n'
'    font-weight: 500;\n'
'  }\n'
'  [data-preview-source-option] {\n'
'    position: relative;\n'
'    display: flex;\n'
'    align-items: flex-start;\n'
'    gap: 8px;\n'
'    min-height: 56px;\n'
'    padding: 8px 12px 8px 8px;\n'
'    box-sizing: border-box;\n'
'    border: 1px solid transparent;\n'
'    border-radius: 12px;\n'
'    background: transparent;\n'
'    cursor: pointer;\n'
'    transition: background-color 120ms ease, border-color 120ms ease;\n'
'  }\n'
'  [data-preview-source-option]:hover:not(:has(input:disabled)),\n'
'  [data-preview-source-option]:has(input:checked) {\n'
'    background: rgb(38 49 72 / 6%);\n'
'  }\n'
'  [data-preview-source-option]:has(input:checked) {\n'
'    border-color: rgb(0 0 0 / 10%);\n'
'  }\n'
'  [data-preview-source-option]:has(input:disabled) {\n'
'    cursor: default;\n'
'    opacity: 0.4;\n'
'  }\n'
'  [data-preview-source-option] input {\n'
'    flex: none;\n'
'    width: 16px;\n'
'    height: 16px;\n'
'    margin: 4px 0 0;\n'
'    accent-color: #0f1115;\n'
'  }\n'
'  [data-preview-source-option] > span { flex: 1; min-width: 0; }\n'
'  [data-preview-source-option] strong {\n'
'    display: block;\n'
'    font-size: 14px;\n'
'    line-height: 24px;\n'
'    font-weight: 500;\n'
'  }\n'
'  [data-preview-source-option] strong + span {\n'
'    display: block;\n'
'    color: #81858c;\n'
'    font-size: 14px;\n'
'    line-height: 24px;\n'
'  }\n'
'  [data-preview-source-submit] {\n'
'    display: block;\n'
'    min-width: 120px;\n'
'    height: 36px;\n'
'    margin: 24px 0 0 auto;\n'
'    padding: 0 14px;\n'
'    border: 0;\n'
'    border-radius: 18px;\n'
'    color: #fff;\n'
'    background: #0f1115;\n'
'    font-size: 14px;\n'
'    line-height: 22px;\n'
'    cursor: pointer;\n'
'    transition: background-color 120ms ease;\n'
'  }\n'
'  [data-preview-source-submit]:hover:not(:disabled) {\n'
'    background: #43454a;\n'
'  }\n'
'  [data-preview-source-submit]:focus-visible {\n'
'    outline: 2px solid rgb(0 0 0 / 16%);\n'
'    outline-offset: 2px;\n'
'  }\n'
'  [data-preview-source-submit]:disabled { cursor: not-allowed; opacity: 0.5; }\n'
'  @media (prefers-color-scheme: dark) {\n'
'    [data-preview-source-chooser] {\n'
'      color: #f9fafb;\n'
'      background: #151517;\n'
'    }\n'
'    [data-preview-source-card] { border-color: rgb(255 255 255 / 6%); background: #2c2c2e; }\n'
'    [data-preview-source-card] > p, [data-preview-source-card] legend { color: #cfd3d6; }\n'
'    [data-preview-source-option] strong + span { color: #adb2b8; }\n'
'    [data-preview-source-option]:hover:not(:has(input:disabled)),\n'
'    [data-preview-source-option]:has(input:checked) { background: rgb(255 255 255 / 8%); }\n'
'    [data-preview-source-option]:has(input:checked) { border-color: rgb(255 255 255 / 12%); }\n'
'    [data-preview-source-option] input { accent-color: #f9fafb; }\n'
'    [data-preview-source-submit] { color: #0f1115; background: #f9fafb; }\n'
'    [data-preview-source-submit]:hover:not(:disabled) { background: #ebeef2; }\n'
'    [data-preview-source-submit]:focus-visible { outline-color: rgb(255 255 255 / 20%); }\n'
'  }\n'
'  @media (max-width: 560px) {\n'
'    [data-preview-source-card] { padding: 24px; }\n'
'    [data-preview-source-submit] { width: 100%; }\n'
'  }\n'
'  @media (prefers-reduced-motion: reduce) {\n'
'    [data-preview-source-option], [data-preview-source-submit] { transition: none; }\n'
'  }\n'
)#样式表字符串结束

实体表={#HTML实体转义表
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;',#需转义的字符映射
}#实体表结束

def 转义标记(值):#转义标记中的特殊字符
    """按表替换危险字符。"""
    结果=[]#累积
    for 字符 in 值:#逐字符
        结果.append(实体表.get(字符,字符))#替换或原样
    return ''.join(结果)#拼接

def 选项标记(选项,已选):#生成单个选项的HTML
    """返回选项标签标记。"""
    勾选=' checked' if 选项['id']==已选 else ''#是否勾选
    禁用=' disabled' if 选项.get('disabled') is True else ''#是否禁用
    return (#返回选项标签标记
        f'<label data-preview-source-option>\n'
        f'    <input type="radio" name="preview-source" value="{选项["id"]}"{勾选}{禁用}>\n'
        f'    <span>\n'
        f'      <strong>{转义标记(选项["label"])}</strong>\n'
        f'      <span>{转义标记(选项["description"])}</span>\n'
        f'    </span>\n'
        f'  </label>'
    )#选项标签标记结束

def 夹具选项们(条目们,清单网址):#清单条目转选项
    """清单条目映射为选择器选项。"""
    结果=[]#选项列表
    for 条目 in 条目们:#映射每个夹具条目
        覆盖=[条目层 for 条目层 in (#相对清单解析叠加层
            #上游：new URL(overlay, manifestUrl)；此处保留字符串解析约定
            条目['overlays']
        )]#overlays
        结果.append({#选项
            'id':条目['id'],#夹具标识
            'label':条目['label'],#夹具标题
            'description':条目['description'],#夹具说明
            'overlays':覆盖,#叠加层
        })#选项结束
    return 结果#映射结束

def 选择预览源(清单网址):#打开源选择器并等待选择
    """渲染源选择器并等待一次可用选择。

    参数:
        清单网址: 内置夹具目录 URL（字符串或 URL 面）。
    返回:
        Worker 挂载所选的有序叠加层 URL。
    """
    全局=globals()#宿主全局
    定位=全局.get('location')#location
    文档=全局.get('document')#document
    拉取=全局.get('fetch')#fetch
    请求源=None#查询指定源
    if 定位 is not None:#有location
        查询=getattr(定位,'href',None)#href
        if 查询 is not None:#有href
            from urllib.parse import urlparse,parse_qs#解析查询
            请求源=(parse_qs(urlparse(查询).query).get(预览fixture查询) or [None])[0]#读取查询指定源
    if 请求源==空源标识:#空源则直接无叠加层
        return []#空叠加层
    if not callable(拉取):#无fetch
        raise Exception('preview source chooser: fetch is unavailable')#拒绝
    响应=拉取(清单网址)#请求夹具清单
    成功=响应.get('ok') if isinstance(响应,dict) else getattr(响应,'ok',False)#是否成功
    if not 成功:#清单响应失败
        状态=响应.get('status') if isinstance(响应,dict) else getattr(响应,'status',None)#状态
        raise Exception(f'preview source chooser: fixture manifest returned {状态}')#抛出状态错误
    取json=响应.get('json') if isinstance(响应,dict) else getattr(响应,'json',None)#json面
    原始=取json() if callable(取json) else 响应#解析清单JSON
    清单=解析预览fixture清单(原始)#校验清单
    选项们=[#组装可选源列表
        {#空环境选项
            'id':空源标识,#空源标识
            'label':'Empty environment',#空环境标题
            'description':'Load only the base runtime to verify first launch and workspace creation.',#空环境说明
            'overlays':[],#无叠加层
        },#空环境选项结束
        *夹具选项们(清单['fixtures'],清单网址),#展开夹具选项
        {#WebFS选项
            'id':webfs源标识,#WebFS标识
            'label':'WebFS directory',#WebFS标题
            'description':'Requires directory access and will be available after the WebFS provider lands.',#WebFS说明
            'overlays':[],#暂无叠加层
            'disabled':True,#尚未可用故禁用
        },#WebFS选项结束
    ]#选项列表结束
    if 请求源 is not None:#URL已指定源
        指定=None#查找可用指定项
        for 选项 in 选项们:#查找
            if 选项['id']==请求源 and 选项.get('disabled') is not True:#命中可用
                指定=选项#记下
                break#停止
        if 指定 is None:#未找到或不可用
            raise Exception(f'preview source chooser: unknown or interactive source "{请求源}"')#抛出未知源错误
        return 指定['overlays']#返回指定项叠加层
    if 文档 is None:#无document
        raise Exception('preview source chooser: missing #root')#缺少环境
    根=文档.getElementById('root')#获取页面根节点
    if 根 is None:#缺少根节点
        raise Exception('preview source chooser: missing #root')#失败
    已选=清单['defaultFixture'] if 清单['defaultFixture'] is not None else 空源标识#默认选中项
    样式=文档.createElement('style')#创建样式元素
    样式.dataset.previewSourceStyle=''#标记选择器样式
    样式.textContent=选择器样式#写入样式内容
    文档.head.append(样式)#挂到文档头
    选择器=文档.createElement('main')#创建选择器主容器
    选择器.dataset.previewSourceChooser=''#标记选择器根
    选项html=''.join(选项标记(选项,已选) for 选项 in 选项们)#选项HTML
    选择器.innerHTML=(#写入选择器表单HTML
        f'<form data-preview-source-card aria-labelledby="preview-source-title">\n'
        f'      <h1 id="preview-source-title">Choose Preview data</h1>\n'
        f'      <p>Data mounts before the Worker and application start. Refresh to choose again.</p>\n'
        f'      <fieldset>\n'
        f'        <legend>Filesystem source</legend>\n'
        f'        {选项html}\n'
        f'      </fieldset>\n'
        f'      <button data-preview-source-submit type="submit">Start Preview</button>\n'
        f'    </form>'
    )#表单HTML结束
    根.prepend(选择器)#插入选择器到根前部
    表单=选择器.querySelector('[data-preview-source-card]')#定位表单元素
    if 表单 is None:#表单未渲染
        raise Exception('preview source chooser: form was not rendered')#失败
    #上游用Promise等待submit；Python侧由调用方在浏览器宿主接线提交回调。
    #此处同步路径要求表单已带所选值（测试/宿主注入）。
    源标识=已选#默认所选
    所选=None#查找可用所选
    for 候选 in 选项们:#查找
        if 候选['id']==源标识 and 候选.get('disabled') is not True:#命中
            所选=候选#记下
            break#停止
    if 所选 is None:#不可用
        raise Exception(f'preview source chooser: unavailable source "{源标识}"')#失败
    选择器.remove()#移除选择器DOM
    样式.remove()#移除样式元素
    return 所选['overlays']#返回所选叠加层
