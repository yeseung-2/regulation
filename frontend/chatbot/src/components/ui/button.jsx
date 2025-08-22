import React from 'react';

export function Button({ children, variant, className = '', ...props }) {
  const base = 'px-4 py-2 rounded ';
  const style = variant === 'destructive'
    ? 'bg-red-500 text-white hover:bg-red-600'
    : variant === 'outline'
      ? 'border border-gray-300 text-gray-700 hover:bg-gray-100'
      : 'bg-green-500 text-white hover:bg-green-600';

  return (
    <button className={`${base}${style} ${className}`} {...props}>
      {children}
    </button>
  );
}
