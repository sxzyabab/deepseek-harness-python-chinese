'为 Web 和 SDK 登记同一段文件链接与交付说明'
__all__=['名称','注入','应用']

名称='deliverable-file-references'
注入=['systemPrompt']
文件引用提示词=(
    'Prefer showing the primary results within your final response alongside a brief explanation. '
    +'Use ![Description](<path/to/image.png>) when an image supports an explanation or comparison. Use [Description](<path/to/image.png>) when referring to an image or listing files. Enclose Markdown file destinations in angle brackets, especially paths containing spaces. '
    +'Do not call present just to list edited source files, or run commands to check whether a diff view will appear. '
    +'Use present to publish complete deliverables, including images, Office documents, spreadsheets, and slide decks, when separate access helps the user. Hosts that support file cards can show the presented file with preview and open actions. '
    +'Avoid repeating results already shown inline unless the separate card adds useful access. '
    +'Outside commands, configuration expressions, and code blocks, link every mention of an existing file, including repeats and tables, to its full path relative to the working directory or absolute; append #L24 or #L24-L30 to the target for known lines. '
    +'Use the filename or a clear alias as the label, adding only enough parent directories to distinguish files; keep full paths out of labels. Default to the name alone; when precise locations matter, append :24 or :24–30, with no # or L in the line suffix.'
)


def 应用(上下文):
    '登记桌面文件引用指导，不挂界面'
    上下文.systemPrompt.段落({
        'name':'ui:deliverable-file-references',
        'order':上下文.systemPrompt.获取段落顺序('DELIVERABLE_FILE_REFERENCES'),
        'text':文件引用提示词,
    })


name=名称
inject=注入
apply=应用
