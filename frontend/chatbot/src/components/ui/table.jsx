import React from 'react';

export function Table({ children, className = '' }) {
  return <table className={`w-full border-collapse ${className}`}>{children}</table>;
}
