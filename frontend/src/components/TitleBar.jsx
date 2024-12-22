import React from 'react';
import { Menu } from '@headlessui/react';
import { CogIcon } from '@heroicons/react/24/outline';

export default function TitleBar() {
  return (
    <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center space-x-4">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          Multi-Agent Education System
        </h1>
        <span className="px-2 py-1 text-sm text-green-800 bg-green-100 rounded-full dark:bg-green-900 dark:text-green-200">
          Active
        </span>
      </div>

      <Menu as="div" className="relative">
        <Menu.Button className="p-2 text-gray-500 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700">
          <CogIcon className="w-6 h-6" />
        </Menu.Button>
        <Menu.Items className="absolute right-0 w-48 mt-2 origin-top-right bg-white dark:bg-gray-800 rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          <div className="py-1">
            <Menu.Item>
              {({ active }) => (
                <button
                  className={`${
                    active ? 'bg-gray-100 dark:bg-gray-700' : ''
                  } w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200`}
                >
                  Settings
                </button>
              )}
            </Menu.Item>
            <Menu.Item>
              {({ active }) => (
                <button
                  className={`${
                    active ? 'bg-gray-100 dark:bg-gray-700' : ''
                  } w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200`}
                >
                  Help
                </button>
              )}
            </Menu.Item>
          </div>
        </Menu.Items>
      </Menu>
    </div>
  );
}
