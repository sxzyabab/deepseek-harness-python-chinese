from . import 客户端
from . import 异常
from . import 已呈现
from . import 呈现打开
from . import 改动

__all__=['应用','客户端','异常','已呈现','呈现打开','改动']

依赖=['systemPrompt','connection','sessionQuery','sessionController','workspaceFiles','fs','sandboxPolicy','workspaceChanges']
文件引用引导=(
    'Prefer showing the primary results within your final response alongside a brief explanation. '
    +'Use ![Description](<path/to/image.png>) when an image supports an explanation or comparison. Use [Description](<path/to/image.png>) when referring to an image or listing files. Enclose Markdown file destinations in angle brackets, especially paths containing spaces. '
    +'Do not call present just to list edited source files, or run commands to check whether a diff view will appear. '
    +'Use present when a separate file card helps the user open the complete deliverable, including images, Office documents, spreadsheets, and slide decks. Each presented file adds a card below the reply, with preview and native-open actions. '
    +'Avoid repeating results already shown inline unless the separate card adds useful access. '
    +'Outside commands, configuration expressions, and code blocks, link every mention of an existing file, including repeats and tables, to its full path relative to the working directory or absolute; append #L24 or #L24-L30 to the target for known lines. '
    +'Use the filename or a clear alias as the label, adding only enough parent directories to distinguish files; keep full paths out of labels. Default to the name alone; when precise locations matter, append :24 or :24–30, with no # or L in the line suffix.'
)


def 应用(上下文):
    '登记 Web 文件引用引导，以及已声明文件的原生打开'
    呈现打开.登记呈现打开(上下文)
    上下文.systemPrompt.section({
        'name':'ui:deliverable-file-references',
        'order':上下文.systemPrompt.getSectionOrder('DELIVERABLE_FILE_REFERENCES'),
        'text':文件引用引导,
    })


inject=依赖
apply=应用
