export default function AIRobotHero() {
  return (
    <div className="relative flex flex-col items-center justify-center py-8 sm:py-10 overflow-hidden">
      {/* Background network pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-60 pointer-events-none" />

      {/* Glow rings */}
      <div className="absolute w-56 h-56 rounded-full border border-blue-200/60" style={{ animation: 'pulse-ring 3s ease-in-out infinite' }} />
      <div className="absolute w-44 h-44 rounded-full border border-blue-300/40" />

      {/* Robot SVG */}
      <div className="animate-float relative z-10">
        <RobotSVG />
      </div>

      {/* Title text */}
      <div className="relative z-10 text-center mt-4">
        <h2 className="text-xl sm:text-2xl font-bold text-navy-900 tracking-tight" style={{ color: '#0f1f3d' }}>
          Your Course Content Assistant
        </h2>
        <p className="text-sm sm:text-base text-blue-600/80 mt-1">
          Ask me anything about your university syllabus
        </p>
      </div>
    </div>
  );
}

function RobotSVG() {
  return (
    <svg
      width="140"
      height="160"
      viewBox="0 0 140 160"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="AI Assistant Robot"
    >
      {/* Antenna */}
      <line x1="70" y1="10" x2="70" y2="28" stroke="#93c5fd" strokeWidth="3" strokeLinecap="round" />
      <circle cx="70" cy="8" r="5" fill="#3b82f6" className="animate-pulse-glow" />

      {/* Head */}
      <rect x="30" y="28" width="80" height="60" rx="16" fill="white" stroke="#bfdbfe" strokeWidth="2" />
      {/* Head shine */}
      <rect x="34" y="32" width="72" height="52" rx="13" fill="url(#headGrad)" />

      {/* Eyes */}
      <ellipse cx="50" cy="52" rx="11" ry="12" fill="#1d4ed8" />
      <ellipse cx="90" cy="52" rx="11" ry="12" fill="#1d4ed8" />
      {/* Eye glow */}
      <ellipse cx="50" cy="52" rx="7" ry="8" fill="#60a5fa" />
      <ellipse cx="90" cy="52" rx="7" ry="8" fill="#60a5fa" />
      {/* Eye pupils */}
      <circle cx="50" cy="52" r="3" fill="#1e40af" />
      <circle cx="90" cy="52" r="3" fill="#1e40af" />
      {/* Eye highlight */}
      <circle cx="52" cy="49" r="2" fill="white" opacity="0.8" />
      <circle cx="92" cy="49" r="2" fill="white" opacity="0.8" />

      {/* Mouth / speaker grill */}
      <rect x="46" y="68" width="48" height="10" rx="5" fill="#dbeafe" />
      <line x1="53" y1="73" x2="57" y2="73" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" />
      <line x1="62" y1="73" x2="66" y2="73" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" />
      <line x1="71" y1="73" x2="75" y2="73" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" />
      <line x1="80" y1="73" x2="84" y2="73" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" />

      {/* Neck */}
      <rect x="58" y="88" width="24" height="10" rx="4" fill="#dbeafe" />

      {/* Body */}
      <rect x="18" y="98" width="104" height="52" rx="18" fill="white" stroke="#bfdbfe" strokeWidth="2" />
      <rect x="22" y="102" width="96" height="44" rx="15" fill="url(#bodyGrad)" />

      {/* Chest panel */}
      <rect x="38" y="110" width="64" height="28" rx="8" fill="#dbeafe" />
      {/* Panel lights */}
      <circle cx="50" cy="120" r="4" fill="#3b82f6" className="animate-pulse" />
      <circle cx="63" cy="120" r="3" fill="#60a5fa" />
      <circle cx="76" cy="120" r="3" fill="#93c5fd" />
      <circle cx="89" cy="120" r="4" fill="#2563eb" />
      {/* Panel line */}
      <rect x="45" y="128" width="50" height="4" rx="2" fill="#bfdbfe" />

      {/* Arms */}
      <rect x="0" y="100" width="20" height="36" rx="10" fill="white" stroke="#bfdbfe" strokeWidth="2" />
      <rect x="120" y="100" width="20" height="36" rx="10" fill="white" stroke="#bfdbfe" strokeWidth="2" />
      {/* Arm joints */}
      <circle cx="10" cy="100" r="6" fill="#dbeafe" stroke="#bfdbfe" strokeWidth="1.5" />
      <circle cx="130" cy="100" r="6" fill="#dbeafe" stroke="#bfdbfe" strokeWidth="1.5" />

      {/* Legs */}
      <rect x="38" y="148" width="24" height="10" rx="5" fill="#bfdbfe" />
      <rect x="78" y="148" width="24" height="10" rx="5" fill="#bfdbfe" />

      {/* Gradients */}
      <defs>
        <linearGradient id="headGrad" x1="34" y1="32" x2="106" y2="84" gradientUnits="userSpaceOnUse">
          <stop stopColor="#f0f9ff" />
          <stop offset="1" stopColor="#e0f2fe" />
        </linearGradient>
        <linearGradient id="bodyGrad" x1="22" y1="102" x2="118" y2="146" gradientUnits="userSpaceOnUse">
          <stop stopColor="#f0f9ff" />
          <stop offset="1" stopColor="#e0f2fe" />
        </linearGradient>
      </defs>
    </svg>
  );
}
