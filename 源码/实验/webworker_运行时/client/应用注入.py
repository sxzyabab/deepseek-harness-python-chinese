"""结构化 index 注入表的页面侧解释器。已服务表单把相同行渲染进
index.html 文本；静态 worker 页面没有已服务 HTML，因此直接执行该表。
行严格按表序执行，因此全局行在读取它的脚本之前落地。

对齐上游 `webworker-runtime/src/client/apply-injections.ts`。公开面仅中文名。
"""
__all__=['应用索引注入']#仅中文公开名

def 断言穷尽(行):#穷尽检查
    """未知注入行种类时抛错。"""
    raise Exception(f'webworker-runtime: unknown index injection row {行!r}')#未知行

def 应用索引注入(行们,加载脚本):#执行注入表
    """按表序执行每一行。

    参数:
        行们: 来自 boot 载荷的注入表。
        加载脚本: 执行一行 script-src；即隧道的 loadBundle，
          因为行 URL（`/plugins/...`）只能经 worker 解析。
    """
    全局=globals()#页面全局
    文档=全局.get('document')#document（浏览器宿主）
    for 行 in 行们:#按序
        种类=行['kind'] if isinstance(行,dict) else getattr(行,'kind',None)#种类
        if 种类=='global':#全局赋值
            名=行['name'] if isinstance(行,dict) else 行.name#名
            值=行['value'] if isinstance(行,dict) else 行.value#值
            全局[名]=值#写入全局
        elif 种类=='script':#内联脚本
            if 文档 is None:#无document
                continue#跳过
            元素=文档.createElement('script')#建script
            文本=行['text'] if isinstance(行,dict) else 行.text#文本
            元素.textContent=文本#写入文本
            放置=行.get('placement') if isinstance(行,dict) else getattr(行,'placement',None)#放置
            (文档.head if 放置=='head' else 文档.body).append(元素)#挂载
        elif 种类=='script-src':#外部脚本
            源=行['src'] if isinstance(行,dict) else 行.src#源
            加载脚本(源)#经隧道加载
        elif 种类=='script-preload':#预加载行
            #worker隧道没有可预热又不执行脚本的浏览器URL；
            #行到达时由loadScript处理真正的请求。
            pass#跳过预热
        elif 种类=='style':#样式
            if 文档 is None:#无document
                continue#跳过
            元素=文档.createElement('style')#建style
            文本=行['text'] if isinstance(行,dict) else 行.text#CSS
            元素.textContent=文本#写入CSS
            文档.head.append(元素)#挂到head
        elif 种类=='html':#HTML片段
            if 文档 is None:#无document
                continue#跳过
            放置=行.get('placement') if isinstance(行,dict) else getattr(行,'placement',None)#放置
            html=行['html'] if isinstance(行,dict) else 行.html#片段
            (文档.head if 放置=='head' else 文档.body).insertAdjacentHTML('beforeend',html)#插入
        else:#穷尽
            断言穷尽(行)#断言
