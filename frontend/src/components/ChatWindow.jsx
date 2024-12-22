import React, { useRef, useEffect } from 'react';
import { Transition } from '@headlessui/react';
import MessageItem from './MessageItem';

export default function ChatWindow({ messages = [] }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
    console.log('ChatWindow messages:', messages);
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4 min-h-[400px]">
      {messages && messages.length > 0 ? (
        messages.map((message, index) => (
          <Transition
            key={index}
            show={true}
            enter="transition-opacity duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity duration-150"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <MessageItem message={message} />
          </Transition>
        ))
      ) : (
        <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
          Start a conversation...
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}
