export default function HeroShield() {
  return (
    <div className="hero__shield-wrap" aria-hidden="true">
      <svg className="shield-svg" viewBox="0 0 560 560" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="shieldGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="var(--model-color)" stopOpacity="0.15"/>
            <stop offset="60%"  stopColor="var(--model-color)" stopOpacity="0.06"/>
            <stop offset="100%" stopColor="var(--model-color)" stopOpacity="0"/>
          </radialGradient>
          <radialGradient id="coreGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="var(--model-color)" stopOpacity="0.3"/>
            <stop offset="100%" stopColor="var(--model-color)" stopOpacity="0"/>
          </radialGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        {/* Outer ring */}
        <g className="ring-outer" filter="url(#glow)">
          <circle cx="280" cy="280" r="240" stroke="var(--model-color)" strokeWidth="0.5" strokeOpacity="0.3" strokeDasharray="8 12" fill="none"/>
          <circle cx="280" cy="280" r="220" stroke="var(--model-color)" strokeWidth="0.3" strokeOpacity="0.2"  fill="none"/>
          <g stroke="var(--model-color)" strokeOpacity="0.5" strokeWidth="1.5">
            <line x1="280" y1="42"  x2="280" y2="55"/>
            <line x1="280" y1="505" x2="280" y2="518"/>
            <line x1="42"  y1="280" x2="55"  y2="280"/>
            <line x1="505" y1="280" x2="518" y2="280"/>
            <line x1="110.5" y1="110.5" x2="119.7" y2="119.7"/>
            <line x1="449.5" y1="110.5" x2="440.3" y2="119.7"/>
            <line x1="110.5" y1="449.5" x2="119.7" y2="440.3"/>
            <line x1="449.5" y1="449.5" x2="440.3" y2="440.3"/>
          </g>
        </g>

        {/* Mid ring */}
        <g className="ring-mid">
          <circle cx="280" cy="280" r="180" stroke="var(--model-color)" strokeWidth="0.4" strokeOpacity="0.25" strokeDasharray="4 8" fill="none"/>
          <circle cx="280" cy="280" r="165" stroke="var(--model-color)" strokeWidth="0.3" strokeOpacity="0.15" fill="none"/>
          <g fill="var(--model-color)" fillOpacity="0.5">
            <polygon points="280,102 283,109 277,109" />
            <polygon points="280,458 283,451 277,451" />
            <polygon points="102,280 109,277 109,283" />
            <polygon points="458,280 451,277 451,283" />
          </g>
        </g>

        {/* Shield body */}
        <path d="M280 80 L420 130 L420 240 Q420 360 280 440 Q140 360 140 240 L140 130 Z"
          fill="url(#shieldGrad)"
          stroke="var(--model-color)"
          strokeWidth="1"
          strokeOpacity="0.4"/>

        <path d="M280 110 L400 152 L400 238 Q400 340 280 410 Q160 340 160 238 L160 152 Z"
          fill="none"
          stroke="var(--model-color)"
          strokeWidth="0.5"
          strokeOpacity="0.2"/>

        {/* Shield check */}
        <path d="M230 270 L265 305 L335 235"
          stroke="var(--model-color)"
          strokeWidth="2"
          strokeOpacity="0.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
          filter="url(#glow)"/>

        {/* Core glow */}
        <circle cx="280" cy="280" r="30" fill="url(#coreGrad)"/>

        {/* Inner ring */}
        <g className="ring-inner">
          <circle cx="280" cy="280" r="120" stroke="var(--model-color)" strokeWidth="0.4" strokeOpacity="0.2" strokeDasharray="3 6" fill="none"/>
          <path d="M280 162 A118 118 0 0 1 383 346" stroke="var(--model-color)" strokeWidth="1" strokeOpacity="0.3" fill="none"/>
          <path d="M280 398 A118 118 0 0 1 177 214" stroke="var(--model-color)" strokeWidth="1" strokeOpacity="0.3" fill="none"/>
        </g>

        {/* Scan line */}
        <rect x="140" y="0" width="280" height="3" fill="var(--model-color)" opacity="0" rx="1">
          <animateTransform attributeName="transform" type="translate" from="0,80" to="0,440" dur="3s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0;0.25;0.25;0" keyTimes="0;0.1;0.9;1" dur="3s" repeatCount="indefinite"/>
        </rect>

        <text x="296" y="185" fontFamily="Space Mono, monospace" fontSize="9" fill="var(--model-color)" fillOpacity="0.5" letterSpacing="2">SYS.ACTIVE</text>
        <text x="210" y="380" fontFamily="Space Mono, monospace" fontSize="9" fill="var(--model-color)" fillOpacity="0.5" letterSpacing="2">v2.4.1</text>
      </svg>
    </div>
  );
}
