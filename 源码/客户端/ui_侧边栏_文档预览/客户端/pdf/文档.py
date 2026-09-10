"""带取消与页清理的画布渲染，由 PDF 正文与真实库冒烟共享。

对齐上游 `ui-sidebar-documentpreview/src/client/pdf/document.ts`。公开面仅中文名。
Python 半无 PDF.js；本模块声明渲染入口，宿主须注入实际后端。
"""
from ..面 import 已中止#中止

__all__=['渲染pdf页']#仅中文公开名


def 渲染pdf页(文档,页号,画布,信号,像素比):
    """把一页渲染进独占画布。

    文档须提供 numPages / getPage；无后端时抛 NotImplementedError。
    返回 dict：width / height（CSS 像素）。
    """
    if 已中止(信号):#已中止
        raise RuntimeError('aborted')
    if not hasattr(文档,'getPage'):#无后端
        raise NotImplementedError('PDF.js document backend is not available')
    页=文档.getPage(页号)#取页
    try:
        if 已中止(信号):#已中止
            raise RuntimeError('aborted')
        视口=页.getViewport({'scale':96/72})#视口
        比率=min(像素比,(16777216/(视口['width']*视口['height']))**0.5)#限栅格
        if hasattr(画布,'width'):#可写
            画布.width=max(1,int(视口['width']*比率))#宽
            画布.height=max(1,int(视口['height']*比率))#高
        任务=页.render({'canvas':画布,'viewport':视口,'transform':None if 比率==1 else [比率,0,0,比率,0,0]})#渲染
        if 已中止(信号) and hasattr(任务,'cancel'):#取消
            任务.cancel()#停
        if hasattr(任务,'promise'):#可等
            任务.promise#同步等待（上游 await）
        if 已中止(信号):#已中止
            raise RuntimeError('aborted')
        return {'width':视口['width'],'height':视口['height']}#尺寸
    finally:
        if hasattr(页,'cleanup'):#清理
            页.cleanup()#释
