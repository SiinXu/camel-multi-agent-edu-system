import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { PaperClipIcon, XMarkIcon } from '@heroicons/react/24/outline';

export function FileUpload({ onFileSelect, maxSize = 10485760 }) { // 10MB default
  const [files, setFiles] = React.useState([]);
  const [error, setError] = React.useState('');

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      setError(`File too large. Maximum size is ${maxSize / 1024 / 1024}MB`);
      return;
    }

    setFiles(acceptedFiles);
    acceptedFiles.forEach(file => {
      onFileSelect(file);
    });
    setError('');
  }, [maxSize, onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize,
    multiple: true
  });

  const removeFile = (fileToRemove) => {
    setFiles(files.filter(file => file !== fileToRemove));
  };

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`p-4 border-2 border-dashed rounded-lg transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-700'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center space-y-2">
          <PaperClipIcon className="w-8 h-8 text-gray-400" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {isDragActive
              ? 'Drop files here...'
              : 'Drag and drop files here, or click to select files'}
          </p>
        </div>
      </div>

      {error && (
        <p className="mt-2 text-sm text-red-500">{error}</p>
      )}

      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded-lg"
            >
              <div className="flex items-center space-x-2">
                <PaperClipIcon className="w-5 h-5 text-gray-400" />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {file.name}
                </span>
                <span className="text-xs text-gray-500">
                  ({(file.size / 1024).toFixed(1)} KB)
                </span>
              </div>
              <button
                onClick={() => removeFile(file)}
                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
