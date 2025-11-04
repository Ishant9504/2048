// In frontend/src/Components/Tooltip.jsx

import React from 'react';

export default function Tooltip({ text }) {
  return (
    // Use a 'group' to control the tooltip's visibility based on the parent's hover state
    <div className="relative flex items-center">
      {/* The visible icon */}
      <div className="ml-2 w-4 h-4 flex items-center justify-center bg-slate-600 text-slate-300 text-xs font-bold rounded-full cursor-help">
        ?
      </div>

      {/* The hidden tooltip text box */}
      <div 
        className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 
                   bg-slate-900 text-gray-300 text-sm rounded-lg shadow-2xl
                   opacity-0 group-hover:opacity-100 transition-opacity duration-300
                   pointer-events-none group-hover:pointer-events-auto"
      >
        {text}
        {/* Little triangle pointing down */}
        <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0
                        border-x-8 border-x-transparent
                        border-t-8 border-t-slate-900">
        </div>
      </div>
    </div>
  );
}