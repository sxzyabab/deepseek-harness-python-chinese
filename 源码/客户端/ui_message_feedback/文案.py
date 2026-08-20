"""`feedback` 命名空间词典。



对齐上游 `ui-message-feedback/src/client/locales.ts`。公开面仅中文公开名。

"""



__all__=['命名空间','中文','英文']#仅中文公开名



命名空间='feedback'#词表命名空间



中文={#简体中文词条

    'action.like':'好的回答',#赞

    'action.likeActive':'取消标记',#已赞取消

    'action.dislike':'有问题的回答',#踩

    'action.dislikeActive':'取消标记',#已踩取消

    'note.open':'补充说明',#打开说明

    'note.placeholder':'这条回答哪里好，或哪里有问题？（可选）',#占位

    'note.save':'保存',#保存

    'note.cancel':'取消',#取消

    'note.aria':'反馈说明',#无障碍名

    'error.conflict':'这条反馈已在别处改动，已显示最新状态',#冲突

    'error.load':'反馈状态加载失败',#加载失败

    'error.generic':'反馈保存失败',#保存失败

}#中文结束



英文={#英文词条

    'action.like':'Good response',#赞

    'action.likeActive':'Remove rating',#已赞取消

    'action.dislike':'Bad response',#踩

    'action.dislikeActive':'Remove rating',#已踩取消

    'note.open':'Add a note',#打开说明

    'note.placeholder':'What was good, or what went wrong? (optional)',#占位

    'note.save':'Save',#保存

    'note.cancel':'Cancel',#取消

    'note.aria':'Feedback note',#无障碍名

    'error.conflict':'This feedback changed elsewhere; the latest state is shown',#冲突

    'error.load':'Could not load feedback',#加载失败

    'error.generic':'Could not save feedback',#保存失败

}#英文结束


