import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 dark:bg-gray-900">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-gray-800 dark:text-gray-200">404</h1>
        <h2 className="text-2xl font-semibold text-gray-600 dark:text-gray-400 mt-4">Page Not Found</h2>
        <p className="text-gray-500 dark:text-gray-500 mt-2">The page you're looking for doesn't exist or has been moved.</p>
        <Link 
          to="/" 
          className="inline-block mt-8 px-6 py-3 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
        >
          Back to Home
        </Link>
      </div>
    </div>
  );
}
