/** 本包内嵌 SERVICE_API 分片 15（对照原版 api-catalog.ts）——subagents */
export const SERVICE_API: readonly ServiceApiEntry[] = [//服务目录
  {//服务
    key: 'subagents',
    summary: 'Named provider registry with one-shot runs, durable discovery, and continuable-child operations.',
    description: 'Named provider registry with one-shot runs, durable discovery, and continuable-child operations.',
    methods: [//公开方法
      {//方法
        signature: 'async startContinuable(spec: ContinuableStartSpec): Promise<ContinuableStart>',
        description: 'Establish one durable continuable child and deliver its initial prompt. Resolves when the child\'s inbox accepts that prompt, without waiting for the turn to start or for the message to reach the Session log; any earlier failure rejects with no ids and rolls back the child entirely.',
        parameters: [{ name: 'spec', description: 'provider, delegation request, and caller cancellation.' }],
        returns: 'the durable child id and the accepted prompt\'s message id.',
        throws: ['when continuation services are unavailable or materialization fails.'],
      },//结束方法
      {//方法
        signature: 'async followup( parent: Agent, childId: SessionId, content: ContentBlock[], options: SubagentFollowupOptions, ): Promise<MessageId>',
        description: 'Deliver one later message to a continuable child as its next FIFO turn. A resident child\'s Agent inbox accepts it directly (waking a `waiting` Activation), while an absent one is cold-resumed from its persisted Session. The Agent inbox is the only queue, so every accepted message has one observable order.',
        parameters: [{ name: 'parent', description: 'the exact live direct parent authorizing this delivery.' }, { name: 'childId', description: 'durable child session id.' }, { name: 'content', description: 'user-role content to deliver.' }, { name: 'options', description: 'the message source fields and caller cancellation, which stops the operation only before inbox acceptance.' }],
        returns: 'the accepted message\'s inbox id.',
        throws: ['when continuation services are unavailable, parent authority is rejected, or the message was not admitted.'],
      },//结束方法
      {//方法
        signature: 'interrupt(targetSessionId: SessionId, authority: SubagentInterruptAuthority): void',
        description: 'Interrupt one live continuable child\'s current turn under a human parent address or an exact live ancestor Agent. Fire-and-return: the cancel signal is issued before this returns, but the target may keep running until it observes the signal. Unclaimed pending inbox work, the Activation, and published descendants are preserved; claimed work is not requeued. Once the interrupted driver is idle, a waking send resumes the parked FIFO queue. An absent target — including a one-shot or unknown id — is an accepted no-op, as is a manager-less composition, which cannot own a live Activation.',
        parameters: [{ name: 'targetSessionId', description: 'the durable child session id to interrupt.' }, { name: 'authority', description: 'the human parent address or exact live ancestor Agent.' }],
        throws: ['{SubagentError} `UNAUTHORIZED` when the authority does not own the live target.'],
      },//结束方法
      {//方法
        signature: 'async reportFrom( child: Agent, content: ContentBlock[], options: SubagentReportOptions, ): Promise<MessageId>',
        description: 'Deliver selected content from one live continuable child to its durable direct parent. The child is the authority credential; callers cannot name a recipient. Reporting does not conclude the child\'s turn or Activation.',
        parameters: [{ name: 'child', description: 'exact live reporting child.' }, { name: 'content', description: 'selected model-facing content.' }, { name: 'options', description: 'parent scheduling and pre-acceptance cancellation.' }],
        returns: 'the stable identity of the parent-accepted message.',
        throws: ['when continuation services are unavailable, sender authorization fails, or the direct parent is not live.'],
      },//结束方法
      {//方法
        signature: 'registerContinuableSetup(contribution: ContinuableSetupContribution): () => void',
        description: 'Compose one deployment capability into every continuable child\'s unpublished creation context on fresh creation and cold resume. Grants wait for the next Activation; removing the contribution revokes every resident installation immediately.',
        parameters: [{ name: 'contribution', description: 'synchronous child-scope installer.' }],
        returns: 'the exact Cordis effect disposer.',
      },//结束方法
      {//方法
        signature: 'async drainContinuableDescendants(parents: readonly Agent[]): Promise<void>',
        description: 'Close continuable admission below exact live parent Agents, stop only their visible descendant Activations synchronously, then await admitted scoped materializations and release those forests child-first. The scoped cutoff lasts until each exact parent leaves the registry; unrelated parent trees remain live.',
        parameters: [{ name: 'parents', description: 'exact host-owned parent Agents entering teardown.' }],
        returns: 'once every retained descendant Activation released its `AgentHandle`.',
        throws: ['an aggregate error after all branches settle when any failed.'],
      },//结束方法
      {//方法
        signature: 'listChildren(parentSessionId: SessionId, signal?: AbortSignal): Promise<SubagentListEntry[]>',
        description: 'Enumerate the parent\'s direct session-backed subagents without loading or resuming an Agent and without any query service: the listing merges the live session store with optional session persistence (live-preferred) and serves each child\'s durable mode/label from the registered `subagent` projection unit down a three-rung ladder — the registry\'s watermark snapshot for a live child; for a cold one, a durable projection-cache row when the optional cache serves an own-suffix identity (its `seq` gate proves the value postdates the fork seed, where a child\'s own descriptor is immutable once appended), else one persistence inspection folded through the registry. The projection fold is the single classification authority; per-child diagnostics relay a fold that served no identity or a failed inspection, never a list-time descriptor parse. Absent persistence, enumeration is live-only (a cold child cannot be resumed then either, so its absence is capability absence, not an error). This service consults no Agent registrations, Activations, or providers.\n\nEvery persistence read receives `signal`, and the listing rechecks cancellation around each of those awaits. Read rejections that settle after an abort become a stable `SubagentError` with code `CANCELLED`.',
        parameters: [{ name: 'parentSessionId', description: 'parent session whose direct children are listed.' }, { name: 'signal', description: 'caller-owned cancellation forwarded to persistence reads and observed around every read await.' }],
        returns: 'children and per-child diagnostics ordered by `createdAt`, then id.',
        throws: ['{@link SubagentError} when the projection registry or the session store is not mounted, or the caller cancels the listing.'],
      },//结束方法
      {//方法
        signature: 'listDescendants(rootSessionId: SessionId, signal?: AbortSignal): Promise<SubagentDescendantListEntry[]>',
        description: 'Enumerate the root\'s complete session-backed subagent tree in stable pre-order from one live-preferred corpus, without loading or resuming an Agent. Ordinary sessions and one-shot children remain traversal nodes so continuable descendants below them are discovered; each returned entry adds its durable `parentId` and root-relative `depth`. Identity resolution, diagnostics, optional persistence, and cancellation follow the same projection-backed contract as listChildren.',
        parameters: [{ name: 'rootSessionId', description: 'session whose complete descendant tree is listed.' }, { name: 'signal', description: 'caller-owned cancellation forwarded to persistence reads and observed around every read await.' }],
        returns: 'children and per-candidate diagnostics with tree position, in stable pre-order.',
        throws: ['{@link SubagentError} under the same conditions as {@link listChildren}.'],
      },//结束方法
      {//方法
        signature: 'registerProvider(provider: SubagentProvider): () => void',
        description: 'Register a provider under its name. Registration is effect-scoped and HMR safe; removing a provider blocks new starts but does not revoke runs that were already returned to their holders.',
        parameters: [{ name: 'provider', description: 'the trusted provider implementation.' }],
        returns: 'the exact Cordis effect disposer.',
      },//结束方法
      {//方法
        signature: 'getProvider(name: string): SubagentProvider | undefined',
        description: 'Look up a provider by name.',
        parameters: [{ name: 'name', description: 'the provider name.' }],
        returns: 'the provider, or undefined when absent.',
      },//结束方法
      {//方法
        signature: 'list(): string[]',
        description: 'List registered provider names in insertion order.',
        parameters: [],//无参数
        returns: 'the registered names.',
      },//结束方法
      {//方法
        signature: 'async start(name: string, request: SubagentStartRequest): Promise<SubagentRun>',
        description: 'Establish a published child on the named provider. Capability and semantic checks run before delegation. Provider ownership lasts until its promise fulfills; a rejection therefore has no run for the caller to dispose and emits no run lifecycle events. Post-publication turn and infrastructure failures settle through the returned run.',
        parameters: [{ name: 'name', description: 'the provider to use.' }, { name: 'request', description: 'child label, prompt, parent, signal, and optional capabilities.' }],
        returns: 'the published holder-owned run.',
      },//结束方法
    ],//结束 methods
  },//结束服务
]
