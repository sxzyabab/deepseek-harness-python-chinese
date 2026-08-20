/** 本包内嵌 SERVICE_API 分片 05（对照原版 api-catalog.ts）：e2b..fs */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'e2b',
    summary: 'Creates one lazily consumable E2B SDK handle and deletes the sandbox at timeout or disposal.',
    description: 'Creates one lazily consumable E2B SDK handle and deletes the sandbox at timeout or disposal. Creation begins at plugin construction; adapters await getSandbox before their first operation.',
    methods: [//公开方法
      {//方法
        signature: 'readonly cwd: string',
        description: 'Validated remote working directory shared by provider adapters.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'readonly runtimeRoot: string',
        description: 'Remote directory reserved for adapter-owned process and terminal state.',
        parameters: [],//无参数
      },//结束方法
      {//方法
        signature: 'async getSandbox(): Promise<Sandbox>',
        description: 'Return the shared live SDK handle.',
        parameters: [],//无参数
        returns: 'the created sandbox after the configured cwd exists.',
        throws: ['when E2B rejects creation or the service is disposing.'],
      },//结束方法
    ],//结束 methods
  },//结束服务
  {//服务
    key: 'fs',
    summary: 'Abstract filesystem provider.',
    description: 'Abstract filesystem provider. Targets must preserve identity across aliases; reads expose regular UTF-8 text or typed errors, listings are stable and content-free, and mutations are atomic. Optional guards add stale protection without changing the unguarded provider contract.',
    methods: [//公开方法
      {//方法
        signature: 'abstract resolve(path: string, opts?: { cwd?: string; signal?: AbortSignal }): Promise<FsTarget>',
        description: 'Resolve a model/plugin-supplied path into a stable FsTarget. May perform I/O (a remote/sandboxed backend may need a round-trip to map a path to a stable identity), hence async even though the local backend only normalizes + realpaths.',
        parameters: [{ name: 'path', description: 'the path to resolve; relative paths resolve against `opts.cwd`.' }, { name: 'opts', description: 'optional cwd override and cancellation signal.' }],
        returns: 'the stable target; the same file yields the same `targetKey`.',
      },//结束方法
      {//方法
        signature: 'abstract processPath(target: FsTarget): string',
        description: 'Return the canonical absolute path a subprocess in this filesystem\'s execution world can open. The path is deliberately separate from FsTarget.targetKey: consumers may pass this value to another OS capability, but must continue treating the target key as opaque.',
        parameters: [{ name: 'target', description: 'the resolved target whose process path is required.' }],
        returns: 'an absolute path in the backend\'s execution world.',
      },//结束方法
      {//方法
        signature: 'abstract fileUrl(target: FsTarget): string',
        description: 'Return the canonical `file:` URI for a target in this filesystem\'s execution world. Backends own URI encoding because the host platform may differ from the execution platform.',
        parameters: [{ name: 'target', description: 'the resolved target to encode.' }],
        returns: 'the target\'s canonical file URI.',
      },//结束方法
      {//方法
        signature: 'abstract contains(parent: FsTarget, child: FsTarget): boolean',
        description: 'Test canonical containment without exposing or parsing backend target keys. Both targets must come from this provider.',
        parameters: [{ name: 'parent', description: 'canonical directory target.' }, { name: 'child', description: 'canonical candidate target.' }],
        returns: 'true when `child` is `parent` or a descendant of it.',
      },//结束方法
      {//方法
        signature: 'abstract stat(target: FsTarget, signal?: AbortSignal): Promise<FsInfo | undefined>',
        description: 'Return target metadata, or `undefined` when the target does not exist.',
        parameters: [{ name: 'target', description: 'the resolved target to stat.' }, { name: 'signal', description: 'aborts the metadata round-trip.' }],
        returns: 'metadata only, never content; undefined for an absent target.',
      },//结束方法
      {//方法
        signature: 'abstract lstat(path: string, opts?: { cwd?: string }, signal?: AbortSignal): Promise<FsPathInfo | undefined>',
        description: 'Return path metadata without following the final path component when it is a symbolic link. This is intentionally path-shaped, not target-shaped: resolve follows symlinks to produce the stable identity used by normal reads/writes, while `lstat` lets a consumer reject the path itself before that follow happens.\n\n`opts.cwd` follows resolve\'s cwd rules. `undefined` means the path is absent.',
        parameters: [{ name: 'path', description: 'the path to inspect; relative paths resolve against `opts.cwd`.' }, { name: 'opts', description: '`cwd` overrides the backend\'s default base for relative paths.' }, { name: 'signal', description: 'aborts the metadata round-trip.' }],
        returns: 'metadata only, never content; undefined for an absent path.',
      },//结束方法
      {//方法
        signature: 'abstract readText(target: FsTarget, signal?: AbortSignal): Promise<string>',
        description: 'Read the whole regular text file as a single decoded string.',
        parameters: [{ name: 'target', description: 'the resolved target to read.' }, { name: 'signal', description: 'aborts the read.' }],
        returns: 'the full decoded UTF-8 content.',
      },//结束方法
      {//方法
        signature: 'abstract streamText(target: FsTarget, signal?: AbortSignal): Promise<AsyncIterable<string>>',
        description: 'Stream the whole regular text file as decoded text chunks (same text semantics as readText, for large files). The backend owns cross-chunk UTF-8 decoding and binary rejection so the policy layer never touches raw bytes.',
        parameters: [{ name: 'target', description: 'the resolved target to read.' }, { name: 'signal', description: 'aborts the stream, including between chunks.' }],
        returns: 'the chunk iterable, decoded and validated like {@link readText}.',
      },//结束方法
      {//方法
        signature: 'abstract readBytes(target: FsTarget, signal: AbortSignal | undefined, maxBytes: number): Promise<Uint8Array>',
        description: 'Read the whole regular file as raw bytes with no decoding or binary rejection. The bound lives at this seam so a backend can never buffer an unbounded file: a target known or discovered to exceed `maxBytes` fails with `FS_TOO_LARGE` instead of returning a truncated result.',
        parameters: [{ name: 'target', description: 'the resolved target to read.' }, { name: 'signal', description: 'aborts the read.' }, { name: 'maxBytes', description: 'inclusive byte cap on the complete content.' }],
        returns: 'the full raw content, at most `maxBytes` long.',
      },//结束方法
      {//方法
        signature: 'abstract listDir(target: FsTarget, signal?: AbortSignal): Promise<FsDirEntry[]>',
        description: 'List direct children of a directory in stable name order. Returns resolved child targets plus cheap metadata only; never reads file contents.',
        parameters: [{ name: 'target', description: 'the resolved directory target.' }, { name: 'signal', description: 'aborts the listing.' }],
        returns: 'one entry per direct child, in stable name order.',
      },//结束方法
      {//方法
        signature: 'abstract writeText( target: FsTarget, content: string, expected?: FsWriteIntent, signal?: AbortSignal, sandboxPolicy?: SandboxExecutionPolicy, ): Promise<FsWriteOutcome>',
        description: 'Atomically create or replace UTF-8 text. `expected` guards intent and staleness; omission allows unconditional overwrite.',
        parameters: [{ name: 'target', description: 'the resolved target to write.' }, { name: 'content', description: 'the full new file content.' }, { name: 'expected', description: 'the write intent guarding the write; omit for unconditional.' }, { name: 'signal', description: 'aborts before atomic publication takes effect.' }, { name: 'sandboxPolicy', description: 'the per-call mode and workspace root this write runs under; a sandboxing backend fences the write by it, the bare backend ignores it. Omit to leave the backend its own default.' }],
        returns: 'the outcome, including the version the write produced.',
      },//结束方法
      {//方法
        signature: 'abstract editText( target: FsTarget, edit: FsEditRequest, expected?: { version: FsVersion }, signal?: AbortSignal, sandboxPolicy?: SandboxExecutionPolicy, ): Promise<FsEditOutcome>',
        description: 'Atomically edit literal text. When supplied, the version guard is checked before matching so stale content reports `FS_STALE_VERSION`; omission edits the current content without a freshness precondition.',
        parameters: [{ name: 'target', description: 'the resolved target to edit.' }, { name: 'edit', description: 'the literal search/replace request.' }, { name: 'expected', description: 'the version guard; omit for an unconditional edit.' }, { name: 'signal', description: 'aborts before atomic publication takes effect.' }, { name: 'sandboxPolicy', description: 'the per-call mode and workspace root this edit runs under; a sandboxing backend fences the edit by it, the bare backend ignores it. Omit to leave the backend its own default.' }],
        returns: 'the outcome, including the version the edit produced.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
