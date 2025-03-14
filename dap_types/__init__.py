from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union, Annotated
from pydantic import BaseModel, Field, RootModel, TypeAdapter, ConfigDict

class DebugAdapterProtocol(BaseModel):
    model_config = ConfigDict(extra='allow')
    pass

class ProtocolMessage(BaseModel):
    model_config = ConfigDict(extra='allow')
    seq: int = Field(..., description='Sequence number of the message (also known as message ID). The `seq` for the first message sent by a client or debug adapter is 1, and for each subsequent message is 1 greater than the previous message sent by that actor. `seq` can be used to order requests, responses, and events, and to associate requests with their corresponding responses. For protocol messages of type `request` the sequence number can be used to cancel the request.')
    type: str = Field(..., description='Message type.')

class Request(ProtocolMessage):
    type: Literal['request']
    command: str = Field(..., description='The command to execute.')
    arguments: Optional[Union[List[Any], bool, int, float, Dict[str, Any], str]] = Field(None, description='Object containing arguments for the command.')

class Event(ProtocolMessage):
    type: Literal['event']
    event: str = Field(..., description='Type of event.')
    body: Optional[Union[List[Any], bool, int, float, Dict[str, Any], str]] = Field(None, description='Event-specific information.')

class Response(ProtocolMessage):
    type: Literal['response']
    request_seq: int = Field(..., description='Sequence number of the corresponding request.')
    success: bool = Field(..., description='Outcome of the request.\nIf true, the request was successful and the `body` attribute may contain the result of the request.\nIf the value is false, the attribute `message` contains the error in short form and the `body` may contain additional information (see `ErrorResponse.body.error`).')
    command: str = Field(..., description='The command requested.')
    message: Optional[str] = Field(None, description='Contains the raw error in short form if `success` is false.\nThis raw error might be interpreted by the client and is not shown in the UI.\nSome predefined values exist.')
    body: Optional[Union[List[Any], bool, int, float, Dict[str, Any], str]] = Field(None, description='Contains request result if success is true and error details if success is false.')

class CancelArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    requestId: Optional[int] = Field(None, description='The ID (attribute `seq`) of the request to cancel. If missing no request is cancelled.\nBoth a `requestId` and a `progressId` can be specified in one request.')
    progressId: Optional[str] = Field(None, description='The ID (attribute `progressId`) of the progress to cancel. If missing no progress is cancelled.\nBoth a `requestId` and a `progressId` can be specified in one request.')

class CancelResponse(Response):
    pass
    success: Literal[True]

class InitializedEvent(Event):
    event: Literal['initialized']

class StoppedEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    reason: str = Field(..., description='The reason for the event.\nFor backward compatibility this string is shown in the UI if the `description` attribute is missing (but it must not be translated).')
    description: Optional[str] = Field(None, description="The full reason for the event, e.g. 'Paused on exception'. This string is shown in the UI as is and can be translated.")
    threadId: Optional[int] = Field(None, description='The thread which was stopped.')
    preserveFocusHint: Optional[bool] = Field(None, description='A value of true hints to the client that this event should not change the focus.')
    text: Optional[str] = Field(None, description='Additional information. E.g. if reason is `exception`, text contains the exception name. This string is shown in the UI.')
    allThreadsStopped: Optional[bool] = Field(None, description='If `allThreadsStopped` is true, a debug adapter can announce that all threads have stopped.\n- The client should use this information to enable that all threads can be expanded to access their stacktraces.\n- If the attribute is missing or false, only the thread with the given `threadId` can be expanded.')
    hitBreakpointIds: Optional[List[int]] = Field(None, description='Ids of the breakpoints that triggered the event. In most cases there is only a single breakpoint but here are some examples for multiple breakpoints:\n- Different types of breakpoints map to the same location.\n- Multiple source breakpoints get collapsed to the same instruction by the compiler/runtime.\n- Multiple function breakpoints with different function names map to the same location.')

class StoppedEvent(Event):
    event: Literal['stopped']
    body: StoppedEventBody

class ContinuedEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadId: int = Field(..., description='The thread which was continued.')
    allThreadsContinued: Optional[bool] = Field(None, description='If omitted or set to `true`, this event signals to the client that all threads have been resumed. The value `false` indicates that not all threads were resumed.')

class ContinuedEvent(Event):
    event: Literal['continued']
    body: ContinuedEventBody

class ExitedEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    exitCode: int = Field(..., description='The exit code returned from the debuggee.')

class ExitedEvent(Event):
    event: Literal['exited']
    body: ExitedEventBody

class TerminatedEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    restart: Optional[Union[List[Any], bool, int, float, Dict[str, Any], str]] = Field(None, description='A debug adapter may set `restart` to true (or to an arbitrary object) to request that the client restarts the session.\nThe value is not interpreted by the client and passed unmodified as an attribute `__restart` to the `launch` and `attach` requests.')

class TerminatedEvent(Event):
    event: Literal['terminated']
    body: Optional[TerminatedEventBody] = None

class ThreadEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    reason: str = Field(..., description='The reason for the event.')
    threadId: int = Field(..., description='The identifier of the thread.')

class ThreadEvent(Event):
    event: Literal['thread']
    body: ThreadEventBody

class ProcessEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: str = Field(..., description="The logical name of the process. This is usually the full path to process's executable file. Example: /home/example/myproj/program.js.")
    systemProcessId: Optional[int] = Field(None, description='The process ID of the debugged process, as assigned by the operating system. This property should be omitted for logical processes that do not map to operating system processes on the machine.')
    isLocalProcess: Optional[bool] = Field(None, description='If true, the process is running on the same computer as the debug adapter.')
    startMethod: Optional[Literal['launch', 'attach', 'attachForSuspendedLaunch']] = Field(None, description='Describes how the debug engine started debugging this process.')
    pointerSize: Optional[int] = Field(None, description='The size of a pointer or address for this process, in bits. This value may be used by clients when formatting addresses for display.')

class ProcessEvent(Event):
    event: Literal['process']
    body: ProcessEventBody

class ProgressStartEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    progressId: str = Field(..., description='An ID that can be used in subsequent `progressUpdate` and `progressEnd` events to make them refer to the same progress reporting.\nIDs must be unique within a debug session.')
    title: str = Field(..., description='Short title of the progress reporting. Shown in the UI to describe the long running operation.')
    requestId: Optional[int] = Field(None, description='The request ID that this progress report is related to. If specified a debug adapter is expected to emit progress events for the long running request until the request has been either completed or cancelled.\nIf the request ID is omitted, the progress report is assumed to be related to some general activity of the debug adapter.')
    cancellable: Optional[bool] = Field(None, description="If true, the request that reports progress may be cancelled with a `cancel` request.\nSo this property basically controls whether the client should use UX that supports cancellation.\nClients that don't support cancellation are allowed to ignore the setting.")
    message: Optional[str] = Field(None, description='More detailed progress message.')
    percentage: Optional[float] = Field(None, description='Progress percentage to display (value range: 0 to 100). If omitted no percentage is shown.')

class ProgressStartEvent(Event):
    event: Literal['progressStart']
    body: ProgressStartEventBody

class ProgressUpdateEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    progressId: str = Field(..., description='The ID that was introduced in the initial `progressStart` event.')
    message: Optional[str] = Field(None, description='More detailed progress message. If omitted, the previous message (if any) is used.')
    percentage: Optional[float] = Field(None, description='Progress percentage to display (value range: 0 to 100). If omitted no percentage is shown.')

class ProgressUpdateEvent(Event):
    event: Literal['progressUpdate']
    body: ProgressUpdateEventBody

class ProgressEndEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    progressId: str = Field(..., description='The ID that was introduced in the initial `ProgressStartEvent`.')
    message: Optional[str] = Field(None, description='More detailed progress message. If omitted, the previous message (if any) is used.')

class ProgressEndEvent(Event):
    event: Literal['progressEnd']
    body: ProgressEndEventBody

class MemoryEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    memoryReference: str = Field(..., description='Memory reference of a memory range that has been updated.')
    offset: int = Field(..., description='Starting offset in bytes where memory has been updated. Can be negative.')
    count: int = Field(..., description='Number of bytes updated.')

class MemoryEvent(Event):
    event: Literal['memory']
    body: MemoryEventBody

class RunInTerminalRequestArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    kind: Optional[Literal['integrated', 'external']] = Field(None, description='What kind of terminal to launch. Defaults to `integrated` if not specified.')
    title: Optional[str] = Field(None, description='Title of the terminal.')
    cwd: str = Field(..., description='Working directory for the command. For non-empty, valid paths this typically results in execution of a change directory command.')
    args: List[str] = Field(..., description='List of arguments. The first argument is the command to run.')
    env: Optional[Dict[str, Optional[str]]] = Field(None, description='Environment key-value pairs that are added to or removed from the default environment.')
    argsCanBeInterpretedByShell: Optional[bool] = Field(None, description='This property should only be set if the corresponding capability `supportsArgsCanBeInterpretedByShell` is true. If the client uses an intermediary shell to launch the application, then the client must not attempt to escape characters with special meanings for the shell. The user is fully responsible for escaping as needed and that arguments using special characters may not be portable across shells.')

class RunInTerminalResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    processId: Optional[int] = Field(None, description='The process ID. The value should be less than or equal to 2147483647 (2^31-1).')
    shellProcessId: Optional[int] = Field(None, description='The process ID of the terminal shell. The value should be less than or equal to 2147483647 (2^31-1).')

class RunInTerminalResponse(Response):
    body: RunInTerminalResponseBody
    success: Literal[True]

class StartDebuggingRequestArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    configuration: Dict[str, Any] = Field(..., description="Arguments passed to the new debug session. The arguments must only contain properties understood by the `launch` or `attach` requests of the debug adapter and they must not contain any client-specific properties (e.g. `type`) or client-specific features (e.g. substitutable 'variables').")
    request: Literal['launch', 'attach'] = Field(..., description='Indicates whether the new debug session should be started with a `launch` or `attach` request.')

class StartDebuggingResponse(Response):
    pass
    success: Literal[True]

class InitializeRequestArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    clientID: Optional[str] = Field(None, description='The ID of the client using this adapter.')
    clientName: Optional[str] = Field(None, description='The human-readable name of the client using this adapter.')
    adapterID: str = Field(..., description='The ID of the debug adapter.')
    locale: Optional[str] = Field(None, description='The ISO-639 locale of the client using this adapter, e.g. en-US or de-CH.')
    linesStartAt1: Optional[bool] = Field(None, description='If true all line numbers are 1-based (default).')
    columnsStartAt1: Optional[bool] = Field(None, description='If true all column numbers are 1-based (default).')
    pathFormat: Optional[str] = Field(None, description='Determines in what format paths are specified. The default is `path`, which is the native format.')
    supportsVariableType: Optional[bool] = Field(None, description='Client supports the `type` attribute for variables.')
    supportsVariablePaging: Optional[bool] = Field(None, description='Client supports the paging of variables.')
    supportsRunInTerminalRequest: Optional[bool] = Field(None, description='Client supports the `runInTerminal` request.')
    supportsMemoryReferences: Optional[bool] = Field(None, description='Client supports memory references.')
    supportsProgressReporting: Optional[bool] = Field(None, description='Client supports progress reporting.')
    supportsInvalidatedEvent: Optional[bool] = Field(None, description='Client supports the `invalidated` event.')
    supportsMemoryEvent: Optional[bool] = Field(None, description='Client supports the `memory` event.')
    supportsArgsCanBeInterpretedByShell: Optional[bool] = Field(None, description='Client supports the `argsCanBeInterpretedByShell` attribute on the `runInTerminal` request.')
    supportsStartDebuggingRequest: Optional[bool] = Field(None, description='Client supports the `startDebugging` request.')
    supportsANSIStyling: Optional[bool] = Field(None, description='The client will interpret ANSI escape sequences in the display of `OutputEvent.output` and `Variable.value` fields when `Capabilities.supportsANSIStyling` is also enabled.')

class ConfigurationDoneArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    pass

class ConfigurationDoneResponse(Response):
    pass
    success: Literal[True]

class LaunchRequestArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    noDebug: Optional[bool] = Field(None, description='If true, the launch request should launch the program without enabling debugging.')
    field__restart: Optional[Union[List[Any], bool, int, float, Dict[str, Any], str]] = Field(None, alias='__restart', description='Arbitrary data from the previous, restarted session.\nThe data is sent as the `restart` attribute of the `terminated` event.\nThe client should leave the data intact.')

class LaunchResponse(Response):
    pass
    success: Literal[True]

class AttachRequestArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    field__restart: Optional[Union[List[Any], bool, int, float, Dict[str, Any], str]] = Field(None, alias='__restart', description='Arbitrary data from the previous, restarted session.\nThe data is sent as the `restart` attribute of the `terminated` event.\nThe client should leave the data intact.')

class AttachResponse(Response):
    pass
    success: Literal[True]

class RestartArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    arguments: Optional[Union[LaunchRequestArguments, AttachRequestArguments]] = Field(None, description='The latest version of the `launch` or `attach` configuration.')

class RestartResponse(Response):
    pass
    success: Literal[True]

class DisconnectArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    restart: Optional[bool] = Field(None, description='A value of true indicates that this `disconnect` request is part of a restart sequence.')
    terminateDebuggee: Optional[bool] = Field(None, description='Indicates whether the debuggee should be terminated when the debugger is disconnected.\nIf unspecified, the debug adapter is free to do whatever it thinks is best.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportTerminateDebuggee` is true.')
    suspendDebuggee: Optional[bool] = Field(None, description='Indicates whether the debuggee should stay suspended when the debugger is disconnected.\nIf unspecified, the debuggee should resume execution.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportSuspendDebuggee` is true.')

class DisconnectResponse(Response):
    pass
    success: Literal[True]

class TerminateArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    restart: Optional[bool] = Field(None, description='A value of true indicates that this `terminate` request is part of a restart sequence.')

class TerminateResponse(Response):
    pass
    success: Literal[True]

class DataBreakpointInfoArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    variablesReference: Optional[int] = Field(None, description="Reference to the variable container if the data breakpoint is requested for a child of the container. The `variablesReference` must have been obtained in the current suspended state. See 'Lifetime of Object References' in the Overview section for details.")
    name: str = Field(..., description="The name of the variable's child to obtain data breakpoint information for.\nIf `variablesReference` isn't specified, this can be an expression, or an address if `asAddress` is also true.")
    frameId: Optional[int] = Field(None, description='When `name` is an expression, evaluate it in the scope of this stack frame. If not specified, the expression is evaluated in the global scope. When `variablesReference` is specified, this property has no effect.')
    bytes: Optional[int] = Field(None, description='If specified, a debug adapter should return information for the range of memory extending `bytes` number of bytes from the address or variable specified by `name`. Breakpoints set using the resulting data ID should pause on data access anywhere within that range.\n\nClients may set this property only if the `supportsDataBreakpointBytes` capability is true.')
    asAddress: Optional[bool] = Field(None, description='If `true`, the `name` is a memory address and the debugger should interpret it as a decimal value, or hex value if it is prefixed with `0x`.\n\nClients may set this property only if the `supportsDataBreakpointBytes`\ncapability is true.')
    mode: Optional[str] = Field(None, description='The mode of the desired breakpoint. If defined, this must be one of the `breakpointModes` the debug adapter advertised in its `Capabilities`.')

class ContinueArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadId: int = Field(..., description='Specifies the active thread. If the debug adapter supports single thread execution (see `supportsSingleThreadExecutionRequests`) and the argument `singleThread` is true, only the thread with this ID is resumed.')
    singleThread: Optional[bool] = Field(None, description='If this flag is true, execution is resumed only for the thread with given `threadId`.')

class ContinueResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    allThreadsContinued: Optional[bool] = Field(None, description='If omitted or set to `true`, this response signals to the client that all threads have been resumed. The value `false` indicates that not all threads were resumed.')

class ContinueResponse(Response):
    body: ContinueResponseBody
    success: Literal[True]

class NextResponse(Response):
    pass
    success: Literal[True]

class StepInResponse(Response):
    pass
    success: Literal[True]

class StepOutResponse(Response):
    pass
    success: Literal[True]

class StepBackResponse(Response):
    pass
    success: Literal[True]

class ReverseContinueArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadId: int = Field(..., description='Specifies the active thread. If the debug adapter supports single thread execution (see `supportsSingleThreadExecutionRequests`) and the `singleThread` argument is true, only the thread with this ID is resumed.')
    singleThread: Optional[bool] = Field(None, description='If this flag is true, backward execution is resumed only for the thread with given `threadId`.')

class ReverseContinueResponse(Response):
    pass
    success: Literal[True]

class RestartFrameArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    frameId: int = Field(..., description="Restart the stack frame identified by `frameId`. The `frameId` must have been obtained in the current suspended state. See 'Lifetime of Object References' in the Overview section for details.")

class RestartFrameResponse(Response):
    pass
    success: Literal[True]

class GotoArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadId: int = Field(..., description='Set the goto target for this thread.')
    targetId: int = Field(..., description='The location where the debuggee will continue to run.')

class GotoResponse(Response):
    pass
    success: Literal[True]

class PauseArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadId: int = Field(..., description='Pause execution for this thread.')

class PauseResponse(Response):
    pass
    success: Literal[True]

class ScopesArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    frameId: int = Field(..., description="Retrieve the scopes for the stack frame identified by `frameId`. The `frameId` must have been obtained in the current suspended state. See 'Lifetime of Object References' in the Overview section for details.")

class SetVariableResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    value: str = Field(..., description='The new value of the variable.')
    type: Optional[str] = Field(None, description='The type of the new value. Typically shown in the UI when hovering over the value.')
    variablesReference: Optional[int] = Field(None, description="If `variablesReference` is > 0, the new value is structured and its children can be retrieved by passing `variablesReference` to the `variables` request as long as execution remains suspended. See 'Lifetime of Object References' in the Overview section for details.\n\nIf this property is included in the response, any `variablesReference` previously associated with the updated variable, and those of its children, are no longer valid.")
    namedVariables: Optional[int] = Field(None, description='The number of named child variables.\nThe client can use this information to present the variables in a paged UI and fetch them in chunks.\nThe value should be less than or equal to 2147483647 (2^31-1).')
    indexedVariables: Optional[int] = Field(None, description='The number of indexed child variables.\nThe client can use this information to present the variables in a paged UI and fetch them in chunks.\nThe value should be less than or equal to 2147483647 (2^31-1).')
    memoryReference: Optional[str] = Field(None, description='A memory reference to a location appropriate for this result.\nFor pointer type eval results, this is generally a reference to the memory address contained in the pointer.\nThis attribute may be returned by a debug adapter if corresponding capability `supportsMemoryReferences` is true.')
    valueLocationReference: Optional[int] = Field(None, description="A reference that allows the client to request the location where the new value is declared. For example, if the new value is function pointer, the adapter may be able to look up the function's location. This should be present only if the adapter is likely to be able to resolve the location.\n\nThis reference shares the same lifetime as the `variablesReference`. See 'Lifetime of Object References' in the Overview section for details.")

class SetVariableResponse(Response):
    body: SetVariableResponseBody
    success: Literal[True]

class SourceResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    content: str = Field(..., description='Content of the source reference.')
    mimeType: Optional[str] = Field(None, description='Content type (MIME type) of the source.')

class SourceResponse(Response):
    body: SourceResponseBody
    success: Literal[True]

class ThreadsRequest(Request):
    command: Literal['threads']

    @classmethod
    def discriminate_response(cls, res: Response) -> ThreadsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[ThreadsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class TerminateThreadsArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadIds: Optional[List[int]] = Field(None, description='Ids of threads to be terminated.')

class TerminateThreadsResponse(Response):
    pass
    success: Literal[True]

class ModulesArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    startModule: Optional[int] = Field(None, description='The index of the first module to return; if omitted modules start at 0.')
    moduleCount: Optional[int] = Field(None, description='The number of modules to return. If `moduleCount` is not specified or 0, all modules are returned.')

class LoadedSourcesArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    pass

class StepInTargetsArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    frameId: int = Field(..., description='The stack frame for which to retrieve the possible step-in targets.')

class CompletionsArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    frameId: Optional[int] = Field(None, description='Returns completions in the scope of this stack frame. If not specified, the completions are returned for the global scope.')
    text: str = Field(..., description='One or more source lines. Typically this is the text users have typed into the debug console before they asked for completion.')
    column: int = Field(..., description='The position within `text` for which to determine the completion proposals. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')
    line: Optional[int] = Field(None, description='A line for which to determine the completion proposals. If missing the first line of the text is assumed.')

class ExceptionInfoArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadId: int = Field(..., description='Thread for which exception information should be retrieved.')

class ReadMemoryArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    memoryReference: str = Field(..., description='Memory reference to the base location from which data should be read.')
    offset: Optional[int] = Field(None, description='Offset (in bytes) to be applied to the reference location before reading data. Can be negative.')
    count: int = Field(..., description='Number of bytes to read at the specified location and offset.')

class ReadMemoryResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    address: str = Field(..., description='The address of the first byte of data returned.\nTreated as a hex value if prefixed with `0x`, or as a decimal value otherwise.')
    unreadableBytes: Optional[int] = Field(None, description='The number of unreadable bytes encountered after the last successfully read byte.\nThis can be used to determine the number of bytes that should be skipped before a subsequent `readMemory` request succeeds.')
    data: Optional[str] = Field(None, description="The bytes read from memory, encoded using base64. If the decoded length of `data` is less than the requested `count` in the original `readMemory` request, and `unreadableBytes` is zero or omitted, then the client should assume it's reached the end of readable memory.")

class ReadMemoryResponse(Response):
    body: Optional[ReadMemoryResponseBody] = None
    success: Literal[True]

class WriteMemoryArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    memoryReference: str = Field(..., description='Memory reference to the base location to which data should be written.')
    offset: Optional[int] = Field(None, description='Offset (in bytes) to be applied to the reference location before writing data. Can be negative.')
    allowPartial: Optional[bool] = Field(None, description='Property to control partial writes. If true, the debug adapter should attempt to write memory even if the entire memory region is not writable. In such a case the debug adapter should stop after hitting the first byte of memory that cannot be written and return the number of bytes written in the response via the `offset` and `bytesWritten` properties.\nIf false or missing, a debug adapter should attempt to verify the region is writable before writing, and fail the response if it is not.')
    data: str = Field(..., description='Bytes to write, encoded using base64.')

class WriteMemoryResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    offset: Optional[int] = Field(None, description='Property that should be returned when `allowPartial` is true to indicate the offset of the first byte of data successfully written. Can be negative.')
    bytesWritten: Optional[int] = Field(None, description='Property that should be returned when `allowPartial` is true to indicate the number of bytes starting from address that were successfully written.')

class WriteMemoryResponse(Response):
    body: Optional[WriteMemoryResponseBody] = None
    success: Literal[True]

class DisassembleArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    memoryReference: str = Field(..., description='Memory reference to the base location containing the instructions to disassemble.')
    offset: Optional[int] = Field(None, description='Offset (in bytes) to be applied to the reference location before disassembling. Can be negative.')
    instructionOffset: Optional[int] = Field(None, description='Offset (in instructions) to be applied after the byte offset (if any) before disassembling. Can be negative.')
    instructionCount: int = Field(..., description="Number of instructions to disassemble starting at the specified location and offset.\nAn adapter must return exactly this number of instructions - any unavailable instructions should be replaced with an implementation-defined 'invalid instruction' value.")
    resolveSymbols: Optional[bool] = Field(None, description='If true, the adapter should attempt to resolve memory addresses and other values to symbolic names.')

class LocationsArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    locationReference: int = Field(..., description='Location reference to resolve.')

class ExceptionBreakpointsFilter(BaseModel):
    model_config = ConfigDict(extra='allow')
    filter: str = Field(..., description='The internal ID of the filter option. This value is passed to the `setExceptionBreakpoints` request.')
    label: str = Field(..., description='The name of the filter option. This is shown in the UI.')
    description: Optional[str] = Field(None, description='A help text providing additional information about the exception filter. This string is typically shown as a hover and can be translated.')
    default: Optional[bool] = Field(None, description='Initial value of the filter option. If not specified a value false is assumed.')
    supportsCondition: Optional[bool] = Field(None, description='Controls whether a condition can be specified for this filter option. If false or missing, a condition can not be set.')
    conditionDescription: Optional[str] = Field(None, description='A help text providing information about the condition. This string is shown as the placeholder text for a text box and can be translated.')

class Message(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: int = Field(..., description='Unique (within a debug adapter implementation) identifier for the message. The purpose of these error IDs is to help extension authors that have the requirement that every user visible error message needs a corresponding error number, so that users or customer support can find information about the specific error more easily.')
    format: str = Field(..., description='A format string for the message. Embedded variables have the form `{name}`.\nIf variable name starts with an underscore character, the variable does not contain user data (PII) and can be safely used for telemetry purposes.')
    variables: Optional[Dict[str, str]] = Field(None, description='An object used as a dictionary for looking up the variables in the format string.')
    sendTelemetry: Optional[bool] = Field(None, description='If true send to telemetry.')
    showUser: Optional[bool] = Field(None, description='If true show user.')
    url: Optional[str] = Field(None, description='A url where additional information about this message can be found.')
    urlLabel: Optional[str] = Field(None, description='A label that is presented to the user as the UI for opening the url.')

class Module(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: Union[int, str] = Field(..., description='Unique identifier for the module.')
    name: str = Field(..., description='A name of the module.')
    path: Optional[str] = Field(None, description='Logical full path to the module. The exact definition is implementation defined, but usually this would be a full path to the on-disk file for the module.')
    isOptimized: Optional[bool] = Field(None, description='True if the module is optimized.')
    isUserCode: Optional[bool] = Field(None, description="True if the module is considered 'user code' by a debugger that supports 'Just My Code'.")
    version: Optional[str] = Field(None, description='Version of Module.')
    symbolStatus: Optional[str] = Field(None, description="User-understandable description of if symbols were found for the module (ex: 'Symbols Loaded', 'Symbols not found', etc.)")
    symbolFilePath: Optional[str] = Field(None, description='Logical full path to the symbol file. The exact definition is implementation defined.')
    dateTimeStamp: Optional[str] = Field(None, description='Module created or modified, encoded as a RFC 3339 timestamp.')
    addressRange: Optional[str] = Field(None, description='Address range covered by this module.')

class ColumnDescriptor(BaseModel):
    model_config = ConfigDict(extra='allow')
    attributeName: str = Field(..., description='Name of the attribute rendered in this column.')
    label: str = Field(..., description='Header UI label of column.')
    format: Optional[str] = Field(None, description='Format to use for the rendered values in this column. TBD how the format strings looks like.')
    type: Optional[Literal['string', 'number', 'boolean', 'unixTimestampUTC']] = Field(None, description='Datatype of values in this column. Defaults to `string` if not specified.')
    width: Optional[int] = Field(None, description='Width of this column in characters (hint only).')

class Thread(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: int = Field(..., description='Unique identifier for the thread.')
    name: str = Field(..., description='The name of the thread.')

class VariablePresentationHint(BaseModel):
    model_config = ConfigDict(extra='allow')
    kind: Optional[str] = Field(None, description='The kind of variable. Before introducing additional values, try to use the listed values.')
    attributes: Optional[List[str]] = Field(None, description='Set of attributes represented as an array of strings. Before introducing additional values, try to use the listed values.')
    visibility: Optional[str] = Field(None, description='Visibility of variable. Before introducing additional values, try to use the listed values.')
    lazy: Optional[bool] = Field(None, description="If true, clients can present the variable with a UI that supports a specific gesture to trigger its evaluation.\nThis mechanism can be used for properties that require executing code when retrieving their value and where the code execution can be expensive and/or produce side-effects. A typical example are properties based on a getter function.\nPlease note that in addition to the `lazy` flag, the variable's `variablesReference` is expected to refer to a variable that will provide the value through another `variable` request.")

class BreakpointLocation(BaseModel):
    model_config = ConfigDict(extra='allow')
    line: int = Field(..., description='Start line of breakpoint location.')
    column: Optional[int] = Field(None, description='The start position of a breakpoint location. Position is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')
    endLine: Optional[int] = Field(None, description='The end line of breakpoint location if the location covers a range.')
    endColumn: Optional[int] = Field(None, description='The end position of a breakpoint location (if the location covers a range). Position is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')

class SourceBreakpoint(BaseModel):
    model_config = ConfigDict(extra='allow')
    line: int = Field(..., description='The source line of the breakpoint or logpoint.')
    column: Optional[int] = Field(None, description='Start position within source line of the breakpoint or logpoint. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')
    condition: Optional[str] = Field(None, description='The expression for conditional breakpoints.\nIt is only honored by a debug adapter if the corresponding capability `supportsConditionalBreakpoints` is true.')
    hitCondition: Optional[str] = Field(None, description='The expression that controls how many hits of the breakpoint are ignored.\nThe debug adapter is expected to interpret the expression as needed.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportsHitConditionalBreakpoints` is true.\nIf both this property and `condition` are specified, `hitCondition` should be evaluated only if the `condition` is met, and the debug adapter should stop only if both conditions are met.')
    logMessage: Optional[str] = Field(None, description="If this attribute exists and is non-empty, the debug adapter must not 'break' (stop)\nbut log the message instead. Expressions within `{}` are interpolated.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportsLogPoints` is true.\nIf either `hitCondition` or `condition` is specified, then the message should only be logged if those conditions are met.")
    mode: Optional[str] = Field(None, description='The mode of this breakpoint. If defined, this must be one of the `breakpointModes` the debug adapter advertised in its `Capabilities`.')

class FunctionBreakpoint(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: str = Field(..., description='The name of the function.')
    condition: Optional[str] = Field(None, description='An expression for conditional breakpoints.\nIt is only honored by a debug adapter if the corresponding capability `supportsConditionalBreakpoints` is true.')
    hitCondition: Optional[str] = Field(None, description='An expression that controls how many hits of the breakpoint are ignored.\nThe debug adapter is expected to interpret the expression as needed.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportsHitConditionalBreakpoints` is true.')

class DataBreakpointAccessType(RootModel[Literal['read', 'write', 'readWrite']]):
    root: Literal['read', 'write', 'readWrite'] = Field(..., description='This enumeration defines all possible access types for data breakpoints.')

class DataBreakpoint(BaseModel):
    model_config = ConfigDict(extra='allow')
    dataId: str = Field(..., description='An id representing the data. This id is returned from the `dataBreakpointInfo` request.')
    accessType: Optional[DataBreakpointAccessType] = Field(None, description='The access type of the data.')
    condition: Optional[str] = Field(None, description='An expression for conditional breakpoints.')
    hitCondition: Optional[str] = Field(None, description='An expression that controls how many hits of the breakpoint are ignored.\nThe debug adapter is expected to interpret the expression as needed.')

class InstructionBreakpoint(BaseModel):
    model_config = ConfigDict(extra='allow')
    instructionReference: str = Field(..., description='The instruction reference of the breakpoint.\nThis should be a memory or instruction pointer reference from an `EvaluateResponse`, `Variable`, `StackFrame`, `GotoTarget`, or `Breakpoint`.')
    offset: Optional[int] = Field(None, description='The offset from the instruction reference in bytes.\nThis can be negative.')
    condition: Optional[str] = Field(None, description='An expression for conditional breakpoints.\nIt is only honored by a debug adapter if the corresponding capability `supportsConditionalBreakpoints` is true.')
    hitCondition: Optional[str] = Field(None, description='An expression that controls how many hits of the breakpoint are ignored.\nThe debug adapter is expected to interpret the expression as needed.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportsHitConditionalBreakpoints` is true.')
    mode: Optional[str] = Field(None, description='The mode of this breakpoint. If defined, this must be one of the `breakpointModes` the debug adapter advertised in its `Capabilities`.')

class SteppingGranularity(RootModel[Literal['statement', 'line', 'instruction']]):
    root: Literal['statement', 'line', 'instruction'] = Field(..., description="The granularity of one 'step' in the stepping requests `next`, `stepIn`, `stepOut`, and `stepBack`.")

class StepInTarget(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: int = Field(..., description='Unique identifier for a step-in target.')
    label: str = Field(..., description='The name of the step-in target (shown in the UI).')
    line: Optional[int] = Field(None, description='The line of the step-in target.')
    column: Optional[int] = Field(None, description='Start position of the range covered by the step in target. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')
    endLine: Optional[int] = Field(None, description='The end line of the range covered by the step-in target.')
    endColumn: Optional[int] = Field(None, description='End position of the range covered by the step in target. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')

class GotoTarget(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: int = Field(..., description='Unique identifier for a goto target. This is used in the `goto` request.')
    label: str = Field(..., description='The name of the goto target (shown in the UI).')
    line: int = Field(..., description='The line of the goto target.')
    column: Optional[int] = Field(None, description='The column of the goto target.')
    endLine: Optional[int] = Field(None, description='The end line of the range covered by the goto target.')
    endColumn: Optional[int] = Field(None, description='The end column of the range covered by the goto target.')
    instructionPointerReference: Optional[str] = Field(None, description='A memory reference for the instruction pointer value represented by this target.')

class CompletionItemType(RootModel[Literal['method', 'function', 'constructor', 'field', 'variable', 'class', 'interface', 'module', 'property', 'unit', 'value', 'enum', 'keyword', 'snippet', 'text', 'color', 'file', 'reference', 'customcolor']]):
    root: Literal['method', 'function', 'constructor', 'field', 'variable', 'class', 'interface', 'module', 'property', 'unit', 'value', 'enum', 'keyword', 'snippet', 'text', 'color', 'file', 'reference', 'customcolor'] = Field(..., description='Some predefined types for the CompletionItem. Please note that not all clients have specific icons for all of them.')

class ChecksumAlgorithm(RootModel[Literal['MD5', 'SHA1', 'SHA256', 'timestamp']]):
    root: Literal['MD5', 'SHA1', 'SHA256', 'timestamp'] = Field(..., description='Names of checksum algorithms that may be supported by a debug adapter.')

class Checksum(BaseModel):
    model_config = ConfigDict(extra='allow')
    algorithm: ChecksumAlgorithm = Field(..., description='The algorithm used to calculate this checksum.')
    checksum: str = Field(..., description='Value of the checksum, encoded as a hexadecimal value.')

class ValueFormat(BaseModel):
    model_config = ConfigDict(extra='allow')
    hex: Optional[bool] = Field(None, description='Display the value in hex.')

class StackFrameFormat(ValueFormat):
    parameters: Optional[bool] = Field(None, description='Displays parameters for the stack frame.')
    parameterTypes: Optional[bool] = Field(None, description='Displays the types of parameters for the stack frame.')
    parameterNames: Optional[bool] = Field(None, description='Displays the names of parameters for the stack frame.')
    parameterValues: Optional[bool] = Field(None, description='Displays the values of parameters for the stack frame.')
    line: Optional[bool] = Field(None, description='Displays the line number of the stack frame.')
    module: Optional[bool] = Field(None, description='Displays the module of the stack frame.')
    includeAll: Optional[bool] = Field(None, description='Includes all stack frames, including those the debug adapter might otherwise hide.')

class ExceptionFilterOptions(BaseModel):
    model_config = ConfigDict(extra='allow')
    filterId: str = Field(..., description='ID of an exception filter returned by the `exceptionBreakpointFilters` capability.')
    condition: Optional[str] = Field(None, description='An expression for conditional exceptions.\nThe exception breaks into the debugger if the result of the condition is true.')
    mode: Optional[str] = Field(None, description='The mode of this exception breakpoint. If defined, this must be one of the `breakpointModes` the debug adapter advertised in its `Capabilities`.')

class ExceptionBreakMode(RootModel[Literal['never', 'always', 'unhandled', 'userUnhandled']]):
    root: Literal['never', 'always', 'unhandled', 'userUnhandled'] = Field(..., description='This enumeration defines all possible conditions when a thrown exception should result in a break.\nnever: never breaks,\nalways: always breaks,\nunhandled: breaks when exception unhandled,\nuserUnhandled: breaks if the exception is not handled by user code.')

class ExceptionPathSegment(BaseModel):
    model_config = ConfigDict(extra='allow')
    negate: Optional[bool] = Field(None, description='If false or missing this segment matches the names provided, otherwise it matches anything except the names provided.')
    names: List[str] = Field(..., description='Depending on the value of `negate` the names that should match or not match.')

class ExceptionDetails(BaseModel):
    model_config = ConfigDict(extra='allow')
    message: Optional[str] = Field(None, description='Message contained in the exception.')
    typeName: Optional[str] = Field(None, description='Short type name of the exception object.')
    fullTypeName: Optional[str] = Field(None, description='Fully-qualified type name of the exception object.')
    evaluateName: Optional[str] = Field(None, description='An expression that can be evaluated in the current scope to obtain the exception object.')
    stackTrace: Optional[str] = Field(None, description='Stack trace at the time the exception was thrown.')
    innerException: Optional[List[ExceptionDetails]] = Field(None, description='Details of the exception contained by this exception, if any.')

class InvalidatedAreas(RootModel[str]):
    root: str = Field(..., description='Logical areas that can be invalidated by the `invalidated` event.')

class BreakpointModeApplicability(RootModel[str]):
    root: str = Field(..., description='Describes one or more type of breakpoint a `BreakpointMode` applies to. This is a non-exhaustive enumeration and may expand as future breakpoint types are added.')

class ErrorResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    error: Optional[Message] = Field(None, description='A structured error message.')

class ErrorResponse(Response):
    body: ErrorResponseBody
    success: Literal[False]

class CancelRequest(Request):
    command: Literal['cancel']
    arguments: Optional[CancelArguments] = None

    @classmethod
    def discriminate_response(cls, res: Response) -> CancelResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[CancelResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class ModuleEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    reason: Literal['new', 'changed', 'removed'] = Field(..., description='The reason for the event.')
    module: Module = Field(..., description='The new, changed, or removed module. In case of `removed` only the module id is used.')

class ModuleEvent(Event):
    event: Literal['module']
    body: ModuleEventBody

class InvalidatedEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    areas: Optional[List[InvalidatedAreas]] = Field(None, description="Set of logical areas that got invalidated. This property has a hint characteristic: a client can only be expected to make a 'best effort' in honoring the areas but there are no guarantees. If this property is missing, empty, or if values are not understood, the client should assume a single value `all`.")
    threadId: Optional[int] = Field(None, description='If specified, the client only needs to refetch data related to this thread.')
    stackFrameId: Optional[int] = Field(None, description='If specified, the client only needs to refetch data related to this stack frame (and the `threadId` is ignored).')

class InvalidatedEvent(Event):
    event: Literal['invalidated']
    body: InvalidatedEventBody

class RunInTerminalRequest(Request):
    command: Literal['runInTerminal']
    arguments: RunInTerminalRequestArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> RunInTerminalResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[RunInTerminalResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class StartDebuggingRequest(Request):
    command: Literal['startDebugging']
    arguments: StartDebuggingRequestArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> StartDebuggingResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[StartDebuggingResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class InitializeRequest(Request):
    command: Literal['initialize']
    arguments: InitializeRequestArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> InitializeResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[InitializeResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class ConfigurationDoneRequest(Request):
    command: Literal['configurationDone']
    arguments: Optional[ConfigurationDoneArguments] = None

    @classmethod
    def discriminate_response(cls, res: Response) -> ConfigurationDoneResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[ConfigurationDoneResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class LaunchRequest(Request):
    command: Literal['launch']
    arguments: LaunchRequestArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> LaunchResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[LaunchResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class AttachRequest(Request):
    command: Literal['attach']
    arguments: AttachRequestArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> AttachResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[AttachResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class RestartRequest(Request):
    command: Literal['restart']
    arguments: Optional[RestartArguments] = None

    @classmethod
    def discriminate_response(cls, res: Response) -> RestartResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[RestartResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class DisconnectRequest(Request):
    command: Literal['disconnect']
    arguments: Optional[DisconnectArguments] = None

    @classmethod
    def discriminate_response(cls, res: Response) -> DisconnectResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[DisconnectResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class TerminateRequest(Request):
    command: Literal['terminate']
    arguments: Optional[TerminateArguments] = None

    @classmethod
    def discriminate_response(cls, res: Response) -> TerminateResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[TerminateResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class BreakpointLocationsResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    breakpoints: List[BreakpointLocation] = Field(..., description='Sorted set of possible breakpoint locations.')

class BreakpointLocationsResponse(Response):
    body: BreakpointLocationsResponseBody
    success: Literal[True]

class SetFunctionBreakpointsArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    breakpoints: List[FunctionBreakpoint] = Field(..., description='The function names of the breakpoints.')

class DataBreakpointInfoRequest(Request):
    command: Literal['dataBreakpointInfo']
    arguments: DataBreakpointInfoArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> DataBreakpointInfoResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[DataBreakpointInfoResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class DataBreakpointInfoResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    dataId: Optional[str] = Field(..., description="An identifier for the data on which a data breakpoint can be registered with the `setDataBreakpoints` request or null if no data breakpoint is available. If a `variablesReference` or `frameId` is passed, the `dataId` is valid in the current suspended state, otherwise it's valid indefinitely. See 'Lifetime of Object References' in the Overview section for details. Breakpoints set using the `dataId` in the `setDataBreakpoints` request may outlive the lifetime of the associated `dataId`.")
    description: str = Field(..., description='UI string that describes on what data the breakpoint is set on or why a data breakpoint is not available.')
    accessTypes: Optional[List[DataBreakpointAccessType]] = Field(None, description='Attribute lists the available access types for a potential data breakpoint. A UI client could surface this information.')
    canPersist: Optional[bool] = Field(None, description='Attribute indicates that a potential data breakpoint could be persisted across sessions.')

class DataBreakpointInfoResponse(Response):
    body: DataBreakpointInfoResponseBody
    success: Literal[True]

class SetDataBreakpointsArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    breakpoints: List[DataBreakpoint] = Field(..., description='The contents of this array replaces all existing data breakpoints. An empty array clears all data breakpoints.')

class SetInstructionBreakpointsArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    breakpoints: List[InstructionBreakpoint] = Field(..., description='The instruction references of the breakpoints')

class ContinueRequest(Request):
    command: Literal['continue']
    arguments: ContinueArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> ContinueResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[ContinueResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class NextArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadId: int = Field(..., description='Specifies the thread for which to resume execution for one step (of the given granularity).')
    singleThread: Optional[bool] = Field(None, description='If this flag is true, all other suspended threads are not resumed.')
    granularity: Optional[SteppingGranularity] = Field(None, description='Stepping granularity. If no granularity is specified, a granularity of `statement` is assumed.')

class StepInArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadId: int = Field(..., description='Specifies the thread for which to resume execution for one step-into (of the given granularity).')
    singleThread: Optional[bool] = Field(None, description='If this flag is true, all other suspended threads are not resumed.')
    targetId: Optional[int] = Field(None, description='Id of the target to step into.')
    granularity: Optional[SteppingGranularity] = Field(None, description='Stepping granularity. If no granularity is specified, a granularity of `statement` is assumed.')

class StepOutArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadId: int = Field(..., description='Specifies the thread for which to resume execution for one step-out (of the given granularity).')
    singleThread: Optional[bool] = Field(None, description='If this flag is true, all other suspended threads are not resumed.')
    granularity: Optional[SteppingGranularity] = Field(None, description='Stepping granularity. If no granularity is specified, a granularity of `statement` is assumed.')

class StepBackArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadId: int = Field(..., description='Specifies the thread for which to resume execution for one step backwards (of the given granularity).')
    singleThread: Optional[bool] = Field(None, description='If this flag is true, all other suspended threads are not resumed.')
    granularity: Optional[SteppingGranularity] = Field(None, description='Stepping granularity to step. If no granularity is specified, a granularity of `statement` is assumed.')

class ReverseContinueRequest(Request):
    command: Literal['reverseContinue']
    arguments: ReverseContinueArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> ReverseContinueResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[ReverseContinueResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class RestartFrameRequest(Request):
    command: Literal['restartFrame']
    arguments: RestartFrameArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> RestartFrameResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[RestartFrameResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class GotoRequest(Request):
    command: Literal['goto']
    arguments: GotoArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> GotoResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[GotoResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class PauseRequest(Request):
    command: Literal['pause']
    arguments: PauseArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> PauseResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[PauseResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class StackTraceArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    threadId: int = Field(..., description='Retrieve the stacktrace for this thread.')
    startFrame: Optional[int] = Field(None, description='The index of the first frame to return; if omitted frames start at 0.')
    levels: Optional[int] = Field(None, description='The maximum number of frames to return. If levels is not specified or 0, all frames are returned.')
    format: Optional[StackFrameFormat] = Field(None, description='Specifies details on how to format the returned `StackFrame.name`. The debug adapter may format requested details in any way that would make sense to a developer.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportsValueFormattingOptions` is true.')

class ScopesRequest(Request):
    command: Literal['scopes']
    arguments: ScopesArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> ScopesResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[ScopesResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class VariablesArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    variablesReference: int = Field(..., description="The variable for which to retrieve its children. The `variablesReference` must have been obtained in the current suspended state. See 'Lifetime of Object References' in the Overview section for details.")
    filter: Optional[Literal['indexed', 'named']] = Field(None, description='Filter to limit the child variables to either named or indexed. If omitted, both types are fetched.')
    start: Optional[int] = Field(None, description='The index of the first variable to return; if omitted children start at 0.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportsVariablePaging` is true.')
    count: Optional[int] = Field(None, description='The number of variables to return. If count is missing or 0, all variables are returned.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportsVariablePaging` is true.')
    format: Optional[ValueFormat] = Field(None, description='Specifies details on how to format the Variable values.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportsValueFormattingOptions` is true.')

class SetVariableArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    variablesReference: int = Field(..., description="The reference of the variable container. The `variablesReference` must have been obtained in the current suspended state. See 'Lifetime of Object References' in the Overview section for details.")
    name: str = Field(..., description='The name of the variable in the container.')
    value: str = Field(..., description='The value of the variable.')
    format: Optional[ValueFormat] = Field(None, description='Specifies details on how to format the response value.')

class ThreadsResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    threads: List[Thread] = Field(..., description='All threads.')

class ThreadsResponse(Response):
    body: ThreadsResponseBody
    success: Literal[True]

class TerminateThreadsRequest(Request):
    command: Literal['terminateThreads']
    arguments: TerminateThreadsArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> TerminateThreadsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[TerminateThreadsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class ModulesRequest(Request):
    command: Literal['modules']
    arguments: ModulesArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> ModulesResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[ModulesResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class ModulesResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    modules: List[Module] = Field(..., description='All modules or range of modules.')
    totalModules: Optional[int] = Field(None, description='The total number of modules available.')

class ModulesResponse(Response):
    body: ModulesResponseBody
    success: Literal[True]

class LoadedSourcesRequest(Request):
    command: Literal['loadedSources']
    arguments: Optional[LoadedSourcesArguments] = None

    @classmethod
    def discriminate_response(cls, res: Response) -> LoadedSourcesResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[LoadedSourcesResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class EvaluateResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    result: str = Field(..., description='The result of the evaluate request.')
    type: Optional[str] = Field(None, description='The type of the evaluate result.\nThis attribute should only be returned by a debug adapter if the corresponding capability `supportsVariableType` is true.')
    presentationHint: Optional[VariablePresentationHint] = Field(None, description='Properties of an evaluate result that can be used to determine how to render the result in the UI.')
    variablesReference: int = Field(..., description="If `variablesReference` is > 0, the evaluate result is structured and its children can be retrieved by passing `variablesReference` to the `variables` request as long as execution remains suspended. See 'Lifetime of Object References' in the Overview section for details.")
    namedVariables: Optional[int] = Field(None, description='The number of named child variables.\nThe client can use this information to present the variables in a paged UI and fetch them in chunks.\nThe value should be less than or equal to 2147483647 (2^31-1).')
    indexedVariables: Optional[int] = Field(None, description='The number of indexed child variables.\nThe client can use this information to present the variables in a paged UI and fetch them in chunks.\nThe value should be less than or equal to 2147483647 (2^31-1).')
    memoryReference: Optional[str] = Field(None, description='A memory reference to a location appropriate for this result.\nFor pointer type eval results, this is generally a reference to the memory address contained in the pointer.\nThis attribute may be returned by a debug adapter if corresponding capability `supportsMemoryReferences` is true.')
    valueLocationReference: Optional[int] = Field(None, description="A reference that allows the client to request the location where the returned value is declared. For example, if a function pointer is returned, the adapter may be able to look up the function's location. This should be present only if the adapter is likely to be able to resolve the location.\n\nThis reference shares the same lifetime as the `variablesReference`. See 'Lifetime of Object References' in the Overview section for details.")

class EvaluateResponse(Response):
    body: EvaluateResponseBody
    success: Literal[True]

class SetExpressionArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    expression: str = Field(..., description='The l-value expression to assign to.')
    value: str = Field(..., description='The value expression to assign to the l-value expression.')
    frameId: Optional[int] = Field(None, description='Evaluate the expressions in the scope of this stack frame. If not specified, the expressions are evaluated in the global scope.')
    format: Optional[ValueFormat] = Field(None, description='Specifies how the resulting value should be formatted.')

class SetExpressionResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    value: str = Field(..., description='The new value of the expression.')
    type: Optional[str] = Field(None, description='The type of the value.\nThis attribute should only be returned by a debug adapter if the corresponding capability `supportsVariableType` is true.')
    presentationHint: Optional[VariablePresentationHint] = Field(None, description='Properties of a value that can be used to determine how to render the result in the UI.')
    variablesReference: Optional[int] = Field(None, description="If `variablesReference` is > 0, the evaluate result is structured and its children can be retrieved by passing `variablesReference` to the `variables` request as long as execution remains suspended. See 'Lifetime of Object References' in the Overview section for details.")
    namedVariables: Optional[int] = Field(None, description='The number of named child variables.\nThe client can use this information to present the variables in a paged UI and fetch them in chunks.\nThe value should be less than or equal to 2147483647 (2^31-1).')
    indexedVariables: Optional[int] = Field(None, description='The number of indexed child variables.\nThe client can use this information to present the variables in a paged UI and fetch them in chunks.\nThe value should be less than or equal to 2147483647 (2^31-1).')
    memoryReference: Optional[str] = Field(None, description='A memory reference to a location appropriate for this result.\nFor pointer type eval results, this is generally a reference to the memory address contained in the pointer.\nThis attribute may be returned by a debug adapter if corresponding capability `supportsMemoryReferences` is true.')
    valueLocationReference: Optional[int] = Field(None, description="A reference that allows the client to request the location where the new value is declared. For example, if the new value is function pointer, the adapter may be able to look up the function's location. This should be present only if the adapter is likely to be able to resolve the location.\n\nThis reference shares the same lifetime as the `variablesReference`. See 'Lifetime of Object References' in the Overview section for details.")

class SetExpressionResponse(Response):
    body: SetExpressionResponseBody
    success: Literal[True]

class StepInTargetsRequest(Request):
    command: Literal['stepInTargets']
    arguments: StepInTargetsArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> StepInTargetsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[StepInTargetsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class StepInTargetsResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    targets: List[StepInTarget] = Field(..., description='The possible step-in targets of the specified source location.')

class StepInTargetsResponse(Response):
    body: StepInTargetsResponseBody
    success: Literal[True]

class GotoTargetsResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    targets: List[GotoTarget] = Field(..., description='The possible goto targets of the specified location.')

class GotoTargetsResponse(Response):
    body: GotoTargetsResponseBody
    success: Literal[True]

class CompletionsRequest(Request):
    command: Literal['completions']
    arguments: CompletionsArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> CompletionsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[CompletionsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class ExceptionInfoRequest(Request):
    command: Literal['exceptionInfo']
    arguments: ExceptionInfoArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> ExceptionInfoResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[ExceptionInfoResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class ExceptionInfoResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    exceptionId: str = Field(..., description='ID of the exception that was thrown.')
    description: Optional[str] = Field(None, description='Descriptive text for the exception.')
    breakMode: ExceptionBreakMode = Field(..., description='Mode that caused the exception notification to be raised.')
    details: Optional[ExceptionDetails] = Field(None, description='Detailed information about the exception.')

class ExceptionInfoResponse(Response):
    body: ExceptionInfoResponseBody
    success: Literal[True]

class ReadMemoryRequest(Request):
    command: Literal['readMemory']
    arguments: ReadMemoryArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> ReadMemoryResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[ReadMemoryResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class WriteMemoryRequest(Request):
    command: Literal['writeMemory']
    arguments: WriteMemoryArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> WriteMemoryResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[WriteMemoryResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class DisassembleRequest(Request):
    command: Literal['disassemble']
    arguments: DisassembleArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> DisassembleResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[DisassembleResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class LocationsRequest(Request):
    command: Literal['locations']
    arguments: LocationsArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> LocationsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[LocationsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class Source(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: Optional[str] = Field(None, description='The short name of the source. Every source returned from the debug adapter has a name.\nWhen sending a source to the debug adapter this name is optional.')
    path: Optional[str] = Field(None, description='The path of the source to be shown in the UI.\nIt is only used to locate and load the content of the source if no `sourceReference` is specified (or its value is 0).')
    sourceReference: Optional[int] = Field(None, description='If the value > 0 the contents of the source must be retrieved through the `source` request (even if a path is specified).\nSince a `sourceReference` is only valid for a session, it can not be used to persist a source.\nThe value should be less than or equal to 2147483647 (2^31-1).')
    presentationHint: Optional[Literal['normal', 'emphasize', 'deemphasize']] = Field(None, description='A hint for how to present the source in the UI.\nA value of `deemphasize` can be used to indicate that the source is not available or that it is skipped on stepping.')
    origin: Optional[str] = Field(None, description="The origin of this source. For example, 'internal module', 'inlined content from source map', etc.")
    sources: Optional[List[Source]] = Field(None, description='A list of sources that are related to this source. These may be the source that generated this source.')
    adapterData: Optional[Union[List[Any], bool, int, float, Dict[str, Any], str]] = Field(None, description='Additional data that a debug adapter might want to loop through the client.\nThe client should leave the data intact and persist it across sessions. The client should not interpret the data.')
    checksums: Optional[List[Checksum]] = Field(None, description='The checksums associated with this file.')

class StackFrame(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: int = Field(..., description='An identifier for the stack frame. It must be unique across all threads.\nThis id can be used to retrieve the scopes of the frame with the `scopes` request or to restart the execution of a stack frame.')
    name: str = Field(..., description='The name of the stack frame, typically a method name.')
    source: Optional[Source] = Field(None, description='The source of the frame.')
    line: int = Field(..., description="The line within the source of the frame. If the source attribute is missing or doesn't exist, `line` is 0 and should be ignored by the client.")
    column: int = Field(..., description="Start position of the range covered by the stack frame. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based. If attribute `source` is missing or doesn't exist, `column` is 0 and should be ignored by the client.")
    endLine: Optional[int] = Field(None, description='The end line of the range covered by the stack frame.')
    endColumn: Optional[int] = Field(None, description='End position of the range covered by the stack frame. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')
    canRestart: Optional[bool] = Field(None, description='Indicates whether this frame can be restarted with the `restartFrame` request. Clients should only use this if the debug adapter supports the `restart` request and the corresponding capability `supportsRestartFrame` is true. If a debug adapter has this capability, then `canRestart` defaults to `true` if the property is absent.')
    instructionPointerReference: Optional[str] = Field(None, description='A memory reference for the current instruction pointer in this frame.')
    moduleId: Optional[Union[int, str]] = Field(None, description='The module associated with this frame, if any.')
    presentationHint: Optional[Literal['normal', 'label', 'subtle']] = Field(None, description="A hint for how to present this frame in the UI.\nA value of `label` can be used to indicate that the frame is an artificial frame that is used as a visual label or separator. A value of `subtle` can be used to change the appearance of a frame in a 'subtle' way.")

class Scope(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: str = Field(..., description="Name of the scope such as 'Arguments', 'Locals', or 'Registers'. This string is shown in the UI as is and can be translated.")
    presentationHint: Optional[str] = Field(None, description='A hint for how to present this scope in the UI. If this attribute is missing, the scope is shown with a generic UI.')
    variablesReference: int = Field(..., description="The variables of this scope can be retrieved by passing the value of `variablesReference` to the `variables` request as long as execution remains suspended. See 'Lifetime of Object References' in the Overview section for details.")
    namedVariables: Optional[int] = Field(None, description='The number of named variables in this scope.\nThe client can use this information to present the variables in a paged UI and fetch them in chunks.')
    indexedVariables: Optional[int] = Field(None, description='The number of indexed variables in this scope.\nThe client can use this information to present the variables in a paged UI and fetch them in chunks.')
    expensive: bool = Field(..., description='If true, the number of variables in this scope is large or expensive to retrieve.')
    source: Optional[Source] = Field(None, description='The source for this scope.')
    line: Optional[int] = Field(None, description='The start line of the range covered by this scope.')
    column: Optional[int] = Field(None, description='Start position of the range covered by the scope. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')
    endLine: Optional[int] = Field(None, description='The end line of the range covered by this scope.')
    endColumn: Optional[int] = Field(None, description='End position of the range covered by the scope. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')

class Variable(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: str = Field(..., description="The variable's name.")
    value: str = Field(..., description="The variable's value.\nThis can be a multi-line text, e.g. for a function the body of a function.\nFor structured variables (which do not have a simple value), it is recommended to provide a one-line representation of the structured object. This helps to identify the structured object in the collapsed state when its children are not yet visible.\nAn empty string can be used if no value should be shown in the UI.")
    type: Optional[str] = Field(None, description="The type of the variable's value. Typically shown in the UI when hovering over the value.\nThis attribute should only be returned by a debug adapter if the corresponding capability `supportsVariableType` is true.")
    presentationHint: Optional[VariablePresentationHint] = Field(None, description='Properties of a variable that can be used to determine how to render the variable in the UI.')
    evaluateName: Optional[str] = Field(None, description="The evaluatable name of this variable which can be passed to the `evaluate` request to fetch the variable's value.")
    variablesReference: int = Field(..., description="If `variablesReference` is > 0, the variable is structured and its children can be retrieved by passing `variablesReference` to the `variables` request as long as execution remains suspended. See 'Lifetime of Object References' in the Overview section for details.")
    namedVariables: Optional[int] = Field(None, description='The number of named child variables.\nThe client can use this information to present the children in a paged UI and fetch them in chunks.')
    indexedVariables: Optional[int] = Field(None, description='The number of indexed child variables.\nThe client can use this information to present the children in a paged UI and fetch them in chunks.')
    memoryReference: Optional[str] = Field(None, description='A memory reference associated with this variable.\nFor pointer type variables, this is generally a reference to the memory address contained in the pointer.\nFor executable data, this reference may later be used in a `disassemble` request.\nThis attribute may be returned by a debug adapter if corresponding capability `supportsMemoryReferences` is true.')
    declarationLocationReference: Optional[int] = Field(None, description="A reference that allows the client to request the location where the variable is declared. This should be present only if the adapter is likely to be able to resolve the location.\n\nThis reference shares the same lifetime as the `variablesReference`. See 'Lifetime of Object References' in the Overview section for details.")
    valueLocationReference: Optional[int] = Field(None, description="A reference that allows the client to request the location where the variable's value is declared. For example, if the variable contains a function pointer, the adapter may be able to look up the function's location. This should be present only if the adapter is likely to be able to resolve the location.\n\nThis reference shares the same lifetime as the `variablesReference`. See 'Lifetime of Object References' in the Overview section for details.")

class Breakpoint(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: Optional[int] = Field(None, description='The identifier for the breakpoint. It is needed if breakpoint events are used to update or remove breakpoints.')
    verified: bool = Field(..., description='If true, the breakpoint could be set (but not necessarily at the desired location).')
    message: Optional[str] = Field(None, description='A message about the state of the breakpoint.\nThis is shown to the user and can be used to explain why a breakpoint could not be verified.')
    source: Optional[Source] = Field(None, description='The source where the breakpoint is located.')
    line: Optional[int] = Field(None, description='The start line of the actual range covered by the breakpoint.')
    column: Optional[int] = Field(None, description='Start position of the source range covered by the breakpoint. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')
    endLine: Optional[int] = Field(None, description='The end line of the actual range covered by the breakpoint.')
    endColumn: Optional[int] = Field(None, description='End position of the source range covered by the breakpoint. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.\nIf no end line is given, then the end column is assumed to be in the start line.')
    instructionReference: Optional[str] = Field(None, description='A memory reference to where the breakpoint is set.')
    offset: Optional[int] = Field(None, description='The offset from the instruction reference.\nThis can be negative.')
    reason: Optional[Literal['pending', 'failed']] = Field(None, description='A machine-readable explanation of why a breakpoint may not be verified. If a breakpoint is verified or a specific reason is not known, the adapter should omit this property. Possible values include:\n\n- `pending`: Indicates a breakpoint might be verified in the future, but the adapter cannot verify it in the current state.\n - `failed`: Indicates a breakpoint was not able to be verified, and the adapter does not believe it can be verified without intervention.')

class CompletionItem(BaseModel):
    model_config = ConfigDict(extra='allow')
    label: str = Field(..., description='The label of this completion item. By default this is also the text that is inserted when selecting this completion.')
    text: Optional[str] = Field(None, description='If text is returned and not an empty string, then it is inserted instead of the label.')
    sortText: Optional[str] = Field(None, description='A string that should be used when comparing this item with other items. If not returned or an empty string, the `label` is used instead.')
    detail: Optional[str] = Field(None, description='A human-readable string with additional information about this item, like type or symbol information.')
    type: Optional[CompletionItemType] = Field(None, description="The item's type. Typically the client uses this information to render the item in the UI with an icon.")
    start: Optional[int] = Field(None, description='Start position (within the `text` attribute of the `completions` request) where the completion text is added. The position is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based. If the start position is omitted the text is added at the location specified by the `column` attribute of the `completions` request.')
    length: Optional[int] = Field(None, description='Length determines how many characters are overwritten by the completion text and it is measured in UTF-16 code units. If missing the value 0 is assumed which results in the completion text being inserted.')
    selectionStart: Optional[int] = Field(None, description='Determines the start of the new selection after the text has been inserted (or replaced). `selectionStart` is measured in UTF-16 code units and must be in the range 0 and length of the completion text. If omitted the selection starts at the end of the completion text.')
    selectionLength: Optional[int] = Field(None, description='Determines the length of the new selection after the text has been inserted (or replaced) and it is measured in UTF-16 code units. The selection can not extend beyond the bounds of the completion text. If omitted the length is assumed to be 0.')

class ExceptionOptions(BaseModel):
    model_config = ConfigDict(extra='allow')
    path: Optional[List[ExceptionPathSegment]] = Field(None, description='A path that selects a single or multiple exceptions in a tree. If `path` is missing, the whole tree is selected.\nBy convention the first segment of the path is a category that is used to group exceptions in the UI.')
    breakMode: ExceptionBreakMode = Field(..., description='Condition when a thrown exception should result in a break.')

class DisassembledInstruction(BaseModel):
    model_config = ConfigDict(extra='allow')
    address: str = Field(..., description='The address of the instruction. Treated as a hex value if prefixed with `0x`, or as a decimal value otherwise.')
    instructionBytes: Optional[str] = Field(None, description='Raw bytes representing the instruction and its operands, in an implementation-defined format.')
    instruction: str = Field(..., description='Text representing the instruction and its operands, in an implementation-defined format.')
    symbol: Optional[str] = Field(None, description='Name of the symbol that corresponds with the location of this instruction, if any.')
    location: Optional[Source] = Field(None, description='Source location that corresponds to this instruction, if any.\nShould always be set (if available) on the first instruction returned,\nbut can be omitted afterwards if this instruction maps to the same source file as the previous instruction.')
    line: Optional[int] = Field(None, description='The line within the source location that corresponds to this instruction, if any.')
    column: Optional[int] = Field(None, description='The column within the line that corresponds to this instruction, if any.')
    endLine: Optional[int] = Field(None, description='The end line of the range that corresponds to this instruction, if any.')
    endColumn: Optional[int] = Field(None, description='The end column of the range that corresponds to this instruction, if any.')
    presentationHint: Optional[Literal['normal', 'invalid']] = Field(None, description="A hint for how to present the instruction in the UI.\n\nA value of `invalid` may be used to indicate this instruction is 'filler' and cannot be reached by the program. For example, unreadable memory addresses may be presented is 'invalid.'")

class BreakpointMode(BaseModel):
    model_config = ConfigDict(extra='allow')
    mode: str = Field(..., description='The internal ID of the mode. This value is passed to the `setBreakpoints` request.')
    label: str = Field(..., description='The name of the breakpoint mode. This is shown in the UI.')
    description: Optional[str] = Field(None, description='A help text providing additional information about the breakpoint mode. This string is typically shown as a hover and can be translated.')
    appliesTo: List[BreakpointModeApplicability] = Field(..., description='Describes one or more type of breakpoint this mode applies to.')

class OutputEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    category: Optional[str] = Field(None, description='The output category. If not specified or if the category is not understood by the client, `console` is assumed.')
    output: str = Field(..., description="The output to report.\n\nANSI escape sequences may be used to influence text color and styling if `supportsANSIStyling` is present in both the adapter's `Capabilities` and the client's `InitializeRequestArguments`. A client may strip any unrecognized ANSI sequences.\n\nIf the `supportsANSIStyling` capabilities are not both true, then the client should display the output literally.")
    group: Optional[Literal['start', 'startCollapsed', 'end']] = Field(None, description='Support for keeping an output log organized by grouping related messages.')
    variablesReference: Optional[int] = Field(None, description="If an attribute `variablesReference` exists and its value is > 0, the output contains objects which can be retrieved by passing `variablesReference` to the `variables` request as long as execution remains suspended. See 'Lifetime of Object References' in the Overview section for details.")
    source: Optional[Source] = Field(None, description='The source location where the output was produced.')
    line: Optional[int] = Field(None, description="The source location's line where the output was produced.")
    column: Optional[int] = Field(None, description='The position in `line` where the output was produced. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')
    data: Optional[Union[List[Any], bool, int, float, Dict[str, Any], str]] = Field(None, description='Additional data to report. For the `telemetry` category the data is sent to telemetry, for the other categories the data is shown in JSON format.')
    locationReference: Optional[int] = Field(None, description="A reference that allows the client to request the location where the new value is declared. For example, if the logged value is function pointer, the adapter may be able to look up the function's location. This should be present only if the adapter is likely to be able to resolve the location.\n\nThis reference shares the same lifetime as the `variablesReference`. See 'Lifetime of Object References' in the Overview section for details.")

class OutputEvent(Event):
    event: Literal['output']
    body: OutputEventBody

class BreakpointEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    reason: str = Field(..., description='The reason for the event.')
    breakpoint: Breakpoint = Field(..., description='The `id` attribute is used to find the target breakpoint, the other attributes are used as the new values.')

class BreakpointEvent(Event):
    event: Literal['breakpoint']
    body: BreakpointEventBody

class LoadedSourceEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    reason: Literal['new', 'changed', 'removed'] = Field(..., description='The reason for the event.')
    source: Source = Field(..., description='The new, changed, or removed source.')

class LoadedSourceEvent(Event):
    event: Literal['loadedSource']
    body: LoadedSourceEventBody

class BreakpointLocationsArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    source: Source = Field(..., description='The source location of the breakpoints; either `source.path` or `source.sourceReference` must be specified.')
    line: int = Field(..., description='Start line of range to search possible breakpoint locations in. If only the line is specified, the request returns all possible locations in that line.')
    column: Optional[int] = Field(None, description='Start position within `line` to search possible breakpoint locations in. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based. If no column is given, the first position in the start line is assumed.')
    endLine: Optional[int] = Field(None, description='End line of range to search possible breakpoint locations in. If no end line is given, then the end line is assumed to be the start line.')
    endColumn: Optional[int] = Field(None, description='End position within `endLine` to search possible breakpoint locations in. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based. If no end column is given, the last position in the end line is assumed.')

class SetBreakpointsArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    source: Source = Field(..., description='The source location of the breakpoints; either `source.path` or `source.sourceReference` must be specified.')
    breakpoints: Optional[List[SourceBreakpoint]] = Field(None, description='The code locations of the breakpoints.')
    lines: Optional[List[int]] = Field(None, description='Deprecated: The code locations of the breakpoints.')
    sourceModified: Optional[bool] = Field(None, description='A value of true indicates that the underlying source has been modified which results in new breakpoint locations.')

class SetBreakpointsResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    breakpoints: List[Breakpoint] = Field(..., description='Information about the breakpoints.\nThe array elements are in the same order as the elements of the `breakpoints` (or the deprecated `lines`) array in the arguments.')

class SetBreakpointsResponse(Response):
    body: SetBreakpointsResponseBody
    success: Literal[True]

class SetFunctionBreakpointsRequest(Request):
    command: Literal['setFunctionBreakpoints']
    arguments: SetFunctionBreakpointsArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> SetFunctionBreakpointsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[SetFunctionBreakpointsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class SetFunctionBreakpointsResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    breakpoints: List[Breakpoint] = Field(..., description='Information about the breakpoints. The array elements correspond to the elements of the `breakpoints` array.')

class SetFunctionBreakpointsResponse(Response):
    body: SetFunctionBreakpointsResponseBody
    success: Literal[True]

class SetExceptionBreakpointsArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    filters: List[str] = Field(..., description='Set of exception filters specified by their ID. The set of all possible exception filters is defined by the `exceptionBreakpointFilters` capability. The `filter` and `filterOptions` sets are additive.')
    filterOptions: Optional[List[ExceptionFilterOptions]] = Field(None, description='Set of exception filters and their options. The set of all possible exception filters is defined by the `exceptionBreakpointFilters` capability. This attribute is only honored by a debug adapter if the corresponding capability `supportsExceptionFilterOptions` is true. The `filter` and `filterOptions` sets are additive.')
    exceptionOptions: Optional[List[ExceptionOptions]] = Field(None, description='Configuration options for selected exceptions.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportsExceptionOptions` is true.')

class SetExceptionBreakpointsResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    breakpoints: Optional[List[Breakpoint]] = Field(None, description='Information about the exception breakpoints or filters.\nThe breakpoints returned are in the same order as the elements of the `filters`, `filterOptions`, `exceptionOptions` arrays in the arguments. If both `filters` and `filterOptions` are given, the returned array must start with `filters` information first, followed by `filterOptions` information.')

class SetExceptionBreakpointsResponse(Response):
    body: Optional[SetExceptionBreakpointsResponseBody] = None
    success: Literal[True]

class SetDataBreakpointsRequest(Request):
    command: Literal['setDataBreakpoints']
    arguments: SetDataBreakpointsArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> SetDataBreakpointsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[SetDataBreakpointsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class SetDataBreakpointsResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    breakpoints: List[Breakpoint] = Field(..., description='Information about the data breakpoints. The array elements correspond to the elements of the input argument `breakpoints` array.')

class SetDataBreakpointsResponse(Response):
    body: SetDataBreakpointsResponseBody
    success: Literal[True]

class SetInstructionBreakpointsRequest(Request):
    command: Literal['setInstructionBreakpoints']
    arguments: SetInstructionBreakpointsArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> SetInstructionBreakpointsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[SetInstructionBreakpointsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class SetInstructionBreakpointsResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    breakpoints: List[Breakpoint] = Field(..., description='Information about the breakpoints. The array elements correspond to the elements of the `breakpoints` array.')

class SetInstructionBreakpointsResponse(Response):
    body: SetInstructionBreakpointsResponseBody
    success: Literal[True]

class NextRequest(Request):
    command: Literal['next']
    arguments: NextArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> NextResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[NextResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class StepInRequest(Request):
    command: Literal['stepIn']
    arguments: StepInArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> StepInResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[StepInResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class StepOutRequest(Request):
    command: Literal['stepOut']
    arguments: StepOutArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> StepOutResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[StepOutResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class StepBackRequest(Request):
    command: Literal['stepBack']
    arguments: StepBackArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> StepBackResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[StepBackResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class StackTraceRequest(Request):
    command: Literal['stackTrace']
    arguments: StackTraceArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> StackTraceResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[StackTraceResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class StackTraceResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    stackFrames: List[StackFrame] = Field(..., description='The frames of the stack frame. If the array has length zero, there are no stack frames available.\nThis means that there is no location information available.')
    totalFrames: Optional[int] = Field(None, description='The total number of frames available in the stack. If omitted or if `totalFrames` is larger than the available frames, a client is expected to request frames until a request returns less frames than requested (which indicates the end of the stack). Returning monotonically increasing `totalFrames` values for subsequent requests can be used to enforce paging in the client.')

class StackTraceResponse(Response):
    body: StackTraceResponseBody
    success: Literal[True]

class ScopesResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    scopes: List[Scope] = Field(..., description='The scopes of the stack frame. If the array has length zero, there are no scopes available.')

class ScopesResponse(Response):
    body: ScopesResponseBody
    success: Literal[True]

class VariablesRequest(Request):
    command: Literal['variables']
    arguments: VariablesArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> VariablesResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[VariablesResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class VariablesResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    variables: List[Variable] = Field(..., description='All (or a range) of variables for the given variable reference.')

class VariablesResponse(Response):
    body: VariablesResponseBody
    success: Literal[True]

class SetVariableRequest(Request):
    command: Literal['setVariable']
    arguments: SetVariableArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> SetVariableResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[SetVariableResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class SourceArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    source: Optional[Source] = Field(None, description='Specifies the source content to load. Either `source.path` or `source.sourceReference` must be specified.')
    sourceReference: int = Field(..., description='The reference to the source. This is the same as `source.sourceReference`.\nThis is provided for backward compatibility since old clients do not understand the `source` attribute.')

class LoadedSourcesResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    sources: List[Source] = Field(..., description='Set of loaded sources.')

class LoadedSourcesResponse(Response):
    body: LoadedSourcesResponseBody
    success: Literal[True]

class EvaluateArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    expression: str = Field(..., description='The expression to evaluate.')
    frameId: Optional[int] = Field(None, description='Evaluate the expression in the scope of this stack frame. If not specified, the expression is evaluated in the global scope.')
    line: Optional[int] = Field(None, description="The contextual line where the expression should be evaluated. In the 'hover' context, this should be set to the start of the expression being hovered.")
    column: Optional[int] = Field(None, description='The contextual column where the expression should be evaluated. This may be provided if `line` is also provided.\n\nIt is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')
    source: Optional[Source] = Field(None, description='The contextual source in which the `line` is found. This must be provided if `line` is provided.')
    context: Optional[str] = Field(None, description='The context in which the evaluate request is used.')
    format: Optional[ValueFormat] = Field(None, description='Specifies details on how to format the result.\nThe attribute is only honored by a debug adapter if the corresponding capability `supportsValueFormattingOptions` is true.')

class SetExpressionRequest(Request):
    command: Literal['setExpression']
    arguments: SetExpressionArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> SetExpressionResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[SetExpressionResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class GotoTargetsArguments(BaseModel):
    model_config = ConfigDict(extra='allow')
    source: Source = Field(..., description='The source location for which the goto targets are determined.')
    line: int = Field(..., description='The line location for which the goto targets are determined.')
    column: Optional[int] = Field(None, description='The position within `line` for which the goto targets are determined. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')

class CompletionsResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    targets: List[CompletionItem] = Field(..., description='The possible completions for .')

class CompletionsResponse(Response):
    body: CompletionsResponseBody
    success: Literal[True]

class DisassembleResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    instructions: List[DisassembledInstruction] = Field(..., description='The list of disassembled instructions.')

class DisassembleResponse(Response):
    body: Optional[DisassembleResponseBody] = None
    success: Literal[True]

class LocationsResponseBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    source: Source = Field(..., description='The source containing the location; either `source.path` or `source.sourceReference` must be specified.')
    line: int = Field(..., description='The line number of the location. The client capability `linesStartAt1` determines whether it is 0- or 1-based.')
    column: Optional[int] = Field(None, description='Position of the location within the `line`. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based. If no column is given, the first position in the start line is assumed.')
    endLine: Optional[int] = Field(None, description='End line of the location, present if the location refers to a range.  The client capability `linesStartAt1` determines whether it is 0- or 1-based.')
    endColumn: Optional[int] = Field(None, description='End position of the location within `endLine`, present if the location refers to a range. It is measured in UTF-16 code units and the client capability `columnsStartAt1` determines whether it is 0- or 1-based.')

class LocationsResponse(Response):
    body: Optional[LocationsResponseBody] = None
    success: Literal[True]

class Capabilities(BaseModel):
    model_config = ConfigDict(extra='allow')
    supportsConfigurationDoneRequest: Optional[bool] = Field(None, description='The debug adapter supports the `configurationDone` request.')
    supportsFunctionBreakpoints: Optional[bool] = Field(None, description='The debug adapter supports function breakpoints.')
    supportsConditionalBreakpoints: Optional[bool] = Field(None, description='The debug adapter supports conditional breakpoints.')
    supportsHitConditionalBreakpoints: Optional[bool] = Field(None, description='The debug adapter supports breakpoints that break execution after a specified number of hits.')
    supportsEvaluateForHovers: Optional[bool] = Field(None, description='The debug adapter supports a (side effect free) `evaluate` request for data hovers.')
    exceptionBreakpointFilters: Optional[List[ExceptionBreakpointsFilter]] = Field(None, description='Available exception filter options for the `setExceptionBreakpoints` request.')
    supportsStepBack: Optional[bool] = Field(None, description='The debug adapter supports stepping back via the `stepBack` and `reverseContinue` requests.')
    supportsSetVariable: Optional[bool] = Field(None, description='The debug adapter supports setting a variable to a value.')
    supportsRestartFrame: Optional[bool] = Field(None, description='The debug adapter supports restarting a frame.')
    supportsGotoTargetsRequest: Optional[bool] = Field(None, description='The debug adapter supports the `gotoTargets` request.')
    supportsStepInTargetsRequest: Optional[bool] = Field(None, description='The debug adapter supports the `stepInTargets` request.')
    supportsCompletionsRequest: Optional[bool] = Field(None, description='The debug adapter supports the `completions` request.')
    completionTriggerCharacters: Optional[List[str]] = Field(None, description='The set of characters that should trigger completion in a REPL. If not specified, the UI should assume the `.` character.')
    supportsModulesRequest: Optional[bool] = Field(None, description='The debug adapter supports the `modules` request.')
    additionalModuleColumns: Optional[List[ColumnDescriptor]] = Field(None, description='The set of additional module information exposed by the debug adapter.')
    supportedChecksumAlgorithms: Optional[List[ChecksumAlgorithm]] = Field(None, description='Checksum algorithms supported by the debug adapter.')
    supportsRestartRequest: Optional[bool] = Field(None, description='The debug adapter supports the `restart` request. In this case a client should not implement `restart` by terminating and relaunching the adapter but by calling the `restart` request.')
    supportsExceptionOptions: Optional[bool] = Field(None, description='The debug adapter supports `exceptionOptions` on the `setExceptionBreakpoints` request.')
    supportsValueFormattingOptions: Optional[bool] = Field(None, description='The debug adapter supports a `format` attribute on the `stackTrace`, `variables`, and `evaluate` requests.')
    supportsExceptionInfoRequest: Optional[bool] = Field(None, description='The debug adapter supports the `exceptionInfo` request.')
    supportTerminateDebuggee: Optional[bool] = Field(None, description='The debug adapter supports the `terminateDebuggee` attribute on the `disconnect` request.')
    supportSuspendDebuggee: Optional[bool] = Field(None, description='The debug adapter supports the `suspendDebuggee` attribute on the `disconnect` request.')
    supportsDelayedStackTraceLoading: Optional[bool] = Field(None, description='The debug adapter supports the delayed loading of parts of the stack, which requires that both the `startFrame` and `levels` arguments and the `totalFrames` result of the `stackTrace` request are supported.')
    supportsLoadedSourcesRequest: Optional[bool] = Field(None, description='The debug adapter supports the `loadedSources` request.')
    supportsLogPoints: Optional[bool] = Field(None, description='The debug adapter supports log points by interpreting the `logMessage` attribute of the `SourceBreakpoint`.')
    supportsTerminateThreadsRequest: Optional[bool] = Field(None, description='The debug adapter supports the `terminateThreads` request.')
    supportsSetExpression: Optional[bool] = Field(None, description='The debug adapter supports the `setExpression` request.')
    supportsTerminateRequest: Optional[bool] = Field(None, description='The debug adapter supports the `terminate` request.')
    supportsDataBreakpoints: Optional[bool] = Field(None, description='The debug adapter supports data breakpoints.')
    supportsReadMemoryRequest: Optional[bool] = Field(None, description='The debug adapter supports the `readMemory` request.')
    supportsWriteMemoryRequest: Optional[bool] = Field(None, description='The debug adapter supports the `writeMemory` request.')
    supportsDisassembleRequest: Optional[bool] = Field(None, description='The debug adapter supports the `disassemble` request.')
    supportsCancelRequest: Optional[bool] = Field(None, description='The debug adapter supports the `cancel` request.')
    supportsBreakpointLocationsRequest: Optional[bool] = Field(None, description='The debug adapter supports the `breakpointLocations` request.')
    supportsClipboardContext: Optional[bool] = Field(None, description='The debug adapter supports the `clipboard` context value in the `evaluate` request.')
    supportsSteppingGranularity: Optional[bool] = Field(None, description='The debug adapter supports stepping granularities (argument `granularity`) for the stepping requests.')
    supportsInstructionBreakpoints: Optional[bool] = Field(None, description='The debug adapter supports adding breakpoints based on instruction references.')
    supportsExceptionFilterOptions: Optional[bool] = Field(None, description='The debug adapter supports `filterOptions` as an argument on the `setExceptionBreakpoints` request.')
    supportsSingleThreadExecutionRequests: Optional[bool] = Field(None, description='The debug adapter supports the `singleThread` property on the execution requests (`continue`, `next`, `stepIn`, `stepOut`, `reverseContinue`, `stepBack`).')
    supportsDataBreakpointBytes: Optional[bool] = Field(None, description='The debug adapter supports the `asAddress` and `bytes` fields in the `dataBreakpointInfo` request.')
    breakpointModes: Optional[List[BreakpointMode]] = Field(None, description="Modes of breakpoints supported by the debug adapter, such as 'hardware' or 'software'. If present, the client may allow the user to select a mode and include it in its `setBreakpoints` request.\n\nClients may present the first applicable mode in this array as the 'default' mode in gestures that set breakpoints.")
    supportsANSIStyling: Optional[bool] = Field(None, description='The debug adapter supports ANSI escape sequences in styling of `OutputEvent.output` and `Variable.value` fields.')

class CapabilitiesEventBody(BaseModel):
    model_config = ConfigDict(extra='allow')
    capabilities: Capabilities = Field(..., description='The set of updated capabilities.')

class CapabilitiesEvent(Event):
    event: Literal['capabilities']
    body: CapabilitiesEventBody

class InitializeResponse(Response):
    body: Optional[Capabilities] = Field(None, description='The capabilities of this debug adapter.')
    success: Literal[True]

class BreakpointLocationsRequest(Request):
    command: Literal['breakpointLocations']
    arguments: Optional[BreakpointLocationsArguments] = None

    @classmethod
    def discriminate_response(cls, res: Response) -> BreakpointLocationsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[BreakpointLocationsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class SetBreakpointsRequest(Request):
    command: Literal['setBreakpoints']
    arguments: SetBreakpointsArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> SetBreakpointsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[SetBreakpointsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class SetExceptionBreakpointsRequest(Request):
    command: Literal['setExceptionBreakpoints']
    arguments: SetExceptionBreakpointsArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> SetExceptionBreakpointsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[SetExceptionBreakpointsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class SourceRequest(Request):
    command: Literal['source']
    arguments: SourceArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> SourceResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[SourceResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class EvaluateRequest(Request):
    command: Literal['evaluate']
    arguments: EvaluateArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> EvaluateResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[EvaluateResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())

class GotoTargetsRequest(Request):
    command: Literal['gotoTargets']
    arguments: GotoTargetsArguments

    @classmethod
    def discriminate_response(cls, res: Response) -> GotoTargetsResponse | ErrorResponse:
        response_adaptor = TypeAdapter(Annotated[GotoTargetsResponse | ErrorResponse, Field(..., discriminator='success')])
        return response_adaptor.validate_python(res.model_dump())
ExceptionDetails.model_rebuild()
Source.model_rebuild()
DiscriminatedRequest = Annotated[ThreadsRequest | CancelRequest | RunInTerminalRequest | StartDebuggingRequest | InitializeRequest | ConfigurationDoneRequest | LaunchRequest | AttachRequest | RestartRequest | DisconnectRequest | TerminateRequest | DataBreakpointInfoRequest | ContinueRequest | ReverseContinueRequest | RestartFrameRequest | GotoRequest | PauseRequest | ScopesRequest | TerminateThreadsRequest | ModulesRequest | LoadedSourcesRequest | StepInTargetsRequest | CompletionsRequest | ExceptionInfoRequest | ReadMemoryRequest | WriteMemoryRequest | DisassembleRequest | LocationsRequest | SetFunctionBreakpointsRequest | SetDataBreakpointsRequest | SetInstructionBreakpointsRequest | NextRequest | StepInRequest | StepOutRequest | StepBackRequest | StackTraceRequest | VariablesRequest | SetVariableRequest | SetExpressionRequest | BreakpointLocationsRequest | SetBreakpointsRequest | SetExceptionBreakpointsRequest | SourceRequest | EvaluateRequest | GotoTargetsRequest, Field(discriminator='command')]
DiscriminatedEvent = Annotated[InitializedEvent | StoppedEvent | ContinuedEvent | ExitedEvent | TerminatedEvent | ThreadEvent | ProcessEvent | ProgressStartEvent | ProgressUpdateEvent | ProgressEndEvent | MemoryEvent | ModuleEvent | InvalidatedEvent | OutputEvent | BreakpointEvent | LoadedSourceEvent | CapabilitiesEvent, Field(discriminator='event')]
DiscriminatedProtocolMessage = Annotated[Union[DiscriminatedRequest, DiscriminatedEvent, Response], Field(discriminator='type')]