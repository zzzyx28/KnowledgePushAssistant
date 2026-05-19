function IconBase({ children }: { children: JSX.Element | JSX.Element[] }) {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
      {children}
    </svg>
  );
}

export function HomeIcon() {
  return (
    <IconBase>
      <path d="M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z" fill="currentColor" />
    </IconBase>
  );
}

export function LibraryIcon() {
  return (
    <IconBase>
      <path d="M5 4h4v16H5zM10 4h4v16h-4zM15 4h4v16h-4z" fill="currentColor" />
    </IconBase>
  );
}

export function LayersIcon() {
  return (
    <IconBase>
      <path d="m12 3 9 5-9 5-9-5 9-5Zm0 8 9 5-9 5-9-5 9-5Z" fill="currentColor" />
    </IconBase>
  );
}

export function SettingsIcon() {
  return (
    <IconBase>
      <path
        d="m19.4 13 .1-2-1.9-.7a5.9 5.9 0 0 0-.5-1.2l.9-1.8-1.4-1.4-1.8.9c-.4-.2-.8-.4-1.2-.5L13 3h-2l-.7 1.9c-.4.1-.8.3-1.2.5l-1.8-.9-1.4 1.4.9 1.8c-.2.4-.4.8-.5 1.2L3 11v2l1.9.7c.1.4.3.8.5 1.2l-.9 1.8 1.4 1.4 1.8-.9c.4.2.8.4 1.2.5L11 21h2l.7-1.9c.4-.1.8-.3 1.2-.5l1.8.9 1.4-1.4-.9-1.8c.2-.4.4-.8.5-1.2L19.4 13ZM12 15.5A3.5 3.5 0 1 1 12 8a3.5 3.5 0 0 1 0 7.5Z"
        fill="currentColor"
      />
    </IconBase>
  );
}

export function SparkIcon() {
  return (
    <IconBase>
      <path d="m12 2 2.2 5.8L20 10l-5.8 2.2L12 18l-2.2-5.8L4 10l5.8-2.2L12 2Z" fill="currentColor" />
    </IconBase>
  );
}

export function ClockIcon() {
  return (
    <IconBase>
      <path d="M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18Zm1 4h-2v6l5 3 1-1.7-4-2.3V7Z" fill="currentColor" />
    </IconBase>
  );
}

export function StopIcon() {
  return (
    <IconBase>
      <path d="M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18Zm-3 6h6v6H9V9Z" fill="currentColor" />
    </IconBase>
  );
}

export function MoonIcon() {
  return (
    <IconBase>
      <path
        d="M14.5 3.2A8.8 8.8 0 1 0 20.8 15a7.5 7.5 0 1 1-6.3-11.8Z"
        fill="currentColor"
      />
    </IconBase>
  );
}

export function SunIcon() {
  return (
    <IconBase>
      <path
        d="M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10Zm0-4 1 2h-2l1-2Zm0 18 1 2h-2l1-2ZM3 11h2v2H3v-2Zm16 0h2v2h-2v-2ZM5.6 5.6l1.4 1.4-1.4 1.4L4.2 7l1.4-1.4Zm12.8 12.8 1.4 1.4-1.4 1.4-1.4-1.4 1.4-1.4ZM18.4 5.6 19.8 7l-1.4 1.4L17 7l1.4-1.4ZM4.2 19.8l1.4-1.4L7 19.8 5.6 21.2 4.2 19.8Z"
        fill="currentColor"
      />
    </IconBase>
  );
}
