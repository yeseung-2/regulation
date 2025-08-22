import React from 'react';

export function Input(props) {
  return (
    <input
      className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-300"
      {...props}
    />
  );
}
