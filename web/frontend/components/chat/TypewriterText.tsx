/**
 * 打字机效果组件
 * 模拟逐字显示的打字机效果，提升流式输出的用户体验
 */

'use client';

import { useEffect, useState, useRef } from 'react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface TypewriterTextProps {
  /** 要显示的完整文本 */
  text: string;
  /** 打字速度（每个字符的延迟，毫秒） */
  speed?: number;
  /** 是否立即显示（跳过动画） */
  instant?: boolean;
  /** 自定义类名 */
  className?: string;
  /** 是否渲染为 Markdown */
  markdown?: boolean;
  /** 动画完成回调 */
  onComplete?: () => void;
  /** 是否暂停 */
  paused?: boolean;
}

export function TypewriterText({
  text,
  speed = 30,
  instant = false,
  className,
  markdown = true,
  onComplete,
  paused = false,
}: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const indexRef = useRef(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // 重置状态
    if (instant) {
      setDisplayedText(text);
      setIsComplete(true);
      onComplete?.();
      return;
    }

    setDisplayedText('');
    setIsComplete(false);
    indexRef.current = 0;

    const typeNextChar = () => {
      if (indexRef.current < text.length) {
        setDisplayedText((prev) => prev + text[indexRef.current]);
        indexRef.current++;

        if (!paused) {
          timerRef.current = setTimeout(typeNextChar, speed);
        }
      } else {
        setIsComplete(true);
        onComplete?.();
      }
    };

    // 开始打字
    if (!paused && text.length > 0) {
      typeNextChar();
    }

    // 清理定时器
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [text, speed, instant, onComplete, paused]);

  // 暂停控制
  useEffect(() => {
    if (!paused && !isComplete && indexRef.current < text.length) {
      // 恢复打字
      const typeNextChar = () => {
        if (indexRef.current < text.length) {
          setDisplayedText((prev) => prev + text[indexRef.current]);
          indexRef.current++;
          timerRef.current = setTimeout(typeNextChar, speed);
        } else {
          setIsComplete(true);
          onComplete?.();
        }
      };
      typeNextChar();
    } else if (paused && timerRef.current) {
      // 暂停打字
      clearTimeout(timerRef.current);
    }
  }, [paused, speed, text, isComplete, onComplete]);

  if (!markdown) {
    return (
      <div className={cn('whitespace-pre-wrap', className)}>
        {displayedText}
        {!isComplete && <span className="animate-pulse ml-1">▊</span>}
      </div>
    );
  }

  return (
    <div className={cn('prose prose-sm dark:prose-invert max-w-none', className)}>
      <ReactMarkdown
        components={{
          code({ className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');
            const inline = !match;
            return !inline && match ? (
              <SyntaxHighlighter
                style={oneDark}
                language={match[1]}
                PreTag="div"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {displayedText}
      </ReactMarkdown>
      {!isComplete && <span className="animate-pulse ml-1 text-primary">▊</span>}
    </div>
  );
}

/**
 * 简化版打字机文本（纯文本，无 Markdown）
 */
export function SimpleTypewriter({
  text,
  speed = 20,
  className,
}: {
  text: string;
  speed?: number;
  className?: string;
}) {
  return <TypewriterText text={text} speed={speed} markdown={false} className={className} />;
}

/**
 * 流式文本容器（自动累积流式 chunks）
 */
interface StreamingTextProps {
  /** 流式文本片段数组 */
  chunks: string[];
  /** 打字速度 */
  speed?: number;
  /** 是否渲染为 Markdown */
  markdown?: boolean;
  className?: string;
}

export function StreamingText({ chunks, speed = 30, markdown = true, className }: StreamingTextProps) {
  const fullText = chunks.join('');

  return (
    <TypewriterText
      text={fullText}
      speed={speed}
      markdown={markdown}
      className={className}
    />
  );
}
