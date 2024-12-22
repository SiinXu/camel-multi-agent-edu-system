import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

const MODEL_NAME = 'Qwen/Qwen2.5-32B-Instruct';

export default function SettingsPage({ show, onClose, apiKeys, onSave }) {
  if (!show) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const newKeys = {
      modelscope: formData.get('modelscope') || '',
      fish_audio: formData.get('fish_audio') || '',
      chunkr: formData.get('chunkr') || '',
      model_name: MODEL_NAME,
    };
    onSave(newKeys);
    onClose();
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50">
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={handleOverlayClick} />
      <div className="fixed inset-0 overflow-y-auto" onClick={handleOverlayClick}>
        <div className="flex min-h-full items-center justify-center p-4">
          <div className="relative w-full max-w-md" onClick={e => e.stopPropagation()}>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold dark:text-white">Settings</h2>
                <button
                  type="button"
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  onClick={onClose}
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      ModelScope API Key
                    </label>
                    <input
                      type="text"
                      name="modelscope"
                      defaultValue={apiKeys?.modelscope || ''}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    />
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                      Using model: Qwen 2.5 32B Instruct
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Fish Audio API Key
                    </label>
                    <input
                      type="text"
                      name="fish_audio"
                      defaultValue={apiKeys?.fish_audio || ''}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Chunkr API Key
                    </label>
                    <input
                      type="text"
                      name="chunkr"
                      defaultValue={apiKeys?.chunkr || ''}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    />
                  </div>

                  <div className="flex justify-end mt-6">
                    <button
                      type="button"
                      onClick={onClose}
                      className="mr-3 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
                    >
                      Save
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
