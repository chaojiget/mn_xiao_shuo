/**
 * DM 交互界面组件
 * 支持 WebSocket 实时连接、流式文本显示、工具调用可视化
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { Zap, Pause, Play, StopCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useGameStore } from '@/stores/gameStore';
import { DmMessage, ToolCall, GameState } from '@/types/game';
import { cn } from '@/lib/utils';
import { ThinkingProcess, ThinkingStep } from '@/components/chat/ThinkingProcess';
import { SuggestionChips, Suggestion } from '@/components/chat/SuggestionChips';
import { TaskProgress, Task } from '@/components/chat/TaskProgress';
import { TypewriterText } from '@/components/chat/TypewriterText';
// 🔥 Shadcn AI Elements
import { Message, MessageContent, MessageAvatar } from '@/components/ui/shadcn-io/ai/message';
import { Conversation, ConversationContent, ConversationScrollButton } from '@/components/ui/shadcn-io/ai/conversation';
import { PromptInput, PromptInputTextarea, PromptInputToolbar, PromptInputSubmit } from '@/components/ui/shadcn-io/ai/prompt-input';
import { Loader } from '@/components/ui/shadcn-io/ai/loader';
import { ErrorDisplay } from '@/components/ui/shadcn-io/ai/error-display';

interface DmInterfaceProps {
  sessionId?: string;
  className?: string;
}

export function DmInterface({ sessionId, className }: DmInterfaceProps) {
  const [messages, setMessages] = useState<DmMessage[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isPaused, setIsPaused] = useState(false); // 🔥 流式暂停状态
  const [canStop, setCanStop] = useState(false); // 🔥 是否可以停止
  const [lastError, setLastError] = useState<string | null>(null); // 🔥 最后的错误
  const [lastInput, setLastInput] = useState<string>(''); // 🔥 保存最后的输入用于重试
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const taskCounterRef = useRef<number>(0); // 🔥 任务计数器，确保唯一 ID
  const thinkingCounterRef = useRef<number>(0); // 🔥 思考步骤计数器

  const getSafeToolName = (name?: string) => {
    if (!name) return '未知工具';
    const trimmed = String(name).trim();
    return trimmed.length > 0 ? trimmed : '未知工具';
  };

  const parseToolInput = (payload: unknown) => {
    if (payload === undefined || payload === null || payload === '') {
      return {};
    }

    if (typeof payload === 'string') {
      const trimmed = payload.trim();
      if (!trimmed) {
        return {};
      }

      if (
        (trimmed.startsWith('{') && trimmed.endsWith('}')) ||
        (trimmed.startsWith('[') && trimmed.endsWith(']'))
      ) {
        try {
          return JSON.parse(trimmed);
        } catch (error) {
          console.warn('[DmInterface] 无法解析工具参数 JSON:', error);
          return trimmed;
        }
      }

      return trimmed;
    }

    return payload;
  };

  const parseToolOutput = (payload: unknown) => {
    if (payload === undefined) {
      return undefined;
    }

    if (typeof payload === 'string') {
      const trimmed = payload.trim();
      if (!trimmed) {
        return '';
      }

      if (
        (trimmed.startsWith('{') && trimmed.endsWith('}')) ||
        (trimmed.startsWith('[') && trimmed.endsWith(']'))
      ) {
        try {
          return JSON.parse(trimmed);
        } catch (error) {
          console.warn('[DmInterface] 无法解析工具输出 JSON:', error);
          return trimmed;
        }
      }

      return trimmed;
    }

    return payload;
  };

  const stringifyToolPayload = (payload: unknown) => {
    if (payload === undefined) {
      return '';
    }

    if (payload === null) {
      return 'null';
    }

    if (typeof payload === 'string') {
      return payload;
    }

    try {
      return JSON.stringify(payload, null, 2);
    } catch (error) {
      console.warn('[DmInterface] 无法序列化工具数据:', error);
      return String(payload);
    }
  };

  const appendToolTask = (toolName: string, rawInput: unknown) => {
    taskCounterRef.current += 1;
    const timestamp = Date.now();
    const normalizedInput = parseToolInput(rawInput);

    const newTask: Task = {
      id: `task_${timestamp}_${taskCounterRef.current}`,
      title: `工具调用: ${toolName}`,
      status: 'in_progress',
      type: 'tool_call',
      timestamp,
      toolName,
      toolInput: normalizedInput,
    };

    setTasks((prev) => [...prev, newTask].slice(-10));

    return { normalizedInput, timestamp };
  };

  const completeToolTask = (toolName: string, rawOutput: unknown, errorMessage?: string) => {
    const normalizedOutput = parseToolOutput(rawOutput);

    setTasks((prev) => {
      const updated = [...prev];
      let updatedTask = false;

      for (let i = updated.length - 1; i >= 0; i -= 1) {
        const task = updated[i];
        if (
          task.type === 'tool_call' &&
          task.status === 'in_progress' &&
          (task.toolName === toolName || task.toolName === '未知工具')
        ) {
          const durationMs = task.timestamp ? Date.now() - task.timestamp : undefined;
          updated[i] = {
            ...task,
            status: errorMessage ? 'error' : 'completed',
            toolOutput: normalizedOutput,
            durationMs,
            error: errorMessage,
          };
          updatedTask = true;
          break;
        }
      }

      if (!updatedTask) {
        for (let i = updated.length - 1; i >= 0; i -= 1) {
          const task = updated[i];
          if (task.type === 'tool_call' && task.status === 'in_progress') {
            const durationMs = task.timestamp ? Date.now() - task.timestamp : undefined;
            updated[i] = {
              ...task,
              status: errorMessage ? 'error' : 'completed',
              toolOutput: normalizedOutput,
              durationMs,
              error: errorMessage,
            };
            updatedTask = true;
            break;
          }
        }
      }

      return updated;
    });

    return normalizedOutput;
  };

  const addToolCallMessage = (toolName: string, payload: unknown) => {
    const uniqueId = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const toolMessage: DmMessage = {
      id: uniqueId,
      role: 'assistant',
      content: `使用工具: ${toolName}`,
      timestamp: Date.now(),
      tool_calls: [
        {
          id: `${uniqueId}_call`,
          type: 'function',
          function: {
            name: toolName,
            arguments: stringifyToolPayload(payload),
          },
        },
      ],
    };

    setMessages((prev) => [...prev, toolMessage]);
  };

  const { gameState, setGameState, isConnected, setIsConnected, setError } = useGameStore();

  // 从 gameState.log 恢复历史消息
  useEffect(() => {
    if (gameState?.log && gameState.log.length > 0 && messages.length === 0) {
      console.log('[DmInterface] 恢复历史消息:', gameState.log.length);
      console.log('[DmInterface] 第一条log数据结构:', gameState.log[0]);

      const historicalMessages: DmMessage[] = gameState.log.map((entry: any, index: number) => {
        // 🔥 优先使用完整字段：content > text > message
        const messageContent = entry.content || entry.text || entry.message || '';

        if (index === 0) {
          console.log('[DmInterface] 第一条消息内容长度:', messageContent.length, '字符');
        }

        return {
          id: `history_${index}`,
          role: entry.actor === 'player' ? 'user' : 'assistant',
          content: messageContent,
          timestamp: entry.timestamp || Date.now(),
        };
      });

      setMessages(historicalMessages);
    }
  }, [gameState]);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText]);

  // WebSocket 连接
  useEffect(() => {
    if (!sessionId) return;

    // WebSocket连接到后端 (端口8000)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendHost = process.env.NEXT_PUBLIC_API_URL?.replace('http://', '').replace('https://', '') || 'localhost:8000';
    const wsUrl = `${protocol}//${backendHost}/api/dm/ws/${sessionId}`;

    console.log('[DM WebSocket] 连接到:', wsUrl);

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[DM WebSocket] 连接成功');
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWsMessage(data);
        } catch (err) {
          console.error('[DM WebSocket] 解析消息失败:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('[DM WebSocket] 错误:', error);
        setError('WebSocket 连接错误');
      };

      ws.onclose = () => {
        console.log('[DM WebSocket] 连接关闭');
        setIsConnected(false);
      };

      return () => {
        ws.close();
      };
    } catch (err) {
      console.error('[DM WebSocket] 创建连接失败:', err);
      setError('无法建立 WebSocket 连接');
    }
  }, [sessionId, setIsConnected, setError]);

  // 处理 WebSocket 消息
  const handleWsMessage = (data: any) => {
    switch (data.type) {
      case 'narration_start':
        setIsTyping(true);
        setStreamingText('');
        setThinkingSteps([]);
        setIsThinking(false);
        break;

      case 'thinking_start':
        setIsThinking(true);
        break;

      case 'thinking_step':
        thinkingCounterRef.current += 1; // 🔥 增加计数器
        const newStep: ThinkingStep = {
          id: `think_${Date.now()}_${thinkingCounterRef.current}`,
          title: `思考步骤 ${thinkingSteps.length + 1}`,
          content: data.content,
          status: 'completed',
          timestamp: Date.now(),
        };
        setThinkingSteps((prev) => [...prev, newStep]);
        break;

      case 'thinking_end':
        setIsThinking(false);
        break;

      case 'narration_chunk':
        setStreamingText((prev) => prev + data.content);
        break;

      case 'narration_end':
        const dmMessage: DmMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: streamingText,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, dmMessage]);
        setStreamingText('');
        setIsTyping(false);
        break;

      case 'tool_call':
        {
          const rawName = data.tool_name || data.tool;
          const safeName = getSafeToolName(rawName);
          const args = data.arguments ?? data.input ?? {};
          const { normalizedInput } = appendToolTask(safeName, args);
          addToolCallMessage(safeName, normalizedInput);
        }
        break;

      case 'tool_result':
        {
          const rawName = data.tool_name || data.tool;
          const safeName = getSafeToolName(rawName);
          const output = data.output ?? data.result;
          const errorMessage = typeof data.error === 'string' ? data.error : undefined;
          completeToolTask(safeName, output, errorMessage);
        }
        break;

      case 'state_update':
        if (data.state) {
          setGameState(data.state as GameState);
        }
        break;

      case 'error':
        const errorMsg = data.error || data.message || '未知错误';
        setError(errorMsg);
        setLastError(errorMsg); // 🔥 保存错误用于重试
        setIsTyping(false);
        setIsThinking(false);
        break;

      case 'heartbeat':
      case 'ping':
      case 'pong':
        // 心跳消息，忽略即可
        break;

      default:
        console.warn('[DM WebSocket] 未知消息类型:', data.type);
    }
  };

  // 发送消息（流式 API）
  const handleSendMessage = async () => {
    if (!input.trim() || !gameState) return;

    const userInput = input.trim();
    setLastInput(userInput); // 🔥 保存输入用于重试
    setLastError(null); // 🔥 清除之前的错误

    const playerMessage: DmMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: userInput,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, playerMessage]);
    setInput('');
    setIsTyping(true);
    setStreamingText('');

    try {
      // 使用流式API
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/game/turn/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          playerInput: userInput,
          currentState: gameState,
        }),
      });

      if (!response.ok) {
        throw new Error(`API 错误: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('无法读取响应流');
      }

      let buffer = '';
      let fullNarration = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        // 解码数据
        buffer += decoder.decode(value, { stream: true });

        // 处理 SSE 格式 (data: {...}\n\n)
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // 保留未完成的行

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6); // 移除 "data: " 前缀
              const data = JSON.parse(jsonStr);

              if (data.type === 'thinking_start') {
                setIsThinking(true);
              } else if (data.type === 'thinking_step') {
                thinkingCounterRef.current += 1; // 🔥 增加计数器
                const newStep: ThinkingStep = {
                  id: `think_${Date.now()}_${thinkingCounterRef.current}`,
                  title: `思考步骤 ${thinkingSteps.length + 1}`,
                  content: data.content,
                  status: 'completed',
                  timestamp: Date.now(),
                };
                setThinkingSteps((prev) => [...prev, newStep]);
              } else if (data.type === 'thinking_end') {
                setIsThinking(false);
              } else if (data.type === 'text' || data.type === 'narration') {
                // 流式显示叙事文本
                fullNarration += data.content;
                setStreamingText(fullNarration);
              } else if (data.type === 'tool_call') {
                const safeName = getSafeToolName(data.tool || data.tool_name);
                const args = data.input ?? data.arguments ?? {};
                const { normalizedInput } = appendToolTask(safeName, args);
                addToolCallMessage(safeName, normalizedInput);
              } else if (data.type === 'tool_result') {
                const safeName = getSafeToolName(data.tool || data.tool_name);
                const output = data.output ?? data.result;
                const errorMessage = typeof data.error === 'string' ? data.error : undefined;
                completeToolTask(safeName, output, errorMessage);
              } else if (data.type === 'state') {
                // 更新游戏状态
                if (data.state) {
                  setGameState(data.state);
                }
              } else if (data.type === 'done') {
                // 完成信号，可以处理metadata
                console.log('[DM Interface] 回合完成:', data.metadata);
              } else if (data.type === 'error') {
                // 错误处理
                setError(data.error || '未知错误');
              }
            } catch (parseError) {
              console.error('[DM Interface] 解析SSE数据失败:', parseError, 'Line:', line);
            }
          }
        }
      }

      // 流式完成后，将完整文本添加到消息历史
      if (fullNarration) {
        const dmMessage: DmMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: fullNarration,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, dmMessage]);
      }

      setStreamingText('');
      setIsTyping(false);

    } catch (error) {
      console.error('[DM Interface] 发送消息失败:', error);
      const errorMsg = error instanceof Error ? error.message : '发送消息失败';
      setError(errorMsg);
      setLastError(errorMsg); // 🔥 保存错误用于重试
      setIsTyping(false);
      setStreamingText('');
    }
  };

  // 🔥 重试上一次失败的请求
  const handleRetry = () => {
    if (lastInput) {
      setInput(lastInput);
      setLastError(null);
      // 自动发送
      setTimeout(() => {
        handleSendMessage();
      }, 100);
    }
  };

  // 渲染单条消息（使用 shadcn AI Message 组件）
  const renderMessage = (message: DmMessage) => {
    const isPlayer = message.role === 'user';
    const isTool = message.tool_calls && message.tool_calls.length > 0;

    // 工具调用消息
    if (isTool) {
      return (
        <div key={message.id} className="flex items-start gap-3 px-4 py-2 bg-amber-500/10 border-l-2 border-amber-500">
          <Zap className="w-4 h-4 text-amber-500 mt-1" />
          <div className="flex-1">
            <p className="text-sm text-amber-500 font-medium">{message.content}</p>
            {message.tool_calls && message.tool_calls.length > 0 && (
              <pre className="text-xs text-muted-foreground mt-2 overflow-x-auto">
                {message.tool_calls[0].function.arguments}
              </pre>
            )}
          </div>
        </div>
      );
    }

    // 普通消息（使用 shadcn AI Elements）
    return (
      <Message key={message.id} from={message.role as 'user' | 'assistant'}>
        <MessageAvatar
          name={isPlayer ? '玩家' : 'DM'}
        />
        <MessageContent>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </MessageContent>
      </Message>
    );
  };

  // 生成 AI 建议
  const generateSuggestions = () => {
    if (!gameState) return;

    const newSuggestions: Suggestion[] = [
      {
        id: 'explore',
        text: '探索周围环境',
        category: 'explore',
      },
      {
        id: 'talk',
        text: '与 NPC 对话',
        category: 'question',
      },
      {
        id: 'search',
        text: '搜索线索',
        category: 'action',
      },
    ];

    setSuggestions(newSuggestions);
  };

  // 处理建议点击
  const handleSuggestionClick = (suggestion: Suggestion) => {
    setInput(suggestion.text);
  };

  return (
    <div className={cn('flex flex-col h-full bg-background border rounded-lg', className)}>
      {/* 消息区域 - 使用 shadcn AI Conversation */}
      <Conversation className="flex-1">
        <ConversationContent>
          <div className="space-y-4">
            {/* 思考过程展示 */}
            {(thinkingSteps.length > 0 || isThinking) && (
              <ThinkingProcess steps={thinkingSteps} isThinking={isThinking} />
            )}

            {/* 任务进度展示 */}
            {tasks.length > 0 && <TaskProgress tasks={tasks} />}

            {/* 历史消息 */}
            {messages.map(renderMessage)}

            {/* 🔥 错误显示 */}
            {lastError && (
              <ErrorDisplay
                error={lastError}
                onRetry={handleRetry}
                retryText="重试上一次请求"
              />
            )}

            {/* 流式文本（打字机效果） - 使用 shadcn AI Message */}
            {isTyping && streamingText && (
              <Message from="assistant">
                <MessageAvatar name="DM" />
                <MessageContent>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Loader size={12} />
                      <span className="text-xs text-muted-foreground">正在生成...</span>
                    </div>
                    {/* 流式控制按钮 */}
                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-6 w-6 p-0"
                        onClick={() => setIsPaused(!isPaused)}
                        title={isPaused ? '继续' : '暂停'}
                      >
                        {isPaused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-6 w-6 p-0"
                        onClick={() => {
                          if (wsRef.current) {
                            wsRef.current.send(JSON.stringify({ type: 'cancel' }));
                          }
                          setIsTyping(false);
                          setStreamingText('');
                        }}
                        title="停止生成"
                      >
                        <StopCircle className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                  {/* 打字机效果 */}
                  <TypewriterText
                    text={streamingText}
                    speed={20}
                    paused={isPaused}
                    markdown={true}
                  />
                </MessageContent>
              </Message>
            )}

            {/* 正在输入指示器 */}
            {isTyping && !streamingText && (
              <div className="flex items-center gap-2 px-4 py-2 text-muted-foreground">
                <Loader size={16} />
                <span className="text-sm">DM 正在思考...</span>
              </div>
            )}
          </div>
        </ConversationContent>

        {/* 滚动到底部按钮 */}
        <ConversationScrollButton />
      </Conversation>

      {/* 输入区域 - 使用 shadcn AI PromptInput */}
      <div className="border-t p-4 space-y-3">
        {/* AI 建议芯片 */}
        {suggestions.length > 0 && (
          <SuggestionChips
            suggestions={suggestions}
            onSelect={handleSuggestionClick}
            onRefresh={generateSuggestions}
          />
        )}

        <PromptInput onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}>
          <PromptInputTextarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入你的行动... (Shift+Enter 换行)"
            disabled={isTyping || !gameState}
          />
          <PromptInputToolbar>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <div
                className={cn(
                  'w-2 h-2 rounded-full',
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                )}
              />
              <span>{isConnected ? 'WebSocket 已连接' : '使用 HTTP 模式'}</span>
            </div>
            <PromptInputSubmit
              status={isTyping ? 'streaming' : 'idle'}
              disabled={isTyping || !input.trim() || !gameState}
            />
          </PromptInputToolbar>
        </PromptInput>
      </div>
    </div>
  );
}
