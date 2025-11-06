/**
 * DM 交互界面组件
 * 支持 WebSocket 实时连接、流式文本显示、工具调用可视化
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useGameStore } from '@/stores/gameStore';
import { DmMessage, ToolCall, GameState } from '@/types/game';
import { cn } from '@/lib/utils';

interface DmInterfaceProps {
  sessionId?: string;
  className?: string;
}

export function DmInterface({ sessionId, className }: DmInterfaceProps) {
  const [messages, setMessages] = useState<DmMessage[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const { gameState, setGameState, isConnected, setIsConnected, setError } = useGameStore();

  // 从 gameState.log 恢复历史消息
  useEffect(() => {
    if (gameState?.log && gameState.log.length > 0 && messages.length === 0) {
      console.log('[DmInterface] 恢复历史消息:', gameState.log.length);

      const historicalMessages: DmMessage[] = gameState.log.map((entry: any, index: number) => ({
        id: `history_${index}`,
        role: entry.actor === 'player' ? 'user' : 'assistant',
        content: entry.text,
        timestamp: entry.timestamp || Date.now(),
      }));

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
        const toolMessage: DmMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `使用工具: ${data.tool_name}`,
          timestamp: Date.now(),
          tool_calls: [
            {
              id: Date.now().toString(),
              type: 'function',
              function: {
                name: data.tool_name,
                arguments: JSON.stringify(data.arguments || {})
              }
            },
          ],
        };
        setMessages((prev) => [...prev, toolMessage]);
        break;

      case 'state_update':
        if (data.state) {
          setGameState(data.state as GameState);
        }
        break;

      case 'error':
        setError(data.error);
        setIsTyping(false);
        break;

      default:
        console.warn('[DM WebSocket] 未知消息类型:', data.type);
    }
  };

  // 发送消息（流式 API）
  const handleSendMessage = async () => {
    if (!input.trim() || !gameState) return;

    const userInput = input.trim();

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

              if (data.type === 'text' || data.type === 'narration') {
                // 流式显示叙事文本
                fullNarration += data.content;
                setStreamingText(fullNarration);
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
      setError(error instanceof Error ? error.message : '发送消息失败');
      setIsTyping(false);
      setStreamingText('');
    }
  };

  // 渲染单条消息
  const renderMessage = (message: DmMessage) => {
    const isPlayer = message.role === 'user';
    const isTool = message.tool_calls && message.tool_calls.length > 0;

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

    return (
      <div
        key={message.id}
        className={cn(
          'flex items-start gap-3 px-4 py-3',
          isPlayer ? 'bg-blue-500/10' : 'bg-transparent'
        )}
      >
        <div
          className={cn(
            'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold',
            isPlayer ? 'bg-blue-500 text-white' : 'bg-purple-500 text-white'
          )}
        >
          {isPlayer ? 'P' : 'DM'}
        </div>
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold">
              {isPlayer ? '玩家' : '地下城主'}
            </span>
            <span className="text-xs text-muted-foreground">
              {message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : ''}
            </span>
          </div>
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  };

  return (
    <div className={cn('flex flex-col h-full bg-background border rounded-lg', className)}>
      {/* 消息区域 */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map(renderMessage)}

          {/* 流式文本 */}
          {isTyping && streamingText && (
            <div className="flex items-start gap-3 px-4 py-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold bg-purple-500 text-white">
                DM
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">地下城主</span>
                  <Loader2 className="w-3 h-3 animate-spin" />
                </div>
                <p className="text-sm whitespace-pre-wrap">{streamingText}</p>
              </div>
            </div>
          )}

          {/* 正在输入指示器 */}
          {isTyping && !streamingText && (
            <div className="flex items-center gap-2 px-4 py-2 text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">DM 正在思考...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* 输入区域 */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder="输入你的行动... (Shift+Enter 换行)"
            className="min-h-[80px] resize-none"
            disabled={isTyping || !gameState}
          />
          <Button
            onClick={handleSendMessage}
            disabled={isTyping || !input.trim() || !gameState}
            size="icon"
            className="h-20 w-20"
          >
            {isTyping ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </Button>
        </div>

        {/* 连接状态指示器 */}
        <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
          <div
            className={cn(
              'w-2 h-2 rounded-full',
              isConnected ? 'bg-green-500' : 'bg-red-500'
            )}
          />
          <span>{isConnected ? 'WebSocket 已连接' : '使用 HTTP 模式'}</span>
        </div>
      </div>
    </div>
  );
}
