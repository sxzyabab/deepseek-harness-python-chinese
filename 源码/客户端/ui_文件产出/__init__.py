from .呈现打开 import 登记呈现打开#原生打开路由

__all__=['注入','应用']#仅中文公开名

注入=['systemPrompt','connection','sessionQuery','sessionController','workspaceFiles','fs','sandboxPolicy','workspaceChanges']#依赖表
文件引用引导=('When you successfully create or modify files, mention the primary outputs in your final response. '
    +'Outside commands, configuration expressions, and code blocks, link every mention of an existing file, including repeats and tables, to its full path relative to the working directory or absolute; append #L24 or #L24-L30 to the target for known lines. '
    +'Use the filename or a clear alias as the label, adding only enough parent directories to distinguish files; keep full paths out of labels. Default to the name alone; when precise locations matter, append :24 or :24–30, with no # or L in the line suffix.')#字面量不翻译

def 应用(上下文):#安装交付物插件
    """登记 Web 文件引用引导与原生打开。"""
    登记呈现打开(上下文)#登记路由
    上下文.systemPrompt.section({#登记段落
        'name':'ui:deliverable-file-references',#段落名
        'order':上下文.systemPrompt.getSectionOrder('DELIVERABLE_FILE_REFERENCES'),#序
        'text':文件引用引导,#引导
    })#结束 section

inject=注入#框架槽
apply=应用#框架槽
