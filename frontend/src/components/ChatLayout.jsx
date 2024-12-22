import React from 'react';
import TitleBar from './TitleBar';
import ChatWindow from './ChatWindow';
import InputArea from './InputArea';

export default function ChatLayout({ messages, onSendMessage, onSendFile }) {
  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      <TitleBar />
      <ChatWindow messages={messages} />
      <InputArea onSendMessage={onSendMessage} onSendFile={onSendFile} />
    </div>
  );
}
